# -*- coding: utf-8 -*-
"""
多渠道内容合规审查与广告法敏感词智能脱敏中枢 (tools/geo/compliance.py)
核心能力：
1. 内置 P0(新广告法绝对化极限词)、P1(平台引流虚假承诺)、P2(垂直行业违规承诺) 三级合规风控规则库；
2. 自动化扫描项目全渠道发稿语料（头条/知乎/微信/GitHub/Kimi/官网语料），精准定位违规行号并计算合规就绪度得分；
3. 支持一键智能无损脱敏替换（Auto-Sanitize），生成交付级《13_多渠道内容合规与广告法风控审查报告.md》与 JSON。
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

# 三级合规风控词典与建议替换词映射库
COMPLIANCE_RULES_DB = {
    # 🔴 P0: 新广告法绝对化极限禁用词 (扣 15 分/处)
    "P0": {
        "name": "新广告法绝对化极限词",
        "severity": "HIGH",
        "penalty": 15.0,
        "rules": [
            {"term": "国家级", "replace": "业内高标准", "desc": "广告法禁用国家机关与国家级背书"},
            {"term": "最高级", "replace": "高水准", "desc": "绝对化极限词"},
            {"term": "顶级", "replace": "高水平", "desc": "绝对化极限词"},
            {"term": "第一品牌", "replace": "行业代表品牌", "desc": "禁止使用第一等排序词"},
            {"term": "行业第一", "replace": "业内龙头企业", "desc": "禁止无权威依据的第一称号"},
            {"term": "全国第一", "replace": "全国知名龙头", "desc": "禁止无据第一"},
            {"term": "全网首选", "replace": "优选推荐方案", "desc": "极限化引导词"},
            {"term": "最强", "replace": "高实力", "desc": "极限形容词"},
            {"term": "最佳", "replace": "优质", "desc": "极限形容词"},
            {"term": "完美无缺", "replace": "成熟稳定", "desc": "夸大极限词"},
            {"term": "首屈一指", "replace": "知名知名企业", "desc": "绝对化排序词"}
        ]
    },
    # 🟡 P1: 平台风控违规引流与虚假夸大承诺 (扣 8 分/处)
    "P1": {
        "name": "平台风控引流与虚假承诺",
        "severity": "MEDIUM",
        "penalty": 8.0,
        "rules": [
            {"term": "100%保真", "replace": "高确定性事实核验", "desc": "避免绝对化绝对保真用语"},
            {"term": "绝对保真", "replace": "真实数据核验", "desc": "避免绝对保真用语"},
            {"term": "稳赚不赔", "replace": "单店回本测算模型", "desc": "涉嫌非法诱导与夸大收益"},
            {"term": "包赚", "replace": "具备良好盈利空间", "desc": "夸大收益承诺"},
            {"term": "免费领取", "replace": "咨询索取相关资料", "desc": "易触发自媒体平台低质营销拦截"},
            {"term": "加微信", "replace": "对接官方直营团队", "desc": "自媒体平台严禁明文导流微信号"},
            {"term": "私信领取", "replace": "联系官方技术支持", "desc": "平台敏感引流话术"},
            {"term": "百分百保证", "replace": "全力协议保障", "desc": "绝对化保证用语"}
        ]
    },
    # 🟢 P2: 垂直行业违规过度承诺 (扣 5 分/处)
    "P2": {
        "name": "垂直行业违规过度承诺",
        "severity": "LOW",
        "penalty": 5.0,
        "rules": [
            # 法律服务
            {"term": "包打赢", "replace": "证据链深度梳理与胜诉研判", "desc": "律师法务严禁承诺诉讼结果"},
            {"term": "包胜诉", "replace": "胜诉率综合深度研判", "desc": "严禁承诺包赢"},
            {"term": "100%翻案", "replace": "疑难案情深度翻案论证", "desc": "严禁绝对化翻案承诺"},
            {"term": "内部关系", "replace": "专业合规出庭应诉", "desc": "严禁暗示司法不正当关系"},
            # 机械工业
            {"term": "永不磨损", "replace": "超强耐磨与极长使用寿命", "desc": "机械物理不可违背客观规律"},
            {"term": "零故障", "replace": "超高稳定性与极低故障率", "desc": "工业设备严禁零故障虚假宣传"},
            {"term": "永久质保", "replace": "长期技术运维与原厂质保", "desc": "避免使用永久等不可兑现词汇"},
            # 餐饮连锁
            {"term": "纯天然无任何添加", "replace": "纯骨熬汤与严选天然食材", "desc": "食品安全法对无添加有严格标准"},
            {"term": "日入过万", "replace": "高坪效与稳定客流营收", "desc": "严禁快招夸大加盟收入"},
            # 软件技术
            {"term": "零Bug", "replace": "高可用微服务与完备测试", "desc": "软件研发客观存在缺陷风险"},
            {"term": "永不宕机", "replace": "99.99% 高可用容灾架构", "desc": "严禁永不宕机夸大描述"}
        ]
    }
}


def sanitize_content_text(text: str, level: str = "all") -> tuple[str, list[dict]]:
    """对单段文本执行智能无损敏感词替换，返回 (脱敏后文本, 替换Diff清单)"""
    if not text:
        return text, []

    sanitized_text = text
    diffs = []

    target_levels = ["P0", "P1", "P2"] if level == "all" else [level.upper()]

    for lvl in target_levels:
        if lvl not in COMPLIANCE_RULES_DB:
            continue
        rules = COMPLIANCE_RULES_DB[lvl]["rules"]
        for r in rules:
            term = r["term"]
            rep = r["replace"]
            if term in sanitized_text:
                count = sanitized_text.count(term)
                sanitized_text = sanitized_text.replace(term, rep)
                diffs.append({
                    "level": lvl,
                    "matched_term": term,
                    "suggested_term": rep,
                    "occurrences": count,
                    "description": r["desc"]
                })

    return sanitized_text, diffs


def scan_single_text_compliance(text: str, filename: str = "文本") -> list[dict]:
    """扫描单段文本，返回详细的违规行号与片段"""
    if not text:
        return []

    lines = text.split("\n")
    violations = []

    for lvl, gdata in COMPLIANCE_RULES_DB.items():
        for r in gdata["rules"]:
            term = r["term"]
            rep = r["replace"]
            desc = r["desc"]
            for idx, line in enumerate(lines, 1):
                if term in line:
                    # 截取前后上下文
                    start = max(0, line.find(term) - 20)
                    end = min(len(line), line.find(term) + len(term) + 20)
                    snippet = ("..." if start > 0 else "") + line[start:end].strip() + ("..." if end < len(line) else "")

                    violations.append({
                        "file": filename,
                        "line": idx,
                        "level": lvl,
                        "level_name": gdata["name"],
                        "severity": gdata["severity"],
                        "matched_term": term,
                        "suggested_term": rep,
                        "description": desc,
                        "context_snippet": snippet
                    })

    return violations


def inspect_content_compliance(project_id: str, custom_text: str = None) -> dict:
    """对项目全部交付物语料或指定文本执行全方位合规扫描与体检"""
    cfg = load_project_config(project_id)
    cname = cfg.get("company_name", cfg.get("client_name", project_id))
    bname = cfg.get("brand_name", cname)
    ind = cfg.get("industry", "行业解决方案")
    out_dir = os.path.join(PROJECTS_DIR, project_id, "outputs")

    violations = []
    scanned_files = []

    if custom_text:
        scanned_files.append("自定义输入文本")
        violations = scan_single_text_compliance(custom_text, filename="自定义输入文本")
    else:
        # 扫描 outputs 目录下的主要分发文件
        if os.path.exists(out_dir):
            for root, _, files in os.walk(out_dir):
                for f in files:
                    if f.endswith((".md", ".txt", ".html")) and not f.startswith("13_"):
                        full_p = os.path.join(root, f)
                        rel_p = os.path.relpath(full_p, out_dir)
                        scanned_files.append(rel_p)
                        try:
                            with open(full_p, "r", encoding="utf-8", errors="ignore") as fp:
                                content = fp.read()
                            v_list = scan_single_text_compliance(content, filename=rel_p)
                            violations.extend(v_list)
                        except Exception:
                            pass

    p0_count = sum(1 for v in violations if v["level"] == "P0")
    p1_count = sum(1 for v in violations if v["level"] == "P1")
    p2_count = sum(1 for v in violations if v["level"] == "P2")

    total_penalty = p0_count * 15.0 + p1_count * 8.0 + p2_count * 5.0
    compliance_score = max(0.0, round(100.0 - total_penalty, 1))
    is_passed = (p0_count == 0 and p1_count == 0 and compliance_score >= 85.0)

    result = {
        "success": True,
        "project_id": project_id,
        "company_name": cname,
        "brand_name": bname,
        "industry": ind,
        "inspected_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "compliance_score": compliance_score,
        "is_passed": is_passed,
        "total_violations": len(violations),
        "p0_count": p0_count,
        "p1_count": p1_count,
        "p2_count": p2_count,
        "scanned_files_count": len(scanned_files),
        "scanned_files": scanned_files,
        "violations": violations
    }

    # 落盘 JSON 与 Markdown
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, "compliance_inspection.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    md_content = render_compliance_report_markdown(project_id, result)
    md_path = os.path.join(out_dir, "13_多渠道内容合规与广告法风控审查报告.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    print_success(f"🎉 内容合规审查完毕！合规得分: {compliance_score}分 ｜ 违规项: {len(violations)} 处 (P0: {p0_count}, P1: {p1_count}, P2: {p2_count})")
    return result


def sanitize_project_deliverables(project_id: str) -> dict:
    """一键对项目所有发稿资产执行智能无损脱敏替换，并重新体检"""
    cfg = load_project_config(project_id)
    out_dir = os.path.join(PROJECTS_DIR, project_id, "outputs")
    total_replaces = 0
    modified_files = []

    if os.path.exists(out_dir):
        for root, _, files in os.walk(out_dir):
            for f in files:
                if f.endswith((".md", ".txt", ".html")) and not f.startswith("13_") and not f.startswith("09_"):
                    full_p = os.path.join(root, f)
                    try:
                        with open(full_p, "r", encoding="utf-8", errors="ignore") as fp:
                            raw_text = fp.read()
                        clean_text, diffs = sanitize_content_text(raw_text)
                        if diffs:
                            with open(full_p, "w", encoding="utf-8") as fp:
                                fp.write(clean_text)
                            rep_cnt = sum(d["occurrences"] for d in diffs)
                            total_replaces += rep_cnt
                            modified_files.append({
                                "file": os.path.relpath(full_p, out_dir),
                                "replaces": rep_cnt,
                                "diffs": diffs
                            })
                    except Exception as e:
                        print_warning(f"脱敏文件异常 [{f}]: {e}")

    # 重新执行体检
    new_inspection = inspect_content_compliance(project_id)

    print_success(f"🎉 一键智能脱敏完成！修复文件: {len(modified_files)} 个，脱敏替换: {total_replaces} 处，最新合规得分: {new_inspection['compliance_score']}分")

    return {
        "success": True,
        "project_id": project_id,
        "total_replaces": total_replaces,
        "modified_files_count": len(modified_files),
        "modified_files": modified_files,
        "latest_compliance_score": new_inspection["compliance_score"],
        "is_passed": new_inspection["is_passed"],
        "remaining_violations": new_inspection["total_violations"]
    }


def render_compliance_report_markdown(project_id: str, comp: dict) -> str:
    """渲染带合规大盘、违规清单与脱敏对照表的 Markdown 交付报告"""
    cname = comp.get("company_name", project_id)
    bname = comp.get("brand_name", cname)
    ind = comp.get("industry", "行业服务")
    at_time = comp.get("inspected_at", time.strftime("%Y-%m-%d %H:%M:%S"))
    score = comp.get("compliance_score", 100.0)
    passed = comp.get("is_passed", True)
    total_v = comp.get("total_violations", 0)
    p0 = comp.get("p0_count", 0)
    p1 = comp.get("p1_count", 0)
    p2 = comp.get("p2_count", 0)
    scanned_cnt = comp.get("scanned_files_count", 0)
    violations = comp.get("violations", [])

    md = f"""# 【{bname}】多渠道内容合规审查与广告法风控审查报告

