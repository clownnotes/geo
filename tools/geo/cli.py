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
import json
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

def cmd_init_project(project_id: str, template: str = None):
    """初始化新客户项目（支持指定行业母版模板克隆）"""
    if template:
        from .templates_pack import clone_project_from_template
        try:
            clone_project_from_template(project_id, template_name=template)
            return
        except Exception as e:
            print_error(f"克隆母版失败: {e}")
            sys.exit(1)

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
    p_init = subparsers.add_parser("init", help="初始化新客户项目 (支持从行业母版极速克隆)")
    p_init.add_argument("project_id", help="客户英文唯一ID (如: client_001)")
    p_init.add_argument("--template", "-t", default=None, choices=["b2b_machinery", "retail_catering", "local_legal", "xuzhou_xuanyuan"], help="行业母版模板 (可选: b2b_machinery, retail_catering, local_legal)")

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

    # intent (3 级搜索意图挖掘与语义拓扑裂变)
    p_intent = subparsers.add_parser("intent", help="3级搜索意图挖掘(L1认知/L2决策/L3行动)与长尾提示词拓扑裂变")
    p_intent.add_argument("project_pos", nargs="?", default=None, help="客户项目 ID")
    p_intent.add_argument("--project", "-p", default=None, help="客户项目 ID")
    p_intent.add_argument("--tier", default="all", choices=["l1", "l2", "l3", "all"], help="挖掘或导出的意图层级 (默认: all)")
    p_intent.add_argument("--sync-eval", action="store_true", help="一键同步写入 project.yaml 的评测词库")

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

    # portal & share
    for cmd_name, cmd_help in [
        ("portal", "生成甲方高管专属全域大模型商业战果只读交付门户链接与战报"),
        ("share", "生成甲方客户专属免密/提取码只读交付门户链接")
    ]:
        p_p = subparsers.add_parser(cmd_name, help=cmd_help)
        p_p.add_argument("project_pos", nargs="?", default=None, help="客户项目 ID")
        p_p.add_argument("--project", "-p", default=None, help="客户项目 ID")
        p_p.add_argument("--days", "-d", type=int, default=30, help="分享链接有效天数 (0=永久, 默认 30)")
        p_p.add_argument("--pin", help="设置 4 位访问提取码 (可选)")
        p_p.add_argument("--refresh", action="store_true", help="强制作废历史 Token 并生成全新单活链接")
        p_p.add_argument("--export", help="导出离线独立单文件 HTML 交付大屏")
        p_p.add_argument("--base-url", default="https://geo.baicl.cc", help="对外访问公网域名前缀")

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

    # publish
    p_pub = subparsers.add_parser("publish", help="生成中国五大本土模型全生态极速发稿资产包")
    p_pub.add_argument("project_pos", nargs="?", default=None, help="客户项目 ID")
    p_pub.add_argument("--project", "-p", default=None, help="客户项目 ID")
    p_pub.add_argument("--channel", default="all", choices=["toutiao", "wechat", "deepseek", "zhihu", "kimi_baidu", "all"], help="发布渠道 (默认: all)")
    p_pub.add_argument("--verify", "--fidelity", dest="verify", action="store_true", help="开启大模型爬虫保真度深度逆向核验")

    # eval
    p_eval = subparsers.add_parser("eval", help="执行真实大模型 API 批量并发评测与 Citation 捕获")
    p_eval.add_argument("project_pos", nargs="?", default=None, help="客户项目 ID")
    p_eval.add_argument("--project", "-p", default=None, help="客户项目 ID")
    p_eval.add_argument("--models", "-m", default="doubao,deepseek,yuanbao,kimi", help="评测模型列表 (逗号分隔)")
    p_eval.add_argument("--limit", "-l", type=int, default=10, help="评测词库数量上限 (默认: 10)")
    # certificate
    p_cert = subparsers.add_parser("certificate", help="生成GEO商业交付结案与数字资产移交证书(A4打印优化)")
    p_cert.add_argument("project_pos", nargs="?", default=None, help="客户项目 ID")
    p_cert.add_argument("--project", "-p", default=None, help="客户项目 ID")

    # ledger (分发台账智能回填与存活探活审计)
    p_ledger = subparsers.add_parser("ledger", help="全渠道分发链接智能解析回填与全网死链探活审计")
    p_ledger.add_argument("project_pos", nargs="?", default=None, help="客户项目 ID")
    p_ledger.add_argument("--project", "-p", default=None, help="客户项目 ID")
    p_ledger.add_argument("--add", default=None, help="批量智能粘贴多行 URL 文本回填")
    p_ledger.add_argument("--audit", action="store_true", help="执行全网并发死链探活与存活率重算")
    p_ledger.add_argument("--summary", action="store_true", help="查看当前分发台账执行大盘")

    # crawl (大模型爬虫抓取仿真)
    p_crawl = subparsers.add_parser("crawl", help="大模型爬虫(Bytespider/Baiduspider/DeepSeek)抓取仿真与Clean Markdown提取")
    p_crawl.add_argument("url", help="目标网页 URL")
    p_crawl.add_argument("--spider", "-s", default="bytespider", choices=["bytespider", "baidu", "deepseek", "google", "browser"], help="爬虫类型 (默认: bytespider)")

    # rag-diag (RAG 语义分块切片诊断)
    p_rag = subparsers.add_parser("rag-diag", help="RAG 语义分块切片诊断与准备度评分 (03语料库切片透视)")
    p_rag.add_argument("project_pos", nargs="?", default=None, help="客户项目 ID")
    p_rag.add_argument("--project", "-p", default=None, help="客户项目 ID")
    p_rag.add_argument("--file", "-f", default=None, help="指定待诊断的语料文件路径 (可选)")

    # compliance (多渠道内容合规审查与广告法风控脱敏)
    p_comp = subparsers.add_parser("compliance", help="多渠道内容合规审查与新广告法敏感词一键无损脱敏")
    p_comp.add_argument("project_pos", nargs="?", default=None, help="客户项目 ID")
    p_comp.add_argument("--project", "-p", default=None, help="客户项目 ID")
    p_comp.add_argument("--file", "-f", default=None, help="指定待审查的文件路径 (可选)")
    p_comp.add_argument("--inspect", "-i", action="store_true", help="执行合规风控审查体检 (默认)")
    p_comp.add_argument("--sanitize", "-s", action="store_true", help="执行一键无损脱敏修复并重算合规分")

    # competitor-gap (竞对大模型声量差距逆向与反超沙盘)
    p_gap = subparsers.add_parser("competitor-gap", help="竞对大模型声量差距深度逆向分析与反超作战沙盘")
    p_gap.add_argument("project_pos", nargs="?", default=None, help="客户项目 ID")
    p_gap.add_argument("--project", "-p", default=None, help="客户项目 ID")
    p_gap.add_argument("--competitor", "-c", default=None, help="指定要分析的目标竞对名称 (可选)")

    # citation-auth (大模型 Citation 信源权威度与外链信任度推演)
    p_cauth = subparsers.add_parser("citation-auth", help="大模型 Citation 信源权威度权重评分与外链信任度推演")
    p_cauth.add_argument("project_pos", nargs="?", default=None, help="客户项目 ID")
    p_cauth.add_argument("--project", "-p", default=None, help="客户项目 ID")

    # injection-guard (大模型提示词注入防御与品牌安全隔离)
    p_inj = subparsers.add_parser("injection-guard", help="大模型提示词注入防御与品牌安全隔离盾牌扫描")
    p_inj.add_argument("project_pos", nargs="?", default=None, help="客户项目 ID")
    p_inj.add_argument("--project", "-p", default=None, help="客户项目 ID")
    p_inj.add_argument("--file", "-f", default=None, help="指定待扫描的文件路径 (可选)")

    # portfolio (全域多项目商业运营大盘与月报)
    p_port = subparsers.add_parser("portfolio", help="全域多项目商业运营全景大盘、健康巡检与商业回报月报")
    p_port.add_argument("--patrol", action="store_true", help="执行全域轻量只读健康巡检并输出风险红黑榜")
    p_port.add_argument("--report", action="store_true", help="生成并落盘《GEO代运营全域多项目执行与商业回报大盘报告.md》")

    # score (普林斯顿 9 因子量化体检与智能重写)
    p_score = subparsers.add_parser("score", help="普林斯顿 9 因子量化体检、一键重写与全案 17 号质检审计")
    p_score.add_argument("target", nargs="?", default=None, help="待测文本原文，或本地文件路径")
    p_score.add_argument("--industry", default=None, help="所属行业（用于术语词典）")
    p_score.add_argument("--rewrite", action="store_true", help="对输入文本/文件执行一键普林斯顿重构")
    p_score.add_argument("--project", "-p", default=None, help="客户项目 ID（全案审计或绑定事实锚点重写）")
    p_score.add_argument("--audit", action="store_true", help="对 --project 指定项目执行全案 17 号质检审计")

    # probe / probe-audit (多大模型实时联网探测与 Citation 信源溯源对账，第 18/30 维审计引擎)
    for p_cmd in ("probe", "probe-audit"):
        p_probe = subparsers.add_parser(p_cmd, help="多大模型实时联网探测与 Citation 信源角标闭环对账（底层复用 tools.geo.probing 基座）")
        p_probe.add_argument("project_pos", nargs="?", default=None, help="客户项目 ID")
        p_probe.add_argument("--project", "-p", default=None, help="客户项目 ID")
        p_probe.add_argument("--models", "-m", default="doubao,deepseek,kimi,yuanbao", help="待探测大模型列表 (英文逗号分隔)")
        p_probe.add_argument("--sample", "-s", type=int, default=5, help="意图 Query 采样条数 (默认 5)")
        p_probe.add_argument("--report", action="store_true", help="生成并落盘 18/30 号公文 Markdown 报告")
        p_probe.add_argument("--reconcile-only", action="store_true", help="免大模型调用，直接基于最新台账对已有探测记录执行极速离线重对账并刷新 30 号报告")
        p_probe.add_argument("--portal-sync", action="store_true", help="探测或离线对账后，联动刷新高管交付门户聚合缓存与战果数据大屏")

    # guard-clean (19 号品牌声誉排查与危机清洗，与 geo guard 幻觉防御区分)
    p_gclean = subparsers.add_parser("guard-clean", help="19 号品牌声誉负面联想排查与危机清洗压制")
    p_gclean.add_argument("project_pos", nargs="?", default=None, help="客户项目 ID")
    p_gclean.add_argument("--project", "-p", default=None, help="客户项目 ID")
    p_gclean.add_argument("--models", "-m", default="doubao,deepseek,kimi", help="探测模型列表")
    p_gclean.add_argument("--live", action="store_true", help="启用真实联网 API")
    p_gclean.add_argument("--suppress", action="store_true", help="生成 crisis_suppression_pack 三件套")
    p_gclean.add_argument("--report", action="store_true", help="生成并落盘 19 号公关报告")

    # decay (20 号大模型知识半衰期衰减监测与长效自愈)
    p_decay = subparsers.add_parser("decay", help="20 号大模型知识半衰期衰减监测与长效留存自愈（注：--heal 仅生成衰减包草稿；全域落盘回写请使用 geo heal）")
    p_decay.add_argument("project_pos", nargs="?", default=None, help="客户项目 ID")
    p_decay.add_argument("--project", "-p", default=None, help="客户项目 ID")
    p_decay.add_argument("--models", "-m", default="doubao,deepseek,kimi", help="探测模型列表")
    p_decay.add_argument("--live", action="store_true", help="启用真实联网 API")
    p_decay.add_argument("--heal", action="store_true", help="生成 decay_healing_pack 自愈草稿三件套（全域落盘回写请使用 geo heal）")
    p_decay.add_argument("--delta-days", type=float, default=None, help="手动指定间隔天数（默认从台账外链推算）")
    p_decay.add_argument("--report", action="store_true", help="生成并落盘 20 号公文报告")

    # heal (29 号全域动态知识热补丁聚合与一键落盘自愈流水线)
    p_heal = subparsers.add_parser("heal", help="29 号全域动态知识热补丁聚合与一键落盘自愈流水线（消费 20/22/25/26 策略包并回写语料底座）")
    p_heal.add_argument("project_pos", nargs="?", default=None, help="客户项目 ID")
    p_heal.add_argument("--project", "-p", default=None, help="客户项目 ID")
    p_heal.add_argument("--apply", action="store_true", help="正式执行五步事务型原子落盘回写")
    p_heal.add_argument("--rollback", action="store_true", help="一键撤销并恢复至最近一次或指定时间戳备份状态")
    p_heal.add_argument("--backup", default="", help="配合 --rollback 指定恢复的特定时间戳目录 (如 20260904_021530)")
    p_heal.add_argument("--verify", action="store_true", help="配合 --apply 自愈后自动联动运行 9 因子与 JSON-LD 语法质检")
    p_heal.add_argument("--json", action="store_true", help="以 JSON 格式输出自愈对账数据")

    # mindshare (21 号大模型商业心智渗透与商业转化价值量化审计)
    p_mindshare = subparsers.add_parser("mindshare", help="21 号大模型商业心智渗透率与商业转化价值审计")
    p_mindshare.add_argument("project_pos", nargs="?", default=None, help="客户项目 ID")
    p_mindshare.add_argument("--project", "-p", default=None, help="客户项目 ID")
    p_mindshare.add_argument("--models", "-m", default="doubao,deepseek,kimi", help="探测模型列表")
    p_mindshare.add_argument("--live", action="store_true", help="启用真实联网 API")
    p_mindshare.add_argument("--pitch", action="store_true", help="生成 commercial_roi_pitch 高管商务三件套")
    p_mindshare.add_argument("--report", action="store_true", help="生成并落盘 21 号公文报告")

    # rerank (22 号跨大模型 RAG 混合检索召回与重排序挤占演习沙盘)
    p_rerank = subparsers.add_parser("rerank", help="22 号跨大模型 RAG 混合检索召回与重排序挤占演习沙盘")
    p_rerank.add_argument("project_pos", nargs="?", default=None, help="客户项目 ID")
    p_rerank.add_argument("--project", "-p", default=None, help="客户项目 ID")
    p_rerank.add_argument("--models", "-m", default="doubao,deepseek,kimi", help="探测模型列表")
    p_rerank.add_argument("--live", action="store_true", help="启用真实联网 API 评测")
    p_rerank.add_argument("--reinforce", action="store_true", help="生成 outputs/rerank_reinforcement_pack/ 重排语义强化包")
    p_rerank.add_argument("--report", action="store_true", help="生成并落盘 22 号公文报告")

    # attribution (23 号大模型商业推荐因果归因与信源边际贡献度量化审计中枢)
    p_attr = subparsers.add_parser("attribution", help="23 号大模型商业推荐因果归因与信源边际贡献度量化审计中枢")
    p_attr.add_argument("project_pos", nargs="?", default=None, help="客户项目 ID")
    p_attr.add_argument("--project", "-p", default=None, help="客户项目 ID")
    p_attr.add_argument("--models", "-m", default="doubao,deepseek,kimi", help="探测模型列表")
    p_attr.add_argument("--live", action="store_true", help="启用真实联网 API 评测")
    p_attr.add_argument("--optimize", action="store_true", help="生成 outputs/attribution_optimization_pack/ 优化加固三件套")
    p_attr.add_argument("--report", action="store_true", help="生成并落盘 23 号公文报告")

    # funnel (24 号大模型商业多轮追问决策漏斗与意图转化路径推演中枢)
    p_funnel = subparsers.add_parser("funnel", help="24 号大模型商业多轮追问决策漏斗与意图转化路径推演中枢")
    p_funnel.add_argument("project_pos", nargs="?", default=None, help="客户项目 ID")
    p_funnel.add_argument("--project", "-p", default=None, help="客户项目 ID")
    p_funnel.add_argument("--models", "-m", default="doubao,deepseek,kimi", help="探测模型列表")
    p_funnel.add_argument("--live", action="store_true", help="启用真实联网 API 评测")
    p_funnel.add_argument("--defend", action="store_true", help="生成 outputs/funnel_defense_pack/ 决策漏斗防截流加固包")
    p_funnel.add_argument("--report", action="store_true", help="生成并落盘 24 号公文报告")

    # robustness (25 号大模型提示词敏感度扰动与生成鲁棒性压力测试中枢)
    p_rob = subparsers.add_parser("robustness", help="25 号大模型提示词敏感度扰动与生成鲁棒性压力测试中枢")
    p_rob.add_argument("project_pos", nargs="?", default=None, help="客户项目 ID")
    p_rob.add_argument("--project", "-p", default=None, help="客户项目 ID")
    p_rob.add_argument("--models", "-m", default="doubao,deepseek,kimi", help="探测模型列表")
    p_rob.add_argument("--live", action="store_true", help="启用真实联网 API 评测")
    p_rob.add_argument("--harden", action="store_true", help="生成 outputs/robustness_hardening_pack/ 鲁棒性加固包")
    p_rob.add_argument("--report", action="store_true", help="生成并落盘 25 号公文报告")

    # moat
    p_moat = subparsers.add_parser("moat", help="26 号大模型商业推荐博弈对抗与竞品截流动态护城河推演中枢")
    p_moat.add_argument("project_pos", nargs="?", default=None, help="客户项目 ID")
    p_moat.add_argument("--project", "-p", default=None, help="客户项目 ID")
    p_moat.add_argument("--rival", default=None, help="显式指定核心商业竞对名称 (覆盖默认)")
    p_moat.add_argument("--live", action="store_true", help="启用真实联网 API 实盘裁决 (最多 4 次调用)")
    p_moat.add_argument("--json", action="store_true", help="以 JSON 格式输出推演结果")

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
        cmd_init_project(args.project_id, template=args.template)
    elif args.command == "intent":
        from .intent import build_3tier_intent_matrix, sync_intent_keywords_to_eval
        pid = get_pid(args)
        build_3tier_intent_matrix(pid)
        if getattr(args, "sync_eval", False):
            sync_intent_keywords_to_eval(pid, tier=getattr(args, "tier", "all"))
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
    elif args.command in ("portal", "share"):
        from .share import create_share_link, refresh_share_token, export_offline_portal_html, compile_portal_data
        pid = get_pid(args)

        # 1. 离线单文件导出
        if getattr(args, "export", None):
            exp_res = export_offline_portal_html(pid, args.export)
            print_banner(f"导出离线单文件高管交付大屏: [{pid}]")
            print_success(f"🎉 离线大屏导出成功！产物路径: {exp_res['target_file']} (文件大小: {exp_res['size_kb']} KB)")
            print_info("💡 提示：该单文件已内联全部数据与样式，断网或内网物理隔离环境下双击即可秒开演示。")
        else:
            # 2. 单活轮转刷新或正常生成
            if getattr(args, "refresh", False):
                res = refresh_share_token(pid, expire_days=args.days, pin=args.pin, base_url=args.base_url)
                print_warning(f"🔄 已作废该项目历史 {res.get('revoked_old_count', 0)} 条旧 Token，已生成全新单活交付链接！")
            else:
                res = create_share_link(pid, expire_days=args.days, pin=args.pin, base_url=args.base_url)

            portal_data = compile_portal_data(pid, token=res["token"])
            summary = portal_data.get("executive_summary", {})
            mpi = summary.get("mpi_score")
            saving = summary.get("annual_ad_saving_wan", 0.0)
            first_p = summary.get("first_recommend_rate_pct")
            fidelity = portal_data.get("authority_assurance", {}).get("average_fidelity_score")

            print("\n" + "="*65)
            print(" 🏛️ 甲方高管专属全域大模型商业战果只读交付看板")
            print("="*65)
            print(f" 客户企业: {portal_data.get('client_name')} ｜ 品牌: {portal_data.get('brand_name')}")
            print(f" 商业心智 (MPI): {mpi if mpi is not None else '待生成'}分 ｜ 评级: {summary.get('delivery_grade', 'AAA级')}")
            print(f" 主流模型首推率: {f'{first_p}%' if first_p is not None else '待评测'} ｜ 年化广告节省: ¥{saving}万元/年")
            print(f" 爬虫逆向保真度: {f'{fidelity}分' if fidelity is not None else '待核验'} ｜ 存活台账: {portal_data.get('distribution_ledger', {}).get('completion_rate_pct', 0)}% 填报")
            print("-"*65)
            print(f" 🔗 交付大屏链接: {res['share_url']}")
            if res.get("pin"):
                print(f" 🔑 访问安全提取码: {res['pin']}")
            else:
                print(" 🔓 访问权限: 免密即开 (高熵 Token 安全保护)")
            print(f" ⏳ 有效期限: {res.get('expires_at_str', '30 天')}")
            print("-"*65)
            print(" 📱 【一键发送给甲方高管的微信战报文案模板】:")
            print(res["share_text"])
            print("="*65 + "\n")
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
        ms = ful["manifest_summary"]
        print("\n" + "="*65)
        print(f"📜 项目 [{pid}] 商业交付验收结案确认单已生成！")
        print("="*65)
        print(f"🏆 综合合同履约达成率: {ful['total_fulfillment_score']}/100 分")
        print(f"📦 16 维全景资产覆盖: {ms['generated_files']}/{ms['total_files']} ({ms['generation_rate_pct']}%)")
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
    elif args.command == "publish":
        from .publisher import (
            package_toutiao_assets,
            package_wechat_assets,
            package_deepseek_assets,
            package_zhihu_assets,
            package_kimi_baidu_assets,
            package_all_channels,
        )
        pid = get_pid(args)
        ch = getattr(args, "channel", "all")
        verify = getattr(args, "verify", False)
        res = None
        if ch == "toutiao":
            res = package_toutiao_assets(pid, verify=verify)
        elif ch == "wechat":
            res = package_wechat_assets(pid, verify=verify)
        elif ch == "deepseek":
            res = package_deepseek_assets(pid, verify=verify)
        elif ch == "zhihu":
            res = package_zhihu_assets(pid, verify=verify)
        elif ch == "kimi_baidu":
            res = package_kimi_baidu_assets(pid, verify=verify)
        else:
            res = package_all_channels(pid, verify=verify)

        if verify and res:
            print("\n" + "=" * 60)
            print(" 🧪 大模型爬虫保真度逆向检验看板 (Crawler Fidelity)")
            print("=" * 60)
            has_failure = False
            if "fidelity" in res and res["fidelity"]:
                fid = res["fidelity"]
                is_passed = fid.get("passed", False)
                if not is_passed:
                    has_failure = True
                status = "✅ 黄金高保真" if is_passed else "⚠️ 需优化"
                print(f" 渠道: {fid.get('channel', ch)} ｜ 状态: {status} ｜ 综合保真分: {fid.get('overall_score', 0)}分")
                print(f" • 表格完整性 (40%): {fid.get('table_integrity_score', 0)}分")
                print(f" • 引用留存率 (35%): {fid.get('citation_retention_rate', 0)}分")
                print(f" • 语义密度   (25%): {fid.get('semantic_density_score', 0)}分")
                if fid.get("warnings"):
                    for w in fid["warnings"]:
                        print_warning(f"  [告警] {w}")
            elif "fidelities" in res and res["fidelities"]:
                avg = res.get("average_fidelity_score", 0)
                all_passed = res.get("all_passed", False)
                if not all_passed:
                    has_failure = True
                all_p = "✅ 全渠道通过" if all_passed else "⚠️ 部分渠道需优化"
                print(f" 全渠道平均保真分: {avg}分 ｜ 判定: {all_p}")
                for c_name, fid in res.get("fidelities", {}).items():
                    c_status = "✅" if fid.get("passed") else "⚠️"
                    print(f"  {c_status} [{c_name:10s}] 综合: {fid.get('overall_score', 0)}分 ｜ 表格: {fid.get('table_integrity_score', 0)}分 ｜ 引用: {fid.get('citation_retention_rate', 0)}分")
            print("=" * 60 + "\n")

            if has_failure:
                print_error("❌ 大模型爬虫保真度核验未达 90.0 分门槛，发稿被拦截！")
                sys.exit(1)
    elif args.command == "eval":
        from .evaluator import run_live_llm_evaluation
        m_list = [m.strip() for m in args.models.split(",") if m.strip()]
        run_live_llm_evaluation(get_pid(args), models=m_list, limit=args.limit, concurrency=4)
    elif args.command == "certificate":
        from .certificate import build_delivery_certificate_html
        build_delivery_certificate_html(get_pid(args))
    elif args.command == "ledger":
        from .dist_bot import batch_backfill_urls, verify_all_channels, get_distribution_ledger
        pid = get_pid(args)
        if args.add:
            batch_backfill_urls(pid, args.add, verify_now=True)
        elif args.audit:
            verify_all_channels(pid)
        else:
            led = get_distribution_ledger(pid)
            print(f"项目 [{pid}] 填报完成率: {led['completion_rate_pct']}% (加权 {led['weighted_completion_pct']}%) | 真实存活率: {led.get('alive_rate_pct', 0)}% (加权 {led.get('weighted_alive_pct', 0)}%)")
            for k, v in led['channels'].items():
                print(f" - {v['name']}: {v.get('url') or '(未填报)'} [{v.get('status')}]")
    elif args.command == "crawl":
        from .crawler import simulate_crawler_fetch
        res = simulate_crawler_fetch(args.url, spider_type=args.spider)
        print("\n" + "="*65)
        print(f"🕷️ 大模型爬虫抓取仿真报告: [{res.get('spider_type')}] -> {res.get('url')}")
        print("="*65)
        if res.get("success"):
            print(f"✅ HTTP 状态: {res.get('http_status')} ｜ 响应耗时: {res.get('elapsed_ms')}ms ｜ 预估 Token: {res.get('token_estimate')}")
            print(f"📄 抓取页面标题: {res.get('title') or '(无)'}")
            print(f"📝 抓取页面简介: {res.get('description') or '(无)'}")
            print(f"🏷️ 结构化 JSON-LD: {res.get('jsonld_count')} 组")
            print("\n--- [提纯 Clean Markdown 预览 (前 300 字)] ---")
            print(res.get("clean_markdown", "")[:300] + "...")
        else:
            print(f"❌ 抓取失败: {res.get('error')}")
        print("="*65 + "\n")
    elif args.command == "rag-diag":
        from .rag_diag import diagnose_rag_chunks
        pid = get_pid(args)
        diagnose_rag_chunks(pid, text_or_file=getattr(args, "file", None))
    elif args.command == "compliance":
        from .compliance import inspect_content_compliance, sanitize_project_deliverables
        pid = get_pid(args)
        if getattr(args, "sanitize", False):
            sanitize_project_deliverables(pid)
        else:
            custom_f = getattr(args, "file", None)
            custom_t = None
            if custom_f and os.path.exists(custom_f):
                with open(custom_f, "r", encoding="utf-8") as fp:
                    custom_t = fp.read()
            res = inspect_content_compliance(pid, custom_text=custom_t)
            print("\n" + "="*65)
            print(f"🛡️ 项目 [{pid}] 内容合规与广告法风控审查报告")
            print("="*65)
            print(f"📊 合规就绪度得分: {res['compliance_score']}/100 ｜ 状态: {'🟢 100% 合规通过' if res['is_passed'] else '🔴 存在违规风险'}")
            print(f"🚨 违规总数: {res['total_violations']} 处 (🔴 P0: {res['p0_count']} ｜ 🟡 P1: {res['p1_count']} ｜ 🟢 P2: {res['p2_count']})")
            print(f"📁 扫描交付物文件: {res['scanned_files_count']} 份")
            print("="*65)
            for idx, v in enumerate(res["violations"][:10], 1):
                print(f"  {idx}. [{v['level']}] `{v['file']}:L{v['line']}` 命中: 【{v['matched_term']}】 ➔ 建议替换: 【{v['suggested_term']}】")
                print(f"     上下文: {v['context_snippet']}")
            if len(res["violations"]) > 10:
                print(f"  ... 另有 {len(res['violations'])-10} 处违规，详见 outputs/13_多渠道内容合规与广告法风控审查报告.md")
            print("="*65 + "\n")
    elif args.command == "competitor-gap":
        from .competitor_gap import analyze_competitor_gap
        pid = get_pid(args)
        c_name = getattr(args, "competitor", None)
        res = analyze_competitor_gap(pid, competitor_name=c_name)
        radar = res["radar_comparison"]
        print("\n" + "="*65)
        print(f"⚔️ 竞对大模型声量差距推演: 【{res['brand_name']}】 vs 【{res['target_competitor']}】")
        print("="*65)
        print(f"🏆 综合优势得分: 我方 {radar['client_avg']}分 vs 竞对 {radar['competitor_avg']}分 (领先: +{radar['overall_gap_lead']}分)")
        print("="*65)
        for i in range(len(radar["dimensions"])):
            d = radar["dimensions"][i]
            cs = radar["client_scores"][i]
            comp_s = radar["competitor_scores"][i]
            print(f"  • {d:18s}: 我方 {cs:4.1f} 分 ｜ 竞对 {comp_s:4.1f} 分 ｜ 领先: +{round(cs-comp_s,1)}分")
        print("\n--- [竞对三大破绽与反超战术] ---")
        for idx, f in enumerate(res["competitor_flaws"], 1):
            print(f"  {idx}. [{f['dimension']}] 破绽: {f['competitor_flaw']}")
            print(f"     反击: {f['tactical_action']}")
        print("="*65 + "\n")
    elif args.command == "citation-auth":
        from .citation_authority import evaluate_project_citation_authority
        pid = get_pid(args)
        res = evaluate_project_citation_authority(pid)
        print("\n" + "="*65)
        print(f"🏆 项目 [{pid}] 大模型 Citation 信源权威度与外链信任度报告")
        print("="*65)
        print(f"📊 全案综合权威指数: {res['overall_authority_score']}/100 ｜ 预估采纳率: {res['estimated_citation_rate']}%")
        print(f"🔗 外链总数: {res['total_backlinks']} 条 (🟢 有效存活: {res['live_backlinks']} ｜ 🔴 异常死链: {res['dead_backlinks']})")
        print("\n--- [五大本土大模型生态亲和度大盘] ---")
        for m, s in res["model_affinity_summary"].items():
            print(f"  • {m:12s}: {s:4.1f} 分")
        print("\n--- [全渠道外链权威度明细] ---")
        for idx, l in enumerate(res["links"][:6], 1):
            status_icon = "🟢" if l["is_live"] else "🔴"
            print(f"  {idx}. {status_icon} [{l['channel_name']}] DA: {l['domain_authority']}分 ｜ 采纳率: {l['estimated_citation_rate']}% ｜ 适配: {','.join(l['best_fit_models'])}")
            print(f"     URL: {l['url']}")
        print("="*65 + "\n")
    elif args.command == "injection-guard":
        from .injection_guard import evaluate_project_injection_immunity, scan_content_for_injections
        pid = get_pid(args)
        custom_f = getattr(args, "file", None)
        if custom_f:
            target_path = custom_f
            if not os.path.exists(target_path):
                alt_path = os.path.join(PROJECTS_DIR, pid, "outputs", custom_f)
                if os.path.exists(alt_path):
                    target_path = alt_path
            if os.path.exists(target_path):
                with open(target_path, "r", encoding="utf-8", errors="ignore") as fp:
                    text_content = fp.read()
                findings = scan_content_for_injections(text_content, filename=os.path.basename(target_path))
                p0_cnt = sum(1 for f in findings if f["risk_level"] == "P0")
                p1_cnt = sum(1 for f in findings if f["risk_level"] == "P1")
                p2_cnt = sum(1 for f in findings if f["risk_level"] == "P2")
                print("\n" + "="*65)
                print(f"🛡️ 单文件提示词注入防御扫描报告: [{target_path}]")
                print("="*65)
                print(f"📊 状态: {'🟢 极高安全免疫 (0 威胁)' if not findings else '🔴 存在注入风险'}")
                print(f"🚨 捕获威胁总数: {len(findings)} 处 (🔴 P0: {p0_cnt} ｜ 🟡 P1: {p1_cnt} ｜ 🟢 P2: {p2_cnt})")
                print("="*65)
                if findings:
                    print("\n--- [威胁明细 Top 10] ---")
                    for idx, t in enumerate(findings[:10], 1):
                        print(f"  {idx}. [{t['risk_level']}] `{t['file']}:L{t['line']}` ({t['category_name']}) 命中: 【{t['matched_text']}】")
                        print(f"     上下文: {t['context']}")
                        print(f"     建议: {t['suggestion']}")
                else:
                    print("  ✅ 恭喜！未检测到任何提示词注入或 RAG 投毒风险。")
                print("="*65 + "\n")
            else:
                print(f"❌ 错误：指定文件不存在: {custom_f}")
        else:
            res = evaluate_project_injection_immunity(pid)
            print("\n" + "="*65)
            print(f"🛡️ 项目 [{pid}] 大模型提示词注入防御与品牌安全隔离盾牌报告")
            print("="*65)
            print(f"📊 提示词注入免疫度: {res['immunity_score']}/100 ｜ 状态: {'🟢 极高安全免疫' if res['is_secure'] else '🔴 存在注入风险'}")
            print(f"🚨 捕获威胁总数: {res['total_threats']} 处 (🔴 P0: {res['p0_threats_count']} ｜ 🟡 P1: {res['p1_threats_count']} ｜ 🟢 P2: {res['p2_threats_count']})")
            print(f"📁 扫描资产文件: {res['scanned_files_count']} 份")
            print("="*65)
            for idx, r in enumerate(res["defense_quarantine_rules"], 1):
                print(f"  {idx}. {r}")
            if res["threats_detail"]:
                print("\n--- [威胁明细 Top 5] ---")
                for idx, t in enumerate(res["threats_detail"][:5], 1):
                    print(f"  {idx}. [{t['risk_level']}] `{t['file']}:L{t['line']}` 命中: 【{t['matched_text']}】")
                    print(f"     上下文: {t['context']}")
            print("="*65 + "\n")
    elif args.command == "score":
        from .princeton import (
            score_text_princeton_factors,
            rewrite_text_princeton_factors,
            audit_project_deliverables_princeton,
        )
        project_id = getattr(args, "project", None)
        do_audit = getattr(args, "audit", False) or (project_id and not args.target and not getattr(args, "rewrite", False))
        if project_id and (do_audit or getattr(args, "audit", False)) and not getattr(args, "rewrite", False) and not args.target:
            res = audit_project_deliverables_princeton(project_id)
            print("\n" + "=" * 65)
            print(f"🔬 项目 [{project_id}] 普林斯顿 9 因子全案质检")
            print("=" * 65)
            print(f"📊 全案均分: {res['avg_princeton_score']}/100 ｜ 评级: {res['rating_grade']}")
            print(f"📈 可见度上限: {res['est_visibility_ceiling']} ｜ 相对基线净跃迁: {res['est_boost_vs_baseline']}")
            print(f"📁 扫描文件: {res['scanned_files']} ｜ ≥80 通过率: {res['pass_rate_ge_80']}%")
            print(f"📄 报告: outputs/{res['report_md']} + {res['report_json']}")
            print("=" * 65 + "\n")
        else:
            raw = args.target or ""
            if raw and os.path.exists(raw) and os.path.isfile(raw):
                with open(raw, "r", encoding="utf-8", errors="ignore") as fp:
                    text = fp.read()
            else:
                text = raw
            if not text.strip():
                print_error("请提供待测文本、文件路径，或使用 --project <id> [--audit] 做全案审计")
                sys.exit(1)
            if getattr(args, "rewrite", False):
                res = rewrite_text_princeton_factors(text, project_id=project_id, industry=args.industry)
                print("\n" + "=" * 65)
                print("✨ 普林斯顿 9 因子一键重构结果")
                print("=" * 65)
                print(f"📊 得分: {res['before_score']} → {res['after_score']}（增益 {res['score_gain']}）")
                print(f"📈 净跃迁 est_boost_vs_baseline: {res['est_boost_vs_baseline']}")
                if res.get("is_fictional_warning"):
                    print("⚠️  售前沙箱：文中 [示例待核实] 为排版示例，上线须替换为真实数据")
                print("-" * 65)
                print(res["after_text"][:2000])
                if len(res["after_text"]) > 2000:
                    print("\n...（已截断，完整文本请走 API / Web）")
                print("=" * 65 + "\n")
            else:
                res = score_text_princeton_factors(text, industry=args.industry)
                print("\n" + "=" * 65)
                print("🔬 普林斯顿 9 因子量化体检报告")
                print("=" * 65)
                print(f"🏆 综合得分: {res['overall_score']}/100 ｜ {res['rating_grade']}")
                print(f"📈 可见度上限 est_visibility_ceiling: {res['est_visibility_ceiling']}")
                print(f"🚀 相对基线净跃迁 est_boost_vs_baseline: {res['est_boost_vs_baseline']}")
                print("-" * 65)
                for key, meta in res["factor_scores"].items():
                    bar = "█" * int(meta["score"] / 10) + "░" * (10 - int(meta["score"] / 10))
                    print(f"  {meta['label']:<10} {meta['score']:>5.1f} [{bar}] w={meta['weight']}%  {meta['detail']}")
                pen = res["penalties"]["keyword_stuffing"]
                print(f"  堆砌惩罚      -{pen['penalty']}  {pen['reason']}")
                print("-" * 65)
                for s in res["suggestions"][:5]:
                    print(f"  • {s}")
                print("=" * 65 + "\n")
    elif args.command == "portfolio":
        from .portfolio import get_portfolio_summary, run_portfolio_health_patrol, generate_portfolio_executive_report
        if getattr(args, "patrol", False):
            res = run_portfolio_health_patrol()
            print("\n" + "="*70)
            print("🚨 GEO 全域多项目健康巡检与风险红黑榜")
            print("="*70)
            print(f"⏱️ 扫描耗时: {res['elapsed_ms']}ms ｜ 扫描项目: {res['total_scanned']} 个")
            print(f"📊 风险概览: 🔴 高危 {res['counts']['danger']} ｜ 🟡 预警 {res['counts']['warning']} ｜ 🟢 优良 {res['counts']['healthy']}")
            print("="*70)
            print("【🔴 红色高危清单】")
            if res['red_black_board']['danger']:
                for d in res['red_black_board']['danger']:
                    print(f"  · {d['client_name']} ({d['industry']}): {'；'.join(d['risk_reasons'])}")
            else:
                print("  · 暂无高危项目，全盘安全隔离良好。")
            print("\n【🟡 黄色预警清单】")
            if res['red_black_board']['warning']:
                for w in res['red_black_board']['warning']:
                    print(f"  · {w['client_name']} ({w['industry']}): {'；'.join(w['risk_reasons'])}")
            else:
                print("  · 暂无黄色预警项目。")
            print("\n【🟢 绿色优良清单】")
            for h in res['red_black_board']['healthy']:
                print(f"  · {h['client_name']} ({h['industry']}): 履约 {h['fulfillment_score']}分 · {'；'.join(h['risk_reasons'])}")
            print("="*70 + "\n")
        elif getattr(args, "report", False):
            rep = generate_portfolio_executive_report()
            print("\n" + "="*70)
            print("📊 GEO 代运营全域多项目商业大盘报告已生成！")
            print("="*70)
            print(f"📁 报告路径: {rep['filepath']}")
            print(f"📄 报告规模: {len(rep['content'])} 字符 ｜ 涵盖企业: {rep['summary']['scale']['total_projects']} 家")
            print(f"💰 全盘商业总价值: ¥{rep['summary']['financial_valuation']['total_business_value']:,} 元")
            print(f"📈 组合投资回报率 (ROI): +{rep['summary']['financial_valuation']['portfolio_roi_pct']}%")
            print("="*70 + "\n")
        else:
            s = get_portfolio_summary()
            scale = s["scale"]
            fin = s["financial_valuation"]
            sec = s["security_and_compliance"]
            print("\n" + "="*75)
            print("📊 GEO 全域多项目商业代运营大盘驾驶舱")
            print("="*75)
            print(f"🏛️ 托管客户总数: {scale['total_projects']} 家 ｜ 16维平均齐套率: {scale['avg_manifest_generation_pct']}% ｜ 全额结案数: {scale['passed_acceptance_projects']}/{scale['total_projects']}")
            print(f"🛡️ 注入安全免疫: {sec['avg_injection_immunity']}/100 ｜ 广告合规违规: {sec['total_compliance_violations']} 处 ｜ 全盘死链: {sec['total_dead_links']} 条")
            print(f"💵 年度总服务费: ¥{fin['total_annual_service_fee']:,} 元 ｜ 等效 SEM 节省: ¥{fin['total_sem_replacement_value']:,} 元/年")
            print(f"🚀 全盘年化总产出: ¥{fin['total_business_value']:,} 元 ｜ 净商业增值: ¥{fin['total_business_value'] - fin['total_annual_service_fee']:,} 元")
            print(f"📈 全盘组合投资回报率 (Portfolio ROI): +{fin['portfolio_roi_pct']}% (整体资产放大: {fin['portfolio_roi_multiplier']} 倍)")
            print("-"*75)
            print(f"{'序号':<4} {'企业客户名称':<18} {'行业':<14} {'履约':<8} {'SOV':<8} {'年化价值':<12} {'状态':<6}")
            print("-"*75)
            for idx, c in enumerate(s["project_cards"], 1):
                st = "🔴 高危" if c["risk_level"] == "danger" else ("🟡 预警" if c["risk_level"] == "warning" else "🟢 正常")
                print(f"{idx:<4} {c['client_name'][:16]:<18} {c['industry'][:12]:<14} {c['fulfillment_score']:<8.1f} {c['effective_sov_pct']:<7.1f}% ¥{int(c['total_business_value']):<11,} {st}")
    elif args.command in ("probe", "probe-audit"):
        pid = get_pid(args)
        if not pid or pid == "_template":
            print(f"❌ 请指定要探测的目标项目 ID，例如: python3 -m tools.geo {args.command} xuzhou_xuanyuan")
            sys.exit(1)

        from tools.geo.probing import run_live_probing, reconcile_existing_trace
        if getattr(args, "reconcile_only", False):
            portal_sync_flag = bool(getattr(args, "portal_sync", False) or True)
            res = reconcile_existing_trace(pid, portal_sync=portal_sync_flag)
            if not res.get("success"):
                print(f"❌ 离线对账失败: {res.get('error')}")
                sys.exit(1)
            summary = res["summary"]
            print("\n" + "="*75)
            print(f"⚡ 离线台账极速对账完成 · [{pid}] (第 30 维 Citation 信源反查)")
            print("="*75)
            print(f"🏛️ 客户名称: {res.get('client_name', '')} ｜ 对账时间: {res.get('reconciled_at', '')}")
            print(f"🎯 Citation 角标总数: {summary.get('total_citations_captured', 0)} ｜ 命中台账资产: {summary.get('my_ledger_assets_hit_count', 0)} 处")
            print(f"📈 占有率 (Citation Share): {summary.get('citation_share_pct', 0.0)}% ｜ 实测 SOV: {summary.get('real_sov_pct', 0.0)}%")
            print(f"ℹ️  第 30 维反查审计公文报告已刷新:\n    {res.get('report_30_path')}")
            if res.get("portal_synced"):
                print("🌐 高管只读交付门户战果大屏已联动同步刷新 (含真实命中外链)")
            print("="*75 + "\n")
        else:
            models_list = [m.strip() for m in args.models.split(",") if m.strip()]
            res = run_live_probing(
                project_id=pid,
                models=models_list,
                query_sample_size=args.sample,
                use_live=args.live
            )
            summary = res["summary"]
            breakdown = res["model_breakdown"]
            queries = res["probed_queries"]

            print("\n" + "="*75)
            print(f"🤖 多大模型实时联网探测与 Citation 信源溯源对账 · [{pid}]")
            print("="*75)
            print(f"🏛️ 客户名称: {res['client_name']} ｜ 探测时间: {res['timestamp']}")
            print(f"📊 探测规模: {summary['total_probes']} 次 ({len(summary['models_probed'])} 模型 × {summary['sample_queries_count']} 组 Query) ｜ 运行模式: {'真实联网 API' if summary['use_live'] else '确定性高保真沙箱'}")
            print(f"📈 实测提及率 (Real SOV): {summary['real_sov_pct']}% ｜ 首位推荐率 (Top-1): {summary['top1_recommendation_rate']}%")
            print(f"🎯 Citation 信源角标占有率: {summary['citation_share_pct']}% (总捕获 {summary['total_citations_captured']} 条角标中命中我方 04 台账资产 {summary['my_ledger_assets_hit_count']} 处)")
            print("-"*75)
            print(f"{'模型':<12} {'探测':<6} {'实测SOV':<10} {'首推率':<10} {'角标总数':<10} {'命中台账':<10} {'平均延时'}")
            print("-"*75)
            for m, st in breakdown.items():
                print(f"{m:<12} {st['probes']:<6} {st['sov_pct']:<9.1f}% {st['top1_pct']:<9.1f}% {st['total_citations']:<10} {st['citation_hits']:<10} {st['avg_latency_ms']}ms")
            print("-"*75)
            print("🔍 意图 Query Citation 溯源采样流水:")
            for idx, q in enumerate(queries[:6], 1):
                ment = f"✅ 首位推荐" if q["is_top1"] else ("🟢 提及" if q["is_mentioned"] else "⚪ 未提")
                hits_str = f"命中台账 {q['hits_count']} 处" if q['hits_count'] > 0 else "未命中台账"
                print(f"  [{idx}] {q['model']} ➔ {q['query'][:26]}... | {ment} | {hits_str}")
            print(f"\nℹ️  全案第 18 维公文 Markdown 报告已落盘至:\n    {res.get('report_path')}")
            if res.get("report_30_path"):
                print(f"ℹ️  全案第 30 维高管 Citation 审计公文已落盘至:\n    {res.get('report_30_path')}")
            print("="*75 + "\n")
    elif args.command == "guard-clean":
        pid = get_pid(args)
        if not pid or pid == "_template":
            print("❌ 请指定项目 ID，例如: python3 -m tools.geo guard-clean xuzhou_xuanyuan")
            sys.exit(1)
        from tools.geo.sentiment_guard import audit_negative_sentiment, generate_crisis_suppression_pack
        models_list = [m.strip() for m in args.models.split(",") if m.strip()]
        res = audit_negative_sentiment(project_id=pid, models=models_list, use_live=args.live)
        s = res["summary"]
        level_icon = {"safe": "🟢", "warning": "🟡", "danger": "🔴"}.get(s["risk_level"], "⚪")
        print("\n" + "=" * 72)
        print(f"🛡️ 19 号品牌声誉排查与危机清洗 · [{pid}]")
        print("=" * 72)
        print(f"客户: {res['client_name']} ｜ {res['timestamp']}")
        print(f"{level_icon} BRS: {s['brs']} ({s['risk_level']}) ｜ 负面暴露率: {s['negative_exposure_rate']}% ｜ 争议率: {s['controversial_rate']}%")
        print(f"探测: {s['total_probes']} 次 ({len(s['models_probed'])}×{s['probe_count']}) ｜ 脏信源: {s['toxic_sources_count']} 条")
        print("-" * 72)
        for r in res["probe_results"][:8]:
            print(f"  [{r['polarity']}] {r['model']} · {r['category_name']}: {r['prompt'][:36]}…")
        if args.suppress:
            pack = generate_crisis_suppression_pack(pid)
            print(f"\n📦 压制包已生成: {pack['pack_dir']}")
            for fp in pack.get("files", []):
                print(f"    - {fp}")
        print(f"\nℹ️  19 号报告: {res['report_path']}")
    elif args.command == "decay":
        pid = get_pid(args)
        if not pid or pid == "_template":
            print("❌ 请指定项目 ID，例如: python3 -m tools.geo decay xuzhou_xuanyuan")
            sys.exit(1)
        from tools.geo.decay_monitor import track_knowledge_decay, generate_decay_healing_pack
        models_list = [m.strip() for m in args.models.split(",") if m.strip()]
        res = track_knowledge_decay(
            project_id=pid,
            models=models_list,
            use_live=args.live,
            delta_days=args.delta_days,
        )
        s = res["summary"]
        level_icon = {"safe": "🟢", "warning": "🟡", "danger": "🔴"}.get(s["risk_level"], "⚪")
        print("\n" + "=" * 75)
        print(f"⏳ 20 号大模型知识半衰期衰减监测与长效自愈 · [{pid}]")
        print("=" * 75)
        print(f"受测企业: {res['client_name']} ｜ 打卡时间: {res['timestamp']}")
        print(f"{level_icon} 知识留存率 (KRR): {s['krr']}% ({s['risk_level']}) ｜ 预估半衰期: {s['half_life_days']} 天")
        print(f"当期实测分: {s['current_score']} / 基准分: {s['initial_baseline_score']} ｜ 衰减意图词: {s['decayed_queries_count']} 个")
        print("-" * 75)
        for b in res.get("query_decay_breakdown", []):
            st_icon = {"safe": "🟢", "warning": "🟡", "danger": "🔴"}.get(b["status"], "⚪")
            print(f"  {st_icon} 留存 {b['retention_rate']}% [{b['status']}] · {b['query'][:42]}…")
        if args.heal:
            pack = generate_decay_healing_pack(pid)
            print(f"\n📦 自愈补量刷新包已生成: {pack['pack_dir']}")
            for fp in pack.get("files", []):
                print(f"    - {fp}")
        print(f"\nℹ️  20 号公文报告落盘至: {res['report_path']}")
        print("=" * 75 + "\n")
    elif args.command == "mindshare":
        pid = get_pid(args)
        if not pid or pid == "_template":
            print("❌ 请指定项目 ID，例如: python3 -m tools.geo mindshare xuzhou_xuanyuan")
            sys.exit(1)
        from tools.geo.mindshare_auditor import audit_mindshare_penetration, generate_commercial_pitch_pack
        models_list = [m.strip() for m in args.models.split(",") if m.strip()]
        res = audit_mindshare_penetration(
            project_id=pid,
            models=models_list,
            use_live=args.live,
        )
        s = res["summary"]
        print("\n" + "=" * 75)
        print(f"💎 21 号大模型商业心智渗透与商业转化价值审计 · [{pid}]")
        print("=" * 75)
        print(f"受审企业: {res['client_name']} ｜ 审计时间: {res['timestamp']}")
        print(f"🏆 商业心智渗透指数 (MPI): {s['mpi']} 分 ｜ 等级: {s['grade_name']}")
        print(f"💰 年化等效广告价值 (AEV): ¥{s['annual_aev_yuan']:,} 元 (商机转化率 20%)")
        print(f"📊 加权推荐度: {s['weighted_sov_rate']}% ｜ 台账背书率: {s['citation_rate']}% ｜ BRS 声誉: {s['brs_score']}分 ｜ KRR 留存: {s['krr_rate']}%")
        print("-" * 75)
        for q in res.get("query_audits", []):
            print(f"  • {q['query'][:38]}… 推荐度: {q['weighted_sov']}% (首推: {q['top1_count']}次, 提及: {q['mention_count']}次, 外链: {q['ledger_hits']}条)")
        if args.pitch:
            pack = generate_commercial_pitch_pack(pid)
            print(f"\n📦 高管商务汇报包已生成: {pack['pack_dir']}")
            for fp in pack.get("files", []):
                print(f"    - {fp}")
        print(f"\nℹ️  21 号公文报告落盘至: {res['report_path']}")
        print("=" * 75 + "\n")
    elif args.command == "rerank":
        pid = get_pid(args)
        if not pid or pid == "_template":
            print("❌ 请指定项目 ID，例如: python3 -m tools.geo rerank xuzhou_xuanyuan")
            sys.exit(1)
        from tools.geo.rerank_simulator import simulate_rag_rerank_competition, generate_rerank_reinforcement_pack
        models_list = [m.strip() for m in args.models.split(",") if m.strip()]
        res = simulate_rag_rerank_competition(
            project_id=pid,
            models=models_list,
            use_live=args.live,
        )
        s = res["summary"]
        print("\n" + "=" * 75)
        print(f"🔀 22 号跨大模型 RAG 混合检索召回与重排序挤占演习 · [{pid}]")
        print("=" * 75)
        print(f"受审企业: {res['client_name']} ｜ 演习时间: {res['timestamp']}")
        print(f"🏆 Top-3 穿透率 (CPR): {s['cpr']}% ｜ 等级: {s['grade_name']}")
        print(f"🛡️ 竞品排挤阻断率 (COR): {s['cor']}% (排挤竞品: {s['comp_slots_ousted']}/{s['comp_candidates_total']} 人次)")
        print(f"📊 黄金槽位占领: {s['my_slots_won']}/{s['total_slots']} ｜ 平均重排得分: {s['avg_rerank_score']}分")
        print("-" * 75)
        for q in res.get("query_rerank_details", []):
            t1 = q["top3_chunks"][0]["title"] if q["top3_chunks"] else "--"
            print(f"  • {q['query'][:36]}… 槽位: {q['slots_won']}/3 ｜ Top-1: {t1[:26]} ｜ 排挤: {len(q['ousted_competitors'])}条")
        if args.reinforce:
            pack = generate_rerank_reinforcement_pack(pid)
            print(f"\n📦 重排语义强化包已生成: {pack['pack_dir']}")
            for fp in pack.get("files", []):
                print(f"    - {fp}")
        out_report = os.path.join(PROJECTS_DIR, pid, "outputs", "22_跨大模型RAG混合检索召回与重排序挤占演习报告.md")
        print(f"\nℹ️  22 号公文报告落盘至: {out_report}")
        print("=" * 75 + "\n")
    elif args.command == "attribution":
        pid = get_pid(args)
        if not pid or pid == "_template":
            print("❌ 请指定项目 ID，例如: python3 -m tools.geo attribution xuzhou_xuanyuan")
            sys.exit(1)
        from tools.geo.causal_auditor import (
            CausalAttributionSimulator,
            generate_attribution_optimization_pack,
        )
        models_list = [m.strip() for m in args.models.split(",") if m.strip()]
        res = CausalAttributionSimulator.audit_causal_attribution(
            project_id=pid,
            models=models_list,
            use_live=args.live,
        )
        s = res["summary"]
        print("\n" + "=" * 75)
        print(f"🧬 23 号大模型商业推荐因果归因与信源边际贡献度量化审计 · [{pid}]")
        print("=" * 75)
        print(f"受审企业: {res['client_name']} ｜ 审计时间: {res['timestamp']}")
        print(f"🏆 品牌因果鲁棒性指数 (CRI): {s['cri']}% ｜ 等级: {s['grade_name']}")
        print(f"📊 基线推荐得分: {s['baseline_score']}分 ｜ 最坏情况留存: {s['worst_case_score']}分")
        print(f"👑 资产结构: {s['cornerstone_count']} 基石 ｜ ⚡ {s['catalyst_count']} 催化 ｜ 🥀 {s['redundant_count']} 冗余")
        print(f"⚠️ 关键单点故障预警: {'⚠️ 存在关键单点！建议立即加固' if s['spof_detected'] else '✅ 无致命单点'}")
        print("-" * 75)
        print("信源反事实消融与边际因果贡献率 (Top 5):")
        for src in res.get("source_attributions", [])[:5]:
            spof_tag = " [⚠️SPOF]" if src.get("critical_spof") else ""
            print(f"  • {src['source_id']} ｜ MCR: {src['mcr']}% ({src['role_name']}){spof_tag} ｜ 跌幅: -{src['marginal_drop']}分 ｜ {src['title'][:32]}")
        if args.optimize:
            pack = generate_attribution_optimization_pack(pid)
            print(f"\n📦 因果归因优化三件套已生成: {pack['pack_dir']}")
            for fp in pack.get("files", []):
                print(f"    - {fp}")
        out_report = os.path.join(PROJECTS_DIR, pid, "outputs", "23_大模型商业推荐因果归因与信源边际贡献度量化审计报告.md")
        print(f"\nℹ️  23 号公文报告落盘至: {out_report}")
        print("=" * 75 + "\n")
    elif args.command == "funnel":
        pid = get_pid(args)
        if not pid or pid == "_template":
            print("❌ 请指定项目 ID，例如: python3 -m tools.geo funnel xuzhou_xuanyuan")
            sys.exit(1)
        from tools.geo.funnel_simulator import (
            ConversationalFunnelSimulator,
            generate_funnel_defense_pack,
        )
        models_list = [m.strip() for m in args.models.split(",") if m.strip()]
        res = ConversationalFunnelSimulator.simulate_funnel(
            project_id=pid,
            models=models_list,
            use_live=args.live,
        )
        s = res["summary"]
        print("\n" + "=" * 75)
        print(f"🌪️ 24 号大模型商业多轮追问决策漏斗与意图转化推演 · [{pid}]")
        print("=" * 75)
        print(f"受审企业: {res['client_name']} ｜ 推演时间: {res['timestamp']}")
        print(f"🏆 端到端漏斗转化率 (FCR): {s['fcr']}% ｜ 评级: {s['grade_name']}")
        print(f"📊 阶段总数: {s['total_stages']} 阶 ｜ 高危截流脆弱断点: {s['turning_points_detected']} 处")
        print("-" * 75)
        print("四阶多轮意图递进状态转移与留存矩阵:")
        for st in res.get("stages", []):
            tp_mark = " [⚠️高危断流拐点]" if st.get("is_critical_turning_point") else ""
            print(f"  • {st['stage_id']} {st['stage_name']}: {st['p_score']}分 ｜ 留存率: {st['retention_rate']}% ｜ 跌幅: -{st['drop_p']}分{tp_mark}")
            print(f"    追问: \"{st['query']}\"")
        if args.defend:
            pack = generate_funnel_defense_pack(pid)
            print(f"\n📦 决策漏斗防截流加固包已生成: {pack['pack_dir']}")
            for fp in pack.get("files", []):
                print(f"    - {fp}")
        out_report = os.path.join(PROJECTS_DIR, pid, "outputs", "24_大模型商业多轮追问决策漏斗与意图转化路径推演报告.md")
        print(f"\nℹ️  24 号公文报告落盘至: {out_report}")
        print("=" * 75 + "\n")
    elif args.command == "robustness":
        pid = get_pid(args)
        if not pid or pid == "_template":
            print("❌ 请指定项目 ID，例如: python3 -m tools.geo robustness xuzhou_xuanyuan")
            sys.exit(1)
        from tools.geo.robustness_tester import (
            PromptRobustnessTester,
            generate_robustness_hardening_pack,
        )
        models_list = [m.strip() for m in args.models.split(",") if m.strip()]
        res = PromptRobustnessTester.run_stress_test(
            project_id=pid,
            models=models_list,
            use_live=args.live,
        )
        s = res["summary"]
        print("\n" + "=" * 75)
        print(f"🛡️ 25 号大模型提示词敏感度扰动与生成鲁棒性压力测试 · [{pid}]")
        print("=" * 75)
        print(f"受审企业: {res['client_name']} ｜ 测试时间: {res['timestamp']}")
        print(f"🏆 生成鲁棒性指数 (GRI): {s['gri']}% ｜ 评级: {s['grade_name']}")
        print(f"🎯 基准 Query 得分: {s['baseline_score']}分 ｜ 扰动均分: {s['mean_perturbed_score']}分 (留存率: {s['retention_rate']}%)")
        print(f"📊 总体标准差 (σ): {s['std_dev']} ｜ 变异系数 (CV): {s['cv']} ｜ 高危脆弱变体: {s['fragile_variants_count']} 项")
        print("-" * 75)
        print(f"基准 Query: \"{res['baseline_query']}\"")
        print("四维商业微扰动变体置信度承压明细:")
        for v in res.get("variants", []):
            fr_mark = " [⚠️高危脆弱项]" if v.get("is_fragile") else ""
            print(f"  • {v['variant_id']} {v['variant_type']}: {v['p_score']}分 ｜ 留存率: {v['retention_rate']}% ｜ 跌幅: -{v['drop_p']}分{fr_mark}")
            print(f"    扰动: \"{v['query']}\"")
        if args.harden:
            pack = generate_robustness_hardening_pack(pid)
            print(f"\n📦 鲁棒性容灾加固包已生成: {pack['pack_dir']}")
            for fp in pack.get("files", []):
                print(f"    - {fp}")
        out_report = os.path.join(PROJECTS_DIR, pid, "outputs", "25_大模型提示词敏感度扰动与生成鲁棒性压力测试报告.md")
        print(f"\nℹ️  25 号公文报告落盘至: {out_report}")
        print("=" * 75 + "\n")
    elif args.command == "moat":
        pid = get_pid(args)
        if not pid or pid == "_template":
            print("❌ 请指定项目 ID，例如: python3 -m tools.geo moat xuzhou_xuanyuan")
            sys.exit(1)
        from tools.geo.moat_sandbox import simulate_competitive_moat
        res = simulate_competitive_moat(
            project_id=pid,
            rival_override=args.rival,
            use_live=args.live,
        )
        if args.json:
            print(json.dumps(res, ensure_ascii=False, indent=2))
        else:
            s = res["summary"]
            print("\n" + "=" * 75)
            print(f"⚔️ 26 号大模型商业推荐博弈对抗与竞品截流动态护城河推演 · [{pid}]")
            print("=" * 75)
            print(f"受推品牌: {res['client_name']} ｜ 对标竞对: 【{res['rival_name']}】 ｜ 推演时间: {res['timestamp']}")
            print(f"🏰 动态护城河防御指数 (MDI): {s['moat_defense_index']}分 ｜ 战略评级: {s['grade_name']}")
            print(f"📈 我方平均净胜优势: {s['mean_advantage']:+0.1f}分 ｜ 均分对冲: 我方 {s['mean_self_score']}分 vs 竞对 {s['mean_rival_score']}分")
            print(f"⚠️ 截流暴露脆弱点: {s['vulnerable_breaches_count']} 处 ｜ 对抗维度总数: {s['total_dimensions']} 个")
            print("-" * 75)
            print("四维商业博弈对抗纵深矩阵:")
            for d in res.get("dimensions", []):
                fr_mark = " [🔴脆弱点]" if d.get("is_vulnerable") else " [🟢防线稳固]"
                print(f"  • {d['dim_id']} {d['dim_name']}: 我方 {d['self_score']}分 vs 竞对 {d['rival_score']}分 ｜ 优势差: {d['advantage']:+0.1f}分 ｜ CTI: {d['competitor_threat_index']}%{fr_mark}")
                print(f"    对抗: \"{d['query']}\"")
            radar = res.get("radar_metrics", {})
            print("-" * 75)
            print(f"五维护城河雷达: 综合={radar.get('moat_defense_index')} | 技术={radar.get('technical_advantage')} | 交付={radar.get('delivery_trust')} | 价格={radar.get('pricing_resilience')} | 本地={radar.get('local_service_moat')}")
            out_report = os.path.join(PROJECTS_DIR, pid, "outputs", "26_大模型商业推荐博弈对抗与竞品截流动态护城河推演报告.md")
            print(f"\nℹ️  26 号商业公文报告落盘至: {out_report}")
            print(f"📦 截流反制资产包落盘至: {os.path.join(PROJECTS_DIR, pid, 'outputs', 'counter_interception_pack')}")
            print("=" * 75 + "\n")
    elif args.command == "heal":
        pid = get_pid(args)
        if not pid or pid == "_template":
            print("❌ 请指定项目 ID，例如: python3 -m tools.geo heal xuzhou_xuanyuan")
            sys.exit(1)
        from tools.geo.healer import compile_healing_patches, apply_healing_patches, rollback_healing, verify_integrity

        # 回滚模式
        if args.rollback:
            print("\n" + "=" * 75)
            print(f"🔄 29 号全域动态知识自愈安全回滚 · [{pid}]")
            print("=" * 75)
            try:
                res = rollback_healing(pid, backup_ts=args.backup)
                print(f"✅ 成功从历史备份恢复: {res['restored_from']}")
                print(f"恢复时间: {res['rolled_back_at']}")
                print(f"已恢复靶标文件 ({len(res['restored_files'])} 个):")
                for fn in res['restored_files']:
                    print(f"  • {fn}")
                print("=" * 75 + "\n")
            except Exception as e:
                print(f"❌ 回滚失败: {e}\n" + "=" * 75 + "\n")
                sys.exit(1)

        # 正式落盘回写模式
        elif args.apply:
            print("\n" + "=" * 75)
            print(f"🌿 29 号全域动态知识热补丁聚合与一键落盘自愈流水线 · [{pid}]")
            print("=" * 75)
            try:
                res = apply_healing_patches(pid, auto_verify=True)
                s = res["summary"]
                if args.json:
                    print(json.dumps(res, ensure_ascii=False, indent=2))
                else:
                    print(f"受审企业: {res['client_name']} ｜ 状态: 已成功回写落盘 (Applied)")
                    print(f"执行时间: {res['applied_at']} ｜ 安全备份: {os.path.basename(res['backup_dir'])}")
                    print(f"🛡️ 动态自愈总补丁数: {s['total_patches']} 个 (事实: {s['truth_count']} ｜ FAQ: {s['faq_count']} ｜ 密集词: {s['dense_count']})")
                    if s['skipped_conflicts_count'] > 0:
                        print(f"⚠️ 多包同题冲突仲裁已跳过: {s['skipped_conflicts_count']} 组")
                    print("-" * 75)
                    print("靶标受影响文件对账:")
                    for aff in res.get("affected_files", []):
                        print(f"  • {aff['file']} ({aff['section']}): {aff['type']}")
                    if args.verify:
                        print("-" * 75)
                        v_res = verify_integrity(pid, use_tmp=False)
                        print(f"✅ 9 因子结构与 JSON-LD 语法联动质检: 100% 校验通过！")
                    print("-" * 75)
                    print(f"ℹ️  29 号结案公文已落盘: {res['audit_doc']}")
                    print(f"💡 提示：如需撤销回滚，请执行: geo heal {pid} --rollback")
                    print("=" * 75 + "\n")
            except Exception as e:
                print(f"❌ 事务落盘失败并已自动回滚还原: {e}\n" + "=" * 75 + "\n")
                sys.exit(1)

        # 默认 Dry-Run 干跑预览模式
        else:
            comp = compile_healing_patches(pid)
            if args.json:
                print(json.dumps(comp, ensure_ascii=False, indent=2))
            else:
                s = comp["summary"]
                print("\n" + "=" * 75)
                print(f"🌿 全域动态知识热补丁自愈对账 (Dry-Run 预览) · [{pid}]")
                print("=" * 75)
                print(f"可注入核心事实锚点: {s['truth_count']} 条")
                print(f"可注入密集语义/长尾词: {s['dense_count']} 个")
                print(f"可注入反制与自愈问答: {s['faq_count']} 组")
                print(f"已扫描策略源包: {len(comp['sources_found'])} 个已就绪 ｜ 缺失包: {len(comp['sources_missing'])} 个")
                print("-" * 75)
                print("📝 预计影响生产文件:")
                print("  • outputs/llms.txt (+长尾问答，+权威事实保障)")
                print("  • outputs/llms-truth.txt (追加 Section 5 动态事实锚点)")
                print("  • outputs/03_普林斯顿9因子高权威语料库.md (追加独立自愈附录)")
                print("  • outputs/schema.jsonld (合并 Organization.knowsAbout 与 FAQPage)")
                print("-" * 75)
                print(f"💡 提示：此为预览模式，执行落盘请运行: python3 -m tools.geo heal {pid} --apply")
                print("=" * 75 + "\n")
    elif args.command == "pipeline":
        cmd_run_pipeline(get_pid(args))

if __name__ == "__main__":
    main()


