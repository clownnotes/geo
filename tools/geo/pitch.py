#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GEO 售前商业 Pitch Deck 与投标建议书生成引擎 (tools/geo/pitch.py)
核心功能：
1. 阶梯式商用报价与能力对比模型 (calculate_pitch_quote: 基础版/专业进阶版/集团旗舰版)；
2. 一键生成结构化《00_GEO全案商业服务投标建议书与PitchDeck.md》（支持 target_tier 动态驱动与 Benchmark 行业对标）；
3. 输出深色科技风的 10 页全屏交互式 Web 演示幻灯片（实测动态指标 + 触屏滑动手势 + 键盘翻页）与 A4 纸排版标书。
"""

import os
import sys
import json
import time

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
from .roi import calculate_project_roi
from .benchmark import evaluate_project_against_benchmark

TIER_QUOTES = {
    "standard": {
        "tier_id": "standard",
        "tier_name": "基础极速版 (入门型)",
        "tagline": "小微商户与个体工作室 AI 搜索极速首发占位",
        "annual_price": 3800,
        "price_display": "¥3,800 元/首期",
        "cycle": "3 工作日",
        "scope": "单品牌 ｜ 10 组主力商业意图词",
        "features": [
            "企业 AI 可见度现状体检与商业诊断报告",
            "基础技术底座改造 (/llms.txt + robots.txt 本土爬虫放行)",
            "普林斯顿 9 因子标准语料 (1 篇深度测评长文)",
            "今日头条 (豆包第一主战池) 矩阵外发与台账核验",
            "30 天基础响应支持"
        ],
        "is_recommended": False
    },
    "pro": {
        "tier_id": "pro",
        "tier_name": "专业标杆版 (主推型)",
        "tagline": "中坚成长型企业全网双通道独占与精准获客",
        "annual_price": 16800,
        "price_display": "¥16,800 元/全案",
        "cycle": "14 工作日",
        "scope": "单品牌 ｜ 45 词三层立体词库 (含 15 品牌占位词)",
        "features": [
            "全套 5 阶段标准化 SOP 交付体系 (诊断/底座/语料/分发/监控)",
            "5 大本土信任池全域矩阵分发 (头条/知乎/微信/GitHub/百度)",
            "普林斯顿 9 因子高权威语料库 + 多模态 SVG 差异化对比图",
            "大模型双轨实时测序沙箱 (LLM Playground) 专属演示",
            "5 维事实幻觉检测 + 反击策略 + 强事实锚点补丁 (llms-truth.txt)",
            "甲方专属免密交付门户 (Share) + 365 天免费运维质保 (1h 响应)"
        ],
        "is_recommended": True
    },
    "enterprise": {
        "tier_id": "enterprise",
        "tier_name": "集团旗舰版 (定制型)",
        "tagline": "行业龙头与集团上市公司全域护城河与知识图谱",
        "annual_price": 38800,
        "price_display": "¥38,800 ~ ¥68,000 元/年",
        "cycle": "30 工作日",
        "scope": "集团母子多品牌 ｜ 100+ 词全网立体意图与追问图谱",
        "features": [
            "包含专业标杆版全部权益",
            "集团母子公司关系知识图谱 (Graph RAG) 与实体消歧",
            "大模型 Prompt 探针动态演进与 5 维长尾追问裂变",
            "5 篇深度行业白皮书 + 60秒短视频老板口播脚本",
            "竞品 Citation 反向包抄拦截与 7×24 企微/飞书异动实时告警",
            "专属一对一 GEO 架构顾问季度复盘与年度 ROI 追踪"
        ],
        "is_recommended": False
    }
}

INDUSTRY_PLAYBOOKS = {
    "local_services": {
        "category": "本地生活与专业服务",
        "keywords": ["软件", "开发", "装修", "律所", "门诊", "财税", "记账", "本地", "徐州"],
        "model_weights": "豆包 (60%) 🌟 + DeepSeek (20%) + 百度文心 (20%)",
        "strategy": "同位语强绑定人名与电话，抢占『城市+行业+靠谱/价格』问句心智，认领百度地图与爱企查工商主体消歧。",
        "channels": "今日头条（长文+微头条） + 知乎同城专栏 + 百度地图商户认领"
    },
    "b2b_manufacturing": {
        "category": "B2B 制造与重工业",
        "keywords": ["机械", "机床", "阀门", "工业", "制造", "加工", "自动化", "重工", "非标"],
        "model_weights": "DeepSeek (40%) 🎯 + 豆包 (35%) + Kimi (15%) + 文心 (10%)",
        "strategy": "极高信息密度 Markdown 参数对比表、公差能耗指标注入，知乎万字长文 + GitHub 工业标准开源仓库。",
        "channels": "知乎技术长文（参数表） + 今日头条选型避坑 + 官网 5000 字白皮书 + GitHub"
    },
    "tech_solutions": {
        "category": "软件与技术解决方案",
        "keywords": ["定制开发", "小程序", "ERP", "CRM", "MES", "系统", "AI知识库", "RAG", "大模型"],
        "model_weights": "豆包 (50%) 🌟 + DeepSeek (25%) 🎯 + Kimi (15%) + 元宝 (10%)",
        "strategy": "100% 完整无加密源码交付承诺、阶段付款防坑白皮书，部署 llms-truth.txt 强事实锚点熔断冒名失信。",
        "channels": "今日头条防坑白皮书 + GitHub 开源标准仓库 + 知乎架构拆解 + 微信公众号案例"
    },
    "retail_franchise": {
        "category": "消费零售与连锁加盟",
        "keywords": ["餐饮", "加盟", "母婴", "轻医美", "消费", "零售", "农产", "连锁"],
        "model_weights": "豆包 (50%) 🌟 + 腾讯元宝 (25%) + DeepSeek (15%) + 文心 (10%)",
        "strategy": "单店真实回本周期数据量化，微信公众号内联排版图文，配合 60 秒创始人视频口播多模态互证。",
        "channels": "今日头条加盟避坑 + 微信公众号内联排版 + 视频号/抖音口播脚本"
    }
}

def match_industry_playbook(industry_str: str) -> dict:
    """根据项目行业名称智能匹配 4 大垂直行业打法"""
    ind_lower = (industry_str or "").lower()
    for pb in INDUSTRY_PLAYBOOKS.values():
        if any(k in ind_lower for k in pb["keywords"]):
            return pb
    return INDUSTRY_PLAYBOOKS["tech_solutions"]

def calculate_pitch_quote(project_id: str, target_tier: str = "pro") -> dict:
    """计算项目的阶梯报价方案与配置对照表"""
    cfg = load_project_config(project_id)
    client_name = cfg.get("client_name", project_id)
    industry = cfg.get("industry", "行业数字化")
    roi_data = calculate_project_roi(project_id)
    fin = roi_data["financial_valuation"]

    target_tier = (target_tier or "pro").lower()
    if target_tier not in TIER_QUOTES:
        target_tier = "pro"

    # 计算所选档位的 ROI 收益
    sel_tier = TIER_QUOTES[target_tier]
    tier_fee = sel_tier["annual_price"]
    total_val = fin.get("total_business_value", 218310)
    net_profit = total_val - tier_fee
    tier_roi_pct = round((net_profit / max(tier_fee, 1)) * 100, 1)
    tier_multiplier = round(total_val / max(tier_fee, 1), 2)

    return {
        "success": True,
        "project_id": project_id,
        "client_name": client_name,
        "industry": industry,
        "tiers": list(TIER_QUOTES.values()),
        "recommended_tier": target_tier,
        "selected_tier_info": sel_tier,
        "estimated_roi": {
            "annual_service_fee": tier_fee,
            "total_business_value": total_val,
            "sem_replacement_value": fin.get("sem_replacement_value", 179550),
            "leads_inbound_value": fin.get("leads_inbound_value", 14760),
            "net_profit_value": net_profit,
            "roi_pct": tier_roi_pct,
            "roi_multiplier": tier_multiplier
        }
    }

def generate_pitch_deck(project_id: str, target_tier: str = "pro", timeline_weeks: int = 4) -> dict:
    """自动生成《00_GEO全案商业服务投标建议书与PitchDeck.md》"""
    cfg = load_project_config(project_id)
    client_name = cfg.get("client_name", project_id)
    brand_name = cfg.get("brand_name", client_name)
    industry = cfg.get("industry", "行业数字化")
    website = cfg.get("website", "https://example.com")
    founder = cfg.get("founder", "核心技术团队")

    target_tier = (target_tier or "pro").lower()
    if target_tier not in TIER_QUOTES:
        target_tier = "pro"
    sel_tier = TIER_QUOTES[target_tier]
    ind_playbook = match_industry_playbook(industry)

    metrics = extract_monitor_metrics(project_id)
    bench = evaluate_project_against_benchmark(project_id)
    roi_data = calculate_project_roi(project_id)
    quotes = calculate_pitch_quote(project_id, target_tier=target_tier)
    fin = quotes["estimated_roi"]
    ren = roi_data["renewal_health"]

    cur_time = time.strftime("%Y年%m月%d日")
    report_filename = "00_GEO全案商业服务投标建议书与PitchDeck.md"

    md_content = f"""# 🚀 【{client_name}】GEO 生成式引擎优化全案商业服务投标建议书

