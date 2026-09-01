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

