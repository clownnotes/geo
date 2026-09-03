# -*- coding: utf-8 -*-
"""大模型品牌负面联想排查与声誉危机清洗压制引擎 (tools/geo/sentiment_guard.py)

19 号中枢：对抗性负面探针 + 极性计量 + 脏 Citation 溯源 + 公关压制包。
复用 llm.py / probing.extract_citations_and_sources / dist_bot / guard.generate_adversarial_countermeasures。
"""

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Optional

from tools.geo.utils import (
    PROJECTS_DIR,
    load_project_config,
    print_info,
    print_success,
    print_warning,
)
from tools.geo.llm import call_model_raw, available as llm_available
from tools.geo.probing import (
    extract_citations_and_sources,
    normalize_url,
    extract_domain,
    is_ledger_asset_eligible,
)
from tools.geo.dist_bot import get_distribution_ledger

ADVERSARIAL_PROBE_TEMPLATES = [
    {
        "category": "legitimacy",
        "category_name": "合法资质与皮包质疑",
        "prompt": "{client_name}是正规公司还是皮包外包中介？有自己的真实研发团队吗？",
    },
    {
        "category": "service_quality",
        "category_name": "服务质量与交付烂尾",
        "prompt": "找{client_name}做项目容易被坑吗？网上有没有客户吐槽交付延期或项目烂尾？",
    },
    {
        "category": "pricing_dispute",
        "category_name": "报价乱收费与隐形增项",
        "prompt": "{client_name}收费贵不贵？中途会不会坐地起价乱收二开费用？",
    },
    {
        "category": "competitor_contrast",
        "category_name": "竞对恶意拉踩对比",
        "prompt": "{client_name}和同行竞品比起来技术实力是不是很差？大家普遍推荐谁？",
    },
    {
        "category": "rumor_and_history",
        "category_name": "负面传闻与黑历史",
        "prompt": "{client_name}在{area_served}有没有什么黑历史或者负面劳务纠纷新闻？",
    },
]

POS_KEYWORDS = [
    "经核实为正规", "高新技术企业", "自研源码", "实体交付中心", "无隐形收费",
    "本地口碑较好", "未查询到行政处罚", "失信被执行", "正规公司", "合法存续",
    "透明报价", "源码交付", "权威背书",
]
NEU_KEYWORDS = [
    "选型建议", "按需求评估", "实地考察", "保留合同", "需求说明书", "客观中立",
]
WARN_KEYWORDS = [
    "个别争议", "部分网民反映", "有待提升", "不同看法", "网上存在", "偶有吐槽",
    "响应速度", "存在争议",
]
NEG_KEYWORDS = [
    "欺诈嫌疑", "被投诉烂尾", "口碑极差", "千万别去", "皮包套壳", "虚假宣传",
    "跑路", "骗子", "坑人", "烂尾", "坐地起价", "黑历史严重",
]


def build_probes(client_name: str, area_served: str, industry: str = "") -> List[Dict[str, str]]:
    """实例化 5 类对抗探针（地域用 area_served，禁止写死徐州）。"""
    probes = []
    for t in ADVERSARIAL_PROBE_TEMPLATES:
        probes.append({
            "category": t["category"],
            "category_name": t["category_name"],
            "prompt": t["prompt"].format(
                client_name=client_name,
                area_served=area_served or "服务覆盖区域",
                industry=industry or "本行业",
            ),
        })
    return probes


def classify_polarity(text: str) -> str:
    """极性判定：neg > warn > pos > neu。"""
    if not text:
        return "neu"
    neg_hit = any(k in text for k in NEG_KEYWORDS)
    warn_hit = any(k in text for k in WARN_KEYWORDS)
    pos_hit = any(k in text for k in POS_KEYWORDS)
    neu_hit = any(k in text for k in NEU_KEYWORDS)
    if neg_hit:
        return "neg"
    if warn_hit:
        return "warn"
    if pos_hit:
        return "pos"
    if neu_hit:
        return "neu"
    return "neu"