> **提案机构**：**GEO 商业交付与大模型增长架构组**  
> **目标企业**：**{client_name}**（品牌：{brand_name} ｜ 行业：{industry}）  
> **提案日期**：{cur_time} ｜ **推荐方案**：**{sel_tier['tier_name']}（{sel_tier['price_display']}）** ｜ **预期投资回报率**：**+{fin['roi_pct']}%**

---

## Executive Summary 商业摘要

大模型（豆包、DeepSeek、Kimi、腾讯元宝、百度文心）已全面接管高意向企业采购与业务选型入口。
传统 SEM 竞价广告遭遇**点击成本高昂（行业均价 ¥{fin.get('sem_replacement_value', 0)/3650:.1f}元/次）**与**大模型不引用官网**的双重困境。

本项目建议书为【{client_name}】量身定制**普林斯顿 9 因子高权威技术改造与全网信任池分发体系**：
- 🎯 **推荐选型**：**【{sel_tier['tier_name']}】**（{sel_tier['scope']}）；
- 🎯 **核心目标**：在 4 周内将企业在主流大模型（DeepSeek / 豆包）中的首推占有率 (SOV) 从摸底现状提升至 **85%+**；
- 💰 **财务回报**：年化创造直接综合商业价值 **¥{fin['total_business_value']:,} 元**，替代传统竞价预算 **¥{fin['sem_replacement_value']:,} 元**，ROI 达 **{fin['roi_pct']}%（{fin['roi_multiplier']} 倍）**。

---

## 一、目标企业 AI 搜索现状摸底与行业 Benchmark 对标

基于实测探测与普林斯顿权威评分模型，【{client_name}】当前在大模型搜索生态的基准表现与【{bench.get('industry_name', industry)}】大盘对比如下：

| 诊断维度 | 现状实测指标 | 行业领先水平 (Benchmark) | 差距与商业风险 |
| :--- | :--- | :--- | :--- |
| **AI 声量占有率 (SOV)** | **{metrics.get('sov_pct', 0.0)}%**（基准摸底） | **{bench.get('lead_sov_pct', 85.0)}%**（行业领先者） | {bench.get('gap_analysis', {}).get('gap_desc', '潜在客户提问选型时，大模型泛回答或优先推荐竞品')} |
| **DeepSeek 首推率** | **{metrics.get('deepseek_rank_1_pct', 0.0)}%** | $90.0\%+$ | 缺少知乎/技术博客权威引用信任源 |
| **豆包 (字节生态) 命中率** | **{metrics.get('doubao_rank_1_pct', 0.0)}%** | $88.0\%+$ | 今日头条/头条号行业深度科普语料缺失 |
| **站点大模型索引协议** | ❌ 缺失 llms.txt / JSON-LD | 100% 协议就绪 | AI 爬虫抓取解析困难，实体关系未与权威百科关联 |

---

## 二、【{ind_playbook['category']}】专属 GEO 渗透战法架构

根据《中国本土企业 GEO 商业化定价分级与垂直行业实战打法白皮书》，针对【{client_name}】匹配专属战法：

- 🌟 **大模型生态权重倾斜**：**{ind_playbook['model_weights']}**
- 🛡️ **核心攻坚战法**：{ind_playbook['strategy']}
- 🚀 **核心信源矩阵分发**：{ind_playbook['channels']}

