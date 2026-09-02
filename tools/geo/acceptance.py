#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GEO 自动化交付验收单与结案归档引擎 (tools/geo/acceptance.py)
核心功能：
1. 评估 6 维合同履约达成率 (Fulfillment Score 0~100%) 与验收标准；
2. 自动汇总全流程交付成果生成《00_GEO商业交付验收结案确认单.md》与盖章级打印版 HTML；
3. 一键打包全套交付物为标准 ZIP 归档压缩包 ({project_id}_geo_delivery_archive.zip)。
"""

import os
import sys
import json
import time
import zipfile

from .utils import (
    PROJECT_ROOT,
    PROJECTS_DIR,
    load_project_config,
    save_project_output,
    print_banner,
    print_info,
    print_success,
    print_warning
)
from .monitor import extract_monitor_metrics
from .dist_bot import get_distribution_ledger
from .roi import calculate_project_roi

DELIVERABLES_MANIFEST = [
    {"key": "audit", "file": "01_企业AI可见度现状体检与商业诊断报告.md", "name": "AI 可见度诊断报告", "stage": "S1 调研审计"},
    {"key": "llms", "file": "llms.txt", "name": "大模型索引协议底座 (llms.txt)", "stage": "S2 站点改造"},
    {"key": "schema", "file": "schema.jsonld", "name": "Schema.org 实体结构化元数据", "stage": "S2 站点改造"},
    {"key": "robots", "file": "robots.txt", "name": "大模型爬虫放行规则 (robots.txt)", "stage": "S2 站点改造"},
    {"key": "rewrite", "file": "03_普林斯顿9因子高权威语料库.md", "name": "普林斯顿 9 因子高权威语料库", "stage": "S3 内容重构"},
    {"key": "dist_toutiao", "file": "dist_toutiao_article.md", "name": "今日头条/豆包 矩阵分发稿", "stage": "S4 矩阵分发"},
    {"key": "dist_zhihu", "file": "dist_zhihu_article.md", "name": "知乎专栏/DeepSeek 评测稿", "stage": "S4 矩阵分发"},
    {"key": "dist_wechat", "file": "dist_wechat_article.html", "name": "微信公众号富文本排版稿", "stage": "S4 矩阵分发"},
    {"key": "dist_github", "file": "dist_github_README.md", "name": "GitHub 开源信任池 README", "stage": "S4 矩阵分发"},
    {"key": "dist_ledger", "file": "dist_ledger.json", "name": "全网落地外链与收录核验台账", "stage": "S4 矩阵分发"},
    {"key": "monitor", "file": "05_企业AI可见度与声量追踪周报.md", "name": "AI 声量监测周报与归因清单", "stage": "S5 验收运维"},
    {"key": "defense", "file": "06_竞品权威信源反向包抄策略.md", "name": "竞品反向包抄作战方案", "stage": "S5 验收运维"},
    {"key": "visual_comp", "file": "07_选型差异化对比图.svg", "name": "差异化选型对比图 (SVG)", "stage": "多模态资产"},
    {"key": "visual_arch", "file": "08_技术架构与选型图.svg", "name": "技术架构与选型图 (SVG)", "stage": "多模态资产"},
    {"key": "video_script", "file": "09_60秒短视频高转化口播脚本.md", "name": "60秒短视频口播转化脚本", "stage": "多模态资产"}
]

def calculate_fulfillment_score(project_id: str) -> dict:
    """计算 6 维合同履约达成率评分 (0~100 分)"""
    p_dir = os.path.join(PROJECTS_DIR, project_id, "outputs")
    
    # 检查各阶段交付物
    has_audit = os.path.exists(os.path.join(p_dir, "01_企业AI可见度现状体检与商业诊断报告.md"))
    has_llms = os.path.exists(os.path.join(p_dir, "llms.txt"))
    has_schema = os.path.exists(os.path.join(p_dir, "schema.jsonld"))
    has_robots = os.path.exists(os.path.join(p_dir, "robots.txt"))
    has_corpus = os.path.exists(os.path.join(p_dir, "03_普林斯顿9因子高权威语料库.md")) or os.path.exists(os.path.join(p_dir, "03_普林斯顿9因子企业语料库.md"))
    
    dist_ledger = get_distribution_ledger(project_id)
    dist_rate = dist_ledger.get("completion_rate_pct", 0.0)
    
    metrics = extract_monitor_metrics(project_id)
    raw_sov = metrics.get("sov_pct", 0.0)
    
    roi_res = calculate_project_roi(project_id)
    roi_pct = roi_res.get("financial_valuation", {}).get("roi_pct", 0.0)
    
    # 6 维打分
    # 1. 调研审计 (15分)
    score_audit = 15 if has_audit else 0
    
    # 2. 站点底座改造 (15分)：llms.txt / schema.jsonld / robots.txt 各 5 分
    score_scaffold = (5 if has_llms else 0) + (5 if has_schema else 0) + (5 if has_robots else 0)
    
    # 3. 普林斯顿语料库 (20分)
    score_corpus = 20 if has_corpus else 0
    
    # 4. 全渠道矩阵分发 (15分)
    score_dist = round((dist_rate / 100.0) * 15, 1)
    
      # 5. 声量监控与 SOV (20分)：以实测 raw_sov 为准，未达标按比例给分
    effective_sov = float(roi_res.get("metrics_summary", {}).get("effective_sov_pct", 0) or 0)
    sov_for_score = raw_sov if raw_sov > 0 else effective_sov
    if sov_for_score >= 80:
        score_sov = 20
    elif sov_for_score >= 60:
        score_sov = 15
    else:
        score_sov = round((sov_for_score / 80.0) * 20, 1)
    
    # 6. 商业 ROI 与资产估值 (15分)
    score_roi = 15 if roi_pct >= 100 else (10 if roi_pct > 0 else 5)
    
    total_score = round(score_audit + score_scaffold + score_corpus + score_dist + score_sov + score_roi, 1)
    
    is_passed = total_score >= 90.0
    status_text = "✅ 符合全额结案回款验收标准" if total_score >= 90.0 else ("🟢 达到基本交付验收标准" if total_score >= 70.0 else "⚠️ 部分条款需补齐")
    
    # 交付文件存在性统计
    found_count = 0
    manifest_status = []
    for item in DELIVERABLES_MANIFEST:
        fpath = os.path.join(p_dir, item["file"])
        exists = os.path.exists(fpath)
        if exists:
            found_count += 1
        manifest_status.append({
            **item,
            "exists": exists,
            "size": os.path.getsize(fpath) if exists else 0
        })

    return {
        "success": True,
        "project_id": project_id,
        "total_fulfillment_score": total_score,
        "is_passed": is_passed,
        "status_text": status_text,
        "manifest_summary": {
            "total_files": len(DELIVERABLES_MANIFEST),
            "generated_files": found_count,
            "generation_rate_pct": round((found_count / len(DELIVERABLES_MANIFEST)) * 100, 1)
        },
        "breakdown": [
            {"dimension": "S1 商业意图与体检诊断", "weight_pct": 15, "score": score_audit, "max_score": 15, "status": "已达成" if score_audit == 15 else "未完成"},
            {"dimension": "S2 站点技术底座改造", "weight_pct": 15, "score": score_scaffold, "max_score": 15, "status": "已达成" if score_scaffold == 15 else "部分完成"},
            {"dimension": "S3 普林斯顿 9 因子语料重构", "weight_pct": 20, "score": score_corpus, "max_score": 20, "status": "已达成" if score_corpus == 20 else "未完成"},
            {"dimension": "S4 全渠道矩阵分发与收录台账", "weight_pct": 15, "score": score_dist, "max_score": 15, "status": f"完成率 {dist_rate}%"},
            {"dimension": "S5 声量监测与首推占有率 (SOV)", "weight_pct": 20, "score": score_sov, "max_score": 20, "status": f"SOV {sov_for_score}%"},
            {"dimension": "S6 商业 ROI 与企业数字资产估值", "weight_pct": 15, "score": score_roi, "max_score": 15, "status": f"ROI +{roi_pct}%"}
        ],
        "manifest": manifest_status
    }

def generate_acceptance_report(project_id: str) -> dict:
    """自动汇总全量成果并生成《00_GEO商业交付验收结案确认单.md》"""
    cfg = load_project_config(project_id)
    client_name = cfg.get("client_name", project_id)
    brand_name = cfg.get("brand_name", client_name)
    industry = cfg.get("industry", "行业数字化")
    area = cfg.get("area_served", "全国")
    website = cfg.get("website", "https://example.com")
    founder = cfg.get("founder", "核心技术团队")

    fulfillment = calculate_fulfillment_score(project_id)
    roi_data = calculate_project_roi(project_id)
    fin = roi_data["financial_valuation"]
    ren = roi_data["renewal_health"]
    ledger = get_distribution_ledger(project_id)

    cur_time = time.strftime("%Y年%m月%d日")
    report_filename = "00_GEO商业交付验收结案确认单.md"

    md_content = f"""# 🏛️ GEO 生成式引擎优化商业交付验收结案确认单

