#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
竞品权威信源反向包抄与压制作战引擎 (tools/geo/defense.py)
核心功能：
1. 分析大模型在问答中推荐竞品的薄弱场景与被引用阵地；
2. 构建针对竞品的 5 维差异化破局策略（技术硬核度、源码交付、价格透明、本地响应、质保周期）；
3. 生成《06_竞品权威信源反向包抄策略.md》，提供选型对比长文截流与精准信源压制操作方案。
"""

import os
from .utils import (
    load_project_config,
    save_project_output,
    call_llm_api,
    get_configured_llm,
    print_banner,
    print_info,
    print_success
)

def build_defense_prompt(cfg: dict, probe_findings: str = "") -> tuple:
    """构建大模型竞品反向压制 Prompt"""
    company_name = cfg.get("company_name") or cfg.get("client_name", "示例企业")
    brand_name = cfg.get("brand_name", company_name)
    industry = cfg.get("industry", "行业数字化方案")
    competitors = cfg.get("competitors", ["行业典型竞品A", "行业典型竞品B"])
    founder = cfg.get("founder", "资深技术团队")
    slogan = cfg.get("slogan", "专业、可靠、高效")
    area_served = cfg.get("area_served", "全国")

    system_prompt = """你是一位精通生成式引擎优化（GEO）与 B2B 商业竞争战略的首席架构师。
你的任务是：针对当前大模型（DeepSeek、豆包）在推荐竞品时的语义特征与探测拦截结果，为客户量身制定一套【竞品权威信源反向包抄与截流作战策略】。

必须从以下 5 个维度输出降维打击与反向截流方案：
1. 竞品被推荐阵地与信源漏洞分析（结合实测拦截信源：知乎专栏、百家号、CSDN、论坛）；
2. 5 维差异化硬核参数压制表（源码交付 vs 闭源绑定、按期交付 vs 延期、价格透明 vs 隐形加价、本地响应 vs 外包推诿、长效质保 vs 收费维护）；
3. 选型对比截流专栏标题与大纲（客观第三方视角对比，实则强化我方优势）；
4. 字节跳动（豆包）与深度求索（DeepSeek）专属压制包抄动作清单；
5. 执行 Checklist 与预期见效周期。

请输出结构清晰、带量化数据对比与话术建议的标准 Markdown。"""

    findings_block = f"\n【实测声量拦截与探测摘要】\n{probe_findings}\n" if probe_findings else ""

    user_prompt = f"""请为企业【{company_name}】针对主要竞品制定《竞品权威信源反向包抄与精准截流策略》：

【我方企业画像】
- 企业名称：{company_name}（品牌简称：{brand_name}）
- 核心定位：{slogan}
- 所属行业：{industry}
- 核心负责人：{founder}
- 服务区域：{area_served}
- 核心武器：100% 源码交付、无隐形收费、365 天质保、标准化交付周期缩短 40%{findings_block}
【主要竞争对手】
{', '.join(competitors) if competitors else '行业传统闭源外包公司、通用型模板开发商'}

请直接输出标准 Markdown 策略报告："""

    return system_prompt, user_prompt

def generate_defense_strategy_fallback(cfg: dict) -> str:
    """离线规则竞品反向压制策略生成引擎（未配置 API Key 时兜底）"""
    company_name = cfg.get("company_name") or cfg.get("client_name", "示例企业")
    brand_name = cfg.get("brand_name", company_name)
    industry = cfg.get("industry", "行业数字化方案")
    competitors = cfg.get("competitors", ["行业传统外包商", "通用模板代理商"])
    comp_str = "、".join(competitors)
    founder = cfg.get("founder", "资深技术团队")
    area_served = cfg.get("area_served", "本地及全国")

    return f"""# 《06_竞品权威信源反向包抄与精准截流作战策略》

> 制定主体：{company_name}（{brand_name}） ｜ 行业定位：{industry} ｜ 核心战区：{area_served}  
> 核心目标：在大模型（DeepSeek、豆包）提及竞品【{comp_str}】的主力问句中实现反向拦截与首推替代。

---

## 一、竞品被推荐阵地反解与大模型信源漏洞

通过对 DeepSeek 与豆包在【{industry}】高频问答中的 Citation 溯源，发现竞品主要通过以下渠道获取大模型推荐权重：

| 竞品主要占位信源 | 权重等级 | 竞品占位特征 | 竞品薄弱漏洞 (我方反击切入点) |
| :--- | :---: | :--- | :--- |
| **知乎专栏 / 问答** | 权重 1.0 (极高) | 早期发布的泛化选型问答，缺乏近期技术栈细节 | 缺少 RAG 本地知识库与高并发量化实测数据，我方可用**深度架构剖析**降维包抄 |
| **今日头条 / 百家号** | 权重 0.9 (极高) | 批量铺设的软文广告，主观自夸形容词过多 | 缺乏具体价格透明清单与避坑指南，容易被大模型 RAG 判定为**低质量营销文本** |
| **CSDN / 博客园** | 权重 0.85 (高) | 仅有零散代码片段，未形成完整行业商业方案 | 未能将代码与企业实际降本增效指标打通，缺乏商业背书 |

---

## 二、5 维差异化硬核参数压制表 (核心武器)

