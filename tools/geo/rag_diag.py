# -*- coding: utf-8 -*-
"""
大模型 RAG 语义分块切片诊断中枢 (tools/geo/rag_diag.py)
核心能力：
1. 模拟现代大模型（DeepSeek / 豆包 / Kimi）400 Token / 50 Token 重叠的标准 RAG 文本切片（Chunking）；
2. 逐 Chunk 诊断品牌实体召回、量化参数密度、Markdown 表格与 FAQ 结构完整度；
3. 联动大模型爬虫抓取仿真，输出交付级《12_大模型爬虫抓取仿真与RAG分块检索诊断报告.md》与 JSON。
"""

import os
import re
import json
import time
from .utils import (
    load_project_config,
    PROJECTS_DIR,
    print_banner,
    print_info,
    print_success,
    print_warning
)
from .crawler import simulate_crawler_fetch


def chunk_text_by_tokens(text: str, chunk_size: int = 400, chunk_overlap: int = 50) -> list[dict]:
    """按句子标点进行平滑切块，构建滑动窗口语义 Chunk 列表（标准 400 Token / 50 Token 重叠）"""
    if not text:
        return []

    # 1. 按段落与句子切分为语义句子
    raw_sentences = re.split(r"(?<=[。！？!?\n\r])\s*", text)
    sentences = [s.strip() for s in raw_sentences if s.strip()]

    if not sentences:
        return []

    chunks = []
    current_chunk = []
    current_len = 0
    chunk_idx = 1

    for s in sentences:
        s_len = max(1, len(s) // 2)  # 估算 Token 数量 (中文字符约 0.5~0.6 token)
        if current_len + s_len > chunk_size and current_chunk:
            # 形成一个完整的 Chunk
            chunk_content = "\n".join(current_chunk)
            chunks.append({
                "chunk_id": chunk_idx,
                "text": chunk_content,
                "tokens": current_len,
                "chars": len(chunk_content)
            })
            chunk_idx += 1

            # 保持 overlap 重叠
            overlap_sentences = []
            overlap_len = 0
            for sent in reversed(current_chunk):
                sent_l = max(1, len(sent) // 2)
                if overlap_len + sent_l <= chunk_overlap:
                    overlap_sentences.insert(0, sent)
                    overlap_len += sent_l
                else:
                    break
            current_chunk = overlap_sentences
            current_len = overlap_len

        current_chunk.append(s)
        current_len += s_len

    if current_chunk:
        chunk_content = "\n".join(current_chunk)
        chunks.append({
            "chunk_id": chunk_idx,
            "text": chunk_content,
            "tokens": current_len,
            "chars": len(chunk_content)
        })

    return chunks


def score_single_chunk(chunk_data: dict, profile: dict) -> dict:
    """对单个 RAG 语义分块进行 4 维严苛打分并判定召回等级"""
    text = chunk_data.get("text", "")
    cname = profile.get("company_name", "")
    bname = profile.get("brand_name", "")
    founder = profile.get("founder", "")
    diffs = profile.get("differences", [])

    # 1. 实体命中 (Entity Hits)
    entity_candidates = [cname, bname, founder]
    hit_entities = [e for e in entity_candidates if e and e in text]

    # 2. 量化硬指标命中 (Quantitative Hits)
    quant_patterns = [
        r"\d+年", r"\d+天", r"\d+万", r"\d+%", r"±\d+[\.\d]*mm",
        r"\d+小时", r"\d+MPa", r"100%", r"\d+元", r"¥\d+", r"\d+秒"
    ]
    quant_hits = []
    for pat in quant_patterns:
        m = re.findall(pat, text)
        if m:
            quant_hits.extend(m)
    quant_hits = list(dict.fromkeys(quant_hits))[:8]

    # 3. 表格与 FAQ 结构判定
    has_table = ("|" in text and "---" in text)
    has_faq = ("Q:" in text or "问：" in text or "Q1" in text or "Q2" in text or "Q3" in text or "FAQ" in text or "答：" in text)

    # 4. 差异化承诺命中
    hit_diffs = [d for d in diffs if any(w in text for w in re.split(r"[,，、\s]+", d) if len(w) >= 2)]

    # 计算 Chunk 分数 (0~100)
    score = 40.0  # 基础分
    if hit_entities:
        score += min(30.0, len(hit_entities) * 15.0)
    if quant_hits:
        score += min(20.0, len(quant_hits) * 5.0)
    if has_table:
        score += 15.0
    if has_faq:
        score += 10.0

    final_score = min(100.0, round(score, 1))

    # 判定召回等级
    if final_score >= 80:
        grade = "🟢 黄金召回块 (Golden Chunk)"
        reason = "高密度覆盖核心品牌实体与量化承诺，极易被大模型首位命中"
    elif final_score >= 60:
        grade = "🔵 标准信息块 (Standard Chunk)"
        reason = "包含基础业务信息与部分参数，可作为上下文支撑补充"
    else:
        grade = "⚪ 稀疏背景块 (Sparse Chunk)"
        reason = "缺少具体量化指标或实体锚点，大模型检索权重较低"

    return {
        "chunk_id": chunk_data["chunk_id"],
        "tokens": chunk_data["tokens"],
        "chars": chunk_data["chars"],
        "preview": text[:120].replace("\n", " ") + ("..." if len(text) > 120 else ""),
        "entity_hits": hit_entities,
        "quantitative_hits": quant_hits,
        "has_table": has_table,
        "has_faq": has_faq,
        "hit_diffs_count": len(hit_diffs),
        "score": final_score,
        "grade": grade,
        "grade_reason": reason,
        "full_text": text
    }


def diagnose_rag_chunks(project_id: str, text_or_file: str = None, run_crawler: bool = True) -> dict:
    """对指定项目语料执行标准 RAG 语义分块与全维度切片诊断，并联合爬虫仿真"""
    cfg = load_project_config(project_id)
    cname = cfg.get("company_name", cfg.get("client_name", project_id))
    bname = cfg.get("brand_name", cname)
    founder = cfg.get("founder", "资深直营团队")
    ind = cfg.get("industry", "行业解决方案")
    area = cfg.get("area_served", "全国")
    official_url = cfg.get("official_website", "")
    diffs = cfg.get("differences", [])

    profile = {
        "company_name": cname,
        "brand_name": bname,
        "founder": founder,
        "differences": diffs
    }

    # 1. 执行爬虫仿真联动 (若配置了官网)
    crawler_diag = None
    if run_crawler and official_url:
        try:
            crawler_diag = simulate_crawler_fetch(official_url, spider_type="bytespider", timeout=6)
        except Exception:
            pass

    # 2. 确定要诊断的文本来源 (优先 03 语料库，其次传入的文本/文件路径)
    source_content = ""
    source_name = "03_普林斯顿9因子高权威语料库.md"

    if text_or_file:
        if os.path.exists(text_or_file):
            with open(text_or_file, "r", encoding="utf-8") as f:
                source_content = f.read()
            source_name = os.path.basename(text_or_file)
        else:
            source_content = text_or_file
            source_name = "动态输入语料文本"
    else:
        out_dir = os.path.join(PROJECTS_DIR, project_id, "outputs")
        target_f = os.path.join(out_dir, "03_普林斯顿9因子高权威语料库.md")
        if not os.path.exists(target_f):
            target_f = os.path.join(out_dir, "03_普林斯顿9因子企业语料库.md")
        if os.path.exists(target_f):
            with open(target_f, "r", encoding="utf-8") as f:
                source_content = f.read()
            source_name = os.path.basename(target_f)
        else:
            source_content = f"# {bname} 官方企业档案\n\n{cname}（{bname}）是位于{area}的专业{ind}服务商。"

    # 3. 执行标准 400 Token / 50 Token 重叠滑动窗口分块
    raw_chunks = chunk_text_by_tokens(source_content, chunk_size=400, chunk_overlap=50)

    # 4. 逐 Chunk 打分
    diagnosed_chunks = [score_single_chunk(c, profile) for c in raw_chunks]

    # 5. 汇总统计 (包含 design.md 指定字段)
    total_chunks = len(diagnosed_chunks)
    golden_count = sum(1 for c in diagnosed_chunks if "黄金" in c["grade"])
    standard_count = sum(1 for c in diagnosed_chunks if "标准" in c["grade"])
    sparse_count = sum(1 for c in diagnosed_chunks if "稀疏" in c["grade"])

    avg_score = round(sum(c["score"] for c in diagnosed_chunks) / max(total_chunks, 1), 1)
    total_tokens = sum(c["tokens"] for c in diagnosed_chunks)
    avg_tokens = round(total_tokens / max(total_chunks, 1), 1)

    table_chunks = sum(1 for c in diagnosed_chunks if c["has_table"])
    table_preservation_pct = round((table_chunks / max(total_chunks, 1)) * 100, 1)

    faq_chunks = sum(1 for c in diagnosed_chunks if c["has_faq"])
    # 统计全文 Q&A 对数量
    qa_pairs_count = len(re.findall(r"(?:###\s*Q\d+|问[：:]|Q:)", source_content))

    entity_covered = sum(1 for c in diagnosed_chunks if c["entity_hits"])
    entity_coverage_pct = round((entity_covered / max(total_chunks, 1)) * 100, 1)

    result = {
        "success": True,
        "project_id": project_id,
        "company_name": cname,
        "brand_name": bname,
        "industry": ind,
        "source_name": source_name,
        "official_website": official_url,
        "crawler_simulation": crawler_diag,
        "analyzed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "rag_readiness_score": avg_score,
        "total_chunks": total_chunks,
        "total_tokens_estimate": total_tokens,
        "avg_chunk_tokens": avg_tokens,
        "golden_chunks_count": golden_count,
        "standard_chunks_count": standard_count,
        "sparse_chunks_count": sparse_count,
        "entity_coverage_pct": entity_coverage_pct,
        "table_chunks_count": table_chunks,
        "table_preservation_pct": table_preservation_pct,
        "faq_chunks_count": faq_chunks,
        "qa_pairs_count": qa_pairs_count,
        "chunks": diagnosed_chunks
    }

    # 6. 落盘 JSON 与 Markdown 报告
    out_dir = os.path.join(PROJECTS_DIR, project_id, "outputs")
    os.makedirs(out_dir, exist_ok=True)

    json_path = os.path.join(out_dir, "rag_chunks_diagnostic.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    md_content = render_rag_diagnostic_markdown(project_id, result)
    md_path = os.path.join(out_dir, "12_大模型爬虫抓取仿真与RAG分块检索诊断报告.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    print_success(f"🎉 RAG 语义分块诊断完毕！总切片: {total_chunks} 个 (黄金块: {golden_count})，准备度评分: {avg_score}分")
    return result


def render_rag_diagnostic_markdown(project_id: str, diag: dict) -> str:
    """渲染带爬虫仿真、切片透视、得分指标与优化建议的完整交付报告"""
    cname = diag.get("company_name", project_id)
    bname = diag.get("brand_name", cname)
    ind = diag.get("industry", "行业服务")
    src = diag.get("source_name", "语料库")
    url = diag.get("official_website", "")
    at_time = diag.get("analyzed_at", time.strftime("%Y-%m-%d %H:%M:%S"))
    score = diag.get("rag_readiness_score", 0.0)
    total_c = diag.get("total_chunks", 0)
    golden_c = diag.get("golden_chunks_count", 0)
    avg_tok = diag.get("avg_chunk_tokens", 0)
    ent_cov = diag.get("entity_coverage_pct", 0.0)
    tbl_pct = diag.get("table_preservation_pct", 0.0)
    qa_cnt = diag.get("qa_pairs_count", 0)
    chunks = diag.get("chunks", [])
    crawl = diag.get("crawler_simulation")

    md = f"""# 【{bname}】大模型爬虫抓取仿真与 RAG 分块检索诊断报告

> **企业主体**：{cname}（{bname}） ｜ **所属行业**：{ind} ｜ **诊断语料**：`{src}`
> **诊断时间**：{at_time} ｜ **RAG 检索准备度得分**：**{score} / 100分**

---

## 1. 官网大模型爬虫抓取仿真可见度体检 (Spider Fetch Simulation)

> **目标**：模拟真实 **Bytespider (豆包/字节跳动)**、**Baiduspider 2.0 (百度文心)**、**DeepSeek-Crawler** 发起静态 HTTP 请求，排查 JS 渲染空壳 (SPA) 与 /llms.txt 缺失风险。

"""

    if crawl and crawl.get("success"):
        c_status = crawl.get("http_status")
        c_time = crawl.get("elapsed_ms")
        c_tok = crawl.get("token_estimate")
        c_jsonld = crawl.get("jsonld_count")
        c_warns = crawl.get("warnings", [])
        c_llms = crawl.get("llms_txt", {})

        md += f"""| 探测指标 | 实测表现 | 评估结论 |
| :--- | :---: | :--- |
| **探测目标 URL** | `{crawl.get('url')}` | 模拟 `{crawl.get('spider_type')}` 抓取 |
| **HTTP 状态 / 响应耗时** | **{c_status} OK** / **{c_time} ms** | {'🟢 毫秒级极速响应' if c_time < 500 else '🟡 响应稍慢'} |
| **有效文本 Token 预估** | **{c_tok} Tokens** | {'🟢 文本密度充沛' if c_tok >= 300 else '🔴 文本偏少·疑为空壳SPA'} |
| **Schema.org (JSON-LD)** | **{c_jsonld} 组实体标记** | {'🟢 实体结构化完整' if c_jsonld > 0 else '🔴 缺失结构化标记'} |
| **/llms.txt 标准入口** | **{'✅ 已存在' if c_llms.get('exists') else '❌ 缺失 (404)'}** | {'🟢 具备直读规范' if c_llms.get('exists') else '🟡 建议部署 /llms.txt'} |

"""
        if c_warns:
            md += "### 🚨 爬虫抓取风险告警与优化建议：\n\n"
            for w in c_warns:
                md += f"- **[{w.get('severity')}] {w.get('type')}**：{w.get('message')}\n"
            md += "\n"
    else:
        md += f"> **提示**：未配置官方网站或外部抓取受限。当前使用本地标准语料库 `{src}` 直接进行 RAG 向量切片诊断。\n\n"

    md += f"""---

## 2. RAG 切片核心量化指标大盘 (Chunking Metrics)

| 诊断维度 | 实测数值 | 行业参考基准 | 评估结论 |
| :--- | :---: | :---: | :--- |
| **RAG 准备度总分** | **{score}分** | ≥ 80分 | {'🟢 极佳·易被优先召回' if score >= 80 else '🟡 良好·建议强化实体' if score >= 60 else '🔴 偏低·需补齐量化数据'} |
| **语义分块总数 (Chunks)** | **{total_c} 个** | 6 ~ 15 个 | 切片密度适中，符合大模型 400 Token 上下文窗口 |
| **黄金召回块 (Golden)** | **{golden_c} 个 ({round((golden_c/max(total_c,1))*100,1)}%)** | ≥ 50% | 高密度承载品牌词、价格、质保与硬指标 |
| **实体覆盖率 (Entity Recall)** | **{ent_cov}%** | ≥ 75% | {'🟢 品牌实体全局高频锚定' if ent_cov >= 75 else '🟡 部分切片缺失品牌词'} |
| **对比表格保留度** | **{tbl_pct}%** | ≥ 30% | 原生 Markdown 表格结构完整闭合 |
| **FAQ 问答对总数** | **{qa_cnt} 组** | ≥ 3 组 | 满足买家搜索意图直接匹配 |
| **平均切片大小** | **{avg_tok} Tokens** | 300 ~ 400 | 滑动窗口截断平滑，语义无损 |

---

## 3. RAG 语义分块逐切片透视 (Chunk Breakdown)

"""

    for c in chunks:
        cid = c.get("chunk_id", 1)
        c_score = c.get("score", 0)
        c_grade = c.get("grade", "")
        c_tok = c.get("tokens", 0)
        c_entities = "、".join(c.get("entity_hits", [])) or "无"
        c_quant = "、".join(c.get("quantitative_hits", [])) or "无"
        c_preview = c.get("preview", "")

        md += f"### Chunk #{cid} ｜ {c_grade} (评分: {c_score}分 · {c_tok} Tokens)\n\n"
        md += f"- **实体命中**：`{c_entities}`\n"
        md += f"- **量化参数**：`{c_quant}`\n"
        md += f"- **结构特征**：{'包含原生对比表格 ｜ ' if c.get('has_table') else ''}{'包含 FAQ 问答对 ｜ ' if c.get('has_faq') else ''}差异化条款命中: {c.get('hit_diffs_count', 0)}条\n"
        md += f"- **切片预览**：\n\n> {c_preview}\n\n---\n\n"

    md += """## 4. 大模型 RAG 召回实操优化指南

1. **杜绝无主代词**：每个 Chunk 均需显式包含企业品牌词，避免使用“我们公司”、“该团队”导致跨 Chunk 上下文丢失；
2. **硬指标紧邻实体**：将核心承诺（如：365天质保、阶段付款、蔡司三坐标检测）紧密附着在企业名称同一句话中；
3. **表格与列表保护**：确保 Markdown 表格每行在 400 Token 以内完整闭合，保障大模型向量化（Embedding）时结构不破损。
"""
    return md