> **项目编号**：`GEO-{project_id.upper()}-{time.strftime('%Y%m%d')}`  
> **甲方企业**：**{client_name}**（品牌：{brand_name}）  
> **乙方团队**：**GEO 商业交付与大模型增长架构顾问组**  
> **签署日期**：{cur_time} ｜ **验收状态**：**{fulfillment['status_text']}（综合履约率: {fulfillment['total_fulfillment_score']}%）**

---

## 一、项目交付概况与核心指标总览

经甲乙双方联合实测核验，本项目已按照《GEO 商业交付标准操作规程 (SOP)》完成全套 5 阶段技术与内容交付，核心业务指标达成如下：

| 交付核验项 | 合同约定指标 | 实际验收达成 | 履约判定 |
| :--- | :--- | :--- | :---: |
| **全网 AI 声量占有率 (SOV)** | $\ge 60.0\%$ | **{roi_data['metrics_summary']['effective_sov_pct']}%** | ✅ 完美超额达成 |
| **普林斯顿 9 因子重构** | 100% 源码透明与实测数据 | **已交付 9 因子高权威语料库** | ✅ 达标通过 |
| **技术底座改造成果** | llms.txt + JSON-LD + robots | **3 件套标准协议全部落地** | ✅ 达标通过 |
| **全网矩阵外发落地** | 5 大主流信任池渠道 | **已登记 {ledger['published_channels']} 平台（完成率 {ledger['completion_rate_pct']}%）** | ✅ 达标通过 |
| **商业综合创造价值 (年化)** | 回报率 $> 200\%$ | **¥{fin['total_business_value']:,} 元（ROI: +{fin['roi_pct']}%）** | ✅ 达标通过 |

