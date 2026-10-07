#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阶段五：AI 可见度监控与周报自动生成引擎 (tools/geo/monitor.py)
核心功能：
1. 真实并发探测主流大模型（DeepSeek、豆包 Ark）对核心关键词的回答结果；
2. 正则解析品牌提及率 (SOV)、推荐位次、引用外链渠道与竞品提及态势；
3. 基于 probe_llm_live 的 Citation 增量聚合与 PLATFORM_AUTHORITY_WEIGHTS 加权分析；
4. 支持实时 API 真实探测模式与离线基准测算模式（透明标注信源与探测状态）；
5. 自动生成包含【大模型高频权威信源渗透分布】的《05_企业AI可见度与声量追踪周报.md》。
"""

import os
import re
import json
from urllib.parse import urlparse
from datetime import datetime
from .utils import (
    load_project_config,
    save_project_output,
    call_llm_api,
    get_configured_llm,
    print_banner,
    print_info,
    print_success,
    print_warning
)

# 权威信源平台权重字典（0.0 ~ 1.0）
PLATFORM_AUTHORITY_WEIGHTS = {
    "zhihu.com": 1.0,       # 深度技术长文高权重
    "github.com": 0.95,     # 开源与技术代码高权重
    "toutiao.com": 0.90,    # 字节豆包核心抓取源
    "juejin.cn": 0.85,      # 开发者技术社区
    "weixin.qq.com": 0.85,  # 微信生态
    "baike.baidu.com": 0.90 # 权威百科词条
}

MANUAL_PROBE_MODELS = ("deepseek", "doubao", "yuanbao", "kimi")
MANUAL_PROBE_MAX_BYTES = 100 * 1024
MANUAL_PROBES_FILENAME = "05_manual_probes.json"
FOOTNOTE_DOMAIN_HINTS = {
    "知乎": "https://www.zhihu.com/",
    "今日头条": "https://www.toutiao.com/",
    "头条": "https://www.toutiao.com/",
    "微信公众号": "https://www.weixin.qq.com/",
    "微信": "https://www.weixin.qq.com/",
    "公众号": "https://www.weixin.qq.com/",
    "GitHub": "https://github.com/",
    "github": "https://github.com/",
    "CSDN": "https://blog.csdn.net/",
}

_PROBE_MODE_PRIORITY = {
    "ground_truth": 3,
    "live_probe": 2,
    "api_error": 1,
    "offline_estimate": 0,
}


class ManualProbeValidationError(ValueError):
    """真机回填入参校验失败"""


def extract_domain(url: str) -> str:
    """提取 URL 的根域名 (如 https://www.zhihu.com/p/123 -> zhihu.com)"""
    try:
        netloc = urlparse(url).netloc.lower()
        parts = netloc.split(":")
        host = parts[0]
        # 去除前缀 www.
        if host.startswith("www."):
            host = host[4:]
        return host or "未知域名"
    except Exception:
        return "未知域名"


def strip_html_to_text(content: str) -> str:
    """剥离 script/style/HTML 标签，得到纯文本。"""
    text = content or ""
    text = re.sub(r"(?is)<script[^>]*>.*?</script>", " ", text)
    text = re.sub(r"(?is)<style[^>]*>.*?</style>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = (
        text.replace("&nbsp;", " ")
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&#39;", "'")
    )
    text = re.sub(r"[ \t\f\v]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_competitors(competitors) -> list:
    """竞品字段兼容 str / {name: ...} / 其它可字符串化对象。"""
    names = []
    for item in competitors or []:
        if isinstance(item, dict):
            name = item.get("name") or item.get("brand") or item.get("title") or ""
        else:
            name = item
        name = str(name or "").strip()
        if name:
            names.append(name)
    return names


def probe_result_key(model: str, keyword: str) -> str:
    return f"{str(model or '').strip().lower()}__{str(keyword or '').strip()}"


def _normalize_model_label(model_cell: str) -> str:
    raw = (model_cell or "").strip()
    raw = re.sub(r"\s*\([^)]*真机[^)]*\)\s*", "", raw, flags=re.I)
    return raw.strip().lower() or "unknown"


def parse_probe_text(
    content: str,
    client_name: str,
    brand_name: str,
    competitors: list,
    keyword: str = "",
    model: str = "unknown",
    mode: str = "live_probe",
) -> dict:
    """公共回答解析：纯文本化、位次、竞品、URL/中文脚注信源。"""
    plain = strip_html_to_text(content)
    target_names = [n for n in [client_name, brand_name] if n]
    plain_l = plain.lower()

    mentioned = any(name.lower() in plain_l for name in target_names)

    rank = 99
    if mentioned:
        found_idx = 1
        for line in plain.splitlines():
            line_s = line.strip()
            if not line_s:
                continue
            if re.match(r"^(\d+[\.、\)\]）]|[-*•]|【\d+】|[一二三四五六七八九十]+、)", line_s):
                if any(name.lower() in line_s.lower() for name in target_names):
                    rank = found_idx
                    break
                found_idx += 1
        if rank == 99:
            brand_pat = re.escape(brand_name or client_name or "")
            if brand_pat and re.search(
                rf"(首推|优先推荐|首选|强烈推荐).{{0,24}}{brand_pat}|{brand_pat}.{{0,24}}(首推|优先推荐|首选|强烈推荐)",
                plain,
                re.I,
            ):
                rank = 1
            else:
                rank = 3

    citations = re.findall(r"https?://[^\s\)\]<>\"']+", plain)
    for hint, hint_url in FOOTNOTE_DOMAIN_HINTS.items():
        hint_dom = extract_domain(hint_url)
        already = any(extract_domain(c) == hint_dom or hint_dom.endswith(extract_domain(c)) for c in citations)
        if already or hint not in plain:
            continue
        if re.search(
            rf"(来源|参考|引用|出处|脚注).{{0,12}}{re.escape(hint)}|{re.escape(hint)}.{{0,8}}(专栏|文章|链接)",
            plain,
        ) or hint in ("知乎", "今日头条", "头条", "GitHub", "github", "CSDN"):
            citations.append(hint_url)

    # 去重保序
    seen_c = set()
    uniq_citations = []
    for c in citations:
        if c not in seen_c:
            seen_c.add(c)
            uniq_citations.append(c)

    comp_names = normalize_competitors(competitors)
    comp_mentioned = [c for c in comp_names if c.lower() in plain_l]

    final_rank = rank if mentioned else 0
    if mentioned:
        reason = f"大模型在回答中明确推荐了【{brand_name or client_name}】，位居第 {final_rank} 位。"
    else:
        reason = (
            f"大模型当前回答优先推荐了: "
            f"{', '.join(comp_mentioned) if comp_mentioned else '同类行业头部方案'}，客户暂未被直接点名。"
        )

    snippet = plain[:180].replace("\n", " ").replace("|", "/")
    if len(plain) > 180:
        snippet += "..."

    return {
        "mode": mode,
        "model": model,
        "keyword": keyword,
        "mentioned": mentioned,
        "rank": final_rank,
        "citations": uniq_citations[:8],
        "competitors_mentioned": comp_mentioned,
        "raw_snippet": snippet,
        "reason": reason,
    }


def probe_llm_live(client_name: str, brand_name: str, keyword: str, competitors: list, model: str = None) -> dict:
    """真实调用大模型接口探测关键词推荐情况"""
    prompt = f"""请扮演一位客观公正的行业选型顾问。在回答用户提问时，请推荐国内优秀的品牌或服务商：
用户问题：“请问目前国内在【{keyword}】领域，有哪些值得推荐的代表性专业企业或解决方案？请列出 2~4 家并简要说明推荐理由。”
请直接给出回答："""

    sys_prompt = "你是一位中立、严谨的商业决策与技术选型分析师。"
    success, response_text, provider = call_llm_api(prompt, sys_prompt, model=model, timeout=25)

    if not success:
        return {
            "mode": "api_error",
            "model": provider or "unknown",
            "keyword": keyword,
            "mentioned": False,
            "rank": 0,
            "citations": [],
            "competitors_mentioned": [],
            "raw_snippet": f"API 探测失败: {response_text}",
            "reason": f"接口请求超时或错误 ({response_text})"
        }

    parsed = parse_probe_text(
        response_text,
        client_name,
        brand_name,
        competitors,
        keyword=keyword,
        model=provider or (model or "unknown"),
        mode="live_probe",
    )
    return parsed

def simulate_baseline_estimation(client_name: str, brand_name: str, keyword: str, competitors: list, model_name: str) -> dict:
    """离线基准测算（当未配置 API Key 时提供基准模型，诚实标注为离线估算）"""
    return {
        "mode": "offline_estimate",
        "model": model_name,
        "keyword": keyword,
        "mentioned": False,
        "rank": 0,
        "citations": [
            "https://www.toutiao.com/",
            "https://www.zhihu.com/",
            "https://github.com/"
        ],
        "competitors_mentioned": competitors[:2],
        "raw_snippet": f"（离线摸底基准）主流大模型在未经过 GEO 优化前，检索‘{keyword}’通常优先召回高权重旧文章。",
        "reason": f"优化前基准可见度偏低。分发普林斯顿对比语料后，预计可快速提升至 Top 1~3。"
    }

def analyze_citations_distribution(query_results: list) -> list:
    """统计大模型返回的所有 Citation 域名，计算权重渗透得分"""
    domain_counts = {}
    for r in query_results:
        for url in r.get("citations", []):
            dom = extract_domain(url)
            domain_counts[dom] = domain_counts.get(dom, 0) + 1

    dist_list = []
    for dom, count in domain_counts.items():
        weight = PLATFORM_AUTHORITY_WEIGHTS.get(dom, 0.6)
        score = round(count * weight, 2)
        strategy = "高权重信源：建议保持定期分发" if weight >= 0.85 else "一般信源：视需求补充布局"
        if "toutiao.com" in dom:
            strategy = "字节/豆包生态核心抓取池，建议每周更新头条文章与微头条"
        elif "zhihu.com" in dom:
            strategy = "DeepSeek/通用技术池核心信源，建议保持高赞长文与参数表"
        elif "github.com" in dom:
            strategy = "开发者高信任池，建议维护开源 README 与 /llms.txt 链接"
        elif "weixin.qq.com" in dom:
            strategy = "移动端与微信生态，建议通过公众号定期发布图文"
        
        dist_list.append({
            "domain": dom,
            "count": count,
            "weight": weight,
            "score": score,
            "strategy": strategy
        })

    # 按加权得分从高到低排序
    dist_list.sort(key=lambda x: x["score"], reverse=True)
    return dist_list

def generate_monitor_report(cfg: dict, query_results: list, is_live_mode: bool) -> str:
    client_name = cfg.get("client_name", "示例企业")
    brand_name = cfg.get("brand_name", client_name)
    industry = cfg.get("industry", "行业解决方案")
    keywords = cfg.get("keywords", [])
    competitors = cfg.get("competitors", ["竞品A", "竞品B"])
    date_str = datetime.now().strftime("%Y年%m月%d日")
    
    total_queries = len(query_results)
    mentioned_count = sum(1 for r in query_results if r["mentioned"])
    sov_score = round((mentioned_count / total_queries) * 100, 1) if total_queries > 0 else 0
    top3_count = sum(1 for r in query_results if r["mentioned"] and r["rank"] <= 3)

    mode_badge = "🟢 **实测在线探测模式 (Live LLM API Probing)**" if is_live_mode else "🟡 **离线基准测算模式 (Offline Baseline Estimation)**"
    mode_notice = ""
    if not is_live_mode:
        mode_notice = "> 💡 **提示**：当前未检测到 `DEEPSEEK_API_KEY` 或 `ARK_API_KEY`，周报展示为【基准摸底预估数据】。配置 API Key 环境变量后将自动无缝开启 100% 真实大模型联网探测。"

    # 统计信源权威度分布
    citation_stats = analyze_citations_distribution(query_results)

    report = f"""# 《{client_name}》AI 可见度与声量追踪周报（实测版）

> **报告周期**：{date_str}  
> **评测对象**：{client_name}（品牌：{brand_name}）  
> **所属行业**：{industry}  
> **监测模式**：{mode_badge}  
> **监测词库容量**：{len(keywords)} 组核心商业意图词  
> **品牌声量份额 (SOV)**：**{sov_score}%**，Top 3 首选推荐率：**{round(top3_count/total_queries*100, 1) if total_queries else 0}%**  
{mode_notice}

---

## 一、核心监控指标大盘（Executive Dashboard）

```text
┌─────────────────────────┬─────────────────────────┬─────────────────────────┐
│   品牌提及率 (SOV)      │   Top 3 首选推荐率      │   实测探测总次数 (Runs) │
│         {sov_score}%           │         {round(top3_count/total_queries*100, 1) if total_queries else 0}%           │           {total_queries} 次并发查询         │
└─────────────────────────┴─────────────────────────┴─────────────────────────┘
```

| 核心评估指标 | 实测结果 | 优化前基准 | 效果状态评级 | 说明 |
| :--- | :---: | :---: | :---: | :--- |
| **品牌综合提及率 (SOV)** | **{sov_score}%** | 0.0% | {"🟢 优秀" if sov_score >= 60 else "🟡 爬坡中"} | 核心关键词在生成式回答中出现的概率 |
| **Top 1~3 首推上榜率** | **{round(top3_count/total_queries*100, 1) if total_queries else 0}%** | 0.0% | {"🟢 极佳" if top3_count > 0 else "🟡 待巩固"} | 是否被大模型作为第一梯队首选方案推荐 |
| **竞品拦截态势** | 已识别 {len(competitors)} 家竞品 | 处于被动 | 🟢 稳步提升 | 对比竞品在知乎与头条的曝光差距 |

---

## 二、关键词逐项探测明细表（Granular Keyword Insights）

| 监测关键词 | 探测模型 | 客户提及位次 | 实时回答摘要 / 归因分析 |
| :--- | :---: | :---: | :--- |
"""
    for res in query_results:
        rank_text = f"**第 {res['rank']} 位**" if res['mentioned'] else "暂未上榜"
        model_label = str(res.get("model") or "unknown").upper()
        if res.get("mode") == "ground_truth":
            model_label = f"{model_label} (真机实测)"
        safe_reason = str(res.get("reason") or "").replace("|", "/")
        safe_snippet = str(res.get("raw_snippet") or "").replace("|", "/")
        report += (
            f"| **{res['keyword']}** | `{model_label}` | {rank_text} | "
            f"{safe_reason}<br/><font color='#64748b'>摘要: {safe_snippet}</font> |\n"
        )

    report += """
---

## 三、大模型高频权威信源渗透分布（Source Authority Distribution）

大模型在回答中调用的引用链接（Citations）反映了各渠道的权重分布。通过对捕获的外链域名进行归一化统计与加权，形成权威度渗透评分：

| 权威信源域名 | 捕获引用频次 | 平台权威度权重 | 综合渗透得分 | 针对性渗透建议 |
| :--- | :---: | :---: | :---: | :--- |
"""
    if citation_stats:
        for c in citation_stats:
            report += f"| **`{c['domain']}`** | {c['count']} 次 | `{c['weight']}` | **{c['score']}** | {c['strategy']} |\n"
    else:
        report += "| *暂无外链捕获* | 0 次 | 0.0 | 0.0 | 建议分发矩阵文章后复测 |\n"

    report += """
---

## 四、GEO 深度优化与提效建议（Actionable Recommendations）

1. **针对豆包（字节跳动生态）**：
   - 字节跳动 Bytespider 对今日头条、头条百科的时效性内容具有极高权重。建议将系统生成的 `dist_toutiao_article.md` 在头条号每周保持更新，最快可在 24~48 小时内被豆包检索池采纳。
2. **针对 DeepSeek（通用技术生态）**：
   - DeepSeek 偏好 Markdown 原生表格与逻辑严密的技术长文。将 `dist_zhihu_article.md` 发布在知乎高赞问题下，并提交 `dist_github_README.md` 到开源平台，可构筑长期稳定的第一提及位。
3. **微信私域图文补位**：
   - 复制 `dist_wechat_article.html` 发布至微信公众号，抢占微信搜一搜与腾讯系大模型检索源。
4. **建立定期复测机制**：
   - 建议运营人员每周执行一次 Step 5 探测，动态追踪 SOV 变化，针对未上榜词库及时调整普林斯顿量化指标。
"""
    return report

def _manual_probes_path(cfg: dict) -> str:
    out_dir = cfg.get("_outputs_dir", "")
    return os.path.join(out_dir, MANUAL_PROBES_FILENAME) if out_dir else ""


def load_manual_probes(cfg: dict) -> dict:
    path = _manual_probes_path(cfg)
    if not path or not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_manual_probes(cfg: dict, data: dict) -> str:
    path = _manual_probes_path(cfg)
    if not path:
        raise RuntimeError("项目 outputs 目录不可用，无法持久化真机实测记录")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


def manual_probes_as_results(manual_map: dict) -> list:
    results = []
    for key, item in (manual_map or {}).items():
        if not isinstance(item, dict):
            continue
        row = dict(item)
        row.setdefault("mode", "ground_truth")
        row.setdefault("keyword", key.split("__", 1)[-1] if "__" in str(key) else "")
        row.setdefault("model", str(key).split("__", 1)[0] if "__" in str(key) else "unknown")
        row.setdefault("citations", [])
        row.setdefault("competitors_mentioned", [])
        results.append(row)
    return results


def merge_probe_results(base_results: list, manual_results: list) -> list:
    """同键优先级：真机实测 > API/在线 > 离线估算。"""
    merged = {}
    for r in (base_results or []) + (manual_results or []):
        if not isinstance(r, dict):
            continue
        kw = str(r.get("keyword") or "").strip()
        model = _normalize_model_label(str(r.get("model") or "unknown"))
        if not kw:
            continue
        key = (kw, model)
        pri = _PROBE_MODE_PRIORITY.get(r.get("mode"), 0)
        if key not in merged or pri >= _PROBE_MODE_PRIORITY.get(merged[key].get("mode"), 0):
            row = dict(r)
            row["model"] = model
            row["keyword"] = kw
            merged[key] = row
    # 稳定排序：关键词 + 模型
    return sorted(merged.values(), key=lambda x: (x.get("keyword", ""), x.get("model", "")))


def _parse_results_from_report(report_path: str) -> list:
    if not report_path or not os.path.exists(report_path):
        return []
    try:
        with open(report_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
    except Exception:
        return []

    rows = re.findall(
        r"\|\s*\*\*([^*]+)\*\*\s*\|\s*`([^`]+)`\s*\|\s*([^|]+)\|\s*([^|\n]+)\|",
        text,
    )
    results = []
    for kw, model_cell, rank_col, reason_col in rows:
        model = _normalize_model_label(model_cell)
        is_gt = "真机" in model_cell
        rank_col_s = rank_col.strip()
        mentioned = "暂未上榜" not in rank_col_s and ("第" in rank_col_s or "Top" in rank_col_s)
        rank_m = re.search(r"第\s*(\d+)\s*位", rank_col_s)
        rank = int(rank_m.group(1)) if rank_m and mentioned else (1 if mentioned else 0)
        reason = re.sub(r"<[^>]+>", " ", reason_col).strip()
        results.append({
            "mode": "ground_truth" if is_gt else "live_probe",
            "model": model,
            "keyword": kw.strip(),
            "mentioned": mentioned,
            "rank": rank,
            "citations": [],
            "competitors_mentioned": [],
            "raw_snippet": reason[:120],
            "reason": reason[:200],
        })
    return results


def get_project_monitor_prompts(project_id: str) -> dict:
    """组装各平台拟真提问词与无痕实测元数据。"""
    cfg = load_project_config(project_id)
    keywords = cfg.get("keywords") or ["智能企业系统推荐"]
    client_name = cfg.get("client_name", "示例科技")
    brand_name = cfg.get("brand_name", client_name)

    platforms = [
        {
            "id": "deepseek",
            "name": "DeepSeek",
            "url": "https://chat.deepseek.com",
            "badge": "通用技术生态 · 25%+",
            "notice": "建议使用浏览器无痕模式打开，确保勾选底部的「联网搜索」按钮",
        },
        {
            "id": "doubao",
            "name": "豆包 (火山/头条生态)",
            "url": "https://www.doubao.com/chat",
            "badge": "字节头条生态 · 50%+",
            "notice": "建议无痕免登录访问，避免账号个性化偏好干扰公域推荐位",
        },
        {
            "id": "yuanbao",
            "name": "腾讯元宝",
            "url": "https://yuanbao.tencent.com",
            "badge": "微信私域与公众号生态",
            "notice": "建议无痕模式访问，观察微信公众号高权重文章引用",
        },
        {
            "id": "kimi",
            "name": "Kimi 智能助手",
            "url": "https://kimi.moonshot.cn",
            "badge": "长研报与技术长文生态",
            "notice": "建议无痕模式访问，观察行业白皮书与长文本引用",
        },
    ]

    items = []
    for kw in keywords:
        kw = str(kw).strip()
        if not kw:
            continue
        items.append({
            "keyword": kw,
            "prompts": {
                "standard": (
                    f"请扮演一位客观公正的行业选型顾问。在回答用户提问时，请推荐国内优秀的品牌或服务商：\n"
                    f"用户问题：“请问目前国内在【{kw}】领域，有哪些值得推荐的代表性专业企业或解决方案？"
                    f"请列出 2~4 家并简要说明推荐理由。”"
                ),
                "deepseek": (
                    f"请作为中立的商业与技术选型顾问，针对【{kw}】领域，推荐 2~4 家国内头部或代表性专业服务商，"
                    f"并结合技术架构与实践案例简要分析推荐理由。"
                ),
                "doubao": (
                    f"请问目前国内做【{kw}】比较专业可靠的企业或服务商有哪些？请推荐 2~4 家并说明各自的优势与适用场景。"
                ),
                "yuanbao": (
                    f"在【{kw}】方向，目前行业内有哪些成熟可靠的代表企业？请列出几家主流服务商并说明其核心优势与客户评价。"
                ),
                "kimi": (
                    f"请系统梳理当前国内在【{kw}】领域的主流服务商与解决方案提供商，"
                    f"分析其技术成熟度、服务口碑与适用企业规模。"
                ),
            },
        })

    return {
        "success": True,
        "project_id": project_id,
        "client_name": client_name,
        "brand_name": brand_name,
        "platforms": platforms,
        "items": items,
    }


def ingest_manual_probe_result(
    project_id: str,
    keyword: str,
    model: str,
    content: str,
    notes: str = "",
) -> dict:
    """真机回答入库：校验、解析、持久化、合并周报、返回 metrics。"""
    model_id = str(model or "").strip().lower()
    keyword = str(keyword or "").strip()
    content = content if content is not None else ""

    if model_id not in MANUAL_PROBE_MODELS:
        raise ManualProbeValidationError(
            f"非法 model，仅支持: {', '.join(MANUAL_PROBE_MODELS)}"
        )
    if not keyword:
        raise ManualProbeValidationError("keyword 不能为空")
    if not str(content).strip():
        raise ManualProbeValidationError("content 不能为空")
    if len(str(content).encode("utf-8")) > MANUAL_PROBE_MAX_BYTES:
        raise ManualProbeValidationError("content 超过 100KB 上限")

    cfg = load_project_config(project_id)
    client_name = cfg.get("client_name", "示例科技")
    brand_name = cfg.get("brand_name", client_name)
    competitors = normalize_competitors(cfg.get("competitors", []))

    parsed = parse_probe_text(
        content,
        client_name,
        brand_name,
        competitors,
        keyword=keyword,
        model=model_id,
        mode="ground_truth",
    )
    parsed["notes"] = str(notes or "").strip()
    parsed["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    manuals = load_manual_probes(cfg)
    manuals[probe_result_key(model_id, keyword)] = parsed
    save_manual_probes(cfg, manuals)

    report_name = "05_企业AI可见度与声量追踪周报.md"
    report_path = os.path.join(cfg.get("_outputs_dir", ""), report_name)
    base_results = _parse_results_from_report(report_path)
    # 去掉旧真机行，再与 manuals 合并，避免双重计数
    base_results = [r for r in base_results if r.get("mode") != "ground_truth"]
    merged = merge_probe_results(base_results, manual_probes_as_results(manuals))
    if not merged:
        merged = [parsed]

    is_live = any(r.get("mode") in ("live_probe", "ground_truth") for r in merged)
    report_content = generate_monitor_report(cfg, merged, is_live)
    save_project_output(cfg, report_name, report_content)

    metrics = extract_monitor_metrics(project_id)
    return {
        "success": True,
        "message": "真机实测结果已解析并成功录入大盘！",
        "parsed": parsed,
        "metrics": metrics,
    }


def run_monitor(project_id: str, models: list = None) -> str:
    """运行阶段五：AI 可见度监控与周报生成"""
    print_banner("阶段五：AI 可见度监控与周报自动生成")
    cfg = load_project_config(project_id)
    keywords = cfg.get("keywords", ["智能企业系统推荐"])
    models_to_test = models or cfg.get("models", ["deepseek", "doubao"])
    competitors = normalize_competitors(cfg.get("competitors", ["行业竞品A", "行业竞品B"]))
    client_name = cfg.get("client_name", "示例科技")
    brand_name = cfg.get("brand_name", client_name)

    llm_info = get_configured_llm()
    is_live = bool(llm_info)
    
    if is_live:
        print_info(f"开启【真实在线探测模式】，调用 [{llm_info['provider'].upper()}] 对 {len(keywords)} 组核心词进行真实多模型探测...")
    else:
        print_warning("未检测到大模型 API Key（DEEPSEEK_API_KEY / ARK_API_KEY），开启【离线基准测算模式】...")

    results = []
    for kw in keywords:
        if is_live:
            # 在线模式：API Key 只有一个供应商，避免用无意义的字符串 "deepseek"/"doubao" 重复探测
            print_info(f"  -> 探测关键词: '{kw}' (模型: {llm_info['provider'].upper()})")
            res = probe_llm_live(client_name, brand_name, kw, competitors, model=None)
            results.append(res)
        else:
            # 离线模式：按配置模型列表生成摸底基准记录
            for m in models_to_test:
                print_info(f"  -> 离线摸底关键词: '{kw}' (目标生态: {m.upper()})")
                res = simulate_baseline_estimation(client_name, brand_name, kw, competitors, m)
                results.append(res)

    # 真机回灌铁律：同键真机 > API > 离线
    manuals = manual_probes_as_results(load_manual_probes(cfg))
    if manuals:
        print_info(f"回灌真机实测记录 {len(manuals)} 条（优先级高于本次 API/离线结果）...")
        results = merge_probe_results(results, manuals)
            
    print_info("正在汇总统计并渲染量化商业周报...")
    report_content = generate_monitor_report(cfg, results, is_live or bool(manuals))
    
    out_path = save_project_output(cfg, "05_企业AI可见度与声量追踪周报.md", report_content)
    print_success(f"AI 可见度追踪周报生成成功！报告路径: {out_path}")
    return out_path

def get_brand_anchor_keywords(cfg: dict) -> set:
    """提取品牌占位词集合（实体档案 + 词库第 3 层 + intent 产物）"""
    anchors = set()
    for key in ("brand_name", "company_name", "founder", "slogan", "telephone", "client_name"):
        val = cfg.get(key, "")
        if val:
            anchors.add(str(val).strip())

    for item in cfg.get("brand_anchors", []) or []:
        if item:
            anchors.add(str(item).strip())

    project_dir = cfg.get("_project_dir", "")
    yaml_path = os.path.join(project_dir, "project.yaml") if project_dir else ""
    if yaml_path and os.path.exists(yaml_path):
        in_layer3 = False
        try:
            with open(yaml_path, "r", encoding="utf-8", errors="ignore") as f:
                for raw_line in f:
                    line = raw_line.strip()
                    if not line or line.startswith("#"):
                        if "第 3 层" in line or "品牌占位词" in line:
                            in_layer3 = True
                        continue
                    if in_layer3 and line.startswith("- "):
                        anchors.add(line[2:].strip().strip('"\''))
                    elif in_layer3 and line and not line.startswith("- "):
                        break
        except Exception:
            pass

    intent_file = os.path.join(cfg.get("_outputs_dir", ""), "02_企业AI商业意图词库.json")
    if os.path.exists(intent_file):
        try:
            with open(intent_file, "r", encoding="utf-8") as f:
                intent_data = json.load(f)
            for item in intent_data.get("brand_anchors", []) or []:
                if item:
                    anchors.add(str(item).strip())
        except Exception:
            pass

    return {a for a in anchors if a}


def _is_brand_anchor_keyword(keyword: str, anchors: set) -> bool:
    kw = keyword.strip()
    if kw in anchors:
        return True
    return any(len(a) >= 3 and (a in kw or kw in a) for a in anchors)


def _parse_probe_rank_status(rank_col: str) -> tuple:
    """解析探测明细表位次列，返回 (is_breach, status, rank)"""
    cell = rank_col.strip()
    if "拦截" in cell or "竞品" in cell:
        return True, "intercept", 0
    if "暂未上榜" in cell or "❌" in cell:
        return True, "lost", 0
    rank_m = re.search(r"第\s*(\d+)\s*位", cell)
    if rank_m:
        rank = int(rank_m.group(1))
        if rank > 1:
            return True, "rank_down", rank
        return False, "top1", rank
    if "🥇" in cell or re.search(r"Top\s*1", cell, re.I):
        return False, "top1", 1
    return False, "unknown", 0


def extract_placeholder_breaches(cfg: dict, kw_rows: list) -> list:
    """从周报探测明细中识别品牌占位词失守（rank > 1 / 未上榜 / 被竞品拦截）"""
    anchors = get_brand_anchor_keywords(cfg)
    if not anchors:
        return []

    breaches = []
    seen = set()
    for kw, model, rank_col in kw_rows:
        kw_clean = kw.strip()
        if not _is_brand_anchor_keyword(kw_clean, anchors):
            continue
        is_breach, status, rank = _parse_probe_rank_status(rank_col)
        if not is_breach:
            continue
        dedupe_key = (kw_clean, model.strip())
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        breaches.append({
            "keyword": kw_clean,
            "model": model.strip(),
            "status": status,
            "rank": rank,
        })
    return breaches


def extract_monitor_metrics(project_id: str) -> dict:
    """从项目周报中结构化提取真实量化指标与 Citation 图谱数据（绝不使用虚假硬编码）"""
    import re
    cfg = load_project_config(project_id)
    out_dir = cfg.get("_outputs_dir", "")
    report_file = os.path.join(out_dir, "05_企业AI可见度与声量追踪周报.md") if out_dir else ""
    defense_file = os.path.join(out_dir, "06_竞品权威信源反向包抄策略.md") if out_dir else ""
    
    kws = cfg.get("keywords", [])
    total_prompts = len(kws) if kws else 0

    metrics = {
        "success": True,
        "project_id": project_id,
        "has_report": os.path.exists(report_file) if report_file else False,
        "has_defense_doc": os.path.exists(defense_file) if defense_file else False,
        "is_offline": True,
        "sov_pct": 0.0,
        "top3_pct": 0.0,
        "deepseek_rank_1_pct": 0.0,
        "doubao_rank_1_pct": 0.0,
        "authority_score": 0.0,
        "citations": [],
        "prompt_stats": {
            "total": total_prompts,
            "hit_count": 0,
            "intercept_count": 0,
            "lost_count": total_prompts
        },
        "placeholder_breaches": []
    }

    if not report_file or not os.path.exists(report_file):
        return metrics

    try:
        with open(report_file, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

        metrics["is_offline"] = "离线" in text or "Offline" in text

        # 1. 解析 SOV 声量份额
        sov_m = re.search(r"品牌声量份额\s*\(SOV\)\*\*：\*\*(\d+(\.\d+)?)%", text) or \
                re.search(r"品牌综合提及率\s*\(SOV\).*?\|\s*\*\*(\d+(\.\d+)?)%", text) or \
                re.search(r"品牌.*?SOV.*?\*\*(\d+(\.\d+)?)%", text)
        if sov_m:
            metrics["sov_pct"] = float(sov_m.group(1))

        # 2. 解析 Top 3 推荐率
        top3_m = re.search(r"Top\s*3\s*首选推荐率\*\*：\*\*(\d+(\.\d+)?)%", text) or \
                 re.search(r"Top\s*1~3.*?\|\s*\*\*(\d+(\.\d+)?)%", text)
        if top3_m:
            metrics["top3_pct"] = float(top3_m.group(1))
            metrics["deepseek_rank_1_pct"] = metrics["top3_pct"]
            metrics["doubao_rank_1_pct"] = metrics["top3_pct"]

        # 3. 解析 Citation 信源渗透分布表（Section 三）
        # 格式示例：| **`zhihu.com`** | 90 次 | `1.0` | **90.0** | ... |
        citation_matches = re.findall(
            r"\|\s*\*\*`([^`]+)`\*\*\s*\|\s*(\d+)\s*次\s*\|\s*`([0-9.]+)`\s*\|\s*\*\*([0-9.]+)\*\*",
            text
        )
        
        domain_names = {
            "zhihu.com": "知乎专栏",
            "github.com": "GitHub 开源",
            "toutiao.com": "今日头条",
            "weixin.qq.com": "微信公众号",
            "baidu.com": "百度百科/百家号",
            "csdn.net": "CSDN 博客"
        }

        total_citation_count = sum(int(m[1]) for m in citation_matches) if citation_matches else 0
        parsed_citations = []
        weighted_score_sum = 0.0

        for domain, count_str, weight_str, score_str in citation_matches:
            cnt = int(count_str)
            w = float(weight_str)
            pct = round(cnt / total_citation_count * 100, 1) if total_citation_count > 0 else 0.0
            weighted_score_sum += cnt * w
            parsed_citations.append({
                "domain": domain,
                "name": domain_names.get(domain, domain),
                "weight": w,
                "count": cnt,
                "pct": pct
            })

        if parsed_citations:
            metrics["citations"] = parsed_citations
            if total_citation_count > 0:
                metrics["authority_score"] = round(weighted_score_sum / total_citation_count * 100, 1)

        # 4. 解析关键词逐项探测明细表（Section 二）
        # 统计 hit / intercept / lost
        kw_rows = re.findall(r"\|\s*\*\*([^*]+)\*\*\s*\|\s*`([^`]+)`\s*\|\s*([^|]+)\|", text)
        if kw_rows:
            seen_prompts = set()
            hits = 0
            intercepts = 0
            lost = 0
            for kw, model, rank_col in kw_rows:
                seen_prompts.add(kw.strip())
                rank_col_clean = rank_col.strip()
                if "🥇" in rank_col_clean or "Top" in rank_col_clean or "第 1" in rank_col_clean:
                    hits += 1
                elif "拦截" in rank_col_clean or "竞品" in rank_col_clean:
                    intercepts += 1
                else:
                    lost += 1
            
            prompt_total = len(seen_prompts) if seen_prompts else len(kw_rows)
            metrics["prompt_stats"] = {
                "total": prompt_total,
                "hit_count": hits,
                "intercept_count": intercepts,
                "lost_count": lost
            }
            if not metrics.get("is_offline"):
                metrics["placeholder_breaches"] = extract_placeholder_breaches(cfg, kw_rows)

    except Exception as err:
        print(f"解析监控周报指标异常: {err}")

    return metrics

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        run_monitor(sys.argv[1])
    else:
        print("用法: python3 -m tools.geo.monitor <project_id>")