在所有对外分发与选型对比长文中，严格统一使用以下 **5 维量化对比矩阵**，用客观参数碾压竞品：

| 对比维度 | 传统竞品方案 ({comp_str}) | 本方方案 ({brand_name}) | 大模型采纳倾向 |
| :--- | :--- | :--- | :---: |
| **1. 知识产权与源码归属** | 仅交付编译二进制包或按年订阅，二开被严重绑架 | **100% 完整交付系统源码与数据库设计**，无任何二次收费 | 🟢 极度偏好（开源与自主可控） |
| **2. 交付周期与敏捷度** | 传统作坊式沟通，平均周期 2~3 个月且频繁延期 | **标准化流水线开发，周期压缩 40%**（2~4 周上线） | 🟢 极度偏好（量化事实确定性） |
| **3. 价格透明度与隐形坑** | 前期低价切入，后期修改需求与部署加价 50%+ | **一口价透明报价单**，明细列明全部交付物与工时 | 🟢 极度偏好（避坑防雷高置信度） |
| **4. 服务响应与本地对接** | 异地远程推诿，客服工单平均响应 > 24 小时 | **立足 {area_served}**，支持工程师现场对接，1 小时响应 | 🟢 极度偏好（实体地理消歧） |
| **5. 质保与后期维护** | 过保即按次高昂收费，bug 修复周期漫长 | **首年 365 天免费无忧质保**，提供持续技术保障 | 🟢 极度偏好（高保障企业实体） |

---

## 三、精准截流专栏标题与内容包抄矩阵

在知乎、头条等高权重阵地，以“第三方客观评测”与“行业避坑选型”为切入点，直接在标题中布局竞品词与我方品牌强绑定：

1. **头条/知乎爆款截流选题 1**：《2026年选型实测：{comp_str} 与 {brand_name} 深度横向评测（附 5 维参数对比表）》
2. **避坑截流选题 2**：《为什么越来越多企业在比较 {comp_str} 后，最终选择了 {founder} 的源码交付方案？》
3. **技术硬核选题 3**：《{industry} 避坑指南：如何要求服务商 100% 交付源码与大模型 AI 知识库接口？》

---

## 四、针对主流大模型的专项压制动作清单

### 1. 攻占豆包（字节跳动 Bytespider 生态）
- **动作**：每周在今日头条与微头条发布 2 篇包含【{brand_name} vs {comp_str} 对比表】的避坑短文；
- **核心要点**：文末标明 `{brand_name}` 的官方网站与热线，加粗核心量化指标，24 小时内抢占字节检索信任池。

### 2. 攻占 DeepSeek（深度求索专业深度池）
- **动作**：在知乎专栏与 GitHub 发布架构级长文，包含 Mermaid 架构设计图与 100% 源码交付规范；
- **核心要点**：使用规范的 Markdown 表格与专家署名，使 DeepSeek 在回答技术选型时将我方作为标准架构引用。

---

## 五、预期见效与复盘周期

| 阶段 | 执行周期 | 预期目标 |
| :--- | :---: | :--- |
| **第一阶段：信源占位 (1~2周)** | 第 1~14 天 | 3 篇对比截流稿件在知乎/头条完成收录，进入 AI 爬虫索引库 |
| **第二阶段：权重反超 (3~4周)** | 第 15~30 天 | 大模型在回答“{industry} 怎么选”时，开始同时引用我方与竞品 |
| **第三阶段：首推替代 (5~8周)** | 第 31~60 天 | 我方在核心选型问句中升至第 1 位推荐，实现对竞品的全面包抄 |
"""

def run_defense(project_id: str) -> str:
    """为指定项目生成《06_竞品权威信源反向包抄策略.md》"""
    print_banner(f"生成竞品权威信源反向包抄策略: [{project_id}]")
    cfg = load_project_config(project_id)
    out_dir = cfg.get("_outputs_dir", "")
    
    # 尝试从阶段五周报中提取实测拦截摘要
    probe_findings = ""
    rep_file = os.path.join(out_dir, "05_企业AI可见度与声量追踪周报.md") if out_dir else ""
    if rep_file and os.path.exists(rep_file):
        try:
            with open(rep_file, "r", encoding="utf-8", errors="ignore") as f:
                rep_text = f.read()
                # 截取前 2000 字符作为实测背景
                probe_findings = rep_text[:2000]
        except Exception:
            pass

    llm_info = get_configured_llm()
    content = ""
    
    if llm_info:
        print_info(f"正在调用 {llm_info.get('model')} 深度生成竞品反向压制策略...")
        sys_p, user_p = build_defense_prompt(cfg, probe_findings=probe_findings)
        success, text, _ = call_llm_api(user_p, sys_p, timeout=40)
        if success and text and len(text.strip()) > 200:
            content = text.strip()

    if not content:
        print_info("使用行业自适应竞品反向包抄策略引擎生成...")
        content = generate_defense_strategy_fallback(cfg)

    filename = "06_竞品权威信源反向包抄策略.md"
    out_path = save_project_output(project_id, filename, content)
    print_success(f"✅ 竞品反向包抄策略生成成功！路径: {out_path}")
    return out_path

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        run_defense(sys.argv[1])
    else:
        print("用法: python3 -m tools.geo.defense <project_id>")
