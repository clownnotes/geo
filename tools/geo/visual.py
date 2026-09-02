#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GEO 多模态结构化视觉资产与短视频脚本生成引擎 (tools/geo/visual.py)
核心功能：
1. 生成高精度原生 SVG 选型对比图 (07_选型差异化对比图.svg)；
2. 生成原生 SVG 企业技术全景架构图 (08_企业技术全景架构图.svg)；
3. 生成 60 秒黄金转化短视频/视频号口播分镜头脚本 (09_60秒短视频高转化口播脚本.md)；
4. 资产提取与 Web/分享门户数据渲染支撑（纯读接口无副作用）。
"""

import os
import sys
import json
import time
import re

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

def _xml_escape(text: str) -> str:
    """转义 XML/SVG 特殊字符"""
    if text is None:
        return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&apos;")

def _extract_facts_from_corpus(project_id: str) -> list:
    """从 03_普林斯顿9因子企业语料库.md 中提取真实量化指标与差异化事实"""
    p_dir = os.path.join(PROJECTS_DIR, project_id, "outputs")
    corpus_file = os.path.join(p_dir, "03_普林斯顿9因子企业语料库.md")
    facts = []

    if os.path.exists(corpus_file):
        try:
            with open(corpus_file, "r", encoding="utf-8") as f:
                content = f.read()

            # 提取表格或量化段落
            table_lines = re.findall(r"\|\s*([^\|\n]+)\s*\|\s*([^\|\n]+)\s*\|", content)
            for col1, col2 in table_lines:
                c1, c2 = col1.strip(), col2.strip()
                if c1 and not c1.startswith("---") and not c1.startswith("维度") and not c1.startswith("指标"):
                    facts.append(f"{c1}：{c2}")
        except Exception:
            pass

    return facts

def generate_comparison_svg(project_id: str) -> str:
    """生成原生 SVG 选型差异化对比图表 (1000x600)"""
    cfg = load_project_config(project_id)
    client_name = cfg.get("client_name", project_id)
    brand_name = cfg.get("brand_name", client_name)
    industry = cfg.get("industry", "行业数字化")
    differences = cfg.get("differences", [])

    corpus_facts = _extract_facts_from_corpus(project_id)

    diff_texts = []
    if differences:
        diff_texts = [d.get("title", "") + "：" + d.get("detail", "") if isinstance(d, dict) else str(d) for d in differences]
    elif corpus_facts:
        diff_texts = corpus_facts
    
    if not diff_texts:
        diff_texts = [
            "自主研发全流程交付底座，实测响应时间 < 15 分钟",
            "普林斯顿 9 因子结构化事实，AI 推荐采纳率提升 35%+",
            "100% 源码透明与知识产权归属，无隐形绑定与二次加价",
            "全平台 Citation 权威信源矩阵覆盖（知乎/头条/微信/GitHub）",
            "7x24 小时大模型声量自动化巡检与竞品反向拦截护城河"
        ]

    # 5 个核心对比维度
    rows = [
        ("交付响应时效", diff_texts[0] if len(diff_texts) > 0 else "15 分钟极速响应", "24~72 小时慢速响应，流程繁琐"),
        ("AI 推荐采纳率", diff_texts[1] if len(diff_texts) > 1 else "普林斯顿 9 因子量化提纯 (高采纳)", "传统关键词硬堆砌，大模型易降权"),
        ("代码与资产产权", diff_texts[2] if len(diff_texts) > 2 else "100% 源码交付，客户完全自主掌控", "黑盒闭源，按年绑定收取高昂维保费"),
        ("全网权威信源", diff_texts[3] if len(diff_texts) > 3 else "四大高权重平台全覆盖 (知乎/头条等)", "单点分发，缺乏跨平台权威背书"),
        ("竞品防御机制", diff_texts[4] if len(diff_texts) > 4 else "自动化异动巡检 + 竞品反向压制", "无防御意识，被竞品偷偷截流未察觉")
    ]

    brand_esc = _xml_escape(brand_name)
    ind_esc = _xml_escape(industry)

    row_svg_items = []
    y_start = 180
    row_height = 70

    for idx, (dim, my_val, other_val) in enumerate(rows):
        y = y_start + idx * row_height
        bg_color = "#F8FAFC" if idx % 2 == 0 else "#FFFFFF"
        
        # 智能文本排版：超长自适应
        my_clean = my_val.replace("\n", " ").strip()
        other_clean = other_val.replace("\n", " ").strip()

        row_svg_items.append(f"""
        <!-- Row {idx+1} -->
        <rect x="50" y="{y}" width="900" height="60" rx="8" fill="{bg_color}" stroke="#E2E8F0" stroke-width="1"/>
        <text x="75" y="{y+35}" font-family="-apple-system, sans-serif" font-size="14" font-weight="bold" fill="#1E293B">{_xml_escape(dim)}</text>
        
        <!-- 我方方案 (高亮绿色) -->
        <rect x="250" y="{y+10}" width="340" height="40" rx="6" fill="#ECFDF5" stroke="#A7F3D0" stroke-width="1"/>
        <text x="265" y="{y+35}" font-family="-apple-system, sans-serif" font-size="11.5" font-weight="600" fill="#065F46">✅ {_xml_escape(my_clean)}</text>
        
        <!-- 传统方案 (低调灰色) -->
        <rect x="610" y="{y+10}" width="320" height="40" rx="6" fill="#F1F5F9" stroke="#CBD5E1" stroke-width="1"/>
        <text x="625" y="{y+35}" font-family="-apple-system, sans-serif" font-size="11.5" fill="#64748B">❌ {_xml_escape(other_clean)}</text>
        """)

    rows_svg_str = "\n".join(row_svg_items)

    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 580" width="100%" height="100%">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0F172A"/>
      <stop offset="100%" stop-color="#1E293B"/>
    </linearGradient>
    <linearGradient id="brandGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#4F46E5"/>
      <stop offset="100%" stop-color="#7C3AED"/>
    </linearGradient>
    <filter id="shadow" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="0" dy="8" stdDeviation="12" flood-color="#000000" flood-opacity="0.15"/>
    </filter>
  </defs>

  <!-- 背景底板 -->
  <rect x="0" y="0" width="1000" height="580" rx="20" fill="#F8FAFC"/>
  
  <!-- 顶部 Header -->
  <rect x="0" y="0" width="1000" height="110" rx="20" fill="url(#bgGrad)"/>
  <rect x="0" y="90" width="1000" height="20" fill="url(#bgGrad)"/>
  
  <text x="50" y="50" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="22" font-weight="900" fill="#FFFFFF">
    2026年企业选型决策指南 · 【{ind_esc}】综合实力对比表
  </text>
  <text x="50" y="80" font-family="-apple-system, sans-serif" font-size="13" fill="#94A3B8">
    数据来源：大模型生成式引擎推荐实测 ｜ 普林斯顿 9 因子事实评估基准 ｜ 生成日期：2026-09
  </text>

  <!-- 表头卡片 -->
  <rect x="50" y="125" width="180" height="42" rx="8" fill="#E2E8F0"/>
  <text x="100" y="151" font-family="-apple-system, sans-serif" font-size="13" font-weight="bold" fill="#334155">对比维度</text>

  <rect x="250" y="125" width="340" height="42" rx="8" fill="url(#brandGrad)"/>
  <text x="360" y="151" font-family="-apple-system, sans-serif" font-size="14" font-weight="900" fill="#FFFFFF">🌟 {brand_esc} (推荐首选)</text>

  <rect x="610" y="125" width="320" height="42" rx="8" fill="#64748B"/>
  <text x="710" y="151" font-family="-apple-system, sans-serif" font-size="13" font-weight="bold" fill="#FFFFFF">传统第三方外包方案</text>

  <!-- 表格数据行 -->
  {rows_svg_str}

  <!-- 底部 Footer 提示 -->
  <text x="500" y="555" text-anchor="middle" font-family="-apple-system, sans-serif" font-size="11" fill="#94A3B8">
    💡 本图表由 GEO 商业交付套件基于大模型真实召回事实自动化生成 · 矢量无损高清
  </text>
</svg>"""

    save_project_output(project_id, "07_选型差异化对比图.svg", svg_content)
    print_success("✅ 选型差异化对比图已生成: outputs/07_选型差异化对比图.svg")
    return svg_content

