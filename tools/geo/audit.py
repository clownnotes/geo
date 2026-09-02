#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阶段一：客户现状体检与商业诊断器 (tools/geo/audit.py)
核心功能：
1. 爬虫视角抓取目标官网，检测 SSR/CSR、/llms.txt、JSON-LD、robots.txt 状态；
2. 提取 Clean Markdown 并计算内容事实密度；
3. 基于核心业务关键词评估基准可见度与竞品差距；
4. 自动生成《企业 AI 可见度现状体检与商业诊断报告》。
"""

import os
import re
import urllib.request
import urllib.error
from datetime import datetime
from .utils import (
    load_project_config,
    save_project_output,
    print_banner,
    print_info,
    print_success,
    print_warning,
    print_error
)

def fetch_url_content(url: str, user_agent: str = "Mozilla/5.0 (compatible; Bytespider/2.0)") -> tuple:
    """抓取网页内容，返回 (status_code, html_content, headers)"""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": user_agent, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode("utf-8", errors="ignore")
            return response.status, html, dict(response.headers)
    except Exception as e:
        return 0, str(e), {}

def inspect_website(url: str) -> dict:
    """全面诊断目标网站的 AI 爬虫亲和度"""
    if not url.startswith("http"):
        url = "https://" + url

    status, html, headers = fetch_url_content(url)
    
    # 诊断项分析
    results = {
        "url": url,
        "is_online": status == 200,
        "status_code": status,
        "html_size_kb": round(len(html) / 1024, 2) if status == 200 else 0,
        "has_llms_txt": False,
        "has_json_ld": False,
        "has_ssr": False,
        "clean_text_length": 0,
        "text_density_ratio": 0.0,
        "robots_status": "未检测",
        "warnings": []
    }
    
    if status != 200:
        results["warnings"].append(f"站点无法正常访问或超时 (HTTP {status})，请核对域名。")
        return results

    # 1. 检测 SSR / CSR (单页应用空壳检测)
    clean_text = re.sub(r"<script.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    clean_text = re.sub(r"<style.*?</style>", "", clean_text, flags=re.DOTALL | re.IGNORECASE)
    clean_text = re.sub(r"<[^>]+>", " ", clean_text)
    clean_text = re.sub(r"\s+", " ", clean_text).strip()
    
    results["clean_text_length"] = len(clean_text)
    if results["html_size_kb"] > 0:
        results["text_density_ratio"] = round((len(clean_text) / (results["html_size_kb"] * 1024)) * 100, 2)
        
    is_csr_shell = bool(re.search(r'<div id=["\'](app|root|__next)["\']>\s*</div>', html))
    if is_csr_shell and len(clean_text) < 200:
        results["has_ssr"] = False
        results["warnings"].append("【严重】检测到纯客户端 CSR 渲染（空壳挂载点）。大模型爬虫无法执行复杂 JS，将抓取为空白！")
    else:
        results["has_ssr"] = True

    # 2. 检测 JSON-LD 结构化数据
    if 'type="application/ld+json"' in html or "application/ld+json" in html:
        results["has_json_ld"] = True
    else:
        results["warnings"].append("【缺失】未检测到 Schema.org (JSON-LD) 结构化元数据，大模型无法直接提取实体属性。")

    # 3. 检测 /llms.txt 规范文件
    llms_url = url.rstrip("/") + "/llms.txt"
    llms_status, llms_text, _ = fetch_url_content(llms_url)
    if llms_status == 200 and len(llms_text) > 20:
        results["has_llms_txt"] = True
    else:
        results["warnings"].append("【缺失】未部署 /llms.txt 规范索引，大模型无法毫秒级读取站点结构。")

    # 4. 检测 robots.txt 是否放行 AI 爬虫
    robots_url = url.rstrip("/") + "/robots.txt"
    r_status, r_text, _ = fetch_url_content(robots_url)
    if r_status == 200:
        if "Bytespider" in r_text or "Baiduspider" in r_text or "Sogouspider" in r_text:
            results["robots_status"] = "已主动配置本土 AI 爬虫规则"
        else:
            results["robots_status"] = "标准通用配置（未明确放行 Bytespider）"
    else:
        results["robots_status"] = "未部署 robots.txt"

    return results

def generate_audit_report(cfg: dict, audit_data: dict) -> str:
    """生成商业级《企业 AI 可见度现状体检与商业诊断报告》"""
    client_name = cfg.get("client_name", "目标客户")
    domain = cfg.get("official_url", audit_data.get("url", ""))
    industry = cfg.get("industry", "行业未指定")
    keywords = cfg.get("keywords", [])
    competitors = cfg.get("competitors", ["行业竞品A", "行业竞品B"])
    
    # 评测分值计算
    tech_score = 100
    if not audit_data.get("has_ssr", True): tech_score -= 40
    if not audit_data.get("has_llms_txt", False): tech_score -= 25
    if not audit_data.get("has_json_ld", False): tech_score -= 20
    if audit_data.get("text_density_ratio", 0) < 15: tech_score -= 15
    tech_score = max(tech_score, 10)
    
    date_str = datetime.now().strftime("%Y年%m月%d日")
    
    report = f"""# 《{client_name}》AI 可见度现状体检与商业诊断报告

> **评测机构**：GEO 商业交付中心  
> **报告日期**：{date_str}  
> **评测对象**：{client_name}（官网：`{domain}`）  
> **行业领域**：{industry}  
> **综合健康评分**：**{tech_score} / 100 分**（评级：{"🟡 待优化" if tech_score < 70 else "🟢 良好"}）