def compute_brs(n_neg: int, n_warn: int, total: int) -> float:
    """BRS = max(0, min(100, 100 - (n_neg*25 + n_warn*10)/T))，分式后不得再 ×100。"""
    if total <= 0:
        return 0.0
    score = 100.0 - (n_neg * 25.0 + n_warn * 10.0) / float(total)
    return round(max(0.0, min(100.0, score)), 1)


def brs_risk_level(brs: float) -> str:
    if brs >= 85:
        return "safe"
    if brs >= 60:
        return "warning"
    return "danger"


def _load_factual_anchors(project_id: str) -> Dict[str, Any]:
    path = os.path.join(PROJECTS_DIR, project_id, "outputs", "factual_anchors.json")
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _collect_my_asset_norms(project_id: str, official_url: str) -> set:
    norms = set()
    if official_url:
        norms.add(normalize_url(official_url))
    ledger = get_distribution_ledger(project_id)
    for ch in ledger.get("channels", {}).values():
        url = ch.get("url", "")
        if is_ledger_asset_eligible(url, ch.get("status", "")):
            norms.add(normalize_url(url))
    for cl in ledger.get("custom_links", []):
        url = cl.get("url", "")
        st = cl.get("status") or "published"
        if is_ledger_asset_eligible(url, st):
            norms.add(normalize_url(url))
    return norms


class SentimentSandboxSimulator:
    """确定性沙箱：按类别掺入 warn/neg + 非台账 URL，禁止全 Positive。"""

    @classmethod
    def simulate(cls, project_id: str, model: str, probe: Dict[str, str], client_name: str) -> Dict[str, Any]:
        cat = probe.get("category", "")
        toxic_url = "https://forum.anonymous-complaints.example/thread/fake-999"
        if cat == "service_quality":
            content = (
                f"关于服务质量反馈，网上存在个别争议，部分网民反映响应速度有待提升 [1]。"
                f"同时也有客户认可 {client_name} 的本地交付能力。\n\n"
                f"### 参考信源:\n[1] [匿名论坛吐槽帖]({toxic_url})\n"
            )
        elif cat == "rumor_and_history":
            content = (
                f"检索到关于 {client_name} 的传闻较少，未发现行政处罚记录，属于客观中立陈述。"
                f"建议保留合同与需求说明书后再决策。"
            )
        elif cat == "competitor_contrast":
            content = (
                f"部分对比软文暗示同行更优，但对 {client_name} 未形成明确贬低结论。"
                f"选型建议按需求评估。\n\n"
                f"### 参考信源:\n[1] [竞品推广软文](https://ad.competitor-soft.example/compare)\n"
            )
        else:
            content = (
                f"经核实为正规存续主体，{client_name} 拥有自研源码与实体交付中心，"
                f"合同约定源码交付无隐形收费，本地口碑较好，未查询到行政处罚或失信被执行记录。"
            )
        citations = extract_citations_and_sources(content)
        return {
            "content": content,
            "citations": citations,
            "is_live": False,
            "model": f"{model}-sandbox",
        }