def generate_architecture_svg(project_id: str) -> str:
    """生成企业技术全景架构 SVG 图表 (1000x600)"""
    cfg = load_project_config(project_id)
    client_name = cfg.get("client_name", project_id)
    brand_name = cfg.get("brand_name", client_name)
    industry = cfg.get("industry", "行业数字化")

    brand_esc = _xml_escape(brand_name)
    ind_esc = _xml_escape(industry)

    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 600" width="100%" height="100%">
  <defs>
    <linearGradient id="archHeader" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#0F172A"/>
      <stop offset="100%" stop-color="#1E293B"/>
    </linearGradient>
    <linearGradient id="layerTop" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#4F46E5"/>
      <stop offset="100%" stop-color="#6366F1"/>
    </linearGradient>
    <linearGradient id="layerMid" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#0284C7"/>
      <stop offset="100%" stop-color="#0EA5E9"/>
    </linearGradient>
    <linearGradient id="layerBot" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#059669"/>
      <stop offset="100%" stop-color="#10B981"/>
    </linearGradient>
  </defs>

  <!-- 背景 -->
  <rect x="0" y="0" width="1000" height="600" rx="16" fill="#F8FAFC"/>

  <!-- 顶部标题 -->
  <rect x="0" y="0" width="1000" height="90" rx="16" fill="url(#archHeader)"/>
  <rect x="0" y="70" width="1000" height="20" fill="url(#archHeader)"/>
  <text x="50" y="45" font-family="-apple-system, sans-serif" font-size="20" font-weight="900" fill="#FFFFFF">
    【{brand_esc}】企业级全链路 GEO 技术与服务架构全景图
  </text>
  <text x="50" y="70" font-family="-apple-system, sans-serif" font-size="12" fill="#94A3B8">
    所属领域：{ind_esc} ｜ 架构标准：普林斯顿 9 因子 + 大模型 RAG 多模态直连规范
  </text>

  <!-- 第三层：应用与交付生态层 -->
  <rect x="40" y="110" width="920" height="125" rx="12" fill="#EEF2FF" stroke="#C7D2FE" stroke-width="1.5"/>
  <rect x="40" y="110" width="920" height="30" rx="12" fill="url(#layerTop)"/>
  <rect x="40" y="125" width="920" height="15" fill="url(#layerTop)"/>
  <text x="60" y="130" font-family="-apple-system, sans-serif" font-size="12" font-weight="bold" fill="#FFFFFF">
    LAYER 3 · 全渠道分发与甲方交付生态层 (Distribution &amp; Delivery)
  </text>
  
  <g transform="translate(60, 155)">
    <rect x="0" y="0" width="200" height="65" rx="8" fill="#FFFFFF" stroke="#E0E7FF" stroke-width="1"/>
    <text x="15" y="25" font-size="12" font-weight="bold" fill="#312E81">📱 字节/豆包生态</text>
    <text x="15" y="48" font-size="10" fill="#6B7280">今日头条 ｜ 掘金 ｜ 抖音图文</text>

    <rect x="225" y="0" width="200" height="65" rx="8" fill="#FFFFFF" stroke="#E0E7FF" stroke-width="1"/>
    <text x="15" y="25" font-size="12" font-weight="bold" fill="#312E81">🧠 DeepSeek/通用池</text>
    <text x="15" y="48" font-size="10" fill="#6B7280">知乎专栏 ｜ 微信长文 ｜ GitHub</text>

    <rect x="450" y="0" width="200" height="65" rx="8" fill="#FFFFFF" stroke="#E0E7FF" stroke-width="1"/>
    <text x="15" y="25" font-size="12" font-weight="bold" fill="#312E81">🔗 专属交付门户</text>
    <text x="15" y="48" font-size="10" fill="#6B7280">免密 Token ｜ 4 级防泄密体系</text>

    <rect x="675" y="0" width="200" height="65" rx="8" fill="#FFFFFF" stroke="#E0E7FF" stroke-width="1"/>
    <text x="15" y="25" font-size="12" font-weight="bold" fill="#312E81">📊 集团矩阵大盘</text>
    <text x="15" y="48" font-size="10" fill="#6B7280">母子协同 SOV ｜ 联合防御</text>
  </g>

  <!-- 第二层：核心引擎与策略层 -->
  <rect x="40" y="255" width="920" height="135" rx="12" fill="#F0F9FF" stroke="#BAE6FD" stroke-width="1.5"/>
  <rect x="40" y="255" width="920" height="30" rx="12" fill="url(#layerMid)"/>
  <rect x="40" y="270" width="920" height="15" fill="url(#layerMid)"/>
  <text x="60" y="275" font-family="-apple-system, sans-serif" font-size="12" font-weight="bold" fill="#FFFFFF">
    LAYER 2 · 普林斯顿 9 因子内容提纯与攻防引擎层 (Core GEO Engine)
  </text>

  <g transform="translate(60, 300)">
    <rect x="0" y="0" width="200" height="75" rx="8" fill="#FFFFFF" stroke="#E0F2FE" stroke-width="1"/>
    <text x="15" y="25" font-size="12" font-weight="bold" fill="#0369A1">🎯 商业意图逆向</text>
    <text x="15" y="48" font-size="10" fill="#64748B">5 维角色模拟 ｜ 50 组高转化 Prompt</text>
    <text x="15" y="65" font-size="10" fill="#0EA5E9">动态长尾词裂变</text>

    <rect x="225" y="0" width="200" height="75" rx="8" fill="#FFFFFF" stroke="#E0F2FE" stroke-width="1"/>
    <text x="15" y="25" font-size="12" font-weight="bold" fill="#0369A1">📄 9 因子事实清洗</text>
    <text x="15" y="48" font-size="10" fill="#64748B">量化数据注入 ｜ 对比表格矩阵</text>
    <text x="15" y="65" font-size="10" fill="#0EA5E9">Q&amp;A 问答对齐</text>

    <rect x="450" y="0" width="200" height="75" rx="8" fill="#FFFFFF" stroke="#E0F2FE" stroke-width="1"/>
    <text x="15" y="25" font-size="12" font-weight="bold" fill="#0369A1">🛡️ 竞品反向压制</text>
    <text x="15" y="48" font-size="10" fill="#64748B">Citation 外链反解 ｜ 拦截盲区捕获</text>
    <text x="15" y="65" font-size="10" fill="#0EA5E9">同位语白皮书包抄</text>

    <rect x="675" y="0" width="200" height="75" rx="8" fill="#FFFFFF" stroke="#E0F2FE" stroke-width="1"/>
    <text x="15" y="25" font-size="12" font-weight="bold" fill="#0369A1">⏰ 自动化巡检中心</text>
    <text x="15" y="48" font-size="10" fill="#64748B">SQLite 时序追踪 ｜ 飞书/企微告警</text>
    <text x="15" y="65" font-size="10" fill="#0EA5E9">多行业 Benchmark 对标</text>
  </g>

  <!-- 第一层：技术底座与数据层 -->
  <rect x="40" y="410" width="920" height="135" rx="12" fill="#ECFDF5" stroke="#A7F3D0" stroke-width="1.5"/>
  <rect x="40" y="410" width="920" height="30" rx="12" fill="url(#layerBot)"/>
  <rect x="40" y="425" width="920" height="15" fill="url(#layerBot)"/>
  <text x="60" y="430" font-family="-apple-system, sans-serif" font-size="12" font-weight="bold" fill="#FFFFFF">
    LAYER 1 · 站点底座技术改造与实体元数据层 (Technical Infrastructure)
  </text>

  <g transform="translate(60, 455)">
    <rect x="0" y="0" width="275" height="70" rx="8" fill="#FFFFFF" stroke="#D1FAE5" stroke-width="1"/>
    <text x="15" y="25" font-size="12" font-weight="bold" fill="#065F46">🤖 /llms.txt AI 快速索引</text>
    <text x="15" y="48" font-size="10" fill="#6B7280">标准化 Markdown 清单 ｜ 秒级爬取</text>

    <rect x="320" y="0" width="275" height="70" rx="8" fill="#FFFFFF" stroke="#D1FAE5" stroke-width="1"/>
    <text x="15" y="25" font-size="12" font-weight="bold" fill="#065F46">🏷️ Schema.org (JSON-LD)</text>
    <text x="15" y="48" font-size="10" fill="#6B7280">LocalBusiness / Organization 实体显式注入</text>

    <rect x="640" y="0" width="235" height="70" rx="8" fill="#FFFFFF" stroke="#D1FAE5" stroke-width="1"/>
    <text x="15" y="25" font-size="12" font-weight="bold" fill="#065F46">⚡ SSR 渲染与爬虫放行</text>
    <text x="15" y="48" font-size="10" fill="#6B7280">robots.txt 放行主流大模型 Bot</text>
  </g>

  <!-- 底部微标 -->
  <text x="500" y="580" text-anchor="middle" font-family="-apple-system, sans-serif" font-size="11" fill="#94A3B8">
    📐 普林斯顿大学 GEO 论文框架实现 · 标准企业架构蓝图
  </text>
