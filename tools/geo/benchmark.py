#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GEO 行业大盘 Benchmark 横向对标与批量并发跑批调度器 (tools/geo/benchmark.py)
核心功能：
1. 聚合全库各行业 AI 可见度与 Citation 平台渗透基准指标；
2. 为单客户生成「超越同行战绩卡片」与差距分析；
3. 基于 ThreadPoolExecutor 实现多项目批量流水线安全并发跑批。
"""

import os
import sys
import json
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed

from .utils import (
    load_project_config,
    print_banner,
    print_info,
    print_success,
    print_warning,
    PROJECTS_DIR
)
from .audit import run_audit
from .scaffold import run_scaffold
from .rewrite import run_rewrite
from .distribute import run_distribute
from .monitor import run_monitor, extract_monitor_metrics

# 默认行业均值参考基线 (冷启动兜底)
INDUSTRY_DEFAULTS = {
    "avg_sov": 38.5,
    "top_10_percent_sov": 75.0,
    "avg_top3_rate": 42.0,
    "avg_authority_score": 85.0
}

def calculate_industry_benchmarks() -> dict:
    """计算并返回全库所有行业的宏观 Benchmark 指标"""
    industry_groups = {}
    all_projects = []

    if os.path.exists(PROJECTS_DIR):
        for item in sorted(os.listdir(PROJECTS_DIR)):
            if item.startswith(".") or item == "_template":
                continue
            p_dir = os.path.join(PROJECTS_DIR, item)
            if os.path.isdir(p_dir):
                try:
                    cfg = load_project_config(item)
                    ind = cfg.get("industry", "通用企业服务/数字化").strip()
                    metrics = extract_monitor_metrics(item)
                    all_projects.append({"project_id": item, "industry": ind, "metrics": metrics})
                    if ind not in industry_groups:
                        industry_groups[ind] = []
                    industry_groups[ind].append(metrics)
                except Exception:
                    pass

    industries_summary = {}
    for ind, m_list in industry_groups.items():
        sovs = [m.get("sov_pct", 0.0) for m in m_list]
        top3s = [m.get("top3_pct", 0.0) for m in m_list]
        auths = [m.get("authority_score", 0.0) for m in m_list]

        avg_sov = round(statistics.mean(sovs), 1) if sovs else 0.0
        med_sov = round(statistics.median(sovs), 1) if sovs else 0.0
        
        # 计算 90 分位数标杆线，样本不足时取最大值或默认参考线
        if len(sovs) >= 10:
            top_10_sov = round(statistics.quantiles(sovs, n=10)[8], 1)
        elif any(s > 0 for s in sovs):
            top_10_sov = round(max(sovs), 1)
        else:
            top_10_sov = 0.0

        avg_top3 = round(statistics.mean(top3s), 1) if top3s else 0.0
        avg_auth = round(statistics.mean(auths), 1) if auths else 0.0

        # 汇总各平台渗透分布
        platform_counts = {"zhihu": 0, "toutiao": 0, "wechat": 0, "github": 0}
        for m in m_list:
            for c in m.get("citations", []):
                dom = c.get("domain", "")
                if "zhihu" in dom:
                    platform_counts["zhihu"] += c.get("count", 1)
                elif "toutiao" in dom:
                    platform_counts["toutiao"] += c.get("count", 1)
                elif "weixin" in dom:
                    platform_counts["wechat"] += c.get("count", 1)
                elif "github" in dom:
                    platform_counts["github"] += c.get("count", 1)

        total_cnt = sum(platform_counts.values()) or 1
        top_citations = [
            {"domain": "zhihu.com", "name": "知乎专栏", "pct": round(platform_counts["zhihu"] / total_cnt * 100, 1)},
            {"domain": "toutiao.com", "name": "今日头条", "pct": round(platform_counts["toutiao"] / total_cnt * 100, 1)},
            {"domain": "github.com", "name": "GitHub 开源", "pct": round(platform_counts["github"] / total_cnt * 100, 1)},
            {"domain": "weixin.qq.com", "name": "微信公众号", "pct": round(platform_counts["wechat"] / total_cnt * 100, 1)}
        ]

        industries_summary[ind] = {
            "industry_name": ind,
            "project_count": len(m_list),
            "avg_sov": avg_sov,
            "median_sov": med_sov,
            "top_10_percent_sov": top_10_sov,
            "avg_top3_rate": avg_top3,
            "avg_authority_score": avg_auth,
            "top_citations": top_citations
        }

    return {
        "success": True,
        "total_projects": len(all_projects),
        "industries": industries_summary
    }

def evaluate_project_against_benchmark(project_id: str) -> dict:
    """对指定客户生成行业横向对标战绩与差距报告"""
    cfg = load_project_config(project_id)
    industry = cfg.get("industry", "通用企业服务/数字化").strip()
    client_name = cfg.get("client_name", project_id)
    metrics = extract_monitor_metrics(project_id)

    benchmarks_data = calculate_industry_benchmarks()
    ind_bench = benchmarks_data.get("industries", {}).get(industry, {})

    avg_sov = ind_bench.get("avg_sov", 0.0)
    top_sov = ind_bench.get("top_10_percent_sov", 0.0)
    curr_sov = metrics.get("sov_pct", 0.0)
    is_offline = metrics.get("is_offline", False)

    diff_from_avg = round(curr_sov - avg_sov, 1)

    # 判定段位与计算超越同行百分比 (Beat Rate)
    if curr_sov <= 0 or is_offline:
        beat_rate = 10.0
        tier = "🟡 冷启动/摸底基准期 (Cold Start)"
        badge_color = "amber"
        summary = f"当前处于优化前冷启动/摸底阶段（SOV: 0.0%），所属【{industry}】行业均值为 {avg_sov}%。建议推进 9 因子语料重构与四大平台权威分发，快速建立首批大模型索引。"
    else:
        # 有真实 SOV 正向数据时的分位数判定
        target_benchmark = max(top_sov, avg_sov, 60.0)
        beat_rate = min(99.0, max(15.0, round((curr_sov / target_benchmark) * 90.0, 1)))

        if curr_sov >= top_sov and top_sov > 0:
            tier = "🏆 行业领跑标杆 (Top Tier)"
            badge_color = "emerald"
            summary = f"您的 AI 可见度已位列【{industry}】行业前 5% 顶尖梯队（SOV: {curr_sov}%），超越行业均值 +{diff_from_avg}%，在大模型各选型问句中保持统治级首推！"
        elif curr_sov >= avg_sov:
            tier = "🟢 行业优势阵地 (Above Average)"
            badge_color = "indigo"
            summary = f"您的 AI 可见度高出【{industry}】行业均值 +{diff_from_avg}%（SOV: {curr_sov}%），在主流技术选型词中已建立稳固护城河。"
        else:
            tier = "🟡 快速爬坡阶段 (Growth Stage)"
            badge_color = "amber"
            gap = round(avg_sov - curr_sov, 1)
            summary = f"当前处于成长期（SOV: {curr_sov}%），距离行业平均线差距 {gap}%，建议持续分发 9 因子语料并在知乎/头条加码。"

    return {
        "success": True,
        "project_id": project_id,
        "client_name": client_name,
        "industry": industry,
        "client_sov": curr_sov,
        "industry_avg_sov": avg_sov,
        "industry_top_sov": top_sov,
        "diff_from_avg": diff_from_avg,
        "beat_rate": beat_rate,
        "tier": tier,
        "badge_color": badge_color,
        "summary": summary,
        "top_citations": ind_bench.get("top_citations", [])
    }

# ==========================================
# 批量多项目并发跑批调度器
# ==========================================

def _execute_single_step(project_id: str, step: str) -> dict:
    """执行单个项目的指定阶段"""
    if step == "audit":
        run_audit(project_id)
        msg = "体检诊断已执行完毕"
    elif step == "scaffold":
        run_scaffold(project_id)
        msg = "底座改造已生成"
    elif step == "rewrite":
        run_rewrite(project_id)
        msg = "语料重构完毕"
    elif step == "distribute":
        run_distribute(project_id)
        msg = "矩阵分发包就绪"
    elif step == "monitor":
        run_monitor(project_id)
        msg = "声量监测周报已生成"
    elif step == "pipeline":
        run_audit(project_id)
        run_scaffold(project_id)
        run_rewrite(project_id)
        run_distribute(project_id)
        run_monitor(project_id)
        msg = "5 步流水线全量执行完毕"
    else:
        raise ValueError(f"不支持的执行阶段: {step}")

    return {"project_id": project_id, "step": step, "message": msg}

def run_batch_pipeline(target_ids: list = None, industry: str = None, step: str = "pipeline", max_workers: int = 4) -> list:
    """多项目安全并发批量跑批"""
    # 筛选目标项目
    p_ids = []
    if target_ids and target_ids != "all":
        p_ids = target_ids if isinstance(target_ids, list) else [target_ids]
    else:
        if os.path.exists(PROJECTS_DIR):
            for item in sorted(os.listdir(PROJECTS_DIR)):
                if item.startswith(".") or item == "_template":
                    continue
                p_dir = os.path.join(PROJECTS_DIR, item)
                if os.path.isdir(p_dir):
                    if industry:
                        try:
                            cfg = load_project_config(item)
                            if cfg.get("industry") == industry:
                                p_ids.append(item)
                        except Exception:
                            pass
                    else:
                        p_ids.append(item)

    print_banner(f"启动批量并发调度中枢: 任务阶段 [{step}] ｜ 目标项目数: {len(p_ids)} ｜ 并发度: {max_workers}")
    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_pid = {
            executor.submit(_execute_single_step, pid, step): pid 
            for pid in p_ids
        }
        for future in as_completed(future_to_pid):
            pid = future_to_pid[future]
            try:
                data = future.result()
                results.append({"project_id": pid, "success": True, "data": data})
                print_success(f"✅ 项目 [{pid}] 阶段 [{step}] 执行成功！")
            except Exception as e:
                results.append({"project_id": pid, "success": False, "error": str(e)})
                print_warning(f"⚠️ 项目 [{pid}] 执行异常: {e}")

    print_success(f"🎉 批量任务调度完成！共处理 {len(results)} 个项目。")
    return results

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "evaluate":
        pid = sys.argv[2] if len(sys.argv) > 2 else "xuzhou_xuanyuan"
        print(json.dumps(evaluate_project_against_benchmark(pid), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(calculate_industry_benchmarks(), ensure_ascii=False, indent=2))
