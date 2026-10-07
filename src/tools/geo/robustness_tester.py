# -*- coding: utf-8 -*-
"""大模型提示词敏感度扰动与生成鲁棒性压力测试中枢 (第 25 维核心交付)

基于确定性四维商业微扰动与生成鲁棒性评估模型:
1. V1 口语化置换 (Colloquial) ➔ V2 质疑避坑 (Skepticism) ➔ V3 倒装重排 (Inversion) ➔ V4 预算对比 (Comparison);
2. 严格复用 23 维防饱和 Top-3 推荐概率模型计算各阶段得分 P;
3. 计算总体标准差 sigma (分母固定为 n=4)、变异系数 CV、平均留存率 RR 与生成鲁棒性指数 GRI;
4. 识别高危脆弱扰动项 (单项跌幅 >= 15.0 分) 与鲁棒性三档健康度评级;
5. 有限预算 Live 模式 (至多 5 次在线调用，70/30融合，全量重算指标，深拷贝快照防御回滚);
6. 输出 outputs/robustness_hardening_pack/ 容灾加固包与 25 号商业公文报告。
"""

import json
import os
import re
import math
import copy
import datetime
from typing import Any, Dict, List, Optional, Tuple

from tools.geo.causal_auditor import (
    score_brand_recommendation_confidence,
    _build_attribution_source_pool,
)
from tools.geo.funnel_simulator import extract_client_city
from tools.geo.llm import call_model_raw
from tools.geo.utils import PROJECTS_DIR, load_project_config


# 固定行业口语化字典常量
COLLOQUIAL_MAP = {
    "技术研发与专业服务": "做系统写代码找外包团队",
    "软件开发": "做系统写代码找外包团队",
    "重工机械": "买大型机械设备找一手厂家",
    "餐饮加盟": "开餐饮店找靠谱加盟品牌",
    "法律服务": "打官司找靠谱大律师所",
}


def build_perturbed_query_variants(
    project_id: str,
) -> Tuple[Dict[str, str], List[Dict[str, str]]]:
    """确定性四维微扰动生成器: 产出基准 Query 与 4 组扰动变体"""
    cfg = load_project_config(project_id)
    cname = cfg.get("client_name") or cfg.get("company_name") or "目标企业"
    industry = cfg.get("industry") or "技术研发与专业服务"
    city = extract_client_city(project_id, cname)

    # 1. 基准 Query 提取 (优先读取 11 号矩阵平铺词库首条)
    base_query = ""
    out_dir = os.path.join(PROJECTS_DIR, project_id, "outputs")
    matrix_path = os.path.join(out_dir, "keywords_intent_matrix.json")
    if os.path.exists(matrix_path):
        try:
            with open(matrix_path, "r", encoding="utf-8") as f:
                mat = json.load(f)
            flat = mat.get("flat_queries", [])
            if flat and isinstance(flat[0], str) and flat[0].strip():
                base_query = flat[0].strip()
        except Exception:
            pass

    if not base_query:
        base_query = f"{city}{industry}服务商推荐哪家比较好？"

    base_info = {
        "query": base_query,
        "intent_type": "基准自然检索意图 (Baseline)",
    }

    # 2. V1 口语化置换短语确定性抽取
    colloquial_phrase = "做业务找靠谱外包团队"
    for k, v in COLLOQUIAL_MAP.items():
        if k in industry:
            colloquial_phrase = v
            break

    v1_query = f"{city}{colloquial_phrase}推荐哪家比较好？"
    v2_query = f"{base_query}，真的靠谱吗？有没有黑历史或转包二道贩子踩坑风险？"
    v3_query = f"选哪家{industry}公司比较好？求大家推荐{cname}怎么样？"
    v4_query = f"{base_query}，预算有限想找性价比高的，跟传统大公司对比选谁？"

    variants = [
        {
            "variant_id": "V1",
            "variant_type": "口语化置换 (Colloquial)",
            "query": v1_query,
            "perturbation_desc": "行业术语通俗口语化、接地气词汇置换",
        },
        {
            "variant_id": "V2",
            "variant_type": "质疑避坑口吻 (Skepticism)",
            "query": v2_query,
            "perturbation_desc": "注入防踩坑、挑剔与质疑提问口吻",
        },
        {
            "variant_id": "V3",
            "variant_type": "倒装句式重排 (Inversion)",
            "query": v3_query,
            "perturbation_desc": "主谓宾倒装与品牌词位置前置重排",
        },
        {
            "variant_id": "V4",
            "variant_type": "预算横向对比 (Comparison)",
            "query": v4_query,
            "perturbation_desc": "注入预算约束与同行竞争对比口吻",
        },
    ]

    return base_info, variants