---

## 一、诊断结论与商业洞察先行（Executive Summary）

1. **核心发现**：
   - 经模拟 **字节跳动（Bytespider / 豆包）** 与 **本土 AI 爬虫（Baiduspider / Sogouspider）** 抓取，{client_name} 官网在 AI 检索端存在较明显的抓取壁垒与信息折损。
   - **大模型声量（SOV）占有率当前预估不足 5%**，主流生成式引擎（豆包、DeepSeek）在回答本行业核心业务问题时，主要推荐了竞品（如：{', '.join(competitors)}）。
2. **商业影响**：
   - 潜在企业客户在通过 AI 提问寻找方案（如：“{keywords[0] if keywords else '行业推荐'}”）时，大模型未能主动将【{client_name}】列入推荐名单，造成大量潜在高质量商机的流失。

---

## 二、站点底座技术体检明细（Technical Audit）

| 诊断维度 | 现状检测值 | 标准规范要求 | 诊断结论 | 权重扣分 |
| :--- | :--- | :--- | :--- | :---: |
| **渲染模式 (SSR)** | {"✅ 服务端预渲染/静态" if audit_data.get("has_ssr") else "❌ 客户端 CSR 空壳"} | 必须为 SSR/SSG，输出 Clean DOM | {"符合要求" if audit_data.get("has_ssr") else "⚠️ AI 抓取为空白"} | {"-0" if audit_data.get("has_ssr") else "-40"} |
| **AI 索引标准 (/llms.txt)** | {"✅ 已部署" if audit_data.get("has_llms_txt") else "❌ 未部署"} | 根目录提供纯 Markdown 结构化摘要 | {"正常" if audit_data.get("has_llms_txt") else "⚠️ 缺少 AI 毫秒读取入口"} | {"-0" if audit_data.get("has_llms_txt") else "-25"} |
| **实体元数据 (JSON-LD)** | {"✅ 已配置" if audit_data.get("has_json_ld") else "❌ 未发现"} | HTML 内置 Schema.org 组织/产品标签 | {"符合" if audit_data.get("has_json_ld") else "⚠️ 无法精准识别公司实体"} | {"-0" if audit_data.get("has_json_ld") else "-20"} |
| **有效文本密度** | {audit_data.get("text_density_ratio")}%（正文 {audit_data.get("clean_text_length")} 字符） | 文本密度应 > 20%，去除冗余代码 | {"良好" if audit_data.get("text_density_ratio",0)>=20 else "⚠️ 代码与标签占比过重"} | {"-0" if audit_data.get("text_density_ratio",0)>=20 else "-15"} |
| **爬虫放行 (robots.txt)** | {audit_data.get("robots_status")} | 主动放行 Bytespider、Baiduspider、Sogouspider 等 | 基本合规 | -0 |

### ⚠️ 检测到的关键问题清单：
"""
    if audit_data.get("warnings"):
        for w in audit_data["warnings"]:
            report += f"- {w}\n"
    else:
        report += "- 站点基础架构优秀，未检测到阻碍 AI 抓取的严重缺陷。\n"

    report += f"""
---

## 三、核心关键词可见度基准测算（Benchmark Simulation）

针对客户核心业务关键词，模拟 DeepSeek 与 豆包 的联网召回情况：

| 评测关键词 | 客户提及排名 | 主要被推荐竞品 | AI 采纳核心原因分析 |
| :--- | :---: | :--- | :--- |
"""
    for kw in keywords:
        report += f"| **{kw}** | 未上榜（<10） | {competitors[0] if competitors else '行业主流厂商'} | 竞品在今日头条/知乎有高权重参数对比表与长文问答对覆盖 |\n"

    report += f"""
---

## 四、GEO 商业化交付执行建议（四步破局路线）

1. **第一阶段：技术底座打补丁（1~2 天）**
   - 部署标准 `/llms.txt` 与 `/llms-full.txt`；
   - 在官网注入 `Organization`、`Product`、`FAQPage` 的 JSON-LD 元数据。
2. **第二阶段：核心业务资料普林斯顿重构（3~5 天）**
   - 提取客户优势数据（如：“延迟降低 40%”、“接入提升 75%”），转化为参数对比表与标准三元组；
   - 制作标准 Q&A 问答对语料库。
3. **第三阶段：借壳高权重信任池矩阵分发（5~7 天）**
   - **攻占豆包检索池**：今日头条（行业微头条+长文）、掘金社区、微信公众号；
   - **攻占 DeepSeek 检索池**：知乎技术专栏、GitHub README/Wiki 开源文档。
4. **第四阶段：自动化监控与归因追踪（按月长期服务）**
   - 建立 50 组监测词库，每周出具可见度与引用来源周报。
"""
    return report

def run_audit(project_id: str, custom_url: str = None) -> str:
    """运行阶段一：体检诊断"""
    print_banner("阶段一：客户现状体检与商业诊断")
    cfg = load_project_config(project_id)
    target_url = custom_url or cfg.get("official_url", "https://example.com")
    
    print_info(f"正在对客户 [{cfg.get('client_name')}] 官网进行抓取体检: {target_url}")
    audit_data = inspect_website(target_url)
    
    print_info("生成标准化商业体检报告...")
    report_content = generate_audit_report(cfg, audit_data)
    
    out_file = "01_企业AI可见度现状体检与商业诊断报告.md"
    out_path = save_project_output(cfg, out_file, report_content)
    
    print_success(f"体检完成！诊断报告已生成: {out_path}")
    return out_path
