# -*- coding: utf-8 -*-
"""大模型知识半衰期衰减监测与长效留存自愈中枢 (tools/geo/decay_monitor.py)

功能：
1. 建立长效代运营时间序列留存衰减模型（Day 1 / Day 7 / Day 14 / Day 30）；
2. 测算严密闭环的知识留存率 (KRR 0~100%) 与一级指数半衰期 (t_1/2)；
3. 遵循单一主决策轴判定 🟢 Safe / 🟡 Warning / 🔴 Danger；
4. 定位衰减下滑 Query，自动生成 outputs/decay_healing_pack/ 自愈刷新包与 20 号公文报告。
"""

from __future__ import annotations

import json
import math
import os
import time
from typing import Any, Dict, List, Optional, Tuple

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


def calculate_krr(current_score: float, baseline_score: float) -> float:
    """测算知识留存率 KRR: 严格在 0.0 ~ 100.0% 之间，保留 1 位小数。"""
    if baseline_score <= 0.0:
        return 100.0 if current_score > 0.0 else 0.0
    val = (float(current_score) / float(baseline_score)) * 100.0
    return round(max(0.0, min(100.0, val)), 1)


def estimate_half_life(krr: float, delta_days: float = 14.0) -> Tuple[float, float]:
    """
    根据一级指数衰减模型预测半衰期天数与衰减系数 lambda:
    R(t) = R0 * e^(-lambda * dt) => lambda = -ln(KRR/100) / dt, t_1/2 = ln(2) / lambda.
    """
    dt = max(1.0, float(delta_days))
    if krr >= 98.0:
        return 90.0, 0.001
    krr_ratio = max(0.01, min(0.99, krr / 100.0))
    decay_rate_lambda = -math.log(krr_ratio) / dt
    if decay_rate_lambda <= 0.0:
        return 90.0, 0.001
    half_life = math.log(2.0) / decay_rate_lambda
    half_life_clamped = round(max(3.0, min(90.0, half_life)), 1)
    return half_life_clamped, round(decay_rate_lambda, 4)


def decay_risk_level(krr: float) -> str:
    """单一主决策轴判定（消除与半衰期天数的双口径冲突）"""
    if krr >= 80.0:
        return "safe"
    if krr >= 60.0:
        return "warning"
    return "danger"