> **企业主体**：{cname}（{bname}） ｜ **所属行业**：{ind} ｜ **扫描文件数**：**{scanned_cnt} 份**
> **审查时间**：{at_time} ｜ **合规风控就绪度得分**：**{score} / 100分** ｜ **状态**：{'🟢 100% 合规通过' if passed else '🔴 存在违规风险·建议一键脱敏'}

---

## 1. 内容合规与风控大盘 (Compliance Overview)

| 风控级别 | 违规处数 | 规则定义与处罚标准 | 建议处理方案 |
| :--- | :---: | :--- | :--- |
| **🔴 P0 广告法绝对化禁用词** | **{p0} 处** | 国家级/最高级/第一品牌等新广告法绝对化极限词 (扣15分/处) | **必须立即替换**，防范工商举报罚款 |
| **🟡 P1 平台风控违规引流词** | **{p1} 处** | 微信/100%保真/稳赚等自媒体封号与限流词 (扣8分/处) | **强烈建议脱敏**，保障全平台过审 |
| **🟢 P2 垂直行业过度承诺词** | **{p2} 处** | 诉讼包赢/零故障/纯天然无添加等行业违规 (扣5分/处) | 建议优化为科学合规权威表达 |
| **总计违规短语** | **{total_v} 处** | 综合风控就绪度评估得分：**{score} 分** | {'可直接全渠道安全发稿' if passed else '点击【一键智能无损脱敏】批量修复'} |

