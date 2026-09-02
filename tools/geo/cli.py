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

    # test / playground
    p_test = subparsers.add_parser("test", help="大模型实时响应模拟器与沙箱即时召回测序")
    p_test.add_argument("project_pos", nargs="?", default=None, help="客户项目 ID")
    p_test.add_argument("--project", "-p", default=None, help="客户项目 ID")
    p_test.add_argument("--query", "-q", default=None, help="自定义测试提问 Prompt")
    p_test.add_argument("--compare", "-c", action="store_true", default=True, help="输出 Before/After 双轨对比")
    p_test.add_argument("--batch", "-b", type=int, default=0, help="批量跑批抽样测序题数 (如 5)")

    # record / distribution
    p_rec = subparsers.add_parser("record", help="回填多平台外发文章落地 URL 台账")
    p_rec.add_argument("project_pos", nargs="?", default=None, help="客户项目 ID")
    p_rec.add_argument("--project", "-p", default=None, help="客户项目 ID")
    p_rec.add_argument("--channel", "-c", required=True, choices=["toutiao", "zhihu", "juejin", "github", "wechat"], help="外发渠道代号")
    p_rec.add_argument("--url", "-u", required=True, help="外发落地的真实 URL")
    p_rec.add_argument("--no-verify", action="store_true", help="跳过存活连通性校验")

    # verify-dist
    p_vdist = subparsers.add_parser("verify-dist", help="一键核验项目全渠道外链存活状态与完成率")
    p_vdist.add_argument("project_pos", nargs="?", default=None, help="客户项目 ID")
    p_vdist.add_argument("--project", "-p", default=None, help="客户项目 ID")

    # roi
    p_roi = subparsers.add_parser("roi", help="测算项目商业投资回报率 (ROI) 与财务估值")
    p_roi.add_argument("project_pos", nargs="?", default=None, help="客户项目 ID")
    p_roi.add_argument("--project", "-p", default=None, help="客户项目 ID")
    p_roi.add_argument("--fee", type=int, default=None, help="年度服务费成本 (元)")
    p_roi.add_argument("--cpl", type=float, default=None, help="行业单条销售线索成本 (元)")
    p_roi.add_argument("--cpc", type=float, default=None, help="搜索单次点击竞价成本 (元)")

    # renewal
    p_rnw = subparsers.add_parser("renewal", help="预测客户续约健康度并生成谈判话术")
    p_rnw.add_argument("project_pos", nargs="?", default=None, help="客户项目 ID")
    p_rnw.add_argument("--project", "-p", default=None, help="客户项目 ID")

    # signoff
    p_sgn = subparsers.add_parser("signoff", help="生成项目商业交付结案确认单 (00_GEO商业交付验收结案确认单.md)")
    p_sgn.add_argument("project_pos", nargs="?", default=None, help="客户项目 ID")
    p_sgn.add_argument("--project", "-p", default=None, help="客户项目 ID")

    # pack
    p_pck = subparsers.add_parser("pack", help="一键将全套交付物打包为标准 ZIP 压缩包")
    p_pck.add_argument("project_pos", nargs="?", default=None, help="客户项目 ID")
    p_pck.add_argument("--project", "-p", default=None, help="客户项目 ID")

    # pitch
    p_ptc = subparsers.add_parser("pitch", help="生成售前商业全案投标建议书与 10 页全屏 Pitch Deck")
    p_ptc.add_argument("project_pos", nargs="?", default=None, help="客户项目 ID")
    p_ptc.add_argument("--project", "-p", default=None, help="客户项目 ID")
    p_ptc.add_argument("--tier", default="pro", choices=["standard", "pro", "enterprise"], help="推荐服务档位")
    p_ptc.add_argument("--slides", action="store_true", help="直接打印交互式幻灯片 HTML 内容")

    # graph
    p_grp = subparsers.add_parser("graph", help="构建企业行业实体知识图谱与三元组拓扑")
    p_grp.add_argument("project_pos", nargs="?", default=None, help="客户项目 ID")
    p_grp.add_argument("--project", "-p", default=None, help="客户项目 ID")
    p_grp.add_argument("--export", choices=["cypher", "jsonld", "svg"], default=None, help="特定格式输出")
    p_grp.add_argument("--query", "-q", default=None, help="长尾多跳子图推理检索关键词")

    # guard
    p_grd = subparsers.add_parser("guard", help="大模型事实幻觉检测、强事实锚点注入与公关反击")
    p_grd.add_argument("project_pos", nargs="?", default=None, help="客户项目 ID")
    p_grd.add_argument("--project", "-p", default=None, help="客户项目 ID")
    p_grd.add_argument("--detect", action="store_true", help="检测大模型事实幻觉与虚假负面")
    p_grd.add_argument("--repair", action="store_true", help="生成强事实纠偏锚点与反击策略")
    p_grd.add_argument("--simulate", action="store_true", help="沙箱推演修复前后的置信度与事实一致性")

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
    elif args.command == "test":
        from .playground import run_playground_simulation, run_batch_simulation
        pid = get_pid(args)
        batch_cnt = getattr(args, "batch", 0)
        if batch_cnt > 0:
            b_res = run_batch_simulation(pid, count=batch_cnt)
            print("\n" + "="*60)
            print(f"🧪 项目 [{pid}] 大模型沙箱批量测序报告 ({b_res['total_tested']} 组问答)")
            print(f"📈 品牌总提及率: {b_res['hit_rate_pct']}% ｜ 🥇 首推率 (Rank 1): {b_res['rank1_rate_pct']}% ｜ 🌟 平均置信度得分: {b_res['avg_confidence_score']}/100")
            print("="*60 + "\n")
        else:
            q = getattr(args, "query", None) or ""
            cmp_res = run_playground_simulation(pid, query=q, compare=True)
            print("\n" + "="*60)
            print(f"🧪 【大模型实时测序沙箱】提问 Prompt: {cmp_res['query']}")
            print("="*60)
            print("\n[👈 未优化基准应答 (Before)]：")
            print(cmp_res['before']['response'])
            print(f"📊 得分: {cmp_res['before']['confidence_score']} ｜ 品牌命中: {bool(cmp_res['before']['brand_mentioned'])}")
            
            print("\n" + "-"*60)
            print("[👉 GEO 增强首选推荐 (After)]：")
            print(cmp_res['after']['response'])
            print(f"🏆 排位: Rank {cmp_res['after']['rank']} ｜ 🌟 置信度得分: {cmp_res['after']['confidence_score']}/100 ｜ 命中事实: {len(cmp_res['after']['facts_hit'])} 条")
            print("="*60 + "\n")
    elif args.command == "record":
        from .dist_bot import record_distributed_url
        pid = get_pid(args)
        ch = args.channel
        u = args.url
        no_v = getattr(args, "no_verify", False)
        record_distributed_url(pid, channel=ch, url=u, verify_now=not no_v)
    elif args.command == "verify-dist":
        from .dist_bot import verify_all_channels
        pid = get_pid(args)
        verify_all_channels(pid)
    elif args.command == "roi":
        from .roi import calculate_project_roi
        pid = get_pid(args)
        custom_p = {}
        if getattr(args, "fee", None):
            custom_p["annual_service_fee"] = args.fee
        if getattr(args, "cpl", None):
            custom_p["cpl"] = args.cpl
        if getattr(args, "cpc", None):
            custom_p["cpc"] = args.cpc
        res = calculate_project_roi(pid, custom_params=custom_p)
        fin = res["financial_valuation"]
        ren = res["renewal_health"]
        print("\n" + "="*65)
        print(f"💰 项目 [{pid}] 商业投资回报率 (ROI) 测算报告")
        print("="*65)
        print(f"💵 年度 GEO 服务费成本: ¥{fin['annual_service_fee']:,} 元")
        print(f"🚀 创造商业综合总价值: ¥{fin['total_business_value']:,} 元 (净回报: ¥{fin['net_profit_value']:,} 元)")
        print(f"📈 综合投资回报率 (ROI): {fin['roi_pct']}% ({fin['roi_multiplier']} 倍)")
        print(f"  · 等效 SEM 竞价替代节省: ¥{fin['sem_replacement_value']:,} 元")
        print(f"  · AI 首推精准销售线索估值: ¥{fin['leads_inbound_value']:,} 元")
        print(f"  · 权威信任池数字资产估值: ¥{fin['digital_asset_value']:,} 元")
        print("-"*65)
        print(f"🎯 续约健康度得分: {ren['score']}/100 ｜ 评级: 【{ren['grade']}】")
        print(f"💡 建议: {ren['tier_advice']}")
        print("="*65 + "\n")
    elif args.command == "renewal":
        from .roi import predict_renewal_health
        pid = get_pid(args)
        ren_res = predict_renewal_health(pid)
        ren = ren_res["renewal_health"]
        print("\n" + "="*65)
        print(f"🤝 项目 [{pid}] 客户续约预测与商务增购谈判提案")
        print("="*65)
        print(f"⭐ 续约健康度得分: {ren['score']}/100 ｜ 状态: 【{ren['grade']}】")
        print(f"📋 商务策略建议: {ren['tier_advice']}")
        print("\n🗣️ 核心商务谈判话术要点:")
        for idx, tp in enumerate(ren["talking_points"], 1):
            print(f"  {idx}. {tp}")
        print("="*65 + "\n")
    elif args.command == "signoff":
        from .acceptance import generate_acceptance_report
        pid = get_pid(args)
        res = generate_acceptance_report(pid)
        ful = res["fulfillment"]
        print("\n" + "="*65)
        print(f"📜 项目 [{pid}] 商业交付验收结案确认单已生成！")
        print("="*65)
        print(f"🏆 综合合同履约达成率: {ful['total_fulfillment_score']}/100 分")
        print(f"📋 验收判定结论: 【{ful['status_text']}】")
        print(f"📄 确认单文档: outputs/{res['filename']}")
        print("="*65 + "\n")
    elif args.command == "pack":
        from .acceptance import export_project_archive_zip
        pid = get_pid(args)
        zpath = export_project_archive_zip(pid)
        print("\n" + "="*65)
        print(f"📦 项目 [{pid}] 全套交付物已打包归档！")
        print(f"📁 归档包路径: {zpath}")
        print("="*65 + "\n")
    elif args.command == "pitch":
        from .pitch import generate_pitch_deck, generate_pitch_presentation_html
        pid = get_pid(args)
        tier = getattr(args, "tier", "pro") or "pro"
        res = generate_pitch_deck(pid, target_tier=tier)
        quotes = res["quotes"]
        fin = res["roi"]["financial_valuation"]
        print("\n" + "="*65)
        print(f"🚀 项目 [{pid}] 售前全案商业投标建议书已生成！")
        print("="*65)
        tier_info = res.get('selected_tier_info', {})
        print(f"🏢 目标企业: {res['client_name']} ({res['brand_name']})")
        print(f"🎯 推荐服务方案: 【{tier_info.get('tier_name', '专业标杆版 (主推型)')}】{tier_info.get('price_display', '¥16,800 元/全案')}")
        print(f"💰 预期综合商业回报: ¥{fin['total_business_value']:,} 元 (ROI: +{fin['roi_pct']}%)")
        print(f"📄 标书文件: outputs/{res['filename']}")
        print(f"🖥️ 交互式放映幻灯片: 在浏览器访问 /api/projects/{pid}/pitch/slides")
        print("="*65 + "\n")
        if getattr(args, "slides", False):
            slides_html = generate_pitch_presentation_html(pid)
            print(f"<!-- HTML 演示文稿生成完毕，长度 {len(slides_html)} 字节 -->")
    elif args.command == "graph":
        from .graph import export_graph_formats, generate_graph_svg
        pid = get_pid(args)
        res = export_graph_formats(pid)
        print("\n" + "="*65)
        print(f"🕸️ 项目 [{pid}] 实体知识图谱与三元组拓扑已生成！")
        print("="*65)
        print(f"🏢 企业主体: {res['graph_data']['client_name']} ({res['graph_data']['brand_name']})")
        print(f"🧩 核心实体节点数: {res['node_count']} 个 ｜ 三元组关联边: {res['edge_count']} 条")
        print(f"📄 拓扑文档: outputs/{res['filename']}")
        print(f"🎨 高清矢量拓扑图: outputs/10_实体知识图谱拓扑图.svg")
        print("="*65 + "\n")
        query_kw = getattr(args, "query", None)
        if query_kw:
            from .graph import query_entity_subgraph
            q_res = query_entity_subgraph(pid, query_kw)
            print(f"🔍 关键词【{query_kw}】多跳子图检索结果 (命中节点: {q_res['matched_node_count']}, 子图节点: {q_res['subgraph_node_count']}, 关系链: {q_res['subgraph_edge_count']}):")
            for chain in q_res.get("reasoning_chains", []):
                flag = "🎯 [直接命中]" if chain["is_direct_hit"] else "🔗 [2跳关联]"
                print(f"  {flag} {chain['subject']} --[{chain['predicate']}]--> {chain['object']}")
            print()
        elif exp == "cypher":
            print(res["cypher_script"])
        elif exp == "jsonld":
            print(json.dumps(res["jsonld_graph"], ensure_ascii=False, indent=2))
        elif exp == "svg":
            print(generate_graph_svg(pid))
    elif args.command == "guard":
        from .guard import detect_factual_hallucinations, generate_adversarial_countermeasures, simulate_guard_repair_effect
        pid = get_pid(args)
        if getattr(args, "simulate", False):
            sim = simulate_guard_repair_effect(pid)
            print("\n" + "="*65)
            print(f"🛡️ 项目 [{pid}] 事实幻觉修复前后沙箱对决推演")
            print("="*65)
            b = sim["simulation"]["before"]
            a = sim["simulation"]["after"]
            print(f"👈 【修复前】{b['state']} (置信度: {b['confidence_score']}分 - {b['status_tag']})")
            print(f"   回答: {b['llm_response'][:80]}...")
            print(f"👉 【修复后】{a['state']} (置信度: {a['confidence_score']}分 - {a['status_tag']})")
            print(f"   回答: {a['llm_response'][:80]}...")
            print("="*65 + "\n")
        elif getattr(args, "repair", False):
            res = generate_adversarial_countermeasures(pid)
            print(f"✅ 已生成反击策略文档: outputs/{res['filename']}")
        else:
            res = detect_factual_hallucinations(pid)
            print("\n" + "="*65)
            print(f"🛡️ 项目 [{pid}] 大模型事实幻觉与虚假信源检测报告")
            print("="*65)
            print(f"🏢 企业主体: {res['client_name']} ({res['brand_name']})")
            print(f"🚨 排查风险总数: {res['total_risks']} 项 (高危: {res['high_severity_count']} 项 ｜ 已修复: {res['repaired_count']} 项)")
            print(f"🛡️ 品牌防御就绪度: {res['defense_readiness_score']}%")
            print("="*65)
            for idx, r in enumerate(res["risks"], 1):
                print(f"  [{r['severity']}] {idx}. {r['category']} ({r['model_affected']})")
                print(f"     诱发问句: {r['test_query']}")
                print(f"     纠偏锚点: {r['truth_anchor'][:60]}...")
            print("="*65 + "\n")
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

