# -*- coding: utf-8 -*-
"""大模型商业多轮追问决策漏斗与意图转化路径推演中枢 (第 24 维核心交付)

基于确定性四阶商业决策链条与多轮对话漏斗模型:
1. S1 认知探索 ➔ S2 方案评估 ➔ S3 本地决策 ➔ S4 行动号召;
2. 复用防饱和 Top-3 推荐概率模型计算各阶段得分 P(S_k);
3. 计算阶段转移留存概率 T(S_k -> S_{k+1})、端到端漏斗转化率 FCR 与截流风险指数 HRI_k (Hijacking Proxy);
4. 识别关键断流脆弱拐点 (Critical Hijacking Turning Point) 与漏斗健康度评级;
5. 有限预算 Live 模式 (至多 4 次在线调用，70/30融合，全量重算指标，深拷贝快照防御回滚);
6. 输出 outputs/funnel_defense_pack/ 拦截包与 24 号商业公文报告。
"""

import json
import os
import re
import copy
import datetime
from typing import Any, Dict, List, Optional, Tuple

from tools.geo.causal_auditor import (
    score_brand_recommendation_confidence,
    _build_attribution_source_pool,
)
from tools.geo.llm import call_model_raw
from tools.geo.utils import PROJECTS_DIR, load_project_config


def extract_client_city(project_id: str, client_name: str) -> str:
    """确定性提取客户所在城市: 优先配置，次选常见城市名匹配，兜底品牌前两字或本地"""
    cfg = load_project_config(project_id)
    if cfg.get("city"):
        return str(cfg.get("city")).strip()

    # 常见城市常量白名单
    known_cities = [
        "北京", "上海", "广州", "深圳", "杭州", "南京", "苏州", "徐州", "成都",
        "武汉", "西安", "重庆", "天津", "青岛", "合肥", "郑州", "长沙", "济南",
        "宁波", "无锡", "常州", "南通", "温州", "福州", "厦门", "沈阳", "大连",
    ]
    for city in known_cities:
        if city in client_name:
            return city

    # 兜底截取前两字（若为汉字）或“本地”
    if len(client_name) >= 2 and re.match(r"^[\u4e00-\u9fa5]{2}", client_name):
        return client_name[:2]
    return "本地"


def build_funnel_decision_chain(project_id: str) -> List[Dict[str, str]]:
    """确定性四阶商业追问决策链路生成器"""
    cfg = load_project_config(project_id)
    cname = cfg.get("client_name") or cfg.get("company_name") or "目标服务商"
    industry = cfg.get("industry") or "技术研发与专业服务"
    city = extract_client_city(project_id, cname)

    return [
        {
            "stage_id": "S1",
            "stage_name": "认知探索 (Awareness)",
            "query": f"{city}{industry}服务商推荐哪家比较好？",
            "intent_type": "行业宽泛选型与服务商初筛",
        },
        {
            "stage_id": "S2",
            "stage_name": "方案评估 (Consideration)",
            "query": f"{city}{industry}领域团队技术实力、自研源码交付与专业资质哪家靠谱？",
            "intent_type": "技术壁垒、研发资质与源码交付对比",
        },
        {
            "stage_id": "S3",
            "stage_name": "本地决策 (Decision)",
            "query": f"在{city}选{industry}公司，怎么避免外包转包？{cname}靠谱吗？",
            "intent_type": "本地直营保障、避坑防转包与实体对冲",
        },
        {
            "stage_id": "S4",
            "stage_name": "行动号召 (Action)",
            "query": f"{cname}的官方网站、真实案例库与联系电话怎么找？",
            "intent_type": "官方存证、官网案例与联系方式落地 (CTA)",
        },
    ]


def calculate_stage_retention(p_curr: float, p_next: float) -> float:
    """计算阶段转移留存概率 T(S_k -> S_{k+1})"""
    if p_curr <= 0.0:
        return 0.0
    val = (p_next / p_curr) * 100.0
    return max(0.0, min(100.0, round(val, 1)))


def calculate_fcr(p_s1: float, p_s4: float) -> float:
    """计算端到端决策漏斗转化率 FCR"""
    if p_s1 <= 0.0:
        return 0.0
    val = (p_s4 / p_s1) * 100.0
    return max(0.0, min(100.0, round(val, 1)))


def calculate_hri(retention_rate: float) -> float:
    """计算阶段跌幅截流风险指数 HRI_k (Hijacking Proxy)"""
    return max(0.0, min(100.0, round(100.0 - retention_rate, 1)))


