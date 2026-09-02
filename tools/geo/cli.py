#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GEO 商业交付工具包 CLI 总调度程序 (tools/geo/cli.py)
支持阶段子命令：
- init: 创建新客户项目工作区
- audit: 阶段一 诊断体检
- scaffold: 阶段二 底座脚手架生成
- rewrite: 阶段三 普林斯顿内容重构
- distribute: 阶段四 多平台分发包生成
- monitor: 阶段五 AI 可见度监控周报
- pipeline: 一键执行五步端到端交付流水线
"""

import os
import sys
import shutil
import argparse
from .utils import (
    PROJECTS_DIR,
    print_banner,
    print_info,
    print_success,
    print_warning,
    print_error
)
from .audit import run_audit
from .scaffold import run_scaffold
from .rewrite import run_rewrite
from .distribute import run_distribute
from .monitor import run_monitor
from .server import start_server

def cmd_init_project(project_id: str):
    """从 _template 初始化新客户项目"""
    print_banner(f"创建新客户项目: {project_id}")
    template_dir = os.path.join(PROJECTS_DIR, "_template")
    target_dir = os.path.join(PROJECTS_DIR, project_id)
    
    if os.path.exists(target_dir):
        print_error(f"项目目录已存在: {target_dir}")
        sys.exit(1)
        
    shutil.copytree(template_dir, target_dir)
    print_success(f"客户项目初始化成功！")
    print_info(f"项目路径: {target_dir}")
    print_info(f"👉 请编辑 `{target_dir}/project.yaml` 填入客户名称、官网和关键词。")

def cmd_run_pipeline(project_id: str):
    """一键执行完整五步交付流水线"""
    print_banner(f"🚀 启动 GEO 全流程商业交付流水线: [{project_id}]")
    
    print_info("▶ [1/5] 执行客户现状体检与商业诊断...")
    run_audit(project_id)
    
    print_info("\n▶ [2/5] 生成站点底座技术改造包 (llms.txt / JSON-LD / robots.txt)...")
    run_scaffold(project_id)
    
    print_info("\n▶ [3/5] 执行普林斯顿 9 因子高权威内容重构...")
    run_rewrite(project_id)
    
    print_info("\n▶ [4/5] 生成多平台高权重信源矩阵分发包 (头条/知乎/GitHub)...")
    run_distribute(project_id)
    
    print_info("\n▶ [5/5] 执行 AI 可见度监测并生成量化交付周报...")
    run_monitor(project_id)
    
    print_banner(f"🎉 客户 [{project_id}] 全套五步商业交付物全部生成完毕！")
    print_success(f"交付物目录: {os.path.join(PROJECTS_DIR, project_id, 'outputs')}")

def main():
    parser = argparse.ArgumentParser(
        prog="geo",
        description="GEO (生成式引擎优化) 商业接单与交付工作台"
    )
    subparsers = parser.add_subparsers(dest="command", help="交付阶段子命令")

    # web
    p_web = subparsers.add_parser("web", help="启动可视化 Web 商业交付管理端")
    p_web.add_argument("--port", "-p", type=int, default=8080, help="Web 服务监听端口 (默认: 8080)")

    # init
    p_init = subparsers.add_parser("init", help="初始化新客户项目")
    p_init.add_argument("project_id", help="客户英文唯一ID (如: client_001)")

    # audit
    p_audit = subparsers.add_parser("audit", help="阶段1: 客户现状体检与商业诊断")
    p_audit.add_argument("project_pos", nargs="?", default=None, help="客户项目 ID")
    p_audit.add_argument("--project", "-p", default=None, help="客户项目 ID")
    p_audit.add_argument("--url", "-u", help="目标官网 URL（覆盖配置文件）")

    # scaffold
    p_scaffold = subparsers.add_parser("scaffold", help="阶段2: 站点底座技术改造包生成")
    p_scaffold.add_argument("project_pos", nargs="?", default=None, help="客户项目 ID")
    p_scaffold.add_argument("--project", "-p", default=None, help="客户项目 ID")

    # rewrite
    p_rewrite = subparsers.add_parser("rewrite", help="阶段3: 普林斯顿 9 因子内容重构")
    p_rewrite.add_argument("project_pos", nargs="?", default=None, help="客户项目 ID")
    p_rewrite.add_argument("--project", "-p", default=None, help="客户项目 ID")
    p_rewrite.add_argument("--input-dir", "-i", help="原始素材目录")

    # distribute
    p_dist = subparsers.add_parser("distribute", help="阶段4: 多平台矩阵分发包导出")
    p_dist.add_argument("project_pos", nargs="?", default=None, help="客户项目 ID")
    p_dist.add_argument("--project", "-p", default=None, help="客户项目 ID")

    # monitor
    p_mon = subparsers.add_parser("monitor", help="阶段5: AI 可见度监控与周报生成")
    p_mon.add_argument("project_pos", nargs="?", default=None, help="客户项目 ID")
    p_mon.add_argument("--project", "-p", default=None, help="客户项目 ID")

    # intent
    p_intent = subparsers.add_parser("intent", help="AI 逆向挖掘买家 5 维商业提问 Prompt 词库")
    p_intent.add_argument("project_pos", nargs="?", default=None, help="客户项目 ID")
    p_intent.add_argument("--project", "-p", default=None, help="客户项目 ID")

    # ingest
    p_ingest = subparsers.add_parser("ingest", help="企业原始多模态素材抓取与事实提纯")
    p_ingest.add_argument("project_pos", nargs="?", default=None, help="客户项目 ID")
    p_ingest.add_argument("--project", "-p", default=None, help="客户项目 ID")
    p_ingest.add_argument("--url", "-u", help="目标官网 URL")
    p_ingest.add_argument("--file", "-f", help="本地素材文件路径")

    # defense
    p_def = subparsers.add_parser("defense", help="生成竞品权威信源反向包抄与压制策略")
    p_def.add_argument("project_pos", nargs="?", default=None, help="客户项目 ID")
    p_def.add_argument("--project", "-p", default=None, help="客户项目 ID")

    # patrol
    p_patrol = subparsers.add_parser("patrol", help="定时自动化巡检与声量异动告警")
    p_patrol.add_argument("project_pos", nargs="?", default=None, help="指定客户项目 ID (可选)")
    p_patrol.add_argument("--project", "-p", default=None, help="指定客户项目 ID")
    p_patrol.add_argument("--all", "-a", action="store_true", help="全量巡检所有活跃客户项目")
    p_patrol.add_argument("--notify", "-n", action="store_true", default=True, help="是否触发 Webhook 异动告警推送 (默认 True)")
    p_patrol.add_argument("--no-notify", dest="notify", action="store_false", help="禁止发送 Webhook 告警")

    # share
    p_share = subparsers.add_parser("share", help="生成甲方客户专属免密/提取码只读交付门户链接")
    p_share.add_argument("project_pos", nargs="?", default=None, help="客户项目 ID")
    p_share.add_argument("--project", "-p", default=None, help="客户项目 ID")
    p_share.add_argument("--days", "-d", type=int, default=30, help="分享链接有效天数 (0=永久, 默认 30)")
    p_share.add_argument("--pin", help="设置 4 位访问提取码 (可选)")
    p_share.add_argument("--base-url", default="https://geo.baicl.cc", help="对外访问公网域名前缀")

    # benchmark
    p_bm = subparsers.add_parser("benchmark", help="查看全行业大盘宏观基准与客户对标")
    p_bm.add_argument("project_pos", nargs="?", default=None, help="客户项目 ID (可选)")
    p_bm.add_argument("--project", "-p", default=None, help="客户项目 ID")
    p_bm.add_argument("--industry", "-i", default=None, help="指定行业名称")

    # batch
    p_batch = subparsers.add_parser("batch", help="批量多项目并发执行流水线")
    p_batch.add_argument("--step", "-s", default="pipeline", choices=["pipeline", "audit", "scaffold", "rewrite", "distribute", "monitor"], help="执行阶段 (默认 pipeline)")
    p_batch.add_argument("--industry", "-i", default=None, help="按行业过滤目标客户项目")
    p_batch.add_argument("--concurrency", "-c", type=int, default=4, help="并发线程数 (默认 4)")
    p_batch.add_argument("--all", "-a", action="store_true", default=True, help="批量处理所有符合条件的项目")

    # evolve
    p_ev = subparsers.add_parser("evolve", help="大模型 Prompt 探针动态演进与追问词裂变")
    p_ev.add_argument("project_pos", nargs="?", default=None, help="客户项目 ID")
    p_ev.add_argument("--project", "-p", default=None, help="客户项目 ID")
    p_ev.add_argument("--count", "-n", type=int, default=15, help="裂变生成候选词数量 (默认 15)")
    p_ev.add_argument("--apply", "-a", action="store_true", help="自动合并新词入库并触发增量流水线")

    # group
    p_grp = subparsers.add_parser("group", help="集团多品牌/子公司层级矩阵与协同声量大盘")
    p_grp.add_argument("group_pos", nargs="?", default=None, help="集团 ID (可选)")
    p_grp.add_argument("--id", "-g", default=None, help="集团 ID")
    p_grp.add_argument("--defense", "-d", action="store_true", help="输出集团级联合竞品防御策略")

    # visual
    p_vis = subparsers.add_parser("visual", help="生成多模态 SVG 对比图、架构图与 60 秒短视频脚本")
    p_vis.add_argument("project_pos", nargs="?", default=None, help="客户项目 ID")
    p_vis.add_argument("--project", "-p", default=None, help="客户项目 ID")
    p_vis.add_argument("--type", "-t", default="all", choices=["all", "svg", "comparison", "architecture", "video"], help="资产类型 (默认 all)")

    # pipeline
    p_pipe = subparsers.add_parser("pipeline", help="端到端一键执行五步完整交付")
    p_pipe.add_argument("project_pos", nargs="?", default=None, help="客户项目 ID")
    p_pipe.add_argument("--project", "-p", default=None, help="客户项目 ID")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    def get_pid(a):
        return getattr(a, "project_pos", None) or getattr(a, "project", None) or "_template"

    if args.command == "web":
        start_server(port=args.port)
    elif args.command == "init":
        cmd_init_project(args.project_id)
    elif args.command == "intent":
        from .intent import mine_project_intent
        mine_project_intent(get_pid(args))
    elif args.command == "ingest":
        from .ingest import ingest_project_materials
        ingest_project_materials(get_pid(args), url=args.url, file_path=args.file)
    elif args.command == "defense":
        from .defense import run_defense
        run_defense(get_pid(args))
    elif args.command == "patrol":
        from .patrol import run_patrol_all, run_patrol_project
        if args.all or (not getattr(args, "project_pos", None) and not getattr(args, "project", None)):
            run_patrol_all(notify=args.notify)
        else:
            run_patrol_project(get_pid(args), notify=args.notify)
    elif args.command == "share":
        from .share import create_share_link
        res = create_share_link(get_pid(args), expire_days=args.days, pin=args.pin, base_url=args.base_url)
        print("\n" + "="*60)
        print(res["share_text"])
        print("="*60 + "\n")
    elif args.command == "benchmark":
        from .benchmark import calculate_industry_benchmarks, evaluate_project_against_benchmark
        pid = getattr(args, "project_pos", None) or getattr(args, "project", None)
        if pid:
            rep = evaluate_project_against_benchmark(pid)
            print("\n" + "="*60)
            print(f"📊 客户 [{rep['client_name']}] 所属行业: {rep['industry']}")
            print(f"📈 客户 SOV: {rep['client_sov']}% ｜ 行业均值: {rep['industry_avg_sov']}% ｜ 行业标杆: {rep['industry_top_sov']}%")
            print(f"🏆 段位评级: {rep['tier']} (超越行业 {rep['beat_rate']}%)")
            print(f"💡 结论分析: {rep['summary']}")
            print("="*60 + "\n")
        else:
            b_data = calculate_industry_benchmarks()
            print("\n" + "="*60)
            print("🌐 全行业 AI 可见度与权威信源宏观基准大盘 (Industry Benchmarks)")
            print("="*60)
            for ind, d in b_data.get("industries", {}).items():
                print(f"\n【{ind}】(托管项目数: {d['project_count']})")
                print(f"  - 行业平均 SOV: {d['avg_sov']}% ｜ 中位数: {d['median_sov']}% ｜ 头部标杆线: {d['top_10_percent_sov']}%")
                print(f"  - 平均 Top3 推荐率: {d['avg_top3_rate']}% ｜ 平均权威得分: {d['avg_authority_score']}/100")
                top_p = "、".join([f"{c['name']} ({c['pct']}%)" for c in d.get('top_citations', [])[:3]])
                print(f"  - 核心被引用渠道: {top_p}")
            print("\n" + "="*60 + "\n")
    elif args.command == "batch":
        from .benchmark import run_batch_pipeline
        run_batch_pipeline(industry=args.industry, step=args.step, max_workers=args.concurrency)
    elif args.command == "evolve":
        from .evolution import analyze_prompt_portfolio, generate_fission_prompts, apply_evolved_prompts
        pid = get_pid(args)
        rep = analyze_prompt_portfolio(pid)
        print("\n" + "="*60)
        print(f"🌱 客户 [{rep['client_name']}] 意图词库生命周期分布评估")
        print(f"📊 词库总量: {rep['total_prompts']} 组 ｜ 🏆 垄断词: {rep['summary']['dominant_count']} ｜ ⚠️ 竞品词: {rep['summary']['intercepted_count']} ｜ 🌱 高潜词: {rep['summary']['potential_count']} ｜ ❄️ 待优化: {rep['summary']['declining_count']}")
        print("="*60)
        fissions = generate_fission_prompts(pid, count=args.count)
        print(f"\n💡 逆向裂变推演出 {len(fissions)} 组高商业转化追问词：")
        for idx, f in enumerate(fissions, 1):
            print(f"  {idx:02d}. [{f['intent_type']} · 转化期望:{f['expected_conversion']}] {f['prompt']}")
            print(f"      推演理由: {f['reason']}")
        if args.apply:
            print("\n🚀 正在自动合并入库...")
            apply_evolved_prompts(pid, fissions, auto_run_pipeline=True)
        else:
            print(f"\n💡 运行 'python3 -m tools.geo evolve {pid} --apply' 可一键合并入库并触发流水线。")
        print("="*60 + "\n")
    elif args.command == "group":
        from .group import load_groups_config, calculate_group_matrix, analyze_group_defense
        gid = getattr(args, "group_pos", None) or getattr(args, "id", None) or "xuanyuan_group"
        if args.defense:
            d_rep = analyze_group_defense(gid)
            print("\n" + "="*60)
            print(f"🛡️ 【{d_rep['group_name']}】集团跨品牌竞品联合防御大盘")
            print("="*60)
            print("共同面临的竞争对手：")
            for c in d_rep.get("top_shared_competitors", []):
                brands = "、".join(c["intercepting_brands"])
                print(f"  - 竞品 [{c['competitor']}] ｜ 威胁等级: {c['threat_level']} ｜ 拦截子品牌: {brands}")
            print(f"\n💡 联合反制策略: {d_rep['joint_defense_strategy']}")
            print("="*60 + "\n")
        else:
            g_rep = calculate_group_matrix(gid)
            print("\n" + "="*60)
            print(f"🏢 【{g_rep['group_name']}】集团多品牌矩阵协同大盘")
            print(f"📈 集团综合 SOV: {g_rep['group_sov']}% ｜ ⚡ 协同效应倍数: {g_rep['synergy_multiplier']}x ｜ 段位: {g_rep['tier']}")
            print(f"💡 结论: {g_rep['summary']}")
            print("="*60)
            print("矩阵子品牌声量贡献表：")
            for c in g_rep.get("children_matrix", []):
                print(f"  - [{c['role']}] {c['client_name']} ({c['brand_name']})")
                print(f"      SOV: {c['sov_pct']}% ｜ 词库量: {c['keywords_count']} 组 ｜ 矩阵声量贡献率: {c['contribution_pct']}%")
            print("\n跨子品牌共享核心信源渠道：")
            for sc in g_rep.get("shared_citations", []):
                b_str = "、".join(sc["shared_by_brands"])
                print(f"  - 🔗 {sc['name']} ({sc['domain']}) ｜ 被引频次: {sc['total_count']} ｜ 赋能品牌: {b_str}")
            print("\n" + "="*60 + "\n")
    elif args.command == "visual":
        from .visual import generate_comparison_svg, generate_architecture_svg, generate_video_script, generate_all_visual_assets
        pid = get_pid(args)
        t = getattr(args, "type", "all")
        if t == "comparison":
            generate_comparison_svg(pid)
        elif t == "architecture":
            generate_architecture_svg(pid)
        elif t == "svg":
            generate_comparison_svg(pid)
            generate_architecture_svg(pid)
        elif t == "video":
            generate_video_script(pid)
        else:
            generate_all_visual_assets(pid)
    elif args.command == "audit":
        run_audit(get_pid(args), custom_url=args.url)
    elif args.command == "scaffold":
        run_scaffold(get_pid(args))
    elif args.command == "rewrite":
        run_rewrite(get_pid(args), input_dir=args.input_dir)
    elif args.command == "distribute":
        run_distribute(get_pid(args))
    elif args.command == "monitor":
        run_monitor(get_pid(args))
    elif args.command == "pipeline":
        cmd_run_pipeline(get_pid(args))

if __name__ == "__main__":
    main()