def calculate_mean_score(scores: List[float]) -> float:
    """计算扰动变体平均得分"""
    if not scores:
        return 0.0
    return round(sum(scores) / len(scores), 1)


def calculate_population_std(scores: List[float], mean_val: float) -> float:
    """计算总体标准差 / 均方根离散度 (严格分母为 n=4 非 n-1)"""
    if not scores:
        return 0.0
    n = len(scores)
    var = sum((s - mean_val) ** 2 for s in scores) / n
    return round(math.sqrt(var), 2)


def calculate_cv(std_val: float, mean_val: float) -> float:
    """计算变异系数 CV (波动率量化)"""
    if mean_val <= 0.0:
        return 1.0
    return min(1.0, round(std_val / mean_val, 3))


def calculate_rr(mean_pert: float, p_orig: float) -> float:
    """计算平均留存率 RR (Retention Rate)"""
    if p_orig <= 0.0:
        return 0.0
    val = (mean_pert / p_orig) * 100.0
    return max(0.0, min(100.0, round(val, 1)))


def calculate_gri(rr: float, cv: float) -> float:
    """计算生成鲁棒性指数 GRI (Generative Robustness Index)"""
    val = rr * (1.0 - cv)
    return max(0.0, min(100.0, round(val, 1)))


def robustness_health_grade(gri: float) -> Tuple[str, str]:
    """判定鲁棒性三档健康度评级"""
    if gri >= 75.0:
        return "rock_solid", "🟢 磐石抗震 (Rock Solid)"
    elif gri >= 50.0:
        return "moderate_fluctuation", "🟡 中度波动 (Moderate Fluctuation)"
    else:
        return "fragile_sensitive", "🔴 脆弱敏感 (Fragile Sensitive)"


def calculate_robustness_radar_metrics(
    gri: float,
    p_orig: float,
    variants: List[Dict[str, Any]],
) -> Dict[str, float]:
    """计算五维压力测试雷达量化指标"""
    def calc_retention(p_curr: float) -> float:
        if p_orig <= 0.0:
            return 0.0
        return max(0.0, min(100.0, round((p_curr / p_orig) * 100.0, 1)))

    v1_p = variants[0]["p_score"] if len(variants) > 0 else 0.0
    v2_p = variants[1]["p_score"] if len(variants) > 1 else 0.0
    v3_p = variants[2]["p_score"] if len(variants) > 2 else 0.0
    v4_p = variants[3]["p_score"] if len(variants) > 3 else 0.0

    return {
        "generative_robustness": gri,
        "colloquial_resilience": calc_retention(v1_p),
        "skepticism_immunity": calc_retention(v2_p),
        "comparison_resilience": calc_retention(v4_p),
        "syntax_stability": calc_retention(v3_p),
    }