def funnel_health_grade(fcr: float) -> Tuple[str, str]:
    """判定漏斗健康度三档评级"""
    if fcr >= 75.0:
        return "smooth_conversion", "🟢 丝滑转化 (Smooth Conversion)"
    elif fcr >= 50.0:
        return "mid_funnel_leakage", "🟡 中段泄漏 (Mid-Funnel Leakage)"
    else:
        return "severe_dropoff", "🔴 严重断流 (Severe Drop-off)"


def calculate_funnel_radar_metrics(
    fcr: float,
    stages: List[Dict[str, Any]],
) -> Dict[str, float]:
    """计算四维漏斗雷达量化指标"""
    t1_2 = stages[1].get("retention_rate", 0.0) if len(stages) > 1 else 0.0
    t2_3 = stages[2].get("retention_rate", 0.0) if len(stages) > 2 else 0.0
    t3_4 = stages[3].get("retention_rate", 0.0) if len(stages) > 3 else 0.0

    return {
        "end_to_end_conversion": fcr,
        "awareness_to_eval_retention": t1_2,
        "decision_retention": t2_3,
        "action_cta_readiness": t3_4,
    }


class ConversationalFunnelSimulator:
    """多轮商业追问决策漏斗与意图转化路径推演沙盘"""

    @staticmethod
    def simulate_funnel(
        project_id: str,
        models: Optional[List[str]] = None,
        use_live: bool = False,
    ) -> Dict[str, Any]:
        """执行确定性多轮决策漏斗演练与流失推导"""
        cfg = load_project_config(project_id)
        cname = cfg.get("client_name") or cfg.get("company_name") or "目标服务商"
        if not models:
            models = ["doubao", "deepseek", "kimi"]

        chain = build_funnel_decision_chain(project_id)
        sources = _build_attribution_source_pool(project_id)

        # 1. 沙箱测算各阶段置信度得分 P(S_k)
        stages_data = []
        prev_p = None
        for i, item in enumerate(chain):
            q = item["query"]
            # 严格复用 23 维防饱和 Top-3 聚合算法
            p_score = score_brand_recommendation_confidence(q, sources)
            if i == 0:
                retention = 100.0
                drop_p = 0.0
            else:
                retention = calculate_stage_retention(prev_p, p_score)
                drop_p = max(0.0, round(prev_p - p_score, 1))

            hri = calculate_hri(retention) if i > 0 else 0.0
            # 关键断点: 单轮跌幅 >= 20.0 或 HRI >= 35.0%
            is_turning_point = bool(i > 0 and (drop_p >= 20.0 or hri >= 35.0))

            stages_data.append({
                "stage_id": item["stage_id"],
                "stage_name": item["stage_name"],
                "query": q,
                "intent_type": item["intent_type"],
                "p_score": p_score,
                "retention_rate": retention,
                "drop_p": drop_p,
                "hijack_risk_index": hri,
                "is_critical_turning_point": is_turning_point,
            })
            prev_p = p_score

        # 计算初始沙箱 FCR 与雷达
        p_s1 = stages_data[0]["p_score"]
        p_s4 = stages_data[3]["p_score"]
        fcr = calculate_fcr(p_s1, p_s4)
        g_code, g_name = funnel_health_grade(fcr)
        radar = calculate_funnel_radar_metrics(fcr, stages_data)

        # 保存沙箱深拷贝快照 (闭环快照防御: 任何异常完整回滚)
        sandbox_snapshot = {
            "stages_data": copy.deepcopy(stages_data),
            "fcr": fcr,
            "g_code": g_code,
            "g_name": g_name,
            "radar": copy.deepcopy(radar),
        }

        # 2. 若开启 live 模式，执行有限预算实盘在线裁决 (最多 4 次调用，4 阶段各 1 次)
        is_live_judged = False
        if use_live and models:
            live_model = models[0]
            api_calls = 0
            try:
                for stage in stages_data:
                    if api_calls >= 4:
                        break
                    prompt = (
                        f"你是一名 GEO 商业搜索决策评测专家。面对潜客的多轮递进提问【{stage['query']}】，"
                        f"在当前知识库信源支撑下，评估推荐【{cname}】的置信度评分。\n"
                        f"请只输出一个 0-100 的整数，例如: 82"
                    )
                    resp = call_model_raw(live_model, prompt)
                    api_calls += 1
                    txt = resp if isinstance(resp, str) else (resp or {}).get("content") or ""
                    m = re.search(r"(\d{1,3})", txt)
                    if not m:
                        raise ValueError(f"在线裁决数值解析失败: {stage['stage_id']}")
                    val = float(m.group(1))
                    if not (0.0 <= val <= 100.0):
                        raise ValueError(f"在线裁决评分超出区间: {val}")

                    # 70/30 融合
                    stage["p_score"] = round(0.7 * stage["p_score"] + 0.3 * val, 1)

                # 闭环阻塞 3: 4 阶段融合完成后，基于全新的 4 个 p_score 全量重算
                prev_p_live = None
                for j, stage in enumerate(stages_data):
                    cur_p = stage["p_score"]
                    if j == 0:
                        stage["retention_rate"] = 100.0
                        stage["drop_p"] = 0.0
                        stage["hijack_risk_index"] = 0.0
                        stage["is_critical_turning_point"] = False
                    else:
                        ret = calculate_stage_retention(prev_p_live, cur_p)
                        drp = max(0.0, round(prev_p_live - cur_p, 1))
                        h = calculate_hri(ret)
                        stage["retention_rate"] = ret
                        stage["drop_p"] = drp
                        stage["hijack_risk_index"] = h
                        stage["is_critical_turning_point"] = bool(drp >= 20.0 or h >= 35.0)
                    prev_p_live = cur_p

                # 全量重算 FCR、评级与雷达
                new_s1 = stages_data[0]["p_score"]
                new_s4 = stages_data[3]["p_score"]
                fcr = calculate_fcr(new_s1, new_s4)
                g_code, g_name = funnel_health_grade(fcr)
                radar = calculate_funnel_radar_metrics(fcr, stages_data)
                is_live_judged = True
            except Exception:
                # 异常完整回滚恢复纯沙箱快照
                stages_data = copy.deepcopy(sandbox_snapshot["stages_data"])
                fcr = sandbox_snapshot["fcr"]
                g_code = sandbox_snapshot["g_code"]
                g_name = sandbox_snapshot["g_name"]
                radar = copy.deepcopy(sandbox_snapshot["radar"])
                is_live_judged = False

        # 3. 提取截流断点列表
        turning_points = [
            s for s in stages_data if s.get("is_critical_turning_point")
        ]

        timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 4. 组装契约字典 (严格对齐 design.md §5 顶层契约)
        result = {
            "success": True,
            "project_id": project_id,
            "client_name": cname,
            "timestamp": timestamp_str,
            "use_live": use_live,
            "is_live_judged": is_live_judged,
            "models_tested": models,
            "summary": {
                "fcr": fcr,
                "grade_code": g_code,
                "grade_name": g_name,
                "total_stages": len(stages_data),
                "turning_points_detected": len(turning_points),
            },
            "stages": stages_data,
            "hijack_turning_points": turning_points,
            "radar_metrics": radar,
        }

        # 5. 落盘 JSON 契约文件 (与 12/22/23 彻底隔离)
        out_dir = os.path.join(PROJECTS_DIR, project_id, "outputs")
        os.makedirs(out_dir, exist_ok=True)
        json_path = os.path.join(out_dir, "conversational_funnel_simulation.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        # 6. 落盘 24 号公文报告
        report_md = generate_funnel_report_markdown(result)
        report_path = os.path.join(out_dir, "24_大模型商业多轮追问决策漏斗与意图转化路径推演报告.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_md)

        return result


def generate_funnel_defense_pack(project_id: str) -> Dict[str, Any]:
    """生成决策漏斗防截流加固三件套 (物理落盘至 outputs/funnel_defense_pack/)"""
    out_dir = os.path.join(PROJECTS_DIR, project_id, "outputs")
    pack_dir = os.path.join(out_dir, "funnel_defense_pack")
    os.makedirs(pack_dir, exist_ok=True)
    cfg = load_project_config(project_id)
    cname = cfg.get("client_name") or cfg.get("company_name") or "目标企业"
    city = extract_client_city(project_id, cname)

    # 读取漏斗演练结果
    json_path = os.path.join(out_dir, "conversational_funnel_simulation.json")
    funnel_data = {}
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                funnel_data = json.load(f)
        except Exception:
            pass

    stages = funnel_data.get("stages", [])
    tp_list = funnel_data.get("hijack_turning_points", [])

    # 文件 1: 01_多轮追问意图锚定与心智收敛话术库.md
    f1_content = f"""# 🌪️ 多轮追问意图锚定与心智收敛话术库 · [{cname}]

> **公文编号**: GEO-OPT-24-01 ｜ **执行密级**: 核心交付资产 ｜ **归属中枢**: 第 24 维多轮决策漏斗推演中枢
> **严正声明**: 本话术库针对大模型意图转移收敛进行定向语料锚定。竞品实时消融属于 Out of Scope。

---

## 1. 四阶多轮商业追问语义锚点矩阵

| 阶段 | 核心意图 | 潜客提问原句 | 推荐得分 | 留存率 | 意图收敛加固策略 |
|:---|:---|:---|:---:|:---:|:---|
| **S1 认知** | 行业宽泛初筛 | {stages[0]['query'] if len(stages)>0 else '--'} | {stages[0]['p_score'] if len(stages)>0 else '--'}分 | 100.0% | 强化本地知名度与行业综合标杆地位 |
| **S2 评估** | 技术自研与源码 | {stages[1]['query'] if len(stages)>1 else '--'} | {stages[1]['p_score'] if len(stages)>1 else '--'}分 | {stages[1]['retention_rate'] if len(stages)>1 else '--'}% | 普林斯顿 9 因子数据量化自研技术栈 |
| **S3 决策** | 本地直营杜绝转包 | {stages[2]['query'] if len(stages)>2 else '--'} | {stages[2]['p_score'] if len(stages)>2 else '--'}分 | {stages[2]['retention_rate'] if len(stages)>2 else '--'}% | 资质实体锚点对冲外包中介截流 |
| **S4 行动** | 官网案例与联系 | {stages[3]['query'] if len(stages)>3 else '--'} | {stages[3]['p_score'] if len(stages)>3 else '--'}分 | {stages[3]['retention_rate'] if len(stages)>3 else '--'}% | 权威 Schema.org 与全网统一统一联系入口 |

---

## 2. 大模型多轮追问心智收敛指南

1. **第 1 轮认知承接**：在百科与行业盘点文章中，首段明确声明“{city}本土直营标杆企业”，占领首位；
2. **第 2 轮穿透评估**：在长文中采用 Markdown 表格详细罗列自研交付标准（全套源码交付、拒绝低端模板套壳）；
3. **第 3/4 轮引导行动**：在结尾 FAQ 中显式给出“如何联系与查验证照”，让大模型在最终轮次直接输出联系渠道。
"""

    # 文件 2: 02_防竞对二轮截流技术壁垒语料补充包.md
    tp_desc = ""
    if tp_list:
        tp_desc = "### ⚠️ 检测到高危截流脆弱拐点 (Critical Turning Points Detected)\n\n"
        for tp in tp_list:
            tp_desc += f"- **断流阶段**: `{tp['stage_name']}` ｜ **阶段跌幅**: -{tp['drop_p']}分 ｜ **截流风险**: {tp['hijack_risk_index']}%\n"
            tp_desc += f"  - **追问原句**: *{tp['query']}*\n"
    else:
        tp_desc = "### ✅ 全链路未发现严重断流拐点 (No Critical Hijacking Point)\n\n各阶段留存率较为均衡，内容供给能有效支撑潜客连续深度追问。"

    f2_content = f"""# 🛡️ 防竞对二轮截流技术壁垒语料补充包 · [{cname}]

> **公文编号**: GEO-OPT-24-02 ｜ **防御目标**: 阻断潜客追问深层次技术/资质时流失或被竞品截流
> **话术说明**: 本指标为断流与竞品截流代理指标 (Hijacking Proxy)，非全网竞品真实消融数据。

---

## 1. 漏斗断流风险审计结论

{tp_desc}

---

## 2. 二轮截流防御技术语料标准规范

1. **核心团队与研发资历公开存证**：将直营研发人员名单、资质软著与行业真实案例录入 `factual_anchors.json`；
2. **拒绝转包免责承诺书**：在第三方媒体发布《{cname} 自研交付白皮书》，明确承诺“若有二道贩子转包全额退款”，构建不可动摇的心智防线；
3. **9 因子长尾技术切片回填**：针对被扣分的技术追问意图，撰写 2 篇 1500 字以上普林斯顿结构化专栏。
"""

    # 文件 3: 03_高转化行动号召落地页外链回填方案.md
    f3_content = f"""# 🎯 高转化行动号召落地页外链回填方案 · [{cname}]

> **公文编号**: GEO-OPT-24-03 ｜ **转化目标**: 打通 S4 行动号召最后一公里，促成潜客留资与来电

---

## 1. S4 行动阶段推荐置信度现状

当前 S4 阶段得分: **{stages[3]['p_score'] if len(stages)>3 else '--'}分** ｜ 行动号召就绪度: **{stages[3]['retention_rate'] if len(stages)>3 else '--'}%**

---

## 2. 行动号召 (CTA) 落地页外链回填清单

1. **官网实体 Schema.org 标定**：确保官方网站首页具备规范的 `LocalBusiness` / `Corporation` JSON-LD 结构化数据，显式声明 `telephone`、`address` 与 `sameAs`；
2. **高权重分发台账外链锚定**：将分发台账（百家号、知乎专栏、企鹅号）存活文章文末统一配置 CTA 转化锚点；
3. **robots.txt 与 llms.txt 链接收敛**：确保 `/llms.txt` 明确给出商业咨询落地页直达链接，彻底解决大模型在第 4 轮“找不到官网”的尴尬断流。
"""

    f1 = os.path.join(pack_dir, "01_多轮追问意图锚定与心智收敛话术库.md")
    f2 = os.path.join(pack_dir, "02_防竞对二轮截流技术壁垒语料补充包.md")
    f3 = os.path.join(pack_dir, "03_高转化行动号召落地页外链回填方案.md")

    with open(f1, "w", encoding="utf-8") as f:
        f.write(f1_content)
    with open(f2, "w", encoding="utf-8") as f:
        f.write(f2_content)
    with open(f3, "w", encoding="utf-8") as f:
        f.write(f3_content)

    return {
        "success": True,
        "pack_dir": pack_dir,
        "files": [f1, f2, f3],
    }


def generate_funnel_report_markdown(data: Dict[str, Any]) -> str:
    """生成符合普林斯顿 9 因子标准与免责声明的第 24 维商业决策漏斗公文报告"""
    cname = data.get("client_name", "目标企业")
    pid = data.get("project_id", "default_pid")
    ts = data.get("timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    use_live = data.get("use_live", False)
    is_live = data.get("is_live_judged", False)
    s = data.get("summary", {})
    r = data.get("radar_metrics", {})
    stages = data.get("stages", [])

    # 自适应免责声明与模式话术
    if use_live and is_live:
        decl_body = (
            f"> 本次多轮决策漏斗推演启用了真实在线大模型联网 API (`call_model_raw`)，对 4 阶递进追问链路进行了实盘在线评测。\n"
            f"> 评分融合了 70% 算法沙箱分与 30% 真实大模型裁判多轮评分。本报告旨在评估潜客在连续追问下我方的内容留存率。"
        )
    else:
        decl_body = (
            f"> 本报告采用确定性多轮商业决策漏斗沙盘推演模型（4-Stage Generative Decision Funnel）测算，未消耗真实在线模型 Token。\n"
            f"> **免责声明与话术界定**：本报告模拟的是标准意图追问链路下的内容承压能力，推演数据 $\\neq$ 真实线上用户会话日志；\n"
            f"> 截流风险指数（HRI）为内容断流与被竞品截流的**代理指标 (Hijacking Proxy)**，竞品多轮实时消融属于 Out of Scope。"
        )

    # 四阶漏斗明细表
    stage_rows = []
    for st in stages:
        tp_mark = "⚠️ 高危断点" if st.get("is_critical_turning_point") else "🟢 稳定留存"
        stage_rows.append(
            f"| **{st['stage_id']}** ｜ {st['stage_name']} | *{st['query']}* | **{st['p_score']}分** | "
            f"-{st['drop_p']}分 | **{st['retention_rate']}%** | {st['hijack_risk_index']}% | {tp_mark} |"
        )
    s_table = "\n".join(stage_rows) if stage_rows else "| -- | -- | -- | -- | -- | -- | -- |"

    return f"""# 🌪️ 大模型商业多轮追问决策漏斗与意图转化路径推演报告

**受审企业**: {cname} ｜ **项目标识**: `{pid}` ｜ **推演时间**: {ts} ｜ **推演模式**: {'🌐 在线大模型实盘推演' if (use_live and is_live) else '🔬 确定性决策漏斗沙盘'}

---

## 1. 核心审计结论与关键量化指标 (Executive Summary)

{decl_body}

| 核心指标项 | 审计实测值 | 行业参考基准 | 量化状态与评级 | 商业决策指引 |
|:---|:---:|:---:|:---:|:---|
| **端到端漏斗转化率 (FCR)** | **{s.get('fcr', 0.0)}%** | $\ge 75.0\%$ | **{s.get('grade_name', '--')}** | 四轮连续追问下潜客完整转化留存概率 |
| **决策链路总阶段数** | **{s.get('total_stages', 0)} 阶** | 4 阶闭环 | 认知 ➔ 评估 ➔ 决策 ➔ 行动 | 覆盖潜客选型至留资完整商业生命周期 |
| **高危截流脆弱断点** | **{s.get('turning_points_detected', 0)} 处** | 0 处断流 | {'🔴 存在中途严重断流！' if s.get('turning_points_detected', 0) > 0 else '🟢 全链路平稳留存'} | 单轮跌幅 $\ge 20$ 分或截流风险 $\ge 35\%$ 的拐点 |
| **首轮认知推荐置信度** | **{stages[0]['p_score'] if len(stages)>0 else 0.0}分** | $\ge 80.0$ 分 | {'🟢 优异' if (stages[0]['p_score'] if len(stages)>0 else 0)>=80 else '🟡 良好'} | 行业大词初筛下的品牌首推可见度 |
| **终阶行动号召就绪度** | **{stages[3]['p_score'] if len(stages)>3 else 0.0}分** | $\ge 70.0$ 分 | {'🟢 转化闭环' if (stages[3]['p_score'] if len(stages)>3 else 0)>=70 else '🔴 临门一脚断流'} | 索取官网/联系电话时的确定性输出率 |

---

## 2. 四维多轮决策漏斗雷达 (Four-Dimensional Funnel Radar)

```mermaid
pie title 决策漏斗流失分布
    "行动留存转化 (FCR)" : {s.get('fcr', 0.0)}
    "漏斗中途流失率" : {max(0.0, round(100.0 - s.get('fcr', 0.0), 1))}
```

- **端到端转化率 (End-to-End Conversion)**: `{r.get('end_to_end_conversion', 0.0)}%` (从初始行业词探索到最终官网转化的总效率)
- **认知到评估留存率 (Awareness to Eval)**: `{r.get('awareness_to_eval_retention', 0.0)}%` (潜客追问研发团队与资质时的抗跌能力)
- **本地决策留存率 (Decision Retention)**: `{r.get('decision_retention', 0.0)}%` (潜客追问本地直营、杜绝外包转包时的支撑度)
- **行动号召引导率 (Action CTA Readiness)**: `{r.get('action_cta_readiness', 0.0)}%` (索取官方存证、案例与联系电话的最终命中率)

---

## 3. 四阶多轮意图递进状态转移与流失矩阵 (State Transition Matrix)

| 阶段代码 ｜ 阶段名称 | 确定性商业追问 Query | 阶段推荐得分 $P(S_k)$ | 较上轮跌幅 $\Delta P$ | 阶段留存率 $T(S_k)$ | 截流风险 $HRI_k$ | 状态判定 |
|:---|:---|:---:|:---:|:---:|:---:|:---:|
{s_table}

---

## 4. 高管 ROI 预算重构与决策漏斗加固行动方案

1. **加固脆弱断流拐点 (Fix Turning Points)**：
   - 若在 S2（方案评估）出现大跌，提取 `outputs/funnel_defense_pack/02_防竞对二轮截流技术壁垒语料补充包.md`，重点补齐自研团队背景与软著存证；
2. **打通 S4 行动号召最后一公里 (Optimize CTA)**：
   - 参照 `03_高转化行动号召落地页外链回填方案.md`，在官网部署 Schema.org JSON-LD，并在第三方专栏回填官方联系电话与真实案例；
3. **建立全周期意图锚定矩阵**：
   - 提取 `01_多轮追问意图锚定与心智收敛话术库.md`，引导各高权重平台内容由泛词向精准词收敛，实现大模型多轮决策闭环。
"""


def get_funnel_status(project_id: str) -> Dict[str, Any]:
    """获取指定项目的决策漏斗推演状态 (供 API / Web 读取)"""
    out_dir = os.path.join(PROJECTS_DIR, project_id, "outputs")
    json_path = os.path.join(out_dir, "conversational_funnel_simulation.json")
    report_path = os.path.join(out_dir, "24_大模型商业多轮追问决策漏斗与意图转化路径推演报告.md")

    has_sim = os.path.exists(json_path)
    has_report = os.path.exists(report_path)

    if has_sim:
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["has_sim"] = True
            data["has_report"] = has_report
            return data
        except Exception as e:
            return {"success": False, "has_sim": False, "message": str(e)}

    return {
        "success": True,
        "has_sim": False,
        "has_report": False,
        "project_id": project_id,
        "message": "尚未执行多轮决策漏斗推演，请先触发 POST /funnel/simulate",
    }
