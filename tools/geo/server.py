#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GEO 可视化 Web 管理端后端服务 (tools/geo/server.py)
提供：
1. 账号密码登录与 Session/Token 鉴权拦截器（敏感信息保密）；
2. 项目列表与管理 CRUD API；
3. 5 阶段向导式 SOP 生产流水线调度接口；
4. 交付文件在线读取与 ZIP 一键打包下载；
5. 静态前端页面托管与公网开放路由。
"""

import os
import sys
import json
import time
import uuid
import zipfile
import io
import shutil
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote

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
from .audit import run_audit
from .scaffold import run_scaffold
from .rewrite import run_rewrite
from .distribute import run_distribute
from .monitor import run_monitor


# 鉴权配置（支持环境变量覆盖）
ADMIN_USERNAME = os.environ.get("GEO_ADMIN_USER", "13150568888")
ADMIN_PASSWORD = os.environ.get("GEO_ADMIN_PASS", "donghai0516")

# 活跃 Session 缓存 {token: {"username": str, "expire_at": float}}
ACTIVE_SESSIONS = {}
SESSION_TIMEOUT_HOURS = 24

WEB_DIR = os.path.join(PROJECT_ROOT, "web")

def create_session(username: str) -> str:
    token = str(uuid.uuid4())
    ACTIVE_SESSIONS[token] = {
        "username": username,
        "expire_at": time.time() + (SESSION_TIMEOUT_HOURS * 3600)
    }
    return token

def is_authenticated(token: str) -> bool:
    if not token or token not in ACTIVE_SESSIONS:
        return False
    session = ACTIVE_SESSIONS[token]
    if time.time() > session["expire_at"]:
        del ACTIVE_SESSIONS[token]
        return False
    return True

class GeoWebHandler(SimpleHTTPRequestHandler):
    """自定义 HTTP 请求处理器"""

    def log_message(self, format, *args):
        """屏蔽默认的 HTTP 访问日志噪音，只保留关键错误"""
        if args and len(args) >= 2 and str(args[1]).startswith(("4", "5")):
            super().log_message(format, *args)

    @staticmethod
    def _yaml_escape(val: str) -> str:
        """转义 YAML 字符串值中的双引号与反斜杠，防止生成格式破损的 project.yaml"""
        return str(val).replace("\\", "\\\\").replace('"', '\\"')

    def send_json(self, data: dict, status: int = 200, headers: dict = None):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        if headers:
            for k, v in headers.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.end_headers()

    def get_auth_token(self) -> str:
        # 1. 尝试从 Authorization Header 获取
        auth_header = self.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:].strip()
        # 2. 尝试从 URL query 获取
        if "?" in self.path:
            try:
                qs = parse_qs(self.path.split("?", 1)[1])
                if "token" in qs and qs["token"]:
                    return qs["token"][0].strip()
            except Exception:
                pass
        # 3. 尝试从 Cookie 获取
        cookies = self.headers.get("Cookie", "")
        for c in cookies.split(";"):
            if "geo_token=" in c:
                return c.split("geo_token=")[1].strip()
        return ""

    def read_json_body(self) -> dict:
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return {}
        raw = self.rfile.read(content_length).decode("utf-8")
        try:
            return json.loads(raw)
        except Exception:
            return {}

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # 1. 登录认证接口 (公开)
        if path == "/api/auth/login":
            body = self.read_json_body()
            user = body.get("username", "").strip()
            pwd = body.get("password", "").strip()

            if user == ADMIN_USERNAME and pwd == ADMIN_PASSWORD:
                token = create_session(user)
                self.send_json({
                    "success": True,
                    "token": token,
                    "username": user,
                    "message": "登录成功！"
                }, headers={"Set-Cookie": f"geo_token={token}; Path=/; HttpOnly"})
            else:
                self.send_json({"success": False, "message": "账号或密码错误！"}, status=401)
            return

        # 2. 登出接口
        if path == "/api/auth/logout":
            token = self.get_auth_token()
            if token in ACTIVE_SESSIONS:
                del ACTIVE_SESSIONS[token]
            self.send_json({"success": True, "message": "已成功退出登录！"})
            return

        # --- 以下私有接口必须通过鉴权拦截 ---
        token = self.get_auth_token()
        if not is_authenticated(token):
            self.send_json({"success": False, "message": "未登录或登录已失效，请重新登录！"}, status=401)
            return

        # 3. AI 商业意图与用户提问逆向挖掘 API: /api/intent/generate
        if path == "/api/intent/generate":
            body = self.read_json_body()
            client_name = body.get("client_name", "").strip()
            industry = body.get("industry", "").strip()
            if not client_name or not industry:
                self.send_json({"success": False, "message": "请先输入企业名称与所属行业后再推演！"}, status=400)
                return
            
            from .intent import generate_intent_for_company
            info = {
                "client_name": client_name,
                "brand_name": body.get("brand_name", client_name),
                "industry": industry,
                "slogan": body.get("slogan", "专业、可靠、高效"),
                "founder": body.get("founder", "资深顾问团队"),
                "area_served": body.get("area_served", "全国"),
                "company_profile": body.get("company_profile", "")
            }
            try:
                res = generate_intent_for_company(info)
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "message": f"推演失败: {str(e)}"}, status=500)
            return

        # 4. 创建新项目 API
        if path == "/api/projects":
            body = self.read_json_body()
            client_id = body.get("client_id", "").strip()
            if not client_id:
                client_id = f"client_{int(time.time())}"
            # 客户ID只允许字母数字与下划线，防止路径注入
            import re as _re
            client_id = _re.sub(r"[^a-zA-Z0-9_\-]", "_", client_id)

            client_dir = os.path.join(PROJECTS_DIR, client_id)
            if os.path.exists(client_dir):
                self.send_json({"success": False, "message": f"项目 ID [{client_id}] 已存在！"}, status=400)
                return

            # 从模板初始化
            template_dir = os.path.join(PROJECTS_DIR, "_template")
            shutil.copytree(template_dir, client_dir)

            # 更新 project.yaml（对所有值进行转义防止 YAML 格式破损）
            e = self._yaml_escape
            config_file = os.path.join(client_dir, "project.yaml")
            kw_list = body.get("keywords", [])
            if isinstance(kw_list, str):
                kw_list = [k.strip() for k in kw_list.split("\n") if k.strip()]

            comp_list = body.get("competitors", [])
            if isinstance(comp_list, str):
                comp_list = [c.strip() for c in comp_list.split("\n") if c.strip()]

            cv_list = body.get("core_values", [])
            if isinstance(cv_list, str):
                cv_list = [v.strip() for v in cv_list.split("\n") if v.strip()]

            yaml_content = f"""client_id: "{e(client_id)}"