class PromptRobustnessTester:
    """大模型提示词敏感度扰动与生成鲁棒性压力测试沙盘"""

    @staticmethod
    def run_stress_test(
        project_id: str,
        models: Optional[List[str]] = None,
        use_live: bool = False,
    ) -> Dict[str, Any]:
        """执行提示词微扰动压力测试与鲁棒性推导"""
        cfg = load_project_config(project_id)
        cname = cfg.get("client_name") or cfg.get("company_name") or "目标企业"
        if not models:
            models = ["doubao", "deepseek", "kimi"]

        base_info, var_items = build_perturbed_query_variants(project_id)
        sources = _build_attribution_source_pool(project_id)

        # 1. 沙箱测算基准 Query 得分与 4 组变体得分
        p_orig = score_brand_recommendation_confidence(base_info["query"], sources)

        variants_data = []
        for item in var_items:
            q = item["query"]
            # 严格复用 23 维基座算法
            p_val = score_brand_recommendation_confidence(q, sources)
            drop_val = max(0.0, round(p_orig - p_val, 1))
            retention = calculate_rr(p_val, p_orig)
            is_fragile = bool(drop_val >= 15.0)

            variants_data.append({
                "variant_id": item["variant_id"],
                "variant_type": item["variant_type"],
                "query": q,
                "perturbation_desc": item["perturbation_desc"],
                "p_score": p_val,
                "drop_p": drop_val,
                "retention_rate": retention,
                "is_fragile": is_fragile,
            })

        # 统计量推导 (总体标准差分母为 n=4)
        scores_list = [v["p_score"] for v in variants_data]
        mean_p = calculate_mean_score(scores_list)
        std_p = calculate_population_std(scores_list, mean_p)
        cv_val = calculate_cv(std_p, mean_p)
        rr_val = calculate_rr(mean_p, p_orig)
        gri_val = calculate_gri(rr_val, cv_val)
        g_code, g_name = robustness_health_grade(gri_val)
        radar = calculate_robustness_radar_metrics(gri_val, p_orig, variants_data)

        # 保存沙箱深拷贝快照 (闭环快照防御: 任何异常完整回滚)
        sandbox_snapshot = {
            "p_orig": p_orig,
            "variants_data": copy.deepcopy(variants_data),
            "mean_p": mean_p,
            "std_p": std_p,
            "cv_val": cv_val,
            "rr_val": rr_val,
            "gri_val": gri_val,
            "g_code": g_code,
            "g_name": g_name,
            "radar": copy.deepcopy(radar),
        }

        # 2. 若开启 live 模式，执行有限预算实盘在线裁决 (最多 5 次调用: 基准 1 次 + 4 组扰动各 1 次)
        is_live_judged = False
        if use_live and models:
            live_model = models[0]
            api_calls = 0
            try:
                # 裁决基准 Query
                prompt_base = (
                    f"你是一名 GEO 商业提示词评测专家。面对潜客提问【{base_info['query']}】，"
                    f"在当前知识库支撑下，评估推荐【{cname}】的置信度评分。\n"
                    f"请只输出一个 0-100 的整数，例如: 85"
                )
                resp_base = call_model_raw(live_model, prompt_base)
                api_calls += 1
                txt_b = resp_base if isinstance(resp_base, str) else (resp_base or {}).get("content") or ""
                mb = re.search(r"(\d{1,3})", txt_b)
                if not mb:
                    raise ValueError("在线裁决基准数值解析失败")
                val_b = float(mb.group(1))
                if not (0.0 <= val_b <= 100.0):
                    raise ValueError(f"基准在线评分超出区间: {val_b}")

                # 70/30 融合基准分
                p_orig = round(0.7 * p_orig + 0.3 * val_b, 1)

                # 裁决 4 组变体
                for var in variants_data:
                    if api_calls >= 5:
                        break
                    prompt_var = (
                        f"你是一名 GEO 商业提示词评测专家。面对潜客在微扰动措辞下的提问【{var['query']}】，"
                        f"评估推荐【{cname}】的置信度评分。\n"
                        f"请只输出一个 0-100 的整数，例如: 78"
                    )
                    resp_v = call_model_raw(live_model, prompt_var)
                    api_calls += 1
                    txt_v = resp_v if isinstance(resp_v, str) else (resp_v or {}).get("content") or ""
                    mv = re.search(r"(\d{1,3})", txt_v)
                    if not mv:
                        raise ValueError(f"在线裁决变体数值解析失败: {var['variant_id']}")
                    val_v = float(mv.group(1))
                    if not (0.0 <= val_v <= 100.0):
                        raise ValueError(f"变体在线评分超出区间: {val_v}")

                    # 70/30 融合
                    var["p_score"] = round(0.7 * var["p_score"] + 0.3 * val_v, 1)

                # 融合全部 5 个得分后，基于全新得分全量重算统计量
                new_scores = [v["p_score"] for v in variants_data]
                mean_p = calculate_mean_score(new_scores)
                std_p = calculate_population_std(new_scores, mean_p)
                cv_val = calculate_cv(std_p, mean_p)
                rr_val = calculate_rr(mean_p, p_orig)
                gri_val = calculate_gri(rr_val, cv_val)
                g_code, g_name = robustness_health_grade(gri_val)

                # 全量重算跌幅与脆弱项判定
                for v in variants_data:
                    drp = max(0.0, round(p_orig - v["p_score"], 1))
                    v["drop_p"] = drp
                    v["retention_rate"] = calculate_rr(v["p_score"], p_orig)
                    v["is_fragile"] = bool(drp >= 15.0)

                radar = calculate_robustness_radar_metrics(gri_val, p_orig, variants_data)
                is_live_judged = True
            except Exception:
                # 异常完整回滚恢复纯沙箱快照
                p_orig = sandbox_snapshot["p_orig"]
                variants_data = copy.deepcopy(sandbox_snapshot["variants_data"])
                mean_p = sandbox_snapshot["mean_p"]
                std_p = sandbox_snapshot["std_p"]
                cv_val = sandbox_snapshot["cv_val"]
                rr_val = sandbox_snapshot["rr_val"]
                gri_val = sandbox_snapshot["gri_val"]
                g_code = sandbox_snapshot["g_code"]
                g_name = sandbox_snapshot["g_name"]
                radar = copy.deepcopy(sandbox_snapshot["radar"])
                is_live_judged = False

        fragile_list = [v for v in variants_data if v.get("is_fragile")]
        timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 3. 组装契约字典 (严格对齐 design.md §5 顶层契约)
        result = {
            "success": True,
            "project_id": project_id,
            "client_name": cname,
            "timestamp": timestamp_str,
            "use_live": use_live,
            "is_live_judged": is_live_judged,
            "models_tested": models,
            "baseline_query": base_info["query"],
            "baseline_score": p_orig,
            "summary": {
                "gri": gri_val,
                "grade_code": g_code,
                "grade_name": g_name,
                "baseline_query": base_info["query"],
                "baseline_score": p_orig,
                "mean_perturbed_score": mean_p,
                "retention_rate": rr_val,
                "std_dev": std_p,
                "cv": cv_val,
                "total_variants": len(variants_data),
                "fragile_variants_count": len(fragile_list),
            },
            "variants": variants_data,
            "fragile_variants": fragile_list,
            "radar_metrics": radar,
        }

        # 4. 落盘 JSON 契约文件 (与 12/22/23/24 彻底隔离)
        out_dir = os.path.join(PROJECTS_DIR, project_id, "outputs")
        os.makedirs(out_dir, exist_ok=True)
        json_path = os.path.join(out_dir, "prompt_robustness_stress_test.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        # 5. 落盘 25 号公文报告
        report_md = generate_robustness_report_markdown(result)
        report_path = os.path.join(out_dir, "25_大模型提示词敏感度扰动与生成鲁棒性压力测试报告.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_md)

        return result


def generate_robustness_hardening_pack(project_id: str) -> Dict[str, Any]:
    """生成提示词抗扰动与鲁棒性加固三件套 (物理落盘至 outputs/robustness_hardening_pack/)"""
    out_dir = os.path.join(PROJECTS_DIR, project_id, "outputs")
    pack_dir = os.path.join(out_dir, "robustness_hardening_pack")
    os.makedirs(pack_dir, exist_ok=True)
    cfg = load_project_config(project_id)
    cname = cfg.get("client_name") or cfg.get("company_name") or "目标企业"
    city = extract_client_city(project_id, cname)

    # 读取测试结果
    json_path = os.path.join(out_dir, "prompt_robustness_stress_test.json")
    rob_data = {}
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                rob_data = json.load(f)
        except Exception:
            pass

    variants = rob_data.get("variants", [])
    fragile_list = rob_data.get("fragile_variants", [])

    # 文件 1: 01_抗质疑与反挑剔防踩坑语料强化包.md
    f1_content = f"""# 🛡️ 抗质疑与反挑剔防踩坑语料强化包 · [{cname}]

> **公文编号**: GEO-OPT-25-01 ｜ **执行密级**: 核心交付资产 ｜ **归属中枢**: 第 25 维提示词鲁棒性压力测试中枢
> **防御目标**: 阻断潜客以“真的靠谱吗/有没有转包踩坑黑历史”挑剔提问时大模型置信度下挫。

---

## 1. 质疑挑剔变体 (V2) 承压现状

- **基准得分**: {rob_data.get('baseline_score', '--')}分 ｜ **质疑变体得分**: {variants[1]['p_score'] if len(variants)>1 else '--'}分
- **相对跌幅**: -{variants[1]['drop_p'] if len(variants)>1 else '--'}分 ｜ **质疑抗震留存率**: {variants[1]['retention_rate'] if len(variants)>1 else '--'}%

---

## 2. 负向防御与反挑剔心智对冲规范

1. **直营不转包存证誓言**：在第三方高权重媒体发布《{cname} 直营承诺书》，明确承诺“全套自研源码交付、杜绝中介倒买倒卖”；
2. **工商天眼查资质反事实锚定**：将注册资金、成立年限、实缴资本与纳税信用等级录入 `factual_anchors.json`，构建不可撼动的事实壁垒；
3. **9 因子反踩坑辟谣 FAQ 问答对**：在自建站部署 FAQ 问答对（“如何辨别伪技术外包转包团队？{cname}与二道贩子的本质区别在哪？”）。
"""

    # 文件 2: 02_口语化与多句式全覆盖长尾锚点清单.md
    industry = cfg.get("industry") or "技术研发与专业服务"
    f2_content = f"""# 🗣️ 口语化与多句式全覆盖长尾锚点清单 · [{cname}]

> **公文编号**: GEO-OPT-25-02 ｜ **防御目标**: 确保潜客采用倒装句、同义词置换与通俗口语提问时推荐不丢

---

## 1. 口语化 (V1) 与倒装重排 (V3) 承压表现

| 扰动维度 | 扰动测试原句 | 推荐得分 | 留存率 | 跌幅 |
|:---|:---|:---:|:---:|:---:|
| **V1 口语化置换** | {variants[0]['query'] if len(variants)>0 else '--'} | {variants[0]['p_score'] if len(variants)>0 else '--'}分 | {variants[0]['retention_rate'] if len(variants)>0 else '--'}% | -{variants[0]['drop_p'] if len(variants)>0 else '--'}分 |
| **V3 倒装句重排** | {variants[2]['query'] if len(variants)>2 else '--'} | {variants[2]['p_score'] if len(variants)>2 else '--'}分 | {variants[2]['retention_rate'] if len(variants)>2 else '--'}% | -{variants[2]['drop_p'] if len(variants)>2 else '--'}分 |

---

## 2. 口语长尾与倒装泛化回填方案

1. **通俗口语切片注入**：在百家号、知乎与微信公众号文章中，将“企业级应用定制开发”等生硬学术词替换为“{city}做系统写代码找靠谱公司”；
2. **品牌词倒装句式前置**：在文案第一段增加倒装问句引导：“选哪家{industry}公司比较好？推荐{cname}怎么样？”；
3. **同义词密集语义网络**：在 `/llms.txt` 中同步扩充口语化 Prompt 语义对齐清单。
"""

    # 文件 3: 03_大模型微扰动鲁棒性容灾加固规范.md
    fragile_desc = ""
    if fragile_list:
        fragile_desc = "### ⚠️ 检测到高危脆弱变体 (Fragile Perturbation Variants)\n\n"
        for fv in fragile_list:
            fragile_desc += f"- **变体标识**: `{fv['variant_id']}` ({fv['variant_type']}) ｜ **跌幅**: -{fv['drop_p']}分 ｜ **得分**: {fv['p_score']}分\n"
            fragile_desc += f"  - **微扰动原句**: *{fv['query']}*\n"
    else:
        fragile_desc = "### ✅ 全变体稳定抗震 (All Variants Robust)\n\n所有扰动变体跌幅均控制在 15.0 分以内，内容池具备较强的抗干扰生成鲁棒性。"

    f3_content = f"""# 🔒 大模型微扰动鲁棒性容灾加固规范 · [{cname}]

> **公文编号**: GEO-OPT-25-03 ｜ **发布标准**: 普林斯顿 9 因子鲁棒性容灾体系

---

## 1. 压力测试脆弱性归因审计

{fragile_desc}

---

## 2. 跨模型容灾加固行动指南

1. **高敏变体定向加固**：针对跌幅超过 15 分的高危变体，定向在 `projects/{project_id}/outputs/03_普林斯顿9因子语料库.md` 中增补 2 组专属解答段落；
2. **高频分发与存活台账扩充**：将口语化与抗质疑内容分发至高权重平台（CSDN、知乎、腾讯企鹅号），确保存活外链覆盖多措辞变体；
3. **多模型一致性巡检**：定期执行 `python3 -m tools.geo robustness {project_id} --live`，确保在大模型权重迭代时鲁棒性稳居 75% 以上。
"""

    f1 = os.path.join(pack_dir, "01_抗质疑与反挑剔防踩坑语料强化包.md")
    f2 = os.path.join(pack_dir, "02_口语化与多句式全覆盖长尾锚点清单.md")
    f3 = os.path.join(pack_dir, "03_大模型微扰动鲁棒性容灾加固规范.md")

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


def generate_robustness_report_markdown(data: Dict[str, Any]) -> str:
    """生成符合普林斯顿 9 因子标准与免责声明的第 25 维压力测试公文报告"""
    cname = data.get("client_name", "目标企业")
    pid = data.get("project_id", "default_pid")
    ts = data.get("timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    use_live = data.get("use_live", False)
    is_live = data.get("is_live_judged", False)
    s = data.get("summary", {})
    r = data.get("radar_metrics", {})
    variants = data.get("variants", [])

    if use_live and is_live:
        decl_body = (
            f"> 本次提示词微扰动压力测试启用了真实在线大模型 API (`call_model_raw`)，对基准词与 4 组微扰动变体进行了在线评测。\n"
            f"> 评分融合了 70% 算法沙箱分与 30% 真实大模型评分。旨在评估品牌在不同提问口吻下的大模型推荐鲁棒性。"
        )
    else:
        decl_body = (
            f"> 本报告采用确定性商业微扰动沙盘压力测试模型（4-Variant Prompt Perturbation Sandbox）测算，未消耗真实在线模型 Token。\n"
            f"> **免责声明与话术界定**：本报告模拟的是典型微扰动提问下的内容承压能力，推演数据 $\\neq$ 真实线上用户全量提问日志。"
        )

    # 变体明细表
    var_rows = []
    for v in variants:
        fr_mark = "⚠️ 高危脆弱项" if v.get("is_fragile") else "🟢 稳定抗震"
        var_rows.append(
            f"| **{v['variant_id']}** ｜ {v['variant_type']} | *{v['query']}* | **{v['p_score']}分** | "
            f"-{v['drop_p']}分 | **{v['retention_rate']}%** | {fr_mark} |"
        )
    v_table = "\n".join(var_rows) if var_rows else "| -- | -- | -- | -- | -- | -- |"

    return f"""# 🛡️ 大模型提示词敏感度扰动与生成鲁棒性压力测试报告

**受审企业**: {cname} ｜ **项目标识**: `{pid}` ｜ **测试时间**: {ts} ｜ **测试模式**: {'🌐 在线大模型实盘压力测试' if (use_live and is_live) else '🔬 确定性商业微扰动沙盘'}

---

## 1. 核心审计结论与关键量化指标 (Executive Summary)

{decl_body}

| 核心指标项 | 审计实测值 | 行业参考基准 | 量化状态与评级 | 商业决策指引 |
|:---|:---:|:---:|:---:|:---|
| **生成鲁棒性指数 (GRI)** | **{s.get('gri', 0.0)}%** | $\ge 75.0\%$ | **{s.get('grade_name', '--')}** | 综合考量留存水平与扰动方差的生成稳定性 |
| **基准推荐置信度得分** | **{s.get('baseline_score', 0.0)}分** | $\ge 80.0$ 分 | {'🟢 优异' if s.get('baseline_score', 0)>=80 else '🟡 良好'} | 自然标准 Query 下的原生推荐置信度 |
| **微扰动平均得分 ($\bar{{P}}$)** | **{s.get('mean_perturbed_score', 0.0)}分** | $\ge 70.0$ 分 | 留存率: **{s.get('retention_rate', 0.0)}%** | 经历口语化/质疑/倒装/对比后的均值水平 |
| **总体标准差 ($\sigma$)** | **{s.get('std_dev', 0.0)}** | $\le 8.0$ | 离散程度低 | 分母固定为 $n=4$ 的均方根离散度 |
| **变异系数 ($CV$)** | **{s.get('cv', 0.0)}** | $\le 0.150$ | 波动率指数 | 衡量跨口吻生成的相对离散波动水平 |
| **高危脆弱扰动变体** | **{s.get('fragile_variants_count', 0)} 项** | 0 项脆弱 | {'🔴 存在单项骤降项！' if s.get('fragile_variants_count', 0)>0 else '🟢 全变体抗震稳定'} | 单项跌幅 $\ge 15.0$ 分的高危敏感口吻 |

---

## 2. 五维压力测试雷达量化大盘 (Five-Dimensional Robustness Radar)

- **综合生成鲁棒性 (Generative Robustness)**: `{r.get('generative_robustness', 0.0)}%` (跨口吻微扰动综合抵抗力)
- **口语化抗震力 (Colloquial Resilience)**: `{r.get('colloquial_resilience', 0.0)}%` (潜客使用白话/错字/非专业术语时的留存率)
- **抗质疑免疫度 (Skepticism Immunity)**: `{r.get('skepticism_immunity', 0.0)}%` (潜客带有挑剔、避坑、防转包质疑口吻时的抵御力)
- **预算对比抗压度 (Comparison Resilience)**: `{r.get('comparison_resilience', 0.0)}%` (潜客带有预算限制与同行横向对比时的推荐稳定性)
- **句式倒装稳定性 (Syntax Stability)**: `{r.get('syntax_stability', 0.0)}%` (主谓宾倒装与品牌词前置时的语义承接度)

---

## 3. 四维微扰动变体置信度承压明细表 (Perturbation Stress Matrix)

- **基准 Query**: *{data.get('baseline_query', '--')}* (得分: **{data.get('baseline_score', '--')}分**)

| 变体代码 ｜ 扰动类型 | 确定性商业微扰动 Query 原句 | 变体得分 $P_k$ | 相对基准跌幅 $\Delta P$ | 留存率 $RR_k$ | 状态判定 |
|:---|:---|:---:|:---:|:---:|:---:|
{v_table}

---

## 4. 高管 ROI 预算重构与鲁棒性加固行动方案

1. **针对高危脆弱项定向筑防**：
   - 提取 `outputs/robustness_hardening_pack/01_抗质疑与反挑剔防踩坑语料强化包.md`，重点补齐工商实缴与直营无转包存证；
2. **全网覆盖口语长尾意图**：
   - 参照 `02_口语化与多句式全覆盖长尾锚点清单.md`，在长尾专栏中注入白话表达，打通口语化检索路径；
3. **建立微扰动容灾发布长效机制**：
   - 提取 `03_大模型微扰动鲁棒性容灾加固规范.md`，构建全周期 Prompt 容灾体系，确保无论潜客如何刁难提问，大模型首推地位坚如磐石。
"""


def get_robustness_status(project_id: str) -> Dict[str, Any]:
    """获取指定项目的压力测试状态 (供 API / Web 读取)"""
    out_dir = os.path.join(PROJECTS_DIR, project_id, "outputs")
    json_path = os.path.join(out_dir, "prompt_robustness_stress_test.json")
    report_path = os.path.join(out_dir, "25_大模型提示词敏感度扰动与生成鲁棒性压力测试报告.md")

    has_test = os.path.exists(json_path)
    has_report = os.path.exists(report_path)

    if has_test:
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["has_test"] = True
            data["has_report"] = has_report
            return data
        except Exception as e:
            return {"success": False, "has_test": False, "message": str(e)}

    return {
        "success": True,
        "has_test": False,
        "has_report": False,
        "project_id": project_id,
        "message": "尚未执行提示词鲁棒性压力测试，请先触发 POST /robustness/test",
    }