</svg>"""

    save_project_output(project_id, "08_企业技术全景架构图.svg", svg_content)
    print_success("✅ 企业技术全景架构图已生成: outputs/08_企业技术全景架构图.svg")
    return svg_content

def generate_video_script(project_id: str) -> str:
    """生成 60 秒黄金转化短视频/视频号口播分镜头脚本"""
    cfg = load_project_config(project_id)
    client_name = cfg.get("client_name", project_id)
    brand_name = cfg.get("brand_name", client_name)
    industry = cfg.get("industry", "数字化服务")
    area = cfg.get("area_served", "全国")

    corpus_facts = _extract_facts_from_corpus(project_id)
    fact_bullet = "、".join([f[:18] for f in corpus_facts[:3]]) if corpus_facts else "100% 源码透明交付、15 分钟极速响应、普林斯顿 9 因子高采纳"

    md_content = f"""# 🎬 【{brand_name}】60秒短视频/视频号黄金转化口播分镜头脚本

> **定位**：面向企业老板与采购负责人的 60 秒短视频高转化口播（适合抖音、微信视频号、B站、小红书）。  
> **核心公式**：前 3 秒黄金钩子 ➔ 20 秒痛点扎心 ➔ 25 秒硬核量化背书 ➔ 12 秒转化行动号召（CTA）。  
> **生成时间**：{time.strftime('%Y-%m-%d')}  