client_name: "{e(body.get('client_name', '新客户'))}"
official_url: "{e(body.get('official_url', 'https://example.com'))}"
industry: "{e(body.get('industry', '行业待定'))}"
company_profile: "{e(body.get('company_profile', '企业级专业方案'))}"

core_values:
"""
            for cv in (cv_list or ["核心技术优势 1", "核心性能提升 30%"]):
                yaml_content += f"  - \"{e(cv)}\"\n"

            yaml_content += "\nkeywords:\n"
            for kw in (kw_list or ["行业核心推荐词", "好用方案对比"]):
                yaml_content += f"  - \"{e(kw)}\"\n"

            yaml_content += "\ncompetitors:\n"
            for comp in (comp_list or ["竞品A", "竞品B"]):
                yaml_content += f"  - \"{e(comp)}\"\n"

            yaml_content += "\nmodels:\n  - \"deepseek\"\n  - \"doubao\"\n"

            with open(config_file, "w", encoding="utf-8") as f:
                f.write(yaml_content)

            self.send_json({"success": True, "client_id": client_id, "message": f"项目 [{client_id}] 创建成功！"})
            return

        # 5. 素材智能抓取与提纯 API: /api/projects/{id}/ingest/url
        if path.startswith("/api/projects/") and path.endswith("/ingest/url"):
            parts = path.split("/")
            project_id = parts[3]
            body = self.read_json_body()
            target_url = body.get("url", "").strip()
            
            try:
                from .ingest import ingest_project_materials
                res = ingest_project_materials(project_id, url=target_url if target_url else None)
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "message": f"官网抓取提纯失败: {str(e)}"}, status=500)
            return

        # 6. 素材文本补充与提纯 API: /api/projects/{id}/ingest/text
        if path.startswith("/api/projects/") and path.endswith("/ingest/text"):
            parts = path.split("/")
            project_id = parts[3]
            body = self.read_json_body()
            content = body.get("content", "").strip()
            filename = body.get("filename", "custom_material.md").strip()
            
            if not content:
                self.send_json({"success": False, "message": "素材内容不能为空！"}, status=400)
                return

            try:
                from .ingest import ingest_project_materials
                res = ingest_project_materials(project_id, raw_text=content, filename=filename)
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "message": f"素材写入提纯失败: {str(e)}"}, status=500)
            return

        # 7. 生成竞品反向压制策略 API: /api/projects/{id}/defense/generate
        if path.startswith("/api/projects/") and path.endswith("/defense/generate"):
            project_id = path.split("/")[3]
            try:
                from .defense import run_defense
                out_path = run_defense(project_id)
                self.send_json({
                    "success": True,
                    "project_id": project_id,
                    "filename": "06_竞品权威信源反向包抄策略.md",
                    "message": "✅ 竞品反向包抄与精准截流策略生成成功！"
                })
            except Exception as e:
                self.send_json({"success": False, "message": f"策略生成失败: {str(e)}"}, status=500)
            return

        # 8. 触发流水线指定步骤 API: /api/projects/{id}/run/{step}
        if path.startswith("/api/projects/") and "/run/" in path:
            parts = path.split("/")
            # /api/projects/<id>/run/<step>
            project_id = parts[3]
            step = parts[5]

            try:
                msg = ""
                if step == "audit":
                    run_audit(project_id)
                    msg = "阶段 1：现状诊断体检已执行完毕！"
                elif step == "scaffold":
                    run_scaffold(project_id)
                    msg = "阶段 2：站点技术底座改造包已生成！"
                elif step == "rewrite":
                    run_rewrite(project_id)
                    msg = "阶段 3：普林斯顿 9 因子内容重构已完成！"
                elif step == "distribute":
                    run_distribute(project_id)
                    msg = "阶段 4：多平台矩阵借壳分发包已就绪！"
                elif step == "monitor":
                    run_monitor(project_id)
                    msg = "阶段 5：AI 可见度监控与周报已生成！"
                elif step == "pipeline":
                    run_audit(project_id)
                    run_scaffold(project_id)
                    run_rewrite(project_id)
                    run_distribute(project_id)
                    run_monitor(project_id)
                    msg = "🎉 全套 5 步商业交付流水线一键执行完毕！"
                else:
                    self.send_json({"success": False, "message": f"未知步骤: {step}"}, status=400)
                    return

                self.send_json({"success": True, "step": step, "message": msg})
            except Exception as e:
                self.send_json({"success": False, "message": f"执行失败: {str(e)}"}, status=500)
            return

        # 5. 更新原始素材 API: /api/projects/{id}/raw_materials
        if path.startswith("/api/projects/") and path.endswith("/raw_materials"):
            project_id = path.split("/")[3]
            body = self.read_json_body()
            content = body.get("content", "")
            try:
                cfg = load_project_config(project_id)
                raw_file = os.path.join(cfg["_raw_materials_dir"], "custom_product_brief.md")
                with open(raw_file, "w", encoding="utf-8") as f:
                    f.write(content)
                self.send_json({"success": True, "message": "原始素材保存成功！"})
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # 6. 删除项目 API: /api/projects/{id}/delete
        if path.startswith("/api/projects/") and path.endswith("/delete"):
            project_id = path.split("/")[3]
            try:
                target_dir = os.path.join(PROJECTS_DIR, project_id)
                if os.path.exists(target_dir) and project_id != "_template":
                    shutil.rmtree(target_dir)
                    self.send_json({"success": True, "message": f"项目 [{project_id}] 已成功删除！"})
                else:
                    self.send_json({"success": False, "message": "项目不存在或不可删除！"}, status=400)
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        self.send_json({"error": "Not Found"}, status=404)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # 1. 检查鉴权状态 API
        if path == "/api/auth/status":
            token = self.get_auth_token()
            authed = is_authenticated(token)
            user = ACTIVE_SESSIONS.get(token, {}).get("username", "") if authed else ""
            self.send_json({"authenticated": authed, "username": user})
            return

        # 2. 行业对标数据接口 (公开)
        if path == "/api/benchmark/comparison":
            self.send_json({
                "success": True,
                "title": "GEO 工业化流水线 vs 传统手工代运营 对标矩阵",
                "dimensions": [
                    {
                        "dim": "理论与算法认知",
                        "manual": "沿用10年前老套关键词密度、人工发帖矩阵与买外链",
                        "industrial": "深入 RAG 切片分块、Token 压缩、普林斯顿 9 因子、实体三元组",
                        "gain": "范式代差：从搜索引擎到生成式模型"
                    },
                    {
                        "dim": "站点底座改造",
                        "manual": "0 代码研发能力，无法改动客户官网底层代码",
                        "industrial": "一键生成 /llms.txt + JSON-LD + robots.txt 补丁",
                        "gain": "大模型官方实体置信度提升 100%"
                    },
                    {
                        "dim": "内容生产与重构",
                        "manual": "纯人工文案，主观形容词泛滥，无结构化数据与参数表",
                        "industrial": "自动注入量化统计指标、原生 Markdown 对比表与 Q&A 库",
                        "gain": "大模型推荐采纳率提升 +30% ~ +41%"
                    },
                    {
                        "dim": "交付周期",
                        "manual": "3 ~ 7 天/单，严重受限于人工打字与排版速度",
                        "industrial": "< 30 秒一键跑通 5 步全套资产自动化生产",
                        "gain": "生产交付效率提升 95% 以上"
                    },
                    {
                        "dim": "边际交付成本",
                        "manual": "线性极高（接 100 家客户需招募 50 个文案与媒介）",
                        "industrial": "边际成本趋近于 0（单机即可并发交付百家企业）",
                        "gain": "企业采购与维护成本直降 70% ~ 90%"
                    },
                    {
                        "dim": "分发模式与合规",
                        "manual": "纯人工发帖或外挂脚本群发，易触发平台风控封号",
                        "industrial": "半自动化发稿助手：一键生成各平台专属排版 + 直达后台",
                        "gain": "兼顾 10 倍排版人效与 100% 账号合规安全"
                    },
                    {
                        "dim": "监控与归因",
                        "manual": "人工手动搜索截图，容易漏报与虚假造假",
                        "industrial": "自动化 Live Probing 并发探测，捕获真实 Citation 域名",
                        "gain": "数据透明真实，具备商业归因闭环"
                    }
                ]
            })
            return

        # 3. 公共文档与静态资源放行 (供 AI 爬虫或公开阅读)
        if path.startswith("/docs") or path == "/llms.txt":
            # 允许公开爬取
            super().do_GET()
            return

        # 4. 页面路由处理
        if path == "/" or path == "/index.html" or path == "/admin":
            # 返回前端单页应用
            index_path = os.path.join(WEB_DIR, "index.html")
            if os.path.exists(index_path):
                with open(index_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return

        # --- 以下 API 必须通过鉴权拦截 ---
        if path.startswith("/api/"):
            token = self.get_auth_token()
            if not is_authenticated(token):
                self.send_json({"success": False, "message": "未登录或登录已失效，请重新登录！"}, status=401)
                return

            # 分发平台排版预览接口: /api/projects/{id}/distribute/preview
            if "/distribute/preview" in path:
                project_id = path.split("/")[3]
                qs = parse_qs(parsed.query)
                platform = qs.get("platform", ["zhihu"])[0].lower()
                platform_file_map = {
                    "zhihu": ("dist_zhihu_article.md", "markdown"),
                    "toutiao": ("dist_toutiao_article.md", "markdown"),
                    "wechat": ("dist_wechat_article.html", "html"),
                    "github": ("dist_github_README.md", "markdown"),
                    "checklist": ("dist_channels_checklist.md", "markdown")
                }
                if platform not in platform_file_map:
                    self.send_json({"success": False, "message": f"不支持的平台: {platform}"}, status=400)
                    return
                filename, fmt = platform_file_map[platform]
                try:
                    cfg = load_project_config(project_id)
                    out_dir = os.path.realpath(cfg["_outputs_dir"])
                    target_file = os.path.realpath(os.path.join(out_dir, filename))
                    if not os.path.exists(target_file):
                        self.send_json({"success": False, "message": f"分发产物 [{filename}] 尚未生成，请先在 Step 4 点击生成！"}, status=404)
                        return
                    with open(target_file, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    self.send_json({
                        "success": True,
                        "platform": platform,
                        "filename": filename,
                        "format": fmt,
                        "content": content
                    })
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 获取原始素材列表接口: /api/projects/{id}/raw_materials
            if path.startswith("/api/projects/") and path.endswith("/raw_materials"):
                project_id = path.split("/")[3]
                try:
                    cfg = load_project_config(project_id)
                    raw_dir = os.path.join(cfg["_project_dir"], "raw_materials")
                    files = []
                    total_size = 0
                    if os.path.exists(raw_dir):
                        for fname in sorted(os.listdir(raw_dir)):
                            if fname.startswith("."):
                                continue
                            fpath = os.path.join(raw_dir, fname)
                            if os.path.isfile(fpath):
                                sz = os.path.getsize(fpath)
                                total_size += sz
                                files.append({
                                    "name": fname,
                                    "size": sz,
                                    "is_facts": fname == "raw_extracted_facts.md"
                                })
                    self.send_json({
                        "success": True,
                        "project_id": project_id,
                        "files": files,
                        "total_files": len(files),
                        "total_size": total_size
                    })
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 获取监控指标结构化图谱数据: /api/projects/{id}/monitor/metrics
            if path.startswith("/api/projects/") and path.endswith("/monitor/metrics"):
                project_id = path.split("/")[3]
                try:
                    from .monitor import extract_monitor_metrics
                    metrics = extract_monitor_metrics(project_id)
                    self.send_json(metrics)
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 美化版交付周报打印/导出页面: /api/projects/{id}/report/print
            if path.startswith("/api/projects/") and path.endswith("/report/print"):
                project_id = path.split("/")[3]
                try:
                    from .monitor import extract_monitor_metrics
                    metrics = extract_monitor_metrics(project_id)
                    cfg = load_project_config(project_id)
                    out_dir = cfg["_outputs_dir"]
                    
                    rep_file = os.path.join(out_dir, "05_企业AI可见度与声量追踪周报.md")
                    def_file = os.path.join(out_dir, "06_竞品权威信源反向包抄策略.md")
                    
                    rep_text = ""
                    if os.path.exists(rep_file):
                        with open(rep_file, "r", encoding="utf-8", errors="ignore") as f:
                            rep_text = f.read()

                    def_text = ""
                    if os.path.exists(def_file):
                        with open(def_file, "r", encoding="utf-8", errors="ignore") as f:
                            def_text = f.read()

                    client_name = cfg.get("client_name", project_id)
                    industry = cfg.get("industry", "行业数字化")
                    
                    # 渲染精美商用报告 HTML
                    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>GEO 商业交付周报 - {client_name}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <style>
    @media print {{
      .no-print {{ display: none !important; }}
      body {{ background: #fff !important; }}
      .page-break {{ page-break-before: always; }}
    }}
  </style>
</head>
<body class="bg-slate-100 text-slate-800 antialiased font-sans p-6 md:p-12">
  <div class="max-w-4xl mx-auto space-y-6">
    <!-- 顶部操作栏 -->
    <div class="no-print bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
      <div class="text-xs font-semibold text-slate-700">📄 商用标准化交付报告预览</div>
      <button onclick="window.print()" class="py-2 px-5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-lg shadow transition flex items-center gap-1.5">
        <span>🖨️ 打印 / 另存为 PDF</span>
      </button>
    </div>

    <!-- 报告正文卡片 -->
    <div class="bg-white p-10 rounded-2xl shadow-xl border border-slate-200 space-y-8">
      <!-- 报告封面页眉 -->
      <div class="border-b border-slate-200 pb-6 flex items-start justify-between">
        <div>
          <div class="text-xs font-bold text-indigo-600 uppercase tracking-wider mb-1">GEO 生成式引擎优化 · 商业交付评估周报</div>
          <h1 class="text-2xl font-black text-slate-900 leading-tight">{client_name}</h1>
          <p class="text-xs text-slate-500 mt-1">所属领域：{industry} ｜ 评估周期：2026年第35周 ｜ 标准：普林斯顿 9 因子体系</p>
        </div>
        <div class="text-right">
          <span class="inline-block py-1 px-3 bg-emerald-100 text-emerald-800 text-xs font-bold rounded-full">
            SOV 达成率: {metrics['sov_pct']}%
          </span>
          <div class="text-[11px] text-slate-400 mt-1">权威度得分: {metrics['authority_score']}/100</div>
        </div>
      </div>

      <!-- 核心指标摘要 -->
      <div class="grid grid-cols-4 gap-4 text-center">
        <div class="bg-slate-50 p-4 rounded-xl border border-slate-200">
          <div class="text-xs text-slate-500 mb-1">AI 综合推荐率</div>
          <div class="text-xl font-bold text-indigo-600">{metrics['sov_pct']}%</div>
        </div>
        <div class="bg-slate-50 p-4 rounded-xl border border-slate-200">
          <div class="text-xs text-slate-500 mb-1">DeepSeek 首推率</div>
          <div class="text-xl font-bold text-blue-600">{metrics['deepseek_rank_1_pct']}%</div>
        </div>
        <div class="bg-slate-50 p-4 rounded-xl border border-slate-200">
          <div class="text-xs text-slate-500 mb-1">豆包 (字节) 首推率</div>
          <div class="text-xl font-bold text-red-600">{metrics['doubao_rank_1_pct']}%</div>
        </div>
        <div class="bg-slate-50 p-4 rounded-xl border border-slate-200">
          <div class="text-xs text-slate-500 mb-1">权威信源覆盖</div>
          <div class="text-xl font-bold text-emerald-600">4 大平台</div>
        </div>
      </div>

      <!-- 报告 Markdown 渲染区 -->
      <div id="report-markdown-content" class="prose prose-sm max-w-none text-slate-700 leading-relaxed"></div>

      <!-- 竞品包抄策略区 (若存在) -->
      <div id="defense-section" class="border-t border-slate-200 pt-6">
        <div id="defense-markdown-content" class="prose prose-sm max-w-none text-slate-700 leading-relaxed"></div>
      </div>

      <!-- 底部印章区 -->
      <div class="border-t border-slate-200 pt-6 flex items-center justify-between text-xs text-slate-400">
        <div>GEO 生成式引擎优化商业交付中枢 · 技术认证与真实探测留档</div>
        <div class="text-right font-mono">报告生成编号: GEO-{project_id}-20260901</div>
      </div>
    </div>
  </div>

  <script>
    const repRaw = {json.dumps(rep_text)};
    const defRaw = {json.dumps(def_text)};
    document.getElementById('report-markdown-content').innerHTML = marked.parse(repRaw || '# 暂无周报内容');
    if (defRaw) {{
      document.getElementById('defense-markdown-content').innerHTML = marked.parse(defRaw);
    }} else {{
      document.getElementById('defense-section').style.display = 'none';
    }}
  </script>
</body>
</html>"""
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(html.encode("utf-8"))
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 获取项目列表 API
            if path == "/api/projects":
                projects = []
                if os.path.exists(PROJECTS_DIR):
                    for item in os.listdir(PROJECTS_DIR):
                        if item.startswith(".") or item == "_template":
                            continue
                        p_dir = os.path.join(PROJECTS_DIR, item)
                        if os.path.isdir(p_dir):
                            try:
                                cfg = load_project_config(item)
                                out_dir = cfg["_outputs_dir"]
                                outputs = os.listdir(out_dir) if os.path.exists(out_dir) else []
                                
                                # 计算完成步数
                                steps_done = 0
                                if any("01_" in f for f in outputs): steps_done += 1
                                if any("02_" in f for f in outputs) or "llms.txt" in outputs: steps_done += 1
                                if any("03_" in f for f in outputs): steps_done += 1
                                if any("04_" in f for f in outputs): steps_done += 1
                                if any("05_" in f for f in outputs): steps_done += 1

                                projects.append({
                                    "client_id": item,
                                    "client_name": cfg.get("client_name", item),
                                    "official_url": cfg.get("official_url", ""),
                                    "industry": cfg.get("industry", ""),
                                    "keywords_count": len(cfg.get("keywords", [])),
                                    "steps_done": steps_done,
                                    "progress_pct": int((steps_done / 5) * 100),
                                    "outputs_count": len(outputs)
                                })
                            except Exception:
                                pass

                self.send_json({"success": True, "projects": projects})
                return

            # 获取单个项目详情与交付物 API: /api/projects/{id}
            if path.startswith("/api/projects/") and len(path.split("/")) == 4:
                project_id = path.split("/")[3]
                try:
                    cfg = load_project_config(project_id)
                    out_dir = cfg["_outputs_dir"]
                    outputs = []
                    if os.path.exists(out_dir):
                        for f in sorted(os.listdir(out_dir)):
                            if not f.startswith("."):
                                fpath = os.path.join(out_dir, f)
                                if os.path.isfile(fpath):
                                    outputs.append({
                                        "name": f,
                                        "size_bytes": os.path.getsize(fpath)
                                    })

                    # 清理私有路径
                    safe_cfg = {k: v for k, v in cfg.items() if not k.startswith("_")}
                    safe_cfg["outputs"] = outputs
                    self.send_json({"success": True, "project": safe_cfg})
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, status=404)
                return

            # 读取指定交付物文件内容: /api/projects/{id}/output/{filename}
            if path.startswith("/api/projects/") and "/output/" in path:
                parts = path.split("/")
                project_id = parts[3]
                # ⚠️ URL 解码并使用 basename 防止路径穿越攻击（支持中文字符）
                raw_filename = unquote("/".join(parts[5:]))
                filename = os.path.basename(raw_filename)
                try:
                    cfg = load_project_config(project_id)
                    out_dir = os.path.realpath(cfg["_outputs_dir"])
                    target_file = os.path.realpath(os.path.join(out_dir, filename))
                    # 确保解析后路径仍在合法 outputs 目录内
                    if not target_file.startswith(out_dir):
                        self.send_json({"success": False, "message": "非法文件路径！"}, status=403)
                        return
                    if not os.path.exists(target_file):
                        self.send_json({"success": False, "message": "文件不存在！"}, status=404)
                        return
                    with open(target_file, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    self.send_json({"success": True, "filename": filename, "content": content})
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 一键导出打包下载 ZIP: /api/projects/{id}/export
            if path.startswith("/api/projects/") and path.endswith("/export"):
                project_id = path.split("/")[3]
                try:
                    cfg = load_project_config(project_id)
                    out_dir = cfg["_outputs_dir"]
                    
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                        for root, _, files in os.walk(out_dir):
                            for file in files:
                                if not file.startswith("."):
                                    fpath = os.path.join(root, file)
                                    arcname = os.path.relpath(fpath, out_dir)
                                    zip_file.write(fpath, arcname)

                    zip_buffer.seek(0)
                    zip_data = zip_buffer.getvalue()

                    self.send_response(200)
                    self.send_header("Content-Type", "application/zip")
                    self.send_header("Content-Disposition", f"attachment; filename=\"{project_id}_geo_deliverables.zip\"")
                    self.send_header("Content-Length", str(len(zip_data)))
                    self.end_headers()
                    self.wfile.write(zip_data)
                    return
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, status=500)
                    return

        # 默认静态资源兜底
        super().do_GET()

def start_server(port: int = 8080):
    """启动 Web 服务"""
    server_address = ("", port)
    httpd = HTTPServer(server_address, GeoWebHandler)
    
    print_banner("GEO 商业交付 Web 管理端已成功启动")
    print_success(f"管理端地址: http://localhost:{port}")
    print_info(f"管理员账号: {ADMIN_USERNAME}")
    print_info(f"管理员密码: {ADMIN_PASSWORD}")
    print_info("提示：非敏感公开文档与 /llms.txt 支持外部直接抓取；客户商业数据必须登录访问。")
    print_info("按 Ctrl + C 停止服务。\n")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n正在停止服务...")
        httpd.server_close()
        print_success("Web 服务已安全关闭。")

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    start_server(port)