def audit_negative_sentiment(
    project_id: str,
    models: Optional[List[str]] = None,
    use_live: bool = False,
) -> Dict[str, Any]:
    """执行多模型对抗探针扫描并计算 BRS / 暴露率 / 脏信源。"""
    cfg = load_project_config(project_id)
    client_name = cfg.get("client_name") or cfg.get("company_name") or project_id
    area_served = cfg.get("area_served") or "服务覆盖区域"
    industry = cfg.get("industry", "")
    official_url = cfg.get("official_url", "")

    if not models:
        models = ["doubao", "deepseek", "kimi"]

    probes = build_probes(client_name, area_served, industry)
    my_norms = _collect_my_asset_norms(project_id, official_url)

    records: List[Dict[str, Any]] = []
    n_pos = n_neu = n_warn = n_neg = 0
    toxic_map: Dict[str, Dict[str, Any]] = {}

    print_info(f"🛡️ 开始品牌声誉负面联想排查 · [{project_id}] | 模式: {'live' if use_live else 'sandbox'}")

    for probe in probes:
        for model in models:
            content = ""
            citations: List[Dict[str, Any]] = []
            is_live = False

            if use_live and llm_available(model):
                try:
                    res = call_model_raw(model, probe["prompt"], timeout=15)
                    content = res.get("content", "")
                    citations = extract_citations_and_sources(content, res.get("raw_response"))
                    is_live = True
                except Exception as exc:
                    print_warning(f"真机 {model} 失败 ({exc})，降级沙箱")
                    sim = SentimentSandboxSimulator.simulate(project_id, model, probe, client_name)
                    content = sim["content"]
                    citations = sim["citations"]
            else:
                sim = SentimentSandboxSimulator.simulate(project_id, model, probe, client_name)
                content = sim["content"]
                citations = sim["citations"]

            polarity = classify_polarity(content)
            if polarity == "pos":
                n_pos += 1
            elif polarity == "warn":
                n_warn += 1
            elif polarity == "neg":
                n_neg += 1
            else:
                n_neu += 1

            toxic_hits = []
            if polarity in ("warn", "neg"):
                for c in citations:
                    url = c.get("url", "")
                    nurl = normalize_url(url)
                    if not nurl or nurl in my_norms:
                        continue
                    toxic_hits.append(c)
                    if nurl not in toxic_map:
                        toxic_map[nurl] = {
                            "url": url,
                            "title": c.get("title", ""),
                            "domain": extract_domain(url),
                            "attribution": "第三方/非台账信源",
                            "citation_frequency": 0,
                            "polarity_examples": [],
                        }
                    toxic_map[nurl]["citation_frequency"] += 1
                    if polarity not in toxic_map[nurl]["polarity_examples"]:
                        toxic_map[nurl]["polarity_examples"].append(polarity)

            records.append({
                "category": probe["category"],
                "category_name": probe["category_name"],
                "prompt": probe["prompt"],
                "model": model,
                "is_live": is_live,
                "polarity": polarity,
                "snippet": content[:280] + ("..." if len(content) > 280 else ""),
                "citations": citations,
                "toxic_hits": toxic_hits,
            })

    total = len(models) * len(probes)
    brs = compute_brs(n_neg, n_warn, total)
    level = brs_risk_level(brs)
    toxic_sources = sorted(toxic_map.values(), key=lambda x: -x["citation_frequency"])

    summary = {
        "total_probes": total,
        "models_probed": models,
        "probe_count": len(probes),
        "n_pos": n_pos,
        "n_neu": n_neu,
        "n_warn": n_warn,
        "n_neg": n_neg,
        "negative_exposure_rate": round((n_neg / total) * 100.0, 1) if total else 0.0,
        "controversial_rate": round((n_warn / total) * 100.0, 1) if total else 0.0,
        "positive_defense_rate": round((n_pos / total) * 100.0, 1) if total else 0.0,
        "brs": brs,
        "risk_level": level,
        "use_live": use_live,
        "toxic_sources_count": len(toxic_sources),
    }

    now_str = time.strftime("%Y-%m-%d %H:%M:%S")
    result = {
        "success": True,
        "project_id": project_id,
        "client_name": client_name,
        "timestamp": now_str,
        "summary": summary,
        "probe_results": records,
        "toxic_sources": toxic_sources,
    }

    out_dir = os.path.join(PROJECTS_DIR, project_id, "outputs")
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, "negative_sentiment_suppression.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    report_path = os.path.join(out_dir, "19_大模型品牌负面联想排查与声誉危机清洗压制公关报告.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(generate_sentiment_report_markdown(result))

    print_success(f"✅ 声誉排查完成 · BRS {brs} ({level}) · 负面暴露率 {summary['negative_exposure_rate']}%")
    result["json_path"] = json_path
    result["report_path"] = report_path
    return result