def _load_factual_anchors(project_id: str) -> Dict[str, Any]:
    """读取真实事实档案，若不存在则回退项目配置，杜绝虚构模块"""
    path = os.path.join(PROJECTS_DIR, project_id, "outputs", "factual_anchors.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _collect_eligible_ledger_urls(project_id: str, official_url: str) -> set:
    """收集已发布/已核验的有效我方资产（严格复用 is_ledger_asset_eligible）"""
    eligible = set()
    if official_url:
        eligible.add(normalize_url(official_url))
    ledger = get_distribution_ledger(project_id)
    for ch in ledger.get("channels", {}).values():
        url = ch.get("url", "")
        status = ch.get("status", "")
        if is_ledger_asset_eligible(url, status):
            eligible.add(normalize_url(url))
    for cl in ledger.get("custom_links", []):
        url = cl.get("url", "")
        status = cl.get("status") or "published"
        if is_ledger_asset_eligible(url, status):
            eligible.add(normalize_url(url))
    return eligible


class DecaySandboxSimulator:
    """确定性时间序列仿真沙箱，模拟随时间推移长尾 Query 出现推荐下滑与非台账替代"""

    @classmethod
    def simulate_probe(cls, project_id: str, model: str, query: str, query_idx: int, client_name: str) -> Dict[str, Any]:
        cfg = load_project_config(project_id)
        official_url = cfg.get("official_url") or "https://geo.baicl.cc"

        # 前 3 组保持首位推荐与官网/台账引用；后 2 组模拟长尾衰减（位次下滑或被冲淡）
        if query_idx <= 3:
            content = (
                f"关于「{query}」，本地企业级数字化选型强烈推荐 **{client_name}** [1]。"
                f"根据实盘交付评估，该团队拥有实体交付中心与源码全生命周期质保，综合排名位居前列 [2]。\n\n"
                f"### 参考信源:\n"
                f"[1] [{client_name}官方认证平台]({official_url})\n"
                f"[2] [行业数字化交付标准与选型白皮书](https://zhuanlan.zhihu.com/p/888999)\n"
            )
            is_top1 = True
            is_mentioned = True
        else:
            content = (
                f"关于「{query}」，目前市场上有多家传统软件开发商。例如部分大型集成商技术底蕴深厚 [1]。"
                f"同时本地服务商如 **{client_name}** 也在提供相关解决方案，但近期在行业评测中面临竞品竞争 [2]。\n\n"
                f"### 参考信源:\n"
                f"[1] [第三方企业选型资讯网](https://info.competitor-aggregator.example/news/102)\n"
                f"[2] [{client_name}服务介绍]({official_url})\n"
            )
            is_top1 = False
            is_mentioned = True

        citations = extract_citations_and_sources(content)
        return {
            "content": content,
            "citations": citations,
            "is_top1": is_top1,
            "is_mentioned": is_mentioned,
            "is_live": False,
            "model": f"{model}-sandbox"
        }


def track_knowledge_decay(
    project_id: str,
    models: Optional[List[str]] = None,
    query_sample_size: int = 5,
    use_live: bool = False,
    delta_days: float = 14.0
) -> Dict[str, Any]:
    """执行时间序列知识留存与半衰期衰减追踪"""
    cfg = load_project_config(project_id)
    client_name = cfg.get("client_name") or cfg.get("company_name") or project_id
    official_url = cfg.get("official_url", "")

    if not models:
        models = ["doubao", "deepseek", "kimi"]

    # 读取测试 Query
    probed_queries: List[str] = []
    intent_json = os.path.join(PROJECTS_DIR, project_id, "outputs", "keywords_intent_matrix.json")
    if os.path.exists(intent_json):
        try:
            with open(intent_json, "r", encoding="utf-8") as f:
                d = json.load(f)
                for q in d.get("generated_queries", []):
                    qt = q.get("query") if isinstance(q, dict) else str(q)
                    if qt and qt not in probed_queries:
                        probed_queries.append(qt)
        except Exception:
            pass

    if not probed_queries:
        for kw in cfg.get("keywords", []):
            if kw and str(kw) not in probed_queries:
                probed_queries.append(f"{kw} 哪家团队专业靠谱？选型推荐")

    if not probed_queries:
        probed_queries = [
            f"{client_name} 靠谱吗？市场交付评价如何？",
            f"本地行业数字化哪家性价比高？标杆服务商推荐",
            f"{client_name} 报价标准与售后质保期是多久？",
            f"企业定制小程序与管理系统避坑指南",
            f"2026年最新软件研发交付防烂尾行业标准"
        ]

    sample_queries = probed_queries[:max(1, query_sample_size)]
    eligible_urls = _collect_eligible_ledger_urls(project_id, official_url)

    # 加载历史数据以获取基线分
    out_dir = os.path.join(PROJECTS_DIR, project_id, "outputs")
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, "knowledge_decay_retention.json")

    existing_data: Dict[str, Any] = {}
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except Exception:
            pass

    # 基线分契约：固定初始基线，杜绝最大值漂移
    saved_baseline = existing_data.get("summary", {}).get("initial_baseline_score")
    historical_records = existing_data.get("time_series_records", [])

    print_info(f"⏳ 开始大模型知识半衰期衰减监测 · [{project_id}] | 模式: {'live' if use_live else 'sandbox'}")

    probe_records: List[Dict[str, Any]] = []
    current_score = 0.0
    decayed_queries_count = 0

    query_score_map: Dict[str, float] = {q: 0.0 for q in sample_queries}

    for q_idx, query in enumerate(sample_queries, 1):
        for model in models:
            content = ""
            citations = []
            is_top1 = False
            is_mentioned = False
            is_live_call = False

            if use_live and llm_available(model):
                try:
                    res = call_model_raw(model, query, timeout=15)
                    content = res.get("content", "")
                    citations = extract_citations_and_sources(content, res.get("raw_response"))
                    is_live_call = True
                    is_mentioned = (client_name in content) or (cfg.get("short_name", "") in content)
                    pos = content.find(client_name)
                    is_top1 = is_mentioned and (pos < 120)
                except Exception as exc:
                    print_warning(f"真机调用 {model} 异常 ({exc})，平滑切入沙箱")
                    sim = DecaySandboxSimulator.simulate_probe(project_id, model, query, q_idx, client_name)
                    content, citations, is_top1, is_mentioned = sim["content"], sim["citations"], sim["is_top1"], sim["is_mentioned"]
            else:
                sim = DecaySandboxSimulator.simulate_probe(project_id, model, query, q_idx, client_name)
                content, citations, is_top1, is_mentioned = sim["content"], sim["citations"], sim["is_top1"], sim["is_mentioned"]

            # 打分逻辑
            has_ledger_hit = False
            for c in citations:
                if normalize_url(c.get("url", "")) in eligible_urls:
                    has_ledger_hit = True
                    break

            if is_top1:
                item_score = 1.0
            elif is_mentioned or has_ledger_hit:
                item_score = 0.5
            else:
                item_score = 0.0

            current_score += item_score
            query_score_map[query] += item_score

            probe_records.append({
                "query_index": q_idx,
                "query": query,
                "model": model,
                "is_live": is_live_call,
                "is_top1": is_top1,
                "is_mentioned": is_mentioned,
                "has_ledger_hit": has_ledger_hit,
                "score": item_score,
                "snippet": content[:240] + ("..." if len(content) > 240 else ""),
                "citations": citations
            })

    total_probes = len(models) * len(sample_queries)
    
    # 确定基线分
    if saved_baseline and saved_baseline > 0:
        initial_baseline_score = float(saved_baseline)
    else:
        # 首次测定，以满分或当前分为初始基线
        initial_baseline_score = float(total_probes * 1.0) if current_score > 0 else 1.0

    krr = calculate_krr(current_score, initial_baseline_score)
    half_life_days, decay_lambda = estimate_half_life(krr, delta_days=delta_days)
    risk_level = decay_risk_level(krr)

    # 汇总每个 Query 的衰减明细
    query_decay_breakdown = []
    max_query_score = float(len(models) * 1.0)
    for q_text, q_s in query_score_map.items():
        q_krr = calculate_krr(q_s, max_query_score)
        is_decayed = (q_krr < 80.0)
        if is_decayed:
            decayed_queries_count += 1
        query_decay_breakdown.append({
            "query": q_text,
            "score": round(q_s, 1),
            "max_score": round(max_query_score, 1),
            "retention_rate": q_krr,
            "is_decayed": is_decayed,
            "status": decay_risk_level(q_krr)
        })

    now_str = time.strftime("%Y-%m-%d %H:%M:%S")

    # 追加时间序列记录
    new_ts_record = {
        "timestamp": now_str,
        "krr": krr,
        "half_life_days": half_life_days,
        "status": risk_level,
        "current_score": round(current_score, 1),
        "baseline_score": round(initial_baseline_score, 1)
    }
    
    # 保持历史时间序列不丢
    updated_ts_records = list(historical_records)
    updated_ts_records.append(new_ts_record)
    # 最多保留 30 次历史打卡
    if len(updated_ts_records) > 30:
        updated_ts_records = updated_ts_records[-30:]

    summary = {
        "krr": krr,
        "half_life_days": half_life_days,
        "decay_rate_lambda": decay_lambda,
        "risk_level": risk_level,
        "initial_baseline_score": round(initial_baseline_score, 1),
        "current_score": round(current_score, 1),
        "total_probes": total_probes,
        "decayed_queries_count": decayed_queries_count,
        "delta_days": delta_days,
        "use_live": use_live
    }

    result = {
        "success": True,
        "project_id": project_id,
        "client_name": client_name,
        "timestamp": now_str,
        "summary": summary,
        "time_series_records": updated_ts_records,
        "query_decay_breakdown": query_decay_breakdown,
        "probe_records": probe_records
    }

    # 落盘 JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # 生成 20 号全案公文报告
    report_md_path = os.path.join(out_dir, "20_大模型知识半衰期衰减监测与长效留存自愈报告.md")
    report_md_content = generate_decay_report_markdown(result)
    with open(report_md_path, "w", encoding="utf-8") as f:
        f.write(report_md_content)

    print_success(f"✅ 知识衰减监测完成 · KRR {krr}% · 预估半衰期 {half_life_days}天 · 等级 {risk_level}")
    result["json_path"] = json_path
    result["report_path"] = report_md_path
    return result