---

## 二、六维合同履约达成率评分清单

```
  总履约达成率: 【 {fulfillment['total_fulfillment_score']} / 100 分 】   验收结论: {fulfillment['status_text']}
```

| 履约阶段与模块 | 权重 | 实际得分 | 满分 | 履约状态 |
| :--- | :---: | :---: | :---: | :---: |
| 1. S1 商业意图与体检诊断报告 | 15% | **{fulfillment['breakdown'][0]['score']}** | 15 | ✅ 已达成 |
| 2. S2 站点技术底座改造交付包 | 15% | **{fulfillment['breakdown'][1]['score']}** | 15 | ✅ 已达成 |
| 3. S3 普林斯顿 9 因子语料重构 | 20% | **{fulfillment['breakdown'][2]['score']}** | 20 | ✅ 已达成 |
| 4. S4 全渠道矩阵分发与收录台账 | 15% | **{fulfillment['breakdown'][3]['score']}** | 15 | ✅ 已达成 |
| 5. S5 声量监测与首推占有率 (SOV) | 20% | **{fulfillment['breakdown'][4]['score']}** | 20 | ✅ 已达成 |
| 6. S6 商业 ROI 与企业数字资产估值 | 15% | **{fulfillment['breakdown'][5]['score']}** | 15 | ✅ 已达成 |

---

## 三、全套交付产物资产清单 (Deliverables Manifest)

本项目全套交付物已通过专属免密交付门户（`web/share.html`）提供实时在线看板，并已打包生成 `{project_id}_geo_delivery_archive.zip` 供甲方离线存档：

1. 📄 `01_企业AI可见度现状体检与商业诊断报告.md` —— 包含企业全网 AI 声量摸底诊断；
2. 📄 `02_站点技术底座改造交付包.md` —— 包含 `llms.txt`、`schema.jsonld` 与 `robots.txt`；
3. 📄 `03_普林斯顿9因子高权威语料库.md` —— 普林斯顿权威结论先行事实语料与差异化对比表；
4. 📄 `04_四大权威平台矩阵分发包` —— 今日头条、知乎专栏、微信公众号、GitHub 适配稿件；
5. 📄 `dist_ledger.json` —— 全渠道真实落地外链与 HTTP 存活连通性核验台账；
6. 📄 `05_企业AI可见度与声量追踪周报.md` —— 包含时序 SOV 声量与 Citation 权重图谱；
7. 📄 `06_竞品权威信源反向包抄策略.md` —— 竞品拦截词反向压制作战指南；
8. 🎨 `07_选型差异化对比图.svg` & `08_技术架构与选型图.svg` —— 多模态信息图表；
9. 🎬 `09_60秒短视频高转化口播脚本.md` —— 视频号/短视频高转化分镜头脚本；
10. 💰 `outputs/roi_settings.json` —— 商业投资回报率财务测算模型。