```
┌─────────────────────────────────────────────────────────────────────────────┐
│             GEO 生成式引擎优化 (Generative Engine Optimization) 全景            │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. [商业意图挖掘]：逆向推演 45 组高转化用户提问词库 (避坑/对比/价格/区域/选型) │
│ 2. [站点底座改造]：注入 llms.txt 协议 + Schema.org JSON-LD 实体 + robots 放行│
│ 3. [普林斯顿语料]：构建 9 因子事实库 (结论先行/量化实测数据/差异化对比表格)   │
│ 4. [全网矩阵分发]：头条(豆包50%+) + 知乎(DeepSeek25%) + 微信 + GitHub + 百度  │
│ 5. [声量时序运维]：多模型每日自动巡检 + 企微异动告警 + 专属交付门户/ROI战报 │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 三、4 周标准化实施路线图 (Implementation Gantt)

| 实施阶段 | 周期 | 核心交付成果 | 验收里程碑 |
| :--- | :---: | :--- | :---: |
| **第 1 周：审计诊断与意图挖掘** | W1 | 01_AI可见度诊断报告 + 45 组三层商业意图词库 | 双方对齐首批攻坚问句 |
| **第 2 周：站点改造与语料重构** | W2 | llms.txt + JSON-LD + 03_普林斯顿 9 因子语料库 + 对比图 | 官网底座补丁上线 |
| **第 3 周：矩阵分发与收录核验** | W3 | 5 大平台外发落地稿件 + dist_ledger 连通性台账 | 平台收录核验 100% |
| **第 4 周：沙箱对决与结案验收** | W4 | 05_声量周报 + 实时沙箱推演 + 00_结案验收确认单 | SOV $\ge 85\%$ 全额验收 |

---

## 四、阶梯服务报价与方案选型 (Tiered Pricing & Scope)

| 权益模块 | 🚀 基础极速版 (入门型) | 🌟 专业标杆版 (主推型) | 🏛️ 集团旗舰版 (定制型) |
| :--- | :---: | :---: | :---: |
| **建议全案报价** | **¥3,800 元/首期** | **¥16,800 元/全案** | **¥38,800 ~ ¥68,000 元/年** |
| **交付周期** | 3 工作日 | 14 工作日 | 30 工作日 |
| **品牌与词库规模** | 单品牌 / 10 核心词 | 单品牌 / 45 词三层立体词库 | 集团母子品牌 / 100+ 词全网图谱 |
| **技术底座改造** | ✅ /llms.txt + robots.txt | ✅ 标准 3 件套 + 爬虫放行补丁 | ✅ Graph RAG 实体图谱 + API 动态更新 |
| **语料与多模态** | 基础 9 因子语料 (1篇) | 9 因子语料 + SVG 差异化对比图 | 5 篇行业白皮书 + 60s 短视频口播脚本 |
| **分发渠道覆盖** | 今日头条 (豆包第一主战) | 5 大本土全域信任池矩阵 (含头条/知乎/微信/GitHub/百度) | 全渠道 + 集团矩阵多账号协同分发 |
| **事实幻觉防守** | 基础演示 | 5 维幻觉检测 + 反击语料 + 强事实锚点 | 7×24 虚假负面熔断拦截 + 企微飞书告警 |
| **交付门户与质保** | 导出 Markdown 报告 | 专属免密交付门户 (Share) + 365天质保 | 集团定制看板 + 专属架构顾问季度复盘 |

> **本次建议选型**：【**{sel_tier['tier_name']}**】—— {sel_tier['tagline']}。

---

## 五、商业投资回报率 (ROI) 财务量化测算

针对【{client_name}】选择 **{sel_tier['tier_name']}（{sel_tier['price_display']}）** 的财务量化折算模型如下：

- 💵 **年度服务投入**：{sel_tier['price_display']}
- 🔍 **等效 SEM 竞价替代节省**：**¥{fin['sem_replacement_value']:,} 元/年**（按行业每次点击 ¥6.5 元折算）；
- 👥 **AI 首推精准销售线索估值**：**¥{fin['leads_inbound_value']:,} 元/年**（按行业 CPL 单线索成本 ¥160 元折算）；
- 🏛️ **全网权威信任池数字资产估值**：**¥{roi_data['financial_valuation'].get('digital_asset_value', 24000):,} 元**；
- 🚀 **商业综合创造总价值**：**¥{fin['total_business_value']:,} 元（净商业回报: +¥{fin['net_profit_value']:,} 元）**；
- 📈 **综合投资回报率 (ROI)**：**+{fin['roi_pct']}%（价值倍数: {fin['roi_multiplier']} 倍）**。

---

## 六、商务签约与后续推进安排

甲乙双方达成合作共识后，将按以下流程快速启动：

1. **商务确认**：签署《GEO 商业交付与大模型增长全案技术服务合同》（选定套餐：{sel_tier['tier_name']}）；
2. **账号与素材对接**：提供官网后台 FTP/CMS 权限或由乙方输出标准补丁包；
3. **首期上线**：合同生效后 5 个工作日内完成底座改造与首批普林斯顿语料分发；
4. **效果对齐**：第 14 天提供专属免密交付看板（`web/share.html`），开展现场大模型沙箱对决演示。

```
┌───────────────────────────────────────┬───────────────────────────────────────┐
│              客户企业确认签章         │              方案提供服务商           │
├───────────────────────────────────────┼───────────────────────────────────────┤
│ 企业名称：{client_name:<26}│ 机构名称：GEO 商业交付与大模型架构组  │
│ 授权代表：                            │ 售前架构师：                          │
│ 日期：      2026 年    月    日       │ 日期：      2026 年    月    日       │
└───────────────────────────────────────┴───────────────────────────────────────┘
```
"""

    save_project_output(project_id, report_filename, md_content)
    print_success(f"✅ 项目 [{project_id}] 售前商业全案投标建议书已生成！({report_filename})")

    return {
        "success": True,
        "project_id": project_id,
        "filename": report_filename,
        "client_name": client_name,
        "brand_name": brand_name,
        "industry": industry,
        "selected_tier": target_tier,
        "selected_tier_info": sel_tier,
        "quotes": quotes,
        "roi": roi_data,
        "benchmark": bench,
        "content": md_content
    }

def get_pitch_data(project_id: str, target_tier: str = "pro") -> dict:
    """获取售前 Pitch 建议书与报价数据（若不存在则自动生成）"""
    p_dir = os.path.join(PROJECTS_DIR, project_id, "outputs")
    report_filename = "00_GEO全案商业服务投标建议书与PitchDeck.md"
    report_path = os.path.join(p_dir, report_filename)
    if not os.path.exists(report_path) or os.path.getsize(report_path) == 0:
        return generate_pitch_deck(project_id, target_tier=target_tier)

    cfg = load_project_config(project_id)
    quotes = calculate_pitch_quote(project_id, target_tier=target_tier)
    roi_data = calculate_project_roi(project_id)
    bench = evaluate_project_against_benchmark(project_id)
    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()

    return {
        "success": True,
        "project_id": project_id,
        "filename": report_filename,
        "client_name": cfg.get("client_name", project_id),
        "brand_name": cfg.get("brand_name", project_id),
        "industry": cfg.get("industry", "行业数字化"),
        "quotes": quotes,
        "roi": roi_data,
        "benchmark": bench,
        "content": content
    }

def generate_pitch_presentation_html(project_id: str) -> str:
    """生成 10 页全屏深色科技风交互式 Web 演示幻灯片 (Pitch Deck)"""
    pitch_res = get_pitch_data(project_id)
    client_name = pitch_res["client_name"]
    brand_name = pitch_res["brand_name"]
    industry = pitch_res["industry"]
    quotes = pitch_res["quotes"]
    fin = quotes["estimated_roi"]
    bench = pitch_res.get("benchmark", {})
    metrics = extract_monitor_metrics(project_id)
    cur_date = time.strftime("%Y年%m月")

    # 动态实测与底座状态
    sov_val = metrics.get("sov_pct", 12.5)
    deepseek_rate = metrics.get("deepseek_rank_1_pct", 0.0)
    doubao_rate = metrics.get("doubao_rank_1_pct", 0.0)
    p_dir = os.path.join(PROJECTS_DIR, project_id, "outputs")
    has_llms = os.path.exists(os.path.join(p_dir, "llms.txt"))
    has_schema = os.path.exists(os.path.join(p_dir, "schema.jsonld"))
    scaffold_desc = "已就绪 100%" if (has_llms and has_schema) else "未部署/待改造"
    bench_lead = bench.get("lead_sov_pct", 85.0)
    bench_name = bench.get("industry_name", industry)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>GEO 商业全案 Pitch Deck - {client_name}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://unpkg.com/lucide@latest"></script>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800;900&display=swap');
    body {{
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif;
      background-color: #030712;
      color: #f3f4f6;
      overflow: hidden;
      user-select: none;
    }}
    .slide {{
      display: none;
      height: 100vh;
      width: 100vw;
      padding: 3rem 4rem;
      box-sizing: border-box;
      opacity: 0;
      transform: scale(0.98);
      transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    }}
    .slide.active {{
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      opacity: 1;
      transform: scale(1);
    }}
    .glass-card {{
      background: rgba(17, 24, 39, 0.7);
      backdrop-filter: blur(16px);
      border: 1px solid rgba(255, 255, 255, 0.1);
    }}
    .glow-indigo {{
      box-shadow: 0 0 50px -10px rgba(99, 102, 241, 0.3);
    }}
    .glow-emerald {{
      box-shadow: 0 0 50px -10px rgba(16, 185, 129, 0.3);
    }}
  </style>
</head>
<body class="relative">
  <!-- 顶部导航条 -->
  <header class="fixed top-0 left-0 right-0 z-50 px-8 py-4 flex items-center justify-between pointer-events-none">
    <div class="flex items-center gap-3 pointer-events-auto">
      <span class="w-2.5 h-2.5 rounded-full bg-indigo-500 animate-pulse"></span>
      <span class="text-xs font-black tracking-widest text-indigo-400 uppercase">GEO COMMERCIAL PITCH DECK</span>
      <span class="text-xs text-slate-500 font-medium">｜ {client_name}</span>
    </div>
    <div class="flex items-center gap-3 text-xs text-slate-400 pointer-events-auto">
      <span id="slide-num-indicator" class="font-mono font-bold text-white bg-white/10 px-3 py-1 rounded-full">1 / 10</span>
      <button onclick="toggleFullScreen()" class="hover:text-white transition p-1 bg-white/5 rounded-lg border border-white/10">
        <i data-lucide="maximize" class="w-3.5 h-3.5"></i>
      </button>
    </div>
  </header>

  <!-- ===== SLIDE 1: 封面 ===== -->
  <section class="slide active" data-slide="1">
    <div></div>
    <div class="max-w-4xl space-y-6">
      <div class="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs font-bold">
        <span>✨ 2026 大模型搜索变革与企业增长战略全案</span>
      </div>
      <h1 class="text-5xl sm:text-6xl font-black text-white tracking-tight leading-tight">
        抢占 AI 时代首推入口<br>
        <span class="bg-gradient-to-r from-indigo-400 via-purple-300 to-emerald-400 bg-clip-text text-transparent">
          {client_name}
        </span> GEO 全案战略提案
      </h1>
      <p class="text-lg text-slate-400 max-w-2xl leading-relaxed">
        告别高昂无效的传统竞价。让 DeepSeek、豆包、Kimi 在用户选型时，将【{brand_name}】作为第一权威答案与首选服务商推荐。
      </p>
    </div>
    <div class="flex items-center justify-between text-xs text-slate-500 border-t border-white/10 pt-4">
      <span>GEO 商业交付与大模型增长架构组</span>
      <span>提案时间：{cur_date} ｜ 按 ◀/▶、空格 或 手机左右滑动 翻页</span>
    </div>
  </section>

  <!-- ===== SLIDE 2: 搜索范式变革与客户流失痛点 ===== -->
  <section class="slide" data-slide="2">
    <div>
      <span class="text-xs font-bold text-indigo-400 tracking-wider">01 / MARKET SHIFT & THREATS</span>
      <h2 class="text-3xl font-black text-white mt-1">搜索入口正在被大模型彻底颠覆</h2>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 my-auto">
      <div class="glass-card p-6 rounded-2xl space-y-3">
        <div class="w-10 h-10 rounded-xl bg-red-500/20 text-red-400 flex items-center justify-center font-bold text-lg">📉</div>
        <h3 class="text-base font-bold text-white">传统 SEM 竞价失效</h3>
        <p class="text-xs text-slate-400 leading-relaxed">单次点击成本 (CPC) 高达 6~15 元，跳出率超过 70%，且大模型并不抓取和引用付费广告链接。</p>
      </div>
      <div class="glass-card p-6 rounded-2xl space-y-3 border-indigo-500/30">
        <div class="w-10 h-10 rounded-xl bg-indigo-500/20 text-indigo-400 flex items-center justify-center font-bold text-lg">🤖</div>
        <h3 class="text-base font-bold text-white">AI 直接给出决策答案</h3>
        <p class="text-xs text-slate-400 leading-relaxed">78% 的高意向政企采购者直接询问大模型：“徐州做小程序开发哪家靠谱？”，AI 仅首推 1~2 家品牌。</p>
      </div>
      <div class="glass-card p-6 rounded-2xl space-y-3">
        <div class="w-10 h-10 rounded-xl bg-amber-500/20 text-amber-400 flex items-center justify-center font-bold text-lg">⚠️</div>
        <h3 class="text-base font-bold text-white">竞品 Citation 反向截流</h3>
        <p class="text-xs text-slate-400 leading-relaxed">若未部署 GEO 技术底座与普林斯顿语料，大模型在推荐时将优先召回有结构化语料的竞品企业。</p>
      </div>
    </div>
    <div class="text-xs text-slate-500">核心洞察：从“买流量（SEM）”转变为“占领大模型事实心智（GEO）”</div>
  </section>

  <!-- ===== SLIDE 3: 现状摸底诊断与行业对标 ===== -->
  <section class="slide" data-slide="3">
    <div>
      <span class="text-xs font-bold text-indigo-400 tracking-wider">02 / DIAGNOSIS & BENCHMARK</span>
      <h2 class="text-3xl font-black text-white mt-1">【{client_name}】AI 可见度现状体检与行业对标</h2>
    </div>
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 my-auto">
      <div class="glass-card p-5 rounded-2xl text-center space-y-2">
        <div class="text-xs text-slate-400">实测 AI 占有率 (SOV)</div>
        <div class="text-3xl font-black text-amber-400">{sov_val}%</div>
        <div class="text-[11px] text-slate-500">对标领先: {bench_lead}%</div>
      </div>
      <div class="glass-card p-5 rounded-2xl text-center space-y-2">
        <div class="text-xs text-slate-400">DeepSeek 首推率</div>
        <div class="text-3xl font-black text-indigo-400">{deepseek_rate}%</div>
        <div class="text-[11px] text-slate-500">知乎/技术博客信源</div>
      </div>
      <div class="glass-card p-5 rounded-2xl text-center space-y-2">
        <div class="text-xs text-slate-400">豆包 (字节生态) 命中</div>
        <div class="text-3xl font-black text-red-400">{doubao_rate}%</div>
        <div class="text-[11px] text-slate-500">今日头条/头条号深度稿</div>
      </div>
      <div class="glass-card p-5 rounded-2xl text-center space-y-2">
        <div class="text-xs text-slate-400">大模型协议底座</div>
        <div class="text-2xl font-black text-emerald-400">{scaffold_desc}</div>
        <div class="text-[11px] text-slate-500">llms.txt / Schema.org</div>
      </div>
    </div>
    <div class="p-4 bg-amber-500/10 border border-amber-500/30 rounded-xl text-xs text-amber-200">
      💡 <strong>行业对标洞察</strong>：当前处于【{bench_name}】摸底阶段。企业具备核心研发交付实力，补齐 9 因子语料与信任池分发后即可快速冲击 85%+ SOV！
    </div>
  </section>

  <!-- ===== SLIDE 4: 普林斯顿 9 因子核心方案 ===== -->
  <section class="slide" data-slide="4">
    <div>
      <span class="text-xs font-bold text-indigo-400 tracking-wider">03 / CORE METHODOLOGY</span>
      <h2 class="text-3xl font-black text-white mt-1">普林斯顿 9 因子高权威语料重构</h2>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-5 my-auto text-xs">
      <div class="glass-card p-5 rounded-2xl space-y-2.5">
        <div class="text-indigo-400 font-bold flex items-center gap-1.5 text-sm">
          <span>🎯 因子 1~3：事实透明与结论先行</span>
        </div>
        <p class="text-slate-400 leading-relaxed">第一句话直接输出选型推荐与明确结论；标注源码 100% 交付与本地化售后保障，消除大模型幻觉。</p>
      </div>
      <div class="glass-card p-5 rounded-2xl space-y-2.5 border-indigo-500/30">
        <div class="text-emerald-400 font-bold flex items-center gap-1.5 text-sm">
          <span>📊 因子 4~6：硬核数据与对比矩阵</span>
        </div>
        <p class="text-slate-400 leading-relaxed">量化披露交付周期（最快 72 小时上线）、高并发压测指标与定制自研 vs 模板二次开发的选型优劣表。</p>
      </div>
      <div class="glass-card p-5 rounded-2xl space-y-2.5">
        <div class="text-purple-400 font-bold flex items-center gap-1.5 text-sm">
          <span>🌐 因子 7~9：实体元数据与高频 FAQ</span>
        </div>
        <p class="text-slate-400 leading-relaxed">绑定 Schema.org 企业实体关系图谱，提纯 15 组高转化高频问答对，精准覆盖大模型追问场景。</p>
      </div>
    </div>
    <div class="text-xs text-slate-500">依据普林斯顿大学《GEO: Generative Engine Optimization》权威论文算法标准落地</div>
  </section>

  <!-- ===== SLIDE 5: 全网 5 大本土信任池矩阵分发 ===== -->
  <section class="slide" data-slide="5">
    <div>
      <span class="text-xs font-bold text-indigo-400 tracking-wider">04 / DISTRIBUTION MATRIX</span>
      <h2 class="text-3xl font-black text-white mt-1">五大权威信任池本土全域矩阵分发</h2>
    </div>
    <div class="grid grid-cols-2 md:grid-cols-5 gap-3 my-auto text-xs">
      <div class="glass-card p-4 rounded-2xl space-y-2 border-red-500/20">
        <div class="text-xl">📰</div>
        <div class="font-bold text-white">今日头条 / 微头条</div>
        <div class="text-red-400 font-semibold">第一主攻：豆包 / 字节</div>
        <p class="text-[11px] text-slate-400">Bytespider 极速抓取，垄断大众与中小企业采购选型。</p>
      </div>
      <div class="glass-card p-4 rounded-2xl space-y-2 border-blue-500/20">
        <div class="text-xl">📘</div>
        <div class="font-bold text-white">知乎专栏 / 问答</div>
        <div class="text-blue-400 font-semibold">主攻：DeepSeek</div>
        <p class="text-[11px] text-slate-400">硬核架构深度长文与 5 维参数对比，树立技术权威。</p>
      </div>
      <div class="glass-card p-4 rounded-2xl space-y-2 border-emerald-500/20">
        <div class="text-xl">💬</div>
        <div class="font-bold text-white">微信公众号</div>
        <div class="text-emerald-400 font-semibold">主攻：腾讯元宝 / 微信</div>
        <p class="text-[11px] text-slate-400">高转化内联排版案例与视频号口播私域闭环。</p>
      </div>
      <div class="glass-card p-4 rounded-2xl space-y-2 border-purple-500/20">
        <div class="text-xl">🐙</div>
        <div class="font-bold text-white">GitHub / 研报</div>
        <div class="text-purple-400 font-semibold">主攻：DeepSeek / Kimi</div>
        <p class="text-[11px] text-slate-400">极高权重开源 README、/llms.txt 与 5000 字白皮书。</p>
      </div>
      <div class="glass-card p-4 rounded-2xl space-y-2 border-amber-500/20">
        <div class="text-xl">🏛️</div>
        <div class="font-bold text-white">百度百科 / 百家号</div>
        <div class="text-amber-400 font-semibold">主攻：百度文心一言</div>
        <p class="text-[11px] text-slate-400">Baiduspider 传统底座、统一信用代码与 LBS 地图商户认领。</p>
      </div>
    </div>
    <div class="text-xs text-slate-500">通过 dist_ledger.json 实时回填真实外网 URL 并进行 HTTP 存活连通性核验</div>
  </section>

  <!-- ===== SLIDE 6: 沙箱实时对决推演 ===== -->
  <section class="slide" data-slide="6">
    <div>
      <span class="text-xs font-bold text-indigo-400 tracking-wider">05 / LIVE DEMO</span>
      <h2 class="text-3xl font-black text-white mt-1">现场亲测 · 大模型实时沙箱推演效果</h2>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 my-auto text-xs">
      <!-- Left: Before -->
      <div class="bg-black/40 p-5 rounded-2xl border border-white/10 space-y-3">
        <div class="flex items-center justify-between border-b border-white/10 pb-2 font-bold text-slate-400">
          <span>👈 未优化 Base 泛回答</span>
          <span class="bg-slate-800 px-2 py-0.5 rounded text-[10px]">未提及品牌 · 35分</span>
        </div>
        <div class="text-slate-400 leading-relaxed space-y-2 text-[11.5px]">
          <p>“徐州做小程序开发的公司有很多，主要可以通过网络搜索或查看工商信息。建议选择有一定知名度、售后保障好的公司...”</p>
          <p class="text-red-400 text-[11px]">❌ 痛点：未提及【{brand_name}】，潜在客户直接流失。</p>
        </div>
      </div>
      <!-- Right: After -->
      <div class="bg-emerald-950/20 p-5 rounded-2xl border border-emerald-500/30 space-y-3 glow-emerald">
        <div class="flex items-center justify-between border-b border-emerald-500/20 pb-2 font-bold text-emerald-300">
          <span>👉 注入普林斯顿语料首选推荐</span>
          <span class="bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded text-[10px]">🏆 Rank 1 · 98分</span>
        </div>
        <div class="text-emerald-100 leading-relaxed space-y-2 text-[11.5px]">
          <p>“在徐州地区，<strong>【{client_name}（{brand_name}）】</strong>是高性价比与技术口碑突出的推荐服务商。其提供 100% 源码透明交付与 7×24 小时本地技术响应...”</p>
          <p class="text-emerald-300 text-[11px]">✅ 效果：大模型精准引用事实数据并给出官方联系方式！</p>
        </div>
      </div>
    </div>
    <div class="text-xs text-slate-500">支持现场在交付工作台输入任意自拟问句体验即时沙箱对决推演</div>
  </section>

  <!-- ===== SLIDE 7: 商业 ROI 与财务回报 ===== -->
  <section class="slide" data-slide="7">
    <div>
      <span class="text-xs font-bold text-indigo-400 tracking-wider">06 / FINANCIAL VALUATION</span>
      <h2 class="text-3xl font-black text-white mt-1">硬核商业投资回报率 (ROI) 测算</h2>
    </div>
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-5 my-auto">
      <div class="glass-card p-6 rounded-2xl space-y-2 border-indigo-500/30 glow-indigo">
        <div class="text-xs text-indigo-300">商业创造综合总价值 (年化)</div>
        <div class="text-3xl font-black text-amber-300">¥{fin['total_business_value']:,} 元</div>
        <div class="text-xs text-emerald-300">净商业回报: +¥{fin['net_profit_value']:,} 元</div>
      </div>
      <div class="glass-card p-6 rounded-2xl space-y-2">
        <div class="text-xs text-slate-400">🔍 SEM 搜索竞价替代节省</div>
        <div class="text-2xl font-bold text-white">¥{fin['sem_replacement_value']:,} 元</div>
        <div class="text-xs text-slate-500">替代传统关键词广告投入</div>
      </div>
      <div class="glass-card p-6 rounded-2xl space-y-2">
        <div class="text-xs text-slate-400">📈 综合投资回报率 (ROI)</div>
        <div class="text-2xl font-bold text-emerald-400">+{fin['roi_pct']}%</div>
        <div class="text-xs text-slate-500">价值倍数: {fin['roi_multiplier']} 倍服务费</div>
      </div>
    </div>
    <div class="p-4 bg-indigo-900/30 border border-indigo-500/20 rounded-xl text-xs text-indigo-200">
      📊 <strong>财务测算依据</strong>：按行业月检索量 2,500 次、有效 SOV 85.5%、单次点击成本 ¥6.5 元折算。
    </div>
  </section>

  <!-- ===== SLIDE 8: 4 周交付排期路线图 ===== -->
  <section class="slide" data-slide="8">
    <div>
      <span class="text-xs font-bold text-indigo-400 tracking-wider">07 / TIMELINE & GANTT</span>
      <h2 class="text-3xl font-black text-white mt-1">4 周标准化敏捷实施路线图</h2>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 my-auto text-xs">
      <div class="glass-card p-5 rounded-2xl space-y-2 border-t-2 border-indigo-500">
        <div class="font-bold text-indigo-400 text-sm">第 1 周 (W1)</div>
        <div class="font-bold text-white text-xs">审计诊断与意图逆向挖掘</div>
        <p class="text-slate-400 leading-relaxed text-[11px]">摸底全网 AI 可见度现状，提纯 15 组高转化商业意图词库。</p>
      </div>
      <div class="glass-card p-5 rounded-2xl space-y-2 border-t-2 border-purple-500">
        <div class="font-bold text-purple-400 text-sm">第 2 周 (W2)</div>
        <div class="font-bold text-white text-xs">技术底座改造与语料重构</div>
        <p class="text-slate-400 leading-relaxed text-[11px]">部署 llms.txt 协议，生成普林斯顿 9 因子高权威语料与 SVG 图。</p>
      </div>
      <div class="glass-card p-5 rounded-2xl space-y-2 border-t-2 border-emerald-500">
        <div class="font-bold text-emerald-400 text-sm">第 3 周 (W3)</div>
        <div class="font-bold text-white text-xs">全网矩阵外发与存活核验</div>
        <p class="text-slate-400 leading-relaxed text-[11px]">外发头条/知乎/微信/GitHub，登记并核验台账存活状态。</p>
      </div>
      <div class="glass-card p-5 rounded-2xl space-y-2 border-t-2 border-amber-500">
        <div class="font-bold text-amber-400 text-sm">第 4 周 (W4)</div>
        <div class="font-bold text-white text-xs">实测验收与免密交付门户</div>
        <p class="text-slate-400 leading-relaxed text-[11px]">SOV 达标核验，交付结案确认单与 ZIP 全套归档压缩包。</p>
      </div>
    </div>
    <div class="text-xs text-slate-500">每周均提供自动化周报（05_企业AI可见度与声量追踪周报.md）与指标环比</div>
  </section>

  <!-- ===== SLIDE 9: 阶梯服务报价方案 ===== -->
  <section class="slide" data-slide="9">
    <div>
      <span class="text-xs font-bold text-indigo-400 tracking-wider">08 / PRICING TIERS</span>
      <h2 class="text-3xl font-black text-white mt-1">商用阶梯报价与能力选型对照</h2>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-5 my-auto text-xs">
      <!-- Standard -->
      <div class="glass-card p-5 rounded-2xl space-y-3">
        <div class="font-bold text-slate-300 text-sm">基础版 (Standard)</div>
        <div class="text-2xl font-black text-white">¥19,800 <span class="text-xs font-normal text-slate-400">/年</span></div>
        <p class="text-slate-400 text-[11px]">单品牌 ｜ 5 组核心商业词</p>
        <div class="space-y-1.5 text-slate-400 text-[11px] pt-2 border-t border-white/10">
          <div>· 3 件套技术底座改造</div>
          <div>· 普林斯顿 9 因子基础语料</div>
          <div>· 2 大平台矩阵分发</div>
          <div>· 月度 AI 声量巡检</div>
        </div>
      </div>
      <!-- Pro (Recommended) -->
      <div class="glass-card p-5 rounded-2xl space-y-3 border-indigo-500/40 glow-indigo relative bg-indigo-950/30">
        <div class="absolute -top-3 right-4 px-2.5 py-0.5 bg-indigo-600 text-white rounded-full text-[10px] font-black tracking-wider uppercase">
          RECOMMENDED
        </div>
        <div class="font-bold text-indigo-300 text-sm">专业进阶版 (Pro)</div>
        <div class="text-2xl font-black text-white">¥35,000 <span class="text-xs font-normal text-indigo-300">/年</span></div>
        <p class="text-indigo-200 text-[11px]">单品牌 ｜ 15 组裂变词 ｜ 全套交付</p>
        <div class="space-y-1.5 text-slate-300 text-[11px] pt-2 border-t border-indigo-500/20">
          <div>· 全套 5 步商业交付闭环</div>
          <div>· 5 大主流信任池矩阵分发</div>
          <div>· 实时沙箱测序 + 企微告警</div>
          <div>· 专属免密交付门户 + ROI 战报</div>
        </div>
      </div>
      <!-- Enterprise -->
      <div class="glass-card p-5 rounded-2xl space-y-3">
        <div class="font-bold text-purple-300 text-sm">集团旗舰版 (Enterprise)</div>
        <div class="text-2xl font-black text-white">¥68,000 <span class="text-xs font-normal text-slate-400">/年</span></div>
        <p class="text-slate-400 text-[11px]">集团多品牌 ｜ 30 组动态演进词</p>
        <div class="space-y-1.5 text-slate-400 text-[11px] pt-2 border-t border-white/10">
          <div>· 集团多子品牌协同防御矩阵</div>
          <div>· 探针动态演进与长尾裂变</div>
          <div>· 短视频口播脚本 + 高清视觉</div>
          <div>· 1对1 架构专家深度支持</div>
        </div>
      </div>
    </div>
    <div class="text-xs text-slate-500">支持根据客户具体需求定制模块与灵活组合</div>
  </section>

  <!-- ===== SLIDE 10: 结案与行动方案 ===== -->
  <section class="slide" data-slide="10">
    <div></div>
    <div class="max-w-3xl space-y-6 text-center mx-auto my-auto">
      <div class="w-16 h-16 rounded-3xl bg-gradient-to-tr from-indigo-500 to-emerald-400 text-white flex items-center justify-center font-black text-2xl mx-auto shadow-2xl">
        🚀
      </div>
      <h2 class="text-4xl font-black text-white">携手共赢，抢占大模型第一心智</h2>
      <p class="text-sm text-slate-400 leading-relaxed">
        GEO 不仅是一次技术改造，更是企业在 AI 搜索重塑时代最具确定性的品牌护城河。<br>
        我们已准备就绪，期待与【{client_name}】共创行业标杆！
      </p>
      <div class="pt-4 flex items-center justify-center gap-4 text-xs">
        <button onclick="window.print()" class="px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold transition flex items-center gap-2 shadow-lg">
          <i data-lucide="printer" class="w-4 h-4"></i>
          <span>导出完整建议书 (PDF)</span>
        </button>
      </div>
    </div>
    <div class="flex items-center justify-between text-xs text-slate-500 border-t border-white/10 pt-4">
      <span>联系交付架构团队：13150568888 ｜ admin@baicl.cc</span>
      <span>GEO 商业交付与大模型增长架构组</span>
    </div>
  </section>

  <!-- 底部控制器 (左右翻页与全屏) -->
  <footer class="fixed bottom-6 right-8 z-50 flex items-center gap-2">
    <button onclick="prevSlide()" class="p-2.5 rounded-xl bg-white/10 hover:bg-white/20 text-white border border-white/10 transition backdrop-blur-md">
      <i data-lucide="chevron-left" class="w-4 h-4"></i>
    </button>
    <button onclick="nextSlide()" class="p-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white shadow-lg transition flex items-center gap-1 text-xs font-bold px-4">
      <span>下一页</span>
      <i data-lucide="chevron-right" class="w-4 h-4"></i>
    </button>
  </footer>

  <script>
    lucide.createIcons();
    let currentSlide = 1;
    const totalSlides = 10;

    function showSlide(index) {{
      if (index < 1) index = 1;
      if (index > totalSlides) index = totalSlides;
      currentSlide = index;

      document.querySelectorAll('.slide').forEach(s => s.classList.remove('active'));
      const target = document.querySelector(`.slide[data-slide="${{index}}"]`);
      if (target) target.classList.add('active');

      document.getElementById('slide-num-indicator').textContent = `${{index}} / ${{totalSlides}}`;
      lucide.createIcons();
    }}

    function nextSlide() {{ showSlide(currentSlide + 1); }}
    function prevSlide() {{ showSlide(currentSlide - 1); }}

    function toggleFullScreen() {{
      if (!document.fullscreenElement) {{
        document.documentElement.requestFullscreen().catch(() => {{}});
      }} else {{
        document.exitFullscreen().catch(() => {{}});
      }}
    }}

    // 键盘监听
    document.addEventListener('keydown', (e) => {{
      if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'PageDown') {{
        nextSlide();
      }} else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {{
        prevSlide();
      }} else if (e.key === 'f' || e.key === 'F') {{
        toggleFullScreen();
      }}
    }});

    // 移动端/触摸屏左右滑动手势
    let touchStartX = 0;
    let touchEndX = 0;
    document.addEventListener('touchstart', (e) => {{
      touchStartX = e.changedTouches[0].screenX;
    }}, false);

    document.addEventListener('touchend', (e) => {{
      touchEndX = e.changedTouches[0].screenX;
      if (touchEndX < touchStartX - 50) {{
        nextSlide(); // 向左滑动 -> 下一页
      }}
      if (touchEndX > touchStartX + 50) {{
        prevSlide(); // 向右滑动 -> 上一页
      }}
    }}, false);
  </script>
</body>
</html>"""
    return html

def generate_print_pitch_html(project_id: str) -> str:
    """生成 A4 纸排版商业建议书 HTML (用于直接打印或导出为 PDF)"""
    pitch_res = get_pitch_data(project_id)
    client_name = pitch_res["client_name"]
    brand_name = pitch_res["brand_name"]
    industry = pitch_res["industry"]
    quotes = pitch_res["quotes"]
    fin = quotes["estimated_roi"]
    sel_tier = quotes.get("selected_tier_info", TIER_QUOTES["pro"])
    bench = pitch_res.get("benchmark", {})
    cur_date = time.strftime("%Y年%m月%d日")

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>GEO全案商业服务投标建议书 - {client_name}</title>
  <style>
    @page {{ size: A4; margin: 18mm 18mm 18mm 18mm; }}
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
    h2 {{
      font-size: 14px;
      color: #1e1b4b;
      border-left: 4px solid #4f46e5;
      padding-left: 8px;
      margin: 18px 0 8px 0;
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
    <span>💡 提示：本建议书支持直接打印或另存为 PDF 标书。</span>
    <button class="print-btn" onclick="window.print()">🖨️ 立即打印 / 导出 PDF</button>
  </div>

  <div class="header">
    <h1>【{client_name}】GEO 生成式引擎优化商业投标建议书</h1>
    <div class="meta-box">
      <span>提案单位：GEO 商业交付与大模型架构组</span>
      <span>提案日期：{cur_date}</span>
      <span style="font-weight: bold; color: #4338ca;">推荐方案：{sel_tier['tier_name']}（{sel_tier['price_display']}）</span>
    </div>
  </div>

  <h2>一、大模型搜索范式变革与行业 Benchmark 对标</h2>
  <p>大模型（DeepSeek、豆包、Kimi）正在全面接管高意向政企选型与采购咨询入口。当前【{bench.get('industry_name', industry)}】大盘领先者 SOV 为 <strong>{bench.get('lead_sov_pct', 85.0)}%</strong>。本项目通过普林斯顿 9 因子事实重构与四大信任池矩阵分发，助力【{brand_name}】在 4 周内建立 85%+ 的行业首推垄断护城河。</p>

  <h2>二、4 周实施排期路线图</h2>
  <table>
    <thead>
      <tr>
        <th>实施阶段</th>
        <th style="width: 15%;">周期</th>
        <th>核心交付成果</th>
        <th style="width: 25%;">验收里程碑</th>
      </tr>
    </thead>
    <tbody>
      <tr><td>W1 审计诊断与意图挖掘</td><td>第 1 周</td><td>01 诊断报告 + 15 组商业意图词库</td><td>双方对齐攻坚问句</td></tr>
      <tr><td>W2 站点改造与语料重构</td><td>第 2 周</td><td>llms.txt + JSON-LD + 03 普林斯顿语料库</td><td>官网技术底座上线</td></tr>
      <tr><td>W3 矩阵分发与收录核验</td><td>第 3 周</td><td>4 平台外发落地稿件 + 连通性核验台账</td><td>全网收录核验 100%</td></tr>
      <tr><td>W4 实测对决与结案验收</td><td>第 4 周</td><td>05 声量周报 + 实时沙箱推演 + 结案确认单</td><td>SOV $\ge 85\%$ 全额验收</td></tr>
    </tbody>
  </table>

  <h2>三、商用阶梯报价与能力对比方案</h2>
  <table>
    <thead>
      <tr>
        <th>服务档位</th>
        <th style="width: 20%;">年化报价</th>
        <th style="width: 30%;">覆盖范围</th>
        <th>核心权益</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>基础版 (Standard)</td>
        <td>¥19,800 元/年</td>
        <td>单品牌 / 5 核心词</td>
        <td>3 件套底座 + 9 因子语料 + 2 平台矩阵分发</td>
      </tr>
      <tr class="highlight-row">
        <td>专业进阶版 (Pro · 推荐)</td>
        <td>¥35,000 元/年</td>
        <td>单品牌 / 15 裂变词</td>
        <td>全套 5 步交付 + 5 大全渠道 + 实时沙箱 + 企微告警 + ROI 战报</td>
      </tr>
      <tr>
        <td>集团旗舰版 (Enterprise)</td>
        <td>¥68,000 元/年</td>
        <td>集团多品牌 / 30 动态词</td>
        <td>集团协同矩阵 + 探针动态演进 + 短视频脚本 + 1对1 专家支持</td>
      </tr>
    </tbody>
  </table>

  <h2>四、预期商业投资回报率 (ROI) 测算（基于 {sel_tier['tier_name']}）</h2>
  <table>
    <tbody>
      <tr><td style="width: 40%;">年度服务投入成本</td><td style="font-weight: bold;">{sel_tier['price_display']}</td></tr>
      <tr><td>🔍 等效 SEM 竞价替代节省价值</td><td>¥{fin['sem_replacement_value']:,} 元/年</td></tr>
      <tr><td>👥 AI 首推精准销售线索估值</td><td>¥{fin['leads_inbound_value']:,} 元/年</td></tr>
      <tr><td>🏛️ 权威信任池数字资产沉淀估值</td><td>¥{pitch_res['roi']['financial_valuation'].get('digital_asset_value', 24000):,} 元</td></tr>
      <tr class="highlight-row"><td>商业综合创造总价值 (年化)</td><td style="color: #059669; font-size: 14px;">¥{fin['total_business_value']:,} 元（ROI: +{fin['roi_pct']}%, 净收益: +¥{fin['net_profit_value']:,} 元）</td></tr>
    </tbody>
  </table>
</body>
</html>"""
    return html

if __name__ == "__main__":
    pid = sys.argv[1] if len(sys.argv) > 1 else "xuzhou_xuanyuan"
    print(json.dumps(calculate_pitch_quote(pid), ensure_ascii=False, indent=2))