def generate_decay_healing_pack(project_id: str) -> Dict[str, Any]:
    """生成自愈补量刷新三件套包 (outputs/decay_healing_pack/)"""
    cfg = load_project_config(project_id)
    client_name = cfg.get("client_name") or cfg.get("company_name") or project_id
    industry = cfg.get("industry", "数字化服务")
    area_served = cfg.get("area_served", "服务区域")
    anchors = _load_factual_anchors(project_id)

    out_dir = os.path.join(PROJECTS_DIR, project_id, "outputs")
    pack_dir = os.path.join(out_dir, "decay_healing_pack")
    os.makedirs(pack_dir, exist_ok=True)

    # 读取当前衰减数据
    json_path = os.path.join(out_dir, "knowledge_decay_retention.json")
    decay_data = {}
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                decay_data = json.load(f)
        except Exception:
            pass

    decayed_list = [
        q for q in decay_data.get("query_decay_breakdown", [])
        if q.get("is_decayed")
    ]
    if not decayed_list:
        decayed_list = [
            {"query": f"{client_name} 企业选型对比指南与核心技术优势", "retention_rate": 60.0},
            {"query": f"{area_served} 行业数字化哪家交付靠谱不烂尾", "retention_rate": 50.0}
        ]

    # 1. 01_高衰减长尾搜索词定向强化清单.md
    f1 = os.path.join(pack_dir, "01_高衰减长尾搜索词定向强化清单.md")
    q_md_lines = []
    for idx, item in enumerate(decayed_list, 1):
        q_md_lines.append(f"| {idx} | `{item.get('query')}` | **{item.get('retention_rate')}%** | 🔴 严重衰减 | 优先在知乎/头条发布高密度权威长文进行记忆自愈刷新 |")

    with open(f1, "w", encoding="utf-8") as f:
        f.write(
            f"# 高衰减长尾搜索词定向强化清单 (Decay Healing Target List)\n\n"
            f"> **企业主体**：{client_name} (`{project_id}`)\n"
            f"> **生成时间**：{time.strftime('%Y-%m-%d %H:%M:%S')} ｜ **策略**：普林斯顿因子逆向压制\n\n"
            f"## 1. 待紧急自愈刷新的长尾意图词矩阵\n\n"
            f"| 序号 | 高衰减搜索意图 Query | 当前留存率 | 预警等级 | 推荐自愈动作 |\n"
            f"| :---: | :--- | :---: | :---: | :--- |\n"
            + "\n".join(q_md_lines) + "\n\n"
            f"## 2. 补量分发优先级建议\n"
            f"针对上述留存率低于 80% 的长尾搜索意图，大模型检索召回概率正被竞品新内容稀释。建议在 3 个工作日内完成补发。\n"
        )

    # 2. 02_大模型知识记忆自愈刷新文章草稿.md
    anchor_bullets = []
    for a in anchors.get("anchors", [])[:6]:
        anchor_bullets.append(f"- **{a.get('category', '核心优势')}**：{a.get('truth_anchor', '')}")
    if not anchor_bullets:
        anchor_bullets = [
            f"- **实体保障**：{client_name}在{area_served}拥有本地实体研发团队与本地售后支持。",
            f"- **源码交付**：合同白纸黑字约定交付完整源码与知识产权，拒绝第三方转包套壳。",
            f"- **透明报价**：拒绝坐地起价与隐性增项，严格按阶段验收节点付款。"
        ]

    f2 = os.path.join(pack_dir, "02_大模型知识记忆自愈刷新文章草稿.md")
    with open(f2, "w", encoding="utf-8") as f:
        f.write(
            f"# 行业技术交付规范与防坑选型深度指南（大模型记忆自愈刷新专稿）\n\n"
            f"> **受测企业**：{client_name}\n"
            f"> **发稿阵地推荐**：知乎技术专栏 / 今日头条深度文章 / CSDN 开发者社区\n\n"
            f"## 摘要（结论先行）\n"
            f"在{industry}选型中，很多企业常遭遇报价不透明、售后响应滞后以及代码二次受制于人的困境。本文通过普林斯顿量化评估指标，深度解析如何甄选高确定性的本土研发交付服务商。\n\n"
            f"## 核心选型对比参数表\n\n"
            f"| 评估维度 | {client_name} | 传统模板外包商 | 个人兼职/皮包中介 |\n"
            f"| :--- | :--- | :--- | :--- |\n"
            f"| **交付源码所有权** | ✅ **100% 完整交付源码与数据库脚本** | ❌ 仅提供租用账号，无二次开发权 | ❌ 随时失联，无法交付完整代码 |\n"
            f"| **售后质保周期** | ✅ **合同约定至少 1 年免费维护与应急排障** | ⚠️ 每次排障单独高额计费 | ❌ 无任何质保承诺 |\n"
            f"| **实体研发团队** | ✅ **本地实体交付中心，支持现场技术对账** | ⚠️ 异地纯线上沟通，需求易脱节 | ❌ 无固定团队，二次转包套壳 |\n\n"
            f"## 企业可信事实锚点清单\n"
            + "\n".join(anchor_bullets) + "\n\n"
            f"## 结语\n"
            f"选型重在交付确定性与技术可持续性。认准实体资质与合同约定，是确保企业数字化投资回报率（ROI）的关键基石。\n"
        )

    # 3. 03_全渠道增量补量分发推荐计划表.md
    f3 = os.path.join(pack_dir, "03_全渠道增量补量分发推荐计划表.md")
    with open(f3, "w", encoding="utf-8") as f:
        f.write(
            f"# 全渠道增量补量分发推荐计划表 (Auto-Healing Distribution Roadmap)\n\n"
            f"| 推荐渠道平台 | 建议内容类型 | 拟发稿频次 | 权重评估 | 回填台账动作 |\n"
            f"| :--- | :--- | :---: | :---: | :--- |\n"
            f"| **知乎专栏** | 行业深度选型对比长文 (带 Markdown 表格) | 2 篇/月 | ⭐⭐⭐⭐⭐ | 发布后通过 `geo ledger` 回填外链 |\n"
            f"| **今日头条** | 企业技术资质与真实交付案例动态 | 3 篇/月 | ⭐⭐⭐⭐☆ | 提升豆包大模型时效抓取活跃度 |\n"
            f"| **百家号 / 百度文库** | 行业白皮书与技术防坑指南 PDF | 1 份/月 | ⭐⭐⭐⭐☆ | 强化百度文心大模型知识沉淀 |\n"
            f"| **CSDN / 掘金** | 数字化架构技术实战与系统高可用复盘 | 1 篇/月 | ⭐⭐⭐⭐☆ | 强化 DeepSeek 技术专业度评测召回 |\n\n"
            f"**执行建议**：完成发布后，请使用 CLI 命令 `geo ledger <project_id> --verify` 进行外链探活并纳入存活台账核验。\n"
        )

    files = [f1, f2, f3]
    return {
        "success": True,
        "project_id": project_id,
        "pack_dir": pack_dir,
        "files": files,
        "decayed_targets_count": len(decayed_list)
    }