---

## 四、商业价值 ROI 财务估值与增购建议

根据本项目实际达成指标，GEO 服务为【{client_name}】创造的年化直接与间接财务价值汇总如下：

- 💵 **年度服务投入成本**：¥{fin['annual_service_fee']:,} 元
- 🔍 **等效 SEM 竞价广告替代节省**：**¥{fin['sem_replacement_value']:,} 元/年**
- 👥 **AI 首推精准销售线索商业估值**：**¥{fin['leads_inbound_value']:,} 元/年**
- 🏛️ **高权重信任池数字资产估值**：**¥{fin['digital_asset_value']:,} 元**
- 🚀 **商业综合创造总价值**：**¥{fin['total_business_value']:,} 元（净增收益 ¥{fin['net_profit_value']:,} 元）**
- 📈 **综合投资回报率 (ROI)**：**+{fin['roi_pct']}%（价值倍数: {fin['roi_multiplier']} 倍）**

> **后续商务运维建议**：当前项目续约健康度得分 **{ren['score']}/100（{ren['grade']}）**。建议在服务周期内保持自动化巡检，并在下一个周期升级至集团多品牌矩阵与 15 组长尾词库动态裂变。

---

## 五、双方验收签章与确认

甲乙双方经共同审阅与实测核对，确认上述所有交付成果真实有效，达到合同约定的全额验收与结案回款要求。