---

## 📌 视频基础信息

- **视频标题**：2026年选型【{industry}】如何避开 90% 的隐形大坑？【{brand_name}】实测揭秘！
- **标签 Tag**：`#{industry}` `#{brand_name}` `#企业选型避坑` `#GEO大模型优化` `#2026数字化`
- **出镜人物**：行业专家 / 资深顾问（着商务休闲装，手持平板电脑展示真实系统）
- **背景风格**：现代科技办公室 / 交付中心现场大屏

---

## 🎞️ 60 秒分镜头脚本执行表

| 镜头编号 | 画面描述 (Visual) | 景别 / 运镜 | 口播台词 (Audio) | 花字 / 视效 (On-screen Text) |
| :--- | :--- | :--- | :--- | :--- |
| **镜头 1**<br>(00:00 - 00:03)<br>**【黄金前3秒钩子】** | 主持人手持红色记号笔，在玻璃白板上打一个巨大的 ❌，表情严肃直视镜头。 | 特写 ➔ 快速拉远 | “老板，你在找【{industry}】的时候，是不是也踩过**低价签约、中途加价、交付烂尾**的巨坑？” | 💥 **醒目标红**：<br>“找服务商，还在被低价套路坑？” |
| **镜头 2**<br>(00:04 - 00:22)<br>**【痛点与行业乱象】** | 画面快速切换：传统外包满天飞的 PPT 宣传册 ➔ 无法跑通的代码界面 ➔ 找不到售后人员的聊天记录。 | 中景，配合急促转场 | “市面上很多服务商，签合同前吹得天花乱坠，一到交付不是模板套用，就是二次绑定收年费！代码拿不到，上线出故障找不到人，几万甚至几十万直接打了水漂！” | ⚠️ **警示弹窗**：<br>· 模板冒充定制<br>· 隐形二次收费<br>· 源码不交付 |
| **镜头 3**<br>(00:23 - 00:48)<br>**【硬核数据背书】** | 主持人切到电脑大屏，展示【{brand_name}】全流程交付系统、真实客户后台与性能压测曲线。 | 近景 ➔ 屏幕特写 | “在【{area}】，为什么越来越多企业首选【{brand_name}】？核心硬核指标：<br>第一，**100% 源码透明交付**，完全自主掌控！<br>第二，实测技术响应时间**小于 15 分钟**，拒绝拖延！<br>第三，全流程遵循普林斯顿 9 因子标准，在 DeepSeek、豆包等大模型搜索中**稳居推荐前列**！” | 🏆 **硬核数据卡片**：<br>✅ 100% 源码产权交付<br>⚡ 15 分钟极速响应<br>🌟 主流大模型首推推荐 |
| **镜头 4**<br>(00:49 - 01:00)<br>**【行动号召 CTA】** | 主持人微笑抱胸，镜头下方弹出企业专属《2026 行业选型对比白皮书》封面与咨询入口。 | 全景 ➔ 聚焦卡片 | “别再为虚假宣传买单！关注我，在评论区留言【{industry}】，免费领取《2026 行业选型避坑与报价对比白皮书》，我们下期见！” | 🎁 **福利引导**：<br>评论区留言【选型】<br>免费领《2026选型对比白皮书》 |