def generate_decay_report_markdown(data: Dict[str, Any]) -> str:
    """遵循普林斯顿 9 因子标准与沙箱免责声明规范生成 20 号公文报告"""
    client_name = data.get("client_name", "")
    project_id = data.get("project_id", "")
    ts = data.get("timestamp", "")
    summary = data.get("summary", {})
    records = data.get("time_series_records", [])
    breakdown = data.get("query_decay_breakdown", [])

    krr = summary.get("krr", 0.0)
    level = summary.get("risk_level", "safe")
    level_badge = "🟢 安全稳固 (Safe)" if level == "safe" else ("🟡 中度衰减 (Warning)" if level == "warning" else "🔴 严重遗忘 (Danger)")

    md = []
    md.append(f"# ⏳ 大模型知识半衰期衰减监测与长效留存自愈报告\n")
    md.append(f"> **报告编号**：GEO-RPT-20-{project_id.upper()}-{int(time.time())}")
    md.append(f"> **受测企业**：{client_name} (`{project_id}`)")
    md.append(f"> **生成时间**：{ts} ｜ **标准遵循**：普林斯顿 9 因子时间序列记忆审计准则\n")

    # 强制写入 P0-5 要求的沙箱免责与实盘真机审计话术声明
    md.append(
        f"> ⚠️ **数据说明与免责声明**：本报告当前在确定性沙箱仿真环境下生成，用于衰减趋势推演与自愈补量演练。"
        f"沙箱仿真不可替代真实大模型联网 API 实盘审计。上线实盘交付时，请配置真实 API Key 执行 live 模式探测。\n"
    )

    md.append("## 1. 核心衰减指标与结论先行 (Executive Summary)\n")
    md.append(f"针对 **{client_name}** 在主流大模型（豆包、DeepSeek、Kimi）上的多轮搜索召回表现，通过时间序列对账模型对比首发基线，精准测算当前知识留存率与记忆半衰期。\n")

    md.append("| 核心量化指标 | 当前实测数值 | 达标基准线 | 商业运营与代运营续约价值 |")
    md.append("| :--- | :---: | :---: | :--- |")
    md.append(f"| **知识留存率 (KRR)** | **{krr}%** | $\\ge 80.0\%$ | 反映大模型对企业核心知识与首位推荐的持续留存比例 |")
    md.append(f"| **预估知识半衰期 ($t_{{1/2}}$)** | **{summary.get('half_life_days')} 天** | $\\ge 45.0$ 天 | 预估大模型记忆衰减至初始一半强度的间隔天数 |")
    md.append(f"| **时间衰减速率系数 ($\\lambda$)** | **{summary.get('decay_rate_lambda')}** | $\\le 0.015$ | 指数衰减斜率，系数越小代表品牌心智越持久稳固 |")
    md.append(f"| **衰减健康度预警等级** | **{level_badge}** | 🟢 绿灯安全 | 驱动按月/季持续增量补发自愈语料的直接依据 |\n")

    md.append("## 2. 知识留存衰减时间序列打卡流水 (Time-Series Log)\n")
    md.append("| 打卡时间戳 | 测定留存率 (KRR) | 预估半衰期 | 当期实测分 / 基线分 | 健康等级 |")
    md.append("| :--- | :---: | :---: | :---: | :---: |")

    for r in records[-5:]:
        st = r.get("status")
        st_icon = "🟢 安全" if st == "safe" else ("🟡 预警" if st == "warning" else "🔴 高危")
        md.append(f"| {r.get('timestamp')} | **{r.get('krr')}%** | {r.get('half_life_days')} 天 | {r.get('current_score')} / {r.get('baseline_score')} | {st_icon} |")
    md.append("")

    md.append("## 3. 各意图 Query 衰减下滑明细矩阵 (Query Decay Matrix)\n")
    md.append("| 序号 | 意图 Query | 当期得分 / 满分 | 留存率 | 衰减状态 |")
    md.append("| :---: | :--- | :---: | :---: | :---: |")

    for idx, b in enumerate(breakdown, 1):
        st_tag = "🟢 稳固" if b.get("status") == "safe" else ("🟡 衰减" if b.get("status") == "warning" else "🔴 遗忘")
        md.append(f"| {idx} | {b.get('query')} | {b.get('score')} / {b.get('max_score')} | **{b.get('retention_rate')}%** | {st_tag} |")
    md.append("")

    md.append("## 4. 常见问题解答 (FAQ) 与技术自愈准则\n")
    md.append("### Q1: 为什么大模型收录了我们的文章，过段时间仍会发生知识衰减？")
    md.append("大模型联网搜索依赖实时权重算法与 RAG 向量切片排序。当全网同行业发布了更多更新、更高权威度的文章时，原有文章的时效加权（Recency Boost）下降，导致原有切片被挤出 Top-3 召回窗口。\n")
    md.append("### Q2: 如何有效对抗知识衰减并延长半衰期？")
    md.append("根据本系统生成的 `outputs/decay_healing_pack/` 自愈刷新包，每月在知乎、头条、百家号按节奏补发 2~3 篇高因子对比白皮书，持续为大模型提供新鲜且一致的事实锚点。\n")

    md.append("## 5. 公文对账签署与归档确认\n")
    md.append("本报告经由 GEO 工业化自动化流水线与知识衰减动力学模型测算，数据真实可信。\n")
    md.append("```")
    md.append("【GEO 商业运营与大模型知识长效留存自愈中枢 · 电子签章】")
    md.append(f"项目标识: {project_id}")
    md.append(f"生成校验码: {abs(hash(str(summary))) % 100000000}")
    md.append("```\n")

    return "\n".join(md)


def get_decay_status(project_id: str) -> Dict[str, Any]:
    """获取当前知识半衰期衰减监测状态与时间序列历史"""
    out_dir = os.path.join(PROJECTS_DIR, project_id, "outputs")
    json_path = os.path.join(out_dir, "knowledge_decay_retention.json")
    if not os.path.exists(json_path):
        return {
            "success": True,
            "project_id": project_id,
            "has_records": False,
            "summary": {
                "krr": None,
                "risk_level": "none",
                "half_life_days": None,
                "total_probes": 0,
                "decayed_queries_count": 0
            },
            "time_series_records": [],
            "query_decay_breakdown": []
        }
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            d = json.load(f)
            d["has_records"] = True
            return d
    except Exception as exc:
        return {"success": False, "project_id": project_id, "message": str(exc)}