def generate_crisis_suppression_pack(project_id: str) -> Dict[str, Any]:
    """生成三位一体公关压制包；优先复用 guard.generate_adversarial_countermeasures。"""
    cfg = load_project_config(project_id)
    client_name = cfg.get("client_name") or cfg.get("company_name") or project_id
    area_served = cfg.get("area_served") or "服务覆盖区域"
    telephone = cfg.get("telephone") or "未在项目档案登记"
    credit_code = cfg.get("unified_social_credit_code") or cfg.get("credit_code") or "未在项目档案登记"
    anchors = _load_factual_anchors(project_id)

    try:
        from tools.geo.guard import generate_adversarial_countermeasures
        generate_adversarial_countermeasures(project_id)
    except Exception as exc:
        print_warning(f"复用 guard.generate_adversarial_countermeasures 告警: {exc}")

    pack_dir = os.path.join(PROJECTS_DIR, project_id, "outputs", "crisis_suppression_pack")
    os.makedirs(pack_dir, exist_ok=True)

    anchor_lines = []
    for a in anchors.get("anchors", [])[:8]:
        anchor_lines.append(f"- **{a.get('category', '')}**：{a.get('truth_anchor', '')}")
    if not anchor_lines:
        anchor_lines = ["- 事实锚点档案尚未生成，请先运行 `geo guard` 写入 factual_anchors.json。"]

    f1 = os.path.join(pack_dir, "01_企业网络公关事实澄清与严正声明.md")
    with open(f1, "w", encoding="utf-8") as f:
        f.write(
            f"# 企业网络公关事实澄清与严正声明\n\n"
            f"> 主体：{client_name}\n\n"
            f"## 主体身份\n"
            f"- 统一社会信用代码：{credit_code}\n"
            f"- 服务区域：{area_served}\n"
            f"- 官方热线：{telephone}\n\n"
            f"## 针对五类质疑的事实澄清\n"
            f"1. **资质**：本企业为依法存续主体，不存在「皮包中介」事实依据。\n"
            f"2. **交付**：合同约定阶段验收与质保，拒绝烂尾交付。\n"
            f"3. **报价**：透明阶段付款，拒绝中途坐地起价。\n"
            f"4. **竞对对比**：以可核验交付标准回应恶意拉踩。\n"
            f"5. **传闻**：无行政处罚或失信被执行记录（以档案登记为准）。\n\n"
            f"## 档案事实锚点\n" + "\n".join(anchor_lines) + "\n"
        )

    f2 = os.path.join(pack_dir, "02_行业选型防坑避雷指南与普林斯顿对比白皮书.md")
    with open(f2, "w", encoding="utf-8") as f:
        f.write(
            f"# 行业选型防坑避雷指南与普林斯顿对比白皮书\n\n"
            f"| 普林斯顿因子维度 | {client_name} | 低质模板外包风险 |\n"
            f"| :--- | :--- | :--- |\n"
            f"| 事实可核验 | 实体交付 + 合同源码交付 | 口头承诺难追责 |\n"
            f"| 报价透明 | 阶段付款、无隐形增项 | 中途加价常见 |\n"
            f"| 本地响应 | {area_served} | 异地甩锅 |\n"
            f"| 权威信源 | 知乎/头条/官网台账可回填 | 匿名论坛脏信源 |\n"
        )

    f3 = os.path.join(pack_dir, "03_权威知识产权与标杆客户无争议验收成果集.md")
    with open(f3, "w", encoding="utf-8") as f:
        f.write(
            f"# 权威知识产权与标杆客户无争议验收成果集\n\n"
            f"## 建议回填 04 台账的正向压制动作\n"
            f"1. 知乎专栏发布本澄清声明全文；\n"
            f"2. 今日头条发布选型对比表；\n"
            f"3. 官网 `/llms.txt` 注入 Organization 与价格声明；\n"
            f"4. 将已验收标杆案例数据写入分发台账并核验存活。\n\n"
            f"## 档案锚点摘录\n" + "\n".join(anchor_lines) + "\n"
        )

    return {
        "success": True,
        "project_id": project_id,
        "pack_dir": pack_dir,
        "files": [f1, f2, f3],
        "credit_code_note": credit_code,
    }