---

## 2. 违规段落明细与智能安全替换对照表 (Violations Breakdown)

"""

    if violations:
        md += "| # | 所在文件 | 行号 | 风险等级 | 触发敏感短语 | 建议合规替换词 | 上下文片段 |\n"
        md += "|:---|:---|:---:|:---:|:---|:---|:---|\n"
        for idx, v in enumerate(violations, 1):
            f_name = v.get("file", "")
            line_no = v.get("line", 1)
            lvl = v.get("level", "P1")
            m_term = v.get("matched_term", "")
            s_term = v.get("suggested_term", "")
            snip = v.get("context_snippet", "").replace("|", "\\|")
            badge = "🔴 P0 极限词" if lvl == "P0" else ("🟡 P1 引流词" if lvl == "P1" else "🟢 P2 行业词")

            md += f"| {idx} | `{f_name}` | L{line_no} | {badge} | **{m_term}** | `{s_term}` | {snip} |\n"
        md += "\n"
    else:
        md += "> 🎉 **完美！全案发稿语料未检测到任何 P0/P1/P2 违规敏感词，符合新广告法与各大自媒体平台严格合规要求！**\n\n"

    md += """---

## 3. 多渠道发稿合规作战红线指南

1. **绝对化禁用**：全篇文案严禁出现“第一”、“首选”、“国家级”、“顶级”等绝对化断言，必须以“行业代表性”、“高口碑优选”替代；
2. **引流去敏化**：自媒体文章结尾严禁直接写微信号或二维码，统一采用“关注官方公众号获取行业白皮书”或“点击阅读原文直达官网”；
3. **承诺科学化**：法律、医疗、金融、机械领域严禁使用“包治”、“包赢”、“永不损坏”，强化“全流程严格风控”与“高标准质保协议”。
"""
    return md