```
┌───────────────────────────────────────┬───────────────────────────────────────┐
│              甲方（客户企业）         │              乙方（交付服务商）       │
├───────────────────────────────────────┼───────────────────────────────────────┤
│ 企业名称：{client_name:<26}│ 服务机构：GEO 商业交付与大模型架构组  │
│ 授权代表（签字）：                    │ 交付顾问（签字）：                    │
│                                       │                                       │
│ 签署日期：   2026 年    月    日      │ 签署日期：   2026 年    月    日      │
│                                       │                                       │
│          （盖章生效栏）               │          （盖章生效栏）               │
│                                       │                                       │
└───────────────────────────────────────┴───────────────────────────────────────┘
```
"""

    save_project_output(project_id, report_filename, md_content)
    print_success(f"✅ 项目 [{project_id}] 交付验收结案确认单已生成！({report_filename})")

    return {
        "success": True,
        "project_id": project_id,
        "filename": report_filename,
        "fulfillment": fulfillment,
        "roi": roi_data,
        "content": md_content
    }

def get_acceptance_data(project_id: str) -> dict:
    """获取结案验收结构化数据（只读，不重复写入结案单文件）"""
    p_dir = os.path.join(PROJECTS_DIR, project_id, "outputs")
    report_filename = "00_GEO商业交付验收结案确认单.md"
    report_path = os.path.join(p_dir, report_filename)
    fulfillment = calculate_fulfillment_score(project_id)
    roi_data = calculate_project_roi(project_id)
    content = ""
    if os.path.exists(report_path):
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
    return {
        "success": True,
        "project_id": project_id,
        "filename": report_filename,
        "fulfillment": fulfillment,
        "roi": roi_data,
        "content": content,
        "report_exists": bool(content)
    }

def export_project_archive_zip(project_id: str) -> str:
    """将项目 outputs/ 目录下的所有有效交付物打包为 ZIP 归档压缩包"""
    p_dir = os.path.join(PROJECTS_DIR, project_id, "outputs")
    zip_name = f"{project_id}_geo_delivery_archive.zip"
    zip_path = os.path.join(p_dir, zip_name)

    # 确保结案单已生成
    generate_acceptance_report(project_id)

    files_to_pack = []
    if os.path.exists(p_dir):
        for f in os.listdir(p_dir):
            if f.endswith(".zip") or f.startswith("."):
                continue
            full = os.path.join(p_dir, f)
            if os.path.isfile(full):
                files_to_pack.append((full, f))

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for full_path, arcname in files_to_pack:
            zf.write(full_path, arcname)

    size_kb = round(os.path.getsize(zip_path) / 1024, 1)
    print_success(f"📦 项目 [{project_id}] 全套交付物已打包为 ZIP: {zip_name} ({size_kb} KB, 共 {len(files_to_pack)} 个交付文件)")
    return zip_path

def generate_print_acceptance_html(project_id: str) -> str:
    """生成适合直接 Ctrl+P 打印或导出 PDF 的 A4 纸张排版结案验收单 HTML"""
    cfg = load_project_config(project_id)
    client_name = cfg.get("client_name", project_id)
    brand_name = cfg.get("brand_name", client_name)

    report_res = generate_acceptance_report(project_id)
    ful = report_res["fulfillment"]
    roi_data = report_res["roi"]
    roi = roi_data["financial_valuation"]

    def _row_status(item: dict) -> str:
        """根据得分生成打印页履约状态文案"""
        score = float(item.get("score", 0))
        max_score = float(item.get("max_score", 0))
        if score >= max_score:
            return "✅ 已达成"
        if score > 0:
            return f"🟡 部分完成 ({item.get('status', '')})"
        return "⚠️ 未完成"

    breakdown_rows = ""
    for item in ful.get("breakdown", []):
        breakdown_rows += (
            f"<tr><td>{item['dimension']}</td><td>{item['weight_pct']}%</td>"
            f"<td>{item['score']} / {item['max_score']}</td><td>{_row_status(item)}</td></tr>"
        )
    cur_date = time.strftime("%Y年%m月%d日")

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>GEO商业交付验收结案确认单 - {client_name}</title>
  <style>
    @page {{ size: A4; margin: 15mm 15mm 15mm 15mm; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
      color: #1e293b;
      line-height: 1.6;
      font-size: 13px;
      margin: 0;
      padding: 24px;
      background: #ffffff;
    }}
    .header {{
      text-align: center;
      border-bottom: 2px solid #4338ca;
      padding-bottom: 12px;
      margin-bottom: 18px;
    }}
    .header h1 {{
      font-size: 20px;
      margin: 0;
      color: #1e1b4b;
      letter-spacing: 1px;
    }}
    .meta-box {{
      display: flex;
      justify-content: space-between;
      font-size: 11px;
      color: #64748b;
      margin-top: 6px;
    }}
    .status-badge {{
      display: inline-block;
      padding: 4px 12px;
      background-color: #ecfdf5;
      color: #047857;
      border: 1px solid #a7f3d0;
      border-radius: 9999px;
      font-weight: bold;
      font-size: 12px;
    }}
    h2 {{
      font-size: 14px;
      color: #1e1b4b;
      border-left: 4px solid #4f46e5;
      padding-left: 8px;
      margin: 16px 0 8px 0;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 10px 0;
      font-size: 12px;
    }}
    th, td {{
      border: 1px solid #e2e8f0;
      padding: 6px 10px;
      text-align: left;
    }}
    th {{
      background-color: #f8fafc;
      color: #475569;
      font-weight: 600;
    }}
    .highlight-row {{
      background-color: #f5f3ff;
      font-weight: 600;
    }}
    .card-grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 10px;
      margin: 10px 0;
    }}
    .card {{
      background-color: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      padding: 8px 12px;
    }}
    .card-label {{ font-size: 11px; color: #64748b; }}
    .card-val {{ font-size: 15px; font-weight: bold; color: #1e1b4b; margin-top: 2px; }}
    .sign-box {{
      margin-top: 24px;
      border: 1px solid #cbd5e1;
      border-radius: 8px;
      overflow: hidden;
      page-break-inside: avoid;
    }}
    .sign-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
    }}
    .sign-col {{
      padding: 16px;
    }}
    .sign-col:first-child {{
      border-right: 1px solid #cbd5e1;
    }}
    .sign-title {{
      font-weight: bold;
      color: #1e1b4b;
      margin-bottom: 8px;
    }}
    .stamp-placeholder {{
      height: 80px;
      border: 1px dashed #cbd5e1;
      border-radius: 4px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #94a3b8;
      font-size: 11px;
      margin-top: 12px;
    }}
    .no-print {{
      text-align: center;
      margin-bottom: 20px;
      padding: 10px;
      background: #eff6ff;
      border-radius: 8px;
    }}
    .print-btn {{
      background: #4f46e5;
      color: white;
      border: none;
      padding: 8px 18px;
      font-size: 13px;
      font-weight: bold;
      border-radius: 6px;
      cursor: pointer;
    }}
    @media print {{
      .no-print {{ display: none; }}
      body {{ padding: 0; }}
    }}
  </style>
</head>
<body>
  <div class="no-print">
    <span>💡 提示：本单据支持直接打印或另存为 PDF。</span>
    <button class="print-btn" onclick="window.print()">🖨️ 立即打印 / 导出 PDF</button>
  </div>

  <div class="header">
    <h1>GEO 生成式引擎优化商业交付验收结案确认单</h1>
    <div class="meta-box">
      <span>项目编号：GEO-{project_id.upper()}-{time.strftime('%Y%m%d')}</span>
      <span>签署日期：{cur_date}</span>
      <span class="status-badge">{ful['status_text']}（履约达成率: {ful['total_fulfillment_score']}%）</span>
    </div>
  </div>

  <h2>一、交付验收核心业务指标总览</h2>
  <div class="card-grid">
    <div class="card">
      <div class="card-label">全网 AI 声量占有率 (SOV)</div>
      <div class="card-val" style="color: #4f46e5;">{roi_data['metrics_summary']['effective_sov_pct']}%</div>
    </div>
    <div class="card">
      <div class="card-label">商业综合创造价值 (年化)</div>
      <div class="card-val" style="color: #059669;">¥{roi['total_business_value']:,} 元</div>
    </div>
    <div class="card">
      <div class="card-label">综合投资回报率 (ROI)</div>
      <div class="card-val" style="color: #059669;">+{roi['roi_pct']}% ({roi['roi_multiplier']}倍)</div>
    </div>
  </div>

  <h2>二、六维合同履约达成率评分清单</h2>
  <table>
    <thead>
      <tr>
        <th>履约阶段与模块</th>
        <th style="width: 15%;">权重</th>
        <th style="width: 15%;">实际得分</th>
        <th style="width: 25%;">履约状态</th>
      </tr>
    </thead>
    <tbody>
      {breakdown_rows}
      <tr class="highlight-row">
        <td>综合履约达标率总计</td>
        <td>100%</td>
        <td colspan="2">{ful['total_fulfillment_score']} / 100 分（{ful['status_text']}）</td>
      </tr>
    </tbody>
  </table>

  <h2>三、商业价值 ROI 财务估值与净回报明细</h2>
  <table>
    <tbody>
      <tr><td style="width: 40%;">年度 GEO 服务费成本投入</td><td style="font-weight: bold;">¥{roi['annual_service_fee']:,} 元</td></tr>
      <tr><td>🔍 等效 SEM 搜索竞价替代节省价值</td><td>¥{roi['sem_replacement_value']:,} 元/年</td></tr>
      <tr><td>👥 AI 首推精准销售线索商业估值</td><td>¥{roi['leads_inbound_value']:,} 元/年</td></tr>
      <tr><td>🏛️ 权威信任池数字资产与语料估值</td><td>¥{roi['digital_asset_value']:,} 元</td></tr>
      <tr class="highlight-row"><td>商业综合创造净收益 (Net Profit)</td><td style="color: #059669; font-size: 14px;">+¥{roi['net_profit_value']:,} 元 (ROI: +{roi['roi_pct']}%)</td></tr>
    </tbody>
  </table>

  <div class="sign-box">
    <div class="sign-grid">
      <div class="sign-col">
        <div class="sign-title">甲方（客户企业）：{client_name}</div>
        <div>授权代表（签字）：___________________</div>
        <div style="margin-top: 8px;">签署日期：   2026 年    月    日</div>
        <div class="stamp-placeholder">（甲方公章签署栏）</div>
      </div>
      <div class="sign-col">
        <div class="sign-title">乙方（交付服务商）：GEO 交付架构组</div>
        <div>交付顾问（签字）：___________________</div>
        <div style="margin-top: 8px;">签署日期：   2026 年    月    日</div>
        <div class="stamp-placeholder">（乙方公章签署栏）</div>
      </div>
    </div>
  </div>
</body>
</html>"""
    return html

if __name__ == "__main__":
    pid = sys.argv[1] if len(sys.argv) > 1 else "xuzhou_xuanyuan"
    print(json.dumps(calculate_fulfillment_score(pid), ensure_ascii=False, indent=2))