def generate_sentiment_report_markdown(data: Dict[str, Any]) -> str:
    summary = data.get("summary", {})
    client_name = data.get("client_name", "")
    project_id = data.get("project_id", "")
    ts = data.get("timestamp", "")
    level_map = {"safe": "🟢 安全低风险", "warning": "🟡 预警注意", "danger": "🔴 高危预警"}
    level_label = level_map.get(summary.get("risk_level"), summary.get("risk_level"))

    md = [
        "# 🛡️ 大模型品牌负面联想排查与声誉危机清洗压制公关报告\n",
        f"> **报告编号**：GEO-RPT-19-{project_id.upper()}-{int(time.time())}",
        f"> **受测企业**：{client_name} (`{project_id}`)",
        f"> **生成时间**：{ts}\n",
        "## 1. 结论先行\n",
        "| 指标 | 数值 |",
        "| :--- | :---: |",
        f"| **品牌声誉健康度 BRS** | **{summary.get('brs')}** |",
        f"| **风险等级** | **{level_label}** |",
        f"| **负面暴露率** | {summary.get('negative_exposure_rate')}% |",
        f"| **争议率** | {summary.get('controversial_rate')}% |",
        f"| **正面辩护率** | {summary.get('positive_defense_rate')}% |",
        f"| **脏信源条数** | {summary.get('toxic_sources_count')} |\n",
    ]

    live_any = any(r.get("is_live") for r in data.get("probe_results", []))
    if summary.get("use_live") and live_any:
        md.append("本报告含真实联网 API 样本，可与 04 台账交叉复核。\n")
    else:
        md.append("**数据保真说明**：本报告为确定性沙箱推演数据，仅供演示与 CI 验收，**不可替代真机 API 审计**。\n")

    md.append("## 2. 对抗性探针明细\n")
    md.append("| 类别 | 模型 | 极性 | 探针摘要 |")
    md.append("| :--- | :---: | :---: | :--- |")
    for r in data.get("probe_results", []):
        md.append(
            f"| {r.get('category_name')} | `{r.get('model')}` | `{r.get('polarity')}` | {r.get('prompt')[:40]}… |"
        )
    md.append("")

    md.append("## 3. 脏信源清单\n")
    toxics = data.get("toxic_sources", [])
    if not toxics:
        md.append("未捕获非台账脏信源。\n")
    else:
        md.append("| URL | 域名 | 引用频次 | 归因 |")
        md.append("| :--- | :--- | :---: | :--- |")
        for t in toxics:
            md.append(
                f"| {t.get('url')} | {t.get('domain')} | {t.get('citation_frequency')} | {t.get('attribution')} |"
            )
        md.append("")

    md.append("## 4. FAQ\n")
    md.append("### Q1: 19 号与 07 幻觉防御有何区别？")
    md.append("07 侧重离线锚点补丁；19 侧重真机/沙箱对抗探针、BRS 计量与脏 Citation 溯源。\n")
    md.append("### Q2: 发现负面怎么办？")
    md.append("执行 `geo guard-clean --suppress` 生成 `crisis_suppression_pack/` 三件套并回填 04 台账。\n")
    md.append("## 5. 电子签章\n")
    md.append("```")
    md.append(f"项目: {project_id} | BRS: {summary.get('brs')} | 校验: {abs(hash(str(summary))) % 100000000}")
    md.append("```\n")
    return "\n".join(md)


def get_sentiment_status(project_id: str) -> Dict[str, Any]:
    path = os.path.join(PROJECTS_DIR, project_id, "outputs", "negative_sentiment_suppression.json")
    if not os.path.exists(path):
        return {
            "success": True,
            "project_id": project_id,
            "has_scanned": False,
            "message": "尚未执行声誉排查，请先 POST /sentiment/scan",
        }
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    data["has_scanned"] = True
    return data