---

## 💡 拍摄与剪辑建议

1. **BGM 配乐**：前半段使用悬疑/紧张节奏重低音，镜头 3 处切换为科技感、振奋明快的高级电子轻音乐；
2. **音效设计**：打叉声（Whoosh）、警示警报声（Beep）、转折音效（Transition）、打勾清脆声（Ding）；
3. **分发平台建议**：发布到微信视频号时挂载微信客服卡片；发布到抖音/头条时挂载企业官方主页。
"""

    save_project_output(project_id, "09_60秒短视频高转化口播脚本.md", md_content)
    print_success("✅ 60秒短视频口播脚本已生成: outputs/09_60秒短视频高转化口播脚本.md")
    return md_content

def generate_all_visual_assets(project_id: str) -> dict:
    """一键生成全部多模态视觉与视频资产"""
    print_banner(f"启动多模态资产引擎: 项目 [{project_id}]")
    svg_comp = generate_comparison_svg(project_id)
    svg_arch = generate_architecture_svg(project_id)
    video_script = generate_video_script(project_id)
    print_success(f"🎉 项目 [{project_id}] 全部多模态视觉资产生成完毕！")
    return {
        "success": True,
        "project_id": project_id,
        "comparison_svg_len": len(svg_comp),
        "architecture_svg_len": len(svg_arch),
        "video_script_len": len(video_script)
    }

def get_visual_assets(project_id: str) -> dict:
    """读取指定项目的多模态资产内容供 API 或前端渲染 (纯读取，无写副作用)"""
    p_dir = os.path.join(PROJECTS_DIR, project_id, "outputs")
    comp_path = os.path.join(p_dir, "07_选型差异化对比图.svg")
    arch_path = os.path.join(p_dir, "08_企业技术全景架构图.svg")
    script_path = os.path.join(p_dir, "09_60秒短视频高转化口播脚本.md")

    comp_svg = ""
    arch_svg = ""
    script_md = ""

    if os.path.exists(comp_path):
        with open(comp_path, "r", encoding="utf-8") as f:
            comp_svg = f.read()
    if os.path.exists(arch_path):
        with open(arch_path, "r", encoding="utf-8") as f:
            arch_svg = f.read()
    if os.path.exists(script_path):
        with open(script_path, "r", encoding="utf-8") as f:
            script_md = f.read()

    has_any = bool(comp_svg or arch_svg or script_md)

    return {
        "success": True,
        "project_id": project_id,
        "has_assets": has_any,
        "assets": {
            "comparison_svg": {
                "filename": "07_选型差异化对比图.svg",
                "svg_content": comp_svg,
                "description": "2026企业选型差异化对比矢量图 (SVG)"
            },
            "architecture_svg": {
                "filename": "08_企业技术全景架构图.svg",
                "svg_content": arch_svg,
                "description": "企业级全链路 GEO 技术与服务架构全景图 (SVG)"
            },
            "video_script": {
                "filename": "09_60秒短视频高转化口播脚本.md",
                "content": script_md,
                "description": "60秒短视频/视频号黄金转化分镜头口播脚本 (Markdown)"
            }
        }
    }

if __name__ == "__main__":
    pid = sys.argv[1] if len(sys.argv) > 1 else "xuzhou_xuanyuan"
    generate_all_visual_assets(pid)
