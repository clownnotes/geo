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
import secrets
import zipfile
import io
import shutil
import threading
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

        # 专属甲方只读沙箱实时测序公开 API: /api/share/{token}/simulate
        if path.startswith("/api/share/") and path.endswith("/simulate"):
            parts = path.split("/")
            share_tok = parts[3]
            from .share import load_shares_data
            data = load_shares_data()
            shares = data.get("shares", {})
            if share_tok not in shares or not shares[share_tok].get("is_active", False):
                self.send_json({"success": False, "message": "分享链接不存在或已失效！"}, status=404)
                return
            rec = shares[share_tok]
            if rec.get("expires_at") and rec["expires_at"] < time.time():
                self.send_json({"success": False, "message": "分享链接已过期！"}, status=403)
                return
            
            body = self.read_json_body()
            if rec.get("has_pin"):
                user_pin = body.get("pin", "")
                salt = rec.get("salt", "")
                if not user_pin or hashlib.sha256((user_pin + salt).encode("utf-8")).hexdigest() != rec.get("pin_hash"):
                    self.send_json({"success": False, "message": "PIN 码不正确或未提供！"}, status=403)
                    return
            
            project_id = rec["project_id"]
            query = body.get("query", "").strip()
            compare = bool(body.get("compare", True))
            from .playground import run_playground_simulation
            try:
                res = run_playground_simulation(project_id, query=query, compare=compare)
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # --- 以下私有接口必须通过鉴权拦截 ---
        token = self.get_auth_token()
        if not is_authenticated(token):
            self.send_json({"success": False, "message": "未登录或登录已失效，请重新登录！"}, status=401)
            return

        # 全域多项目健康巡检 API: /api/portfolio/patrol
        if path == "/api/portfolio/patrol":
            try:
                from .portfolio import run_portfolio_health_patrol
                res = run_portfolio_health_patrol()
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
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

        # 8. 保存通知与告警设置 API: /api/settings/notifications
        if path == "/api/settings/notifications":
            body = self.read_json_body()
            from .patrol import save_notification_settings
            ok = save_notification_settings(body)
            self.send_json({"success": ok, "message": "告警配置已保存！" if ok else "保存失败"})
            return

        # 9. 测试 Webhook 发送 API: /api/settings/notifications/test
        if path == "/api/settings/notifications/test":
            body = self.read_json_body()
            webhook_url = body.get("webhook_url", "").strip()
            webhook_type = body.get("webhook_type", "auto")
            if not webhook_url:
                self.send_json({"success": False, "message": "请先输入 Webhook URL！"}, status=400)
                return
            from .patrol import send_webhook_alert
            fake_metrics = {
                "sov_pct": 58.5,
                "top3_pct": 60.0,
                "prompt_stats": { "hit_count": 26, "intercept_count": 4 }
            }
            ok, msg = send_webhook_alert(
                webhook_url,
                "示例客户企业（演示测试）",
                "这是一条来自 GEO 商业交付中枢的机器人连通性演练测试消息。",
                fake_metrics,
                webhook_type=webhook_type,
                is_test=True
            )
            self.send_json({"success": ok, "message": msg})
            return

        # 10. 手动触发自动化巡检 API: /api/patrol/trigger
        if path == "/api/patrol/trigger":
            body = self.read_json_body()
            target_id = body.get("project_id", "all")
            notify = body.get("notify", True)
            from .patrol import run_patrol_all, run_patrol_project
            try:
                if target_id == "all":
                    def _run_patrol_all():
                        try:
                            run_patrol_all(notify=notify)
                        except Exception as err:
                            print(f"后台全量巡检异常: {err}")

                    threading.Thread(target=_run_patrol_all, daemon=True).start()
                    self.send_json({
                        "success": True,
                        "async": True,
                        "message": "全量巡检任务已在后台启动，完成后可在告警设置中查看最近巡检时间。"
                    })
                else:
                    res = run_patrol_project(target_id, notify=notify)
                    self.send_json({"success": True, "result": res, "message": f"项目 [{target_id}] 巡检完成！"})
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # 11. 触发流水线指定步骤 API: /api/projects/{id}/run/{step}
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

        # 7. 生成专属客户只读分享链接 API: /api/projects/{id}/share/create
        if path.startswith("/api/projects/") and path.endswith("/share/create"):
            project_id = path.split("/")[3]
            body = self.read_json_body()
            expire_days = int(body.get("expire_days", 30))
            pin = body.get("pin", "").strip() or None
            from .share import create_share_link
            host = self.headers.get("Host", "geo.baicl.cc")
            proto = "https" if "baicl.cc" in host else "http"
            base_url = f"{proto}://{host}"
            try:
                res = create_share_link(project_id, expire_days=expire_days, pin=pin, base_url=base_url)
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # 9. 批量并发生产跑批 API: /api/batch/trigger
        if path == "/api/batch/trigger":
            body = self.read_json_body()
            step = body.get("step", "pipeline")
            industry = body.get("industry", "").strip() or None
            target_ids = body.get("target_ids", "all")
            max_workers = int(body.get("max_workers", 4))
            task_id = f"batch_{int(time.time())}_{secrets.token_hex(4)}"
            
            # 计算目标总数
            target_count = 0
            if os.path.exists(PROJECTS_DIR):
                for item in os.listdir(PROJECTS_DIR):
                    if not item.startswith(".") and item != "_template":
                        p_dir = os.path.join(PROJECTS_DIR, item)
                        if os.path.isdir(p_dir):
                            if not industry:
                                target_count += 1
                            else:
                                try:
                                    cfg = load_project_config(item)
                                    if cfg.get("industry") == industry:
                                        target_count += 1
                                except Exception:
                                    pass

            from .benchmark import run_batch_pipeline
            def _run_batch():
                try:
                    run_batch_pipeline(target_ids=target_ids, industry=industry, step=step, max_workers=max_workers)
                except Exception as err:
                    print(f"后台批量生产异常 [{task_id}]: {err}")
            import threading
            threading.Thread(target=_run_batch, daemon=True).start()
            self.send_json({
                "success": True,
                "task_id": task_id,
                "total": target_count,
                "message": f"批量并发任务 [{task_id}] 已在后台启动（目标: {target_count} 个项目 ｜ 阶段: {step} ｜ 并发度: {max_workers}）！"
            })
            return

        # 10. 大模型 Prompt 动态演进与追问词裂变生成 API: /api/projects/{id}/evolution/generate
        if path.startswith("/api/projects/") and path.endswith("/evolution/generate"):
            project_id = path.split("/")[3]
            body = self.read_json_body()
            count = int(body.get("count", 15))
            from .evolution import generate_fission_prompts
            try:
                prompts = generate_fission_prompts(project_id, count=count)
                self.send_json({"success": True, "project_id": project_id, "generated_prompts": prompts})
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # 11. 一键合并裂变新词入库 API: /api/projects/{id}/evolution/apply
        if path.startswith("/api/projects/") and path.endswith("/evolution/apply"):
            project_id = path.split("/")[3]
            body = self.read_json_body()
            new_prompts = body.get("new_prompts", [])
            auto_run = bool(body.get("auto_run_pipeline", False))
            from .evolution import apply_evolved_prompts
            try:
                res = apply_evolved_prompts(project_id, new_prompts, auto_run_pipeline=auto_run)
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # 12. 创建或更新集团矩阵配置 API: /api/groups
        if path == "/api/groups":
            body = self.read_json_body()
            group_id = body.get("group_id", "").strip()
            group_name = body.get("group_name", "").strip()
            parent_id = body.get("parent_project_id", "").strip()
            children = body.get("children", [])
            desc = body.get("description", "").strip()
            if not group_id or not group_name:
                self.send_json({"success": False, "message": "集团 ID 与集团名称不能为空！"}, status=400)
                return
            from .group import save_group_config
            try:
                res = save_group_config(group_id, group_name, parent_id, children, description=desc)
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # 13. 生成或重新生成多模态视觉与短视频资产 API: /api/projects/{id}/visual/generate
        if path.startswith("/api/projects/") and path.endswith("/visual/generate"):
            project_id = path.split("/")[3]
            from .visual import generate_all_visual_assets
            try:
                res = generate_all_visual_assets(project_id)
                self.send_json({"success": True, "project_id": project_id, "message": "多模态视觉资产与短视频脚本已全部生成！", "details": res})
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # 14. 大模型沙箱单条实时测序 API: /api/projects/{id}/playground/simulate
        if path.startswith("/api/projects/") and path.endswith("/playground/simulate"):
            project_id = path.split("/")[3]
            body = self.read_json_body()
            query = body.get("query", "").strip()
            compare = bool(body.get("compare", True))
            from .playground import run_playground_simulation
            try:
                res = run_playground_simulation(project_id, query=query, compare=compare)
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # 15. 大模型沙箱批量并发测序 API: /api/projects/{id}/playground/batch
        if path.startswith("/api/projects/") and path.endswith("/playground/batch"):
            project_id = path.split("/")[3]
            body = self.read_json_body()
            count = int(body.get("count", 5))
            from .playground import run_batch_simulation
            try:
                res = run_batch_simulation(project_id, count=count)
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return
        # 16. 分发外链回填 API: /api/projects/{id}/distribution/record
        if path.startswith("/api/projects/") and path.endswith("/distribution/record"):
            project_id = path.split("/")[3]
            body = self.read_json_body()
            channel = body.get("channel", "").strip()
            url = body.get("url", "").strip()
            verify_now = bool(body.get("verify_now", True))
            from .dist_bot import record_distributed_url
            try:
                res = record_distributed_url(project_id, channel=channel, url=url, verify_now=verify_now)
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # 17. 一键全量核验外链 API: /api/projects/{id}/distribution/verify
        if path.startswith("/api/projects/") and path.endswith("/distribution/verify"):
            project_id = path.split("/")[3]
            from .dist_bot import verify_all_channels
            try:
                res = verify_all_channels(project_id)
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # 18. 保存商业 ROI 参数 API: /api/projects/{id}/roi/settings
        if path.startswith("/api/projects/") and path.endswith("/roi/settings"):
            project_id = path.split("/")[3]
            body = self.read_json_body()
            from .roi import save_roi_settings
            try:
                res = save_roi_settings(project_id, body)
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # 一键生成事实幻觉纠偏与公关反击策略: /api/projects/{id}/guard/repair
        if path.startswith("/api/projects/") and path.endswith("/guard/repair"):
            project_id = path.split("/")[3]
            body = self.read_json_body()
            target_risk_id = body.get("risk_id", "all")
            try:
                from .guard import generate_adversarial_countermeasures
                res = generate_adversarial_countermeasures(project_id, target_risk_id=target_risk_id)
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # 一键触发真实大模型 API 批量并发评测: /api/projects/{id}/eval/run
        if path.startswith("/api/projects/") and path.endswith("/eval/run"):
            project_id = path.split("/")[3]
            body = self.read_json_body()
            models = body.get("models", ["doubao", "deepseek", "yuanbao", "kimi"])
            limit = body.get("limit", 10)
            try:
                from .evaluator import run_live_llm_evaluation
                res = run_live_llm_evaluation(project_id, models=models, limit=limit)
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # 一键生成微信公众号/视频号发稿包: /api/projects/{id}/wechat/build
        if path.startswith("/api/projects/") and path.endswith("/wechat/build"):
            project_id = path.split("/")[3]
            try:
                from .publisher import package_wechat_assets
                res = package_wechat_assets(project_id)
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # 一键生成 DeepSeek / 知乎 / GitHub 技术发稿包: /api/projects/{id}/deepseek/build
        if path.startswith("/api/projects/") and path.endswith("/deepseek/build"):
            project_id = path.split("/")[3]
            try:
                from .publisher import package_deepseek_assets
                res = package_deepseek_assets(project_id)
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # 一键生成 Kimi 研报与百度百科资产包: /api/projects/{id}/kimi_baidu/build
        if path.startswith("/api/projects/") and path.endswith("/kimi_baidu/build"):
            project_id = path.split("/")[3]
            try:
                from .publisher import package_kimi_baidu_assets
                res = package_kimi_baidu_assets(project_id)
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # 智能混合文本批量提取与回填分发外链: /api/projects/{id}/ledger/batch-add
        if path.startswith("/api/projects/") and path.endswith("/ledger/batch-add"):
            project_id = path.split("/")[3]
            try:
                raw_text = data.get("raw_text", "")
                verify_now = data.get("verify_now", True)
                from .dist_bot import batch_backfill_urls
                res = batch_backfill_urls(project_id, raw_text, verify_now=verify_now)
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # 全网并发死链探活审计与存活率重算: /api/projects/{id}/ledger/audit
        if path.startswith("/api/projects/") and path.endswith("/ledger/audit"):
            project_id = path.split("/")[3]
            try:
                from .dist_bot import verify_all_channels
                res = verify_all_channels(project_id)
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # 3 级搜索意图矩阵生成: /api/projects/{id}/intent/generate
        if path.startswith("/api/projects/") and path.endswith("/intent/generate"):
            project_id = path.split("/")[3]
            try:
                from .intent import build_3tier_intent_matrix
                res = build_3tier_intent_matrix(project_id)
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # 3 级搜索意图一键同步至评测词库: /api/projects/{id}/intent/sync-eval
        if path.startswith("/api/projects/") and path.endswith("/intent/sync-eval"):
            project_id = path.split("/")[3]
            tier = data.get("tier", "all") if 'data' in locals() and isinstance(data, dict) else "all"
            try:
                from .intent import sync_intent_keywords_to_eval
                res = sync_intent_keywords_to_eval(project_id, tier=tier)
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # 大模型爬虫抓取仿真 API: /api/crawler/simulate
        if path == "/api/crawler/simulate" or (path.startswith("/api/projects/") and path.endswith("/crawler/simulate")):
            body = self.read_json_body()
            url = body.get("url", "").strip()
            spider = body.get("spider_type", "bytespider").strip()
            if not url:
                self.send_json({"success": False, "message": "请输入要抓取的网页 URL！"}, status=400)
                return
            try:
                from .crawler import simulate_crawler_fetch
                res = simulate_crawler_fetch(url, spider_type=spider)
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # RAG 语义分块切片诊断 API: /api/projects/{id}/rag/diagnose (POST)
        if path.startswith("/api/projects/") and path.endswith("/rag/diagnose"):
            project_id = path.split("/")[3]
            body = self.read_json_body() if self.headers.get("Content-Length") else {}
            custom_text = body.get("text")
            try:
                from .rag_diag import diagnose_rag_chunks
                res = diagnose_rag_chunks(project_id, text_or_file=custom_text)
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # 内容合规审查 API: /api/projects/{id}/compliance/inspect (POST)
        if path.startswith("/api/projects/") and path.endswith("/compliance/inspect"):
            project_id = path.split("/")[3]
            body = self.read_json_body() if self.headers.get("Content-Length") else {}
            custom_text = body.get("text")
            try:
                from .compliance import inspect_content_compliance
                res = inspect_content_compliance(project_id, custom_text=custom_text)
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # 一键智能无损脱敏替换 API: /api/projects/{id}/compliance/sanitize (POST)
        if path.startswith("/api/projects/") and path.endswith("/compliance/sanitize"):
            project_id = path.split("/")[3]
            try:
                from .compliance import sanitize_project_deliverables
                res = sanitize_project_deliverables(project_id)
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # 竞对大模型声量差距逆向与反超沙盘 API: /api/projects/{id}/competitor/gap (POST)
        if path.startswith("/api/projects/") and path.endswith("/competitor/gap"):
            project_id = path.split("/")[3]
            body = self.read_json_body() if self.headers.get("Content-Length") else {}
            comp_name = body.get("competitor_name")
            try:
                from .competitor_gap import analyze_competitor_gap
                res = analyze_competitor_gap(project_id, competitor_name=comp_name)
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # Citation 信源权威度评分与推演 API: /api/projects/{id}/citation/authority (POST)
        if path.startswith("/api/projects/") and path.endswith("/citation/authority"):
            project_id = path.split("/")[3]
            try:
                from .citation_authority import evaluate_project_citation_authority
                res = evaluate_project_citation_authority(project_id)
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # 提示词注入防御与品牌安全隔离 API: /api/projects/{id}/guard/injection (POST)
        if path.startswith("/api/projects/") and path.endswith("/guard/injection"):
            project_id = path.split("/")[3]
            body = self.read_json_body() if self.headers.get("Content-Length") else {}
            custom_text = body.get("text")
            try:
                from .injection_guard import evaluate_project_injection_immunity, scan_content_for_injections
                if custom_text:
                    findings = scan_content_for_injections(custom_text)
                    self.send_json({"success": True, "findings": findings, "count": len(findings)})
                else:
                    res = evaluate_project_injection_immunity(project_id)
                    self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # 普林斯顿 9 因子打分 API: POST /api/princeton/score
        if path == "/api/princeton/score":
            body = self.read_json_body() if self.headers.get("Content-Length") else {}
            text = (body.get("text") or "").strip()
            industry = body.get("industry")
            if not text:
                self.send_json({"success": False, "message": "请先粘贴待测文案！"}, status=400)
                return
            try:
                from .princeton import score_text_princeton_factors
                brand_hints = body.get("brand_hints") or []
                res = score_text_princeton_factors(text, industry=industry, brand_hints=brand_hints)
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # 普林斯顿 9 因子一键重写 API: POST /api/princeton/rewrite
        if path == "/api/princeton/rewrite":
            body = self.read_json_body() if self.headers.get("Content-Length") else {}
            text = (body.get("text") or "").strip()
            project_id = body.get("project_id")
            industry = body.get("industry")
            if not text:
                self.send_json({"success": False, "message": "请先粘贴待重构文案！"}, status=400)
                return
            try:
                from .princeton import rewrite_text_princeton_factors
                res = rewrite_text_princeton_factors(text, project_id=project_id, industry=industry)
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # 普林斯顿全案审计触发 API: POST /api/projects/{id}/princeton/audit
        if path.startswith("/api/projects/") and path.endswith("/princeton/audit"):
            project_id = path.split("/")[3]
            try:
                from .princeton import audit_project_deliverables_princeton
                res = audit_project_deliverables_princeton(project_id)
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # 多大模型实时联网探测与 Citation 溯源触发 API: POST /api/projects/{id}/probing/run
        if path.startswith("/api/projects/") and path.endswith("/probing/run"):
            project_id = path.split("/")[3]
            body = self.read_json_body() if self.headers.get("Content-Length") else {}
            models = body.get("models")
            query_sample_size = body.get("sample_size", 5)
            use_live = body.get("use_live", False)
            try:
                from .probing import run_live_probing
                res = run_live_probing(
                    project_id=project_id,
                    models=models,
                    query_sample_size=int(query_sample_size),
                    use_live=bool(use_live)
                )
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # 19 号声誉排查扫描: POST /api/projects/{id}/sentiment/scan
        if path.startswith("/api/projects/") and path.endswith("/sentiment/scan"):
            project_id = path.split("/")[3]
            body = self.read_json_body() if self.headers.get("Content-Length") else {}
            models = body.get("models")
            use_live = body.get("use_live", False)
            try:
                from .sentiment_guard import audit_negative_sentiment
                res = audit_negative_sentiment(
                    project_id=project_id,
                    models=models,
                    use_live=bool(use_live),
                )
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # 19 号公关压制包: POST /api/projects/{id}/sentiment/suppress
        if path.startswith("/api/projects/") and path.endswith("/sentiment/suppress"):
            project_id = path.split("/")[3]
            try:
                from .sentiment_guard import generate_crisis_suppression_pack
                self.send_json(generate_crisis_suppression_pack(project_id))
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # 20 号衰减追踪: POST /api/projects/{id}/decay/track
        if path.startswith("/api/projects/") and path.endswith("/decay/track"):
            project_id = path.split("/")[3]
            try:
                from .decay_monitor import track_knowledge_decay
                data = self.read_json_body()
                models = data.get("models")
                raw_dt = data.get("delta_days")
                delta_days = float(raw_dt) if (raw_dt is not None and str(raw_dt).strip() != "") else None
                res = track_knowledge_decay(
                    project_id=project_id,
                    models=models,
                    use_live=use_live,
                    delta_days=delta_days
                )
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # 20 号自愈补量包: POST /api/projects/{id}/decay/heal
        if path.startswith("/api/projects/") and path.endswith("/decay/heal"):
            project_id = path.split("/")[3]
            try:
                from .decay_monitor import generate_decay_healing_pack
                self.send_json(generate_decay_healing_pack(project_id))
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # 21 号商业心智审计: POST /api/projects/{id}/mindshare/audit
        if path.startswith("/api/projects/") and path.endswith("/mindshare/audit"):
            project_id = path.split("/")[3]
            try:
                from .mindshare_auditor import audit_mindshare_penetration
                data = self.read_json_body()
                models = data.get("models")
                use_live = bool(data.get("use_live", False))
                cpa_override = data.get("cpa_override")
                if cpa_override is not None:
                    cpa_override = int(cpa_override)
                res = audit_mindshare_penetration(
                    project_id=project_id,
                    models=models,
                    use_live=use_live,
                    cpa_override=cpa_override,
                )
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # 21 号高管汇报包: POST /api/projects/{id}/mindshare/pitch
        if path.startswith("/api/projects/") and path.endswith("/mindshare/pitch"):
            project_id = path.split("/")[3]
            try:
                from .mindshare_auditor import generate_commercial_pitch_pack
                self.send_json(generate_commercial_pitch_pack(project_id))
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # 22 号 RAG 重排演习: POST /api/projects/{id}/rerank/simulate
        if path.startswith("/api/projects/") and path.endswith("/rerank/simulate"):
            project_id = path.split("/")[3]
            try:
                from .rerank_simulator import simulate_rag_rerank_competition
                data = self.read_json_body()
                models = data.get("models")
                use_live = bool(data.get("use_live", False))
                res = simulate_rag_rerank_competition(
                    project_id=project_id,
                    models=models,
                    use_live=use_live,
                )
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # 22 号重排语义强化包: POST /api/projects/{id}/rerank/reinforce
        if path.startswith("/api/projects/") and path.endswith("/rerank/reinforce"):
            project_id = path.split("/")[3]
            try:
                from .rerank_simulator import generate_rerank_reinforcement_pack
                self.send_json(generate_rerank_reinforcement_pack(project_id))
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        self.send_json({"error": "Not Found"}, status=404)

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # 鉴权拦截
        token = self.get_auth_token()
        if not is_authenticated(token):
            self.send_json({"success": False, "message": "未登录或登录已失效，请重新登录！"}, status=401)
            return

        # 作废分享链接 API: /api/share/{token}
        if path.startswith("/api/share/"):
            share_token = path.split("/")[3]
            from .share import revoke_share_link
            ok = revoke_share_link(share_token)
            self.send_json({"success": ok, "message": "分享链接已成功作废！" if ok else "未找到该链接"})
            return

        # 删除客户项目 API: /api/projects/{id}
        if path.startswith("/api/projects/") and len(path.split("/")) == 4:
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

        # 3. 行业大盘宏观基准数据接口: /api/benchmark/industries (公开/管理通用)
        if path == "/api/benchmark/industries":
            from .benchmark import calculate_industry_benchmarks
            b_data = calculate_industry_benchmarks()
            self.send_json(b_data)
            return

        # 4. 公共文档与静态资源放行 (供 AI 爬虫或公开阅读)
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

        # 5. 专属甲方只读交付门户页面路由: /share/{token}
        if path.startswith("/share/"):
            share_path = os.path.join(WEB_DIR, "share.html")
            if os.path.exists(share_path):
                with open(share_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.send_header("X-Robots-Tag", "noindex, nofollow, noarchive")
                self.end_headers()
                self.wfile.write(content)
                return

        # 6. 专属甲方只读沙箱数据公开 API: /api/share/{token}/data
        if path.startswith("/api/share/") and path.endswith("/data"):
            parts = path.split("/")
            share_token = parts[3]
            pin = self.headers.get("X-Share-Pin") or parse_qs(parsed.query).get("pin", [None])[0]
            from .share import get_share_portal_data
            data = get_share_portal_data(share_token, client_pin=pin)
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Robots-Tag", "noindex, nofollow, noarchive")
            self.end_headers()
            self.wfile.write(body)
            return

        # 7. 专属甲方一键打包下载公开 API: /api/share/{token}/download
        if path.startswith("/api/share/") and path.endswith("/download"):
            parts = path.split("/")
            share_token = parts[3]
            pin = self.headers.get("X-Share-Pin") or parse_qs(parsed.query).get("pin", [None])[0]
            from .share import verify_share_access
            ok, status, rec = verify_share_access(share_token, client_pin=pin)
            if not ok:
                self.send_json({"success": False, "message": "该分享链接已失效或提取码未验证"}, status=403)
                return
            project_id = rec["project_id"]
            try:
                cfg = load_project_config(project_id)
                out_dir = os.path.realpath(cfg["_outputs_dir"])
                import io, zipfile
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                    for root, _, files in os.walk(out_dir):
                        for f in files:
                            full_p = os.path.join(root, f)
                            rel_p = os.path.relpath(full_p, out_dir)
                            zf.write(full_p, rel_p)
                zip_bytes = zip_buffer.getvalue()
                fname = f"GEO_Deliverables_{project_id}.zip"
                self.send_response(200)
                self.send_header("Content-Type", "application/zip")
                self.send_header("Content-Disposition", f'attachment; filename="{fname}"')
                self.send_header("Content-Length", str(len(zip_bytes)))
                self.send_header("X-Robots-Tag", "noindex, nofollow, noarchive")
                self.end_headers()
                self.wfile.write(zip_bytes)
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # 8. 专属甲方美化打印周报公开 API: /api/share/{token}/print
        if path.startswith("/api/share/") and path.endswith("/print"):
            parts = path.split("/")
            share_token = parts[3]
            pin = self.headers.get("X-Share-Pin") or parse_qs(parsed.query).get("pin", [None])[0]
            from .share import verify_share_access
            ok, status, rec = verify_share_access(share_token, client_pin=pin)
            if not ok:
                self.send_json({"success": False, "message": "该分享链接已失效或提取码未验证"}, status=403)
                return
            project_id = rec["project_id"]
            try:
                cfg = load_project_config(project_id)
                out_dir = os.path.realpath(cfg["_outputs_dir"])
                report_file = os.path.join(out_dir, "05_企业AI可见度与声量追踪周报.md")
                md_content = "# 暂无周报"
                if os.path.exists(report_file):
                    with open(report_file, "r", encoding="utf-8", errors="ignore") as fp:
                        md_content = fp.read()

                client_name = cfg.get("client_name", project_id)
                html_body = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>《{client_name}》企业 AI 可见度与声量追踪周报</title>
  <meta name="robots" content="noindex, nofollow, noarchive">
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <style>
    @media print {{
      body {{ background: #fff !important; }}
      .no-print {{ display: none !important; }}
      .page-break {{ page-break-before: always; }}
    }}
  </style>
</head>
<body class="bg-slate-100 min-h-screen py-8 text-slate-800 antialiased font-sans">
  <div class="max-w-4xl mx-auto bg-white p-10 sm:p-14 rounded-2xl shadow-xl border border-slate-200 relative">
    <div class="no-print mb-6 flex justify-between items-center bg-indigo-50 p-4 rounded-xl border border-indigo-100 text-xs">
      <span class="font-bold text-indigo-900">📄 商用周报交付视图（支持直接打印或存为 PDF）</span>
      <button onclick="window.print()" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-lg shadow transition">
        🖨️ 立即打印 / 存为 PDF
      </button>
    </div>
    <div id="content" class="prose max-w-none text-sm leading-relaxed"></div>
  </div>
  <script>
    document.getElementById('content').innerHTML = marked.parse({json.dumps(md_content)});
  </script>
</body>
</html>"""
                body_bytes = html_body.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body_bytes)))
                self.send_header("X-Robots-Tag", "noindex, nofollow, noarchive")
                self.end_headers()
                self.wfile.write(body_bytes)
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # 9. 专属甲方查看/打印商业交付结案确认单公开 API: /api/share/{token}/acceptance
        if path.startswith("/api/share/") and path.endswith("/acceptance"):
            parts = path.split("/")
            share_token = parts[3]
            pin = self.headers.get("X-Share-Pin") or parse_qs(parsed.query).get("pin", [None])[0]
            from .share import verify_share_access
            ok, status, rec = verify_share_access(share_token, client_pin=pin)
            if not ok:
                self.send_json({"success": False, "message": "该分享链接已失效或提取码未验证"}, status=403)
                return
            project_id = rec["project_id"]
            try:
                from .acceptance import generate_print_acceptance_html
                html_body = generate_print_acceptance_html(project_id)
                body_bytes = html_body.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body_bytes)))
                self.send_header("X-Robots-Tag", "noindex, nofollow, noarchive")
                self.end_headers()
                self.wfile.write(body_bytes)
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # 专属甲方查看/打印 GEO 商业交付结案证书公开 API: /api/share/{token}/certificate
        if path.startswith("/api/share/") and path.endswith("/certificate"):
            parts = path.split("/")
            share_token = parts[3]
            pin = self.headers.get("X-Share-Pin") or parse_qs(parsed.query).get("pin", [None])[0]
            from .share import verify_share_access
            ok, status, rec = verify_share_access(share_token, client_pin=pin)
            if not ok:
                self.send_json({"success": False, "message": "该分享链接已失效或提取码未验证"}, status=403)
                return
            project_id = rec["project_id"]
            try:
                qs = parse_qs(parsed.query)
                regenerate = qs.get("regenerate", ["0"])[0].lower() in ("1", "true", "yes")
                cert_file = os.path.join(PROJECTS_DIR, project_id, "outputs", "09_GEO全案商业交付结案与数字资产移交证书.html")
                if os.path.exists(cert_file) and not regenerate:
                    with open(cert_file, "r", encoding="utf-8") as cf:
                        html_body = cf.read()
                else:
                    from .certificate import build_delivery_certificate_html
                    html_body = build_delivery_certificate_html(project_id)
                body_bytes = html_body.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body_bytes)))
                self.send_header("X-Robots-Tag", "noindex, nofollow, noarchive")
                self.end_headers()
                self.wfile.write(body_bytes)
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # 10. 专属甲方一键下载全套交付物 ZIP 归档包公开 API: /api/share/{token}/download-zip 或 /archive
        if path.startswith("/api/share/") and (path.endswith("/download-zip") or path.endswith("/archive")):
            parts = path.split("/")
            share_token = parts[3]
            pin = self.headers.get("X-Share-Pin") or parse_qs(parsed.query).get("pin", [None])[0]
            from .share import verify_share_access
            ok, status, rec = verify_share_access(share_token, client_pin=pin)
            if not ok:
                self.send_json({"success": False, "message": "该分享链接已失效或提取码未验证"}, status=403)
                return
            project_id = rec["project_id"]
            try:
                from .acceptance import export_project_archive_zip
                zip_path = export_project_archive_zip(project_id)
                with open(zip_path, "rb") as zf:
                    zip_bytes = zf.read()
                fname = f"GEO_Delivery_Archive_{project_id}.zip"
                self.send_response(200)
                self.send_header("Content-Type", "application/zip")
                self.send_header("Content-Disposition", f'attachment; filename="{fname}"')
                self.send_header("Content-Length", str(len(zip_bytes)))
                self.send_header("X-Robots-Tag", "noindex, nofollow, noarchive")
                self.end_headers()
                self.wfile.write(zip_bytes)
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # 专属甲方读取 16 维单项资产内容公开 API: /api/share/{token}/file?key={key}
        if path.startswith("/api/share/") and path.endswith("/file"):
            parts = path.split("/")
            share_token = parts[3]
            pin = self.headers.get("X-Share-Pin") or parse_qs(parsed.query).get("pin", [None])[0]
            req_key = parse_qs(parsed.query).get("key", ["acceptance"])[0]

            from .share import get_share_single_file_content
            file_res = get_share_single_file_content(share_token, req_key, client_pin=pin)
            if not file_res.get("success"):
                self.send_json(file_res, status=file_res.get("status", 400))
                return
            self.send_json(file_res)
            return

        # 11. 专属甲方全屏放映商业 Pitch Deck 幻灯片公开 API: /api/share/{token}/pitch/slides
        if path.startswith("/api/share/") and path.endswith("/pitch/slides"):
            parts = path.split("/")
            share_token = parts[3]
            pin = self.headers.get("X-Share-Pin") or parse_qs(parsed.query).get("pin", [None])[0]
            from .share import verify_share_access
            ok, status, rec = verify_share_access(share_token, client_pin=pin)
            if not ok:
                self.send_json({"success": False, "message": "该分享链接已失效或提取码未验证"}, status=403)
                return
            project_id = rec["project_id"]
            try:
                from .pitch import generate_pitch_presentation_html
                html_body = generate_pitch_presentation_html(project_id)
                body_bytes = html_body.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body_bytes)))
                self.send_header("X-Robots-Tag", "noindex, nofollow, noarchive")
                self.end_headers()
                self.wfile.write(body_bytes)
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # 12. 专属甲方商业投标建议书 A4 打印公开 API: /api/share/{token}/pitch/print
        if path.startswith("/api/share/") and path.endswith("/pitch/print"):
            parts = path.split("/")
            share_token = parts[3]
            pin = self.headers.get("X-Share-Pin") or parse_qs(parsed.query).get("pin", [None])[0]
            from .share import verify_share_access
            ok, status, rec = verify_share_access(share_token, client_pin=pin)
            if not ok:
                self.send_json({"success": False, "message": "该分享链接已失效或提取码未验证"}, status=403)
                return
            project_id = rec["project_id"]
            try:
                from .pitch import generate_print_pitch_html
                html_body = generate_print_pitch_html(project_id)
                body_bytes = html_body.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body_bytes)))
                self.send_header("X-Robots-Tag", "noindex, nofollow, noarchive")
                self.end_headers()
                self.wfile.write(body_bytes)
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # 13. 专属甲方知识图谱数据公开 API: /api/share/{token}/graph/data
        if path.startswith("/api/share/") and path.endswith("/graph/data"):
            parts = path.split("/")
            share_token = parts[3]
            pin = self.headers.get("X-Share-Pin") or parse_qs(parsed.query).get("pin", [None])[0]
            from .share import verify_share_access
            ok, status, rec = verify_share_access(share_token, client_pin=pin)
            if not ok:
                self.send_json({"success": False, "message": "该分享链接已失效或提取码未验证"}, status=403)
                return
            project_id = rec["project_id"]
            try:
                from .graph import build_entity_knowledge_graph
                res = build_entity_knowledge_graph(project_id)
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # 14. 专属甲方知识图谱 SVG 矢量图公开 API: /api/share/{token}/graph/svg
        if path.startswith("/api/share/") and path.endswith("/graph/svg"):
            parts = path.split("/")
            share_token = parts[3]
            pin = self.headers.get("X-Share-Pin") or parse_qs(parsed.query).get("pin", [None])[0]
            from .share import verify_share_access
            ok, status, rec = verify_share_access(share_token, client_pin=pin)
            if not ok:
                self.send_json({"success": False, "message": "该分享链接已失效或提取码未验证"}, status=403)
                return
            project_id = rec["project_id"]
            try:
                from .graph import generate_graph_svg
                svg_content = generate_graph_svg(project_id)
                body_bytes = svg_content.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "image/svg+xml; charset=utf-8")
                self.send_header("Content-Length", str(len(body_bytes)))
                self.send_header("X-Robots-Tag", "noindex, nofollow, noarchive")
                self.end_headers()
                self.wfile.write(body_bytes)
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # 15. 专属甲方知识图谱多跳子图检索公开 API: /api/share/{token}/graph/query
        if path.startswith("/api/share/") and path.endswith("/graph/query"):
            parts = path.split("/")
            share_token = parts[3]
            pin = self.headers.get("X-Share-Pin") or parse_qs(parsed.query).get("pin", [None])[0]
            from .share import verify_share_access
            ok, status, rec = verify_share_access(share_token, client_pin=pin)
            if not ok:
                self.send_json({"success": False, "message": "该分享链接已失效或提取码未验证"}, status=403)
                return
            project_id = rec["project_id"]
            kw = parse_qs(parsed.query).get("q", [""])[0] or parse_qs(parsed.query).get("keyword", [""])[0]
            try:
                from .graph import query_entity_subgraph
                res = query_entity_subgraph(project_id, kw)
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # 16. 专属甲方品牌幻觉风险清单公开 API: /api/share/{token}/guard/risks
        if path.startswith("/api/share/") and path.endswith("/guard/risks"):
            parts = path.split("/")
            share_token = parts[3]
            pin = self.headers.get("X-Share-Pin") or parse_qs(parsed.query).get("pin", [None])[0]
            from .share import verify_share_access
            ok, status, rec = verify_share_access(share_token, client_pin=pin)
            if not ok:
                self.send_json({"success": False, "message": "该分享链接已失效或提取码未验证"}, status=403)
                return
            project_id = rec["project_id"]
            try:
                from .guard import detect_factual_hallucinations
                res = detect_factual_hallucinations(project_id)
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # 17. 专属甲方幻觉修复前后沙箱推演公开 API: /api/share/{token}/guard/simulation
        if path.startswith("/api/share/") and path.endswith("/guard/simulation"):
            parts = path.split("/")
            share_token = parts[3]
            pin = self.headers.get("X-Share-Pin") or parse_qs(parsed.query).get("pin", [None])[0]
            from .share import verify_share_access
            ok, status, rec = verify_share_access(share_token, client_pin=pin)
            if not ok:
                self.send_json({"success": False, "message": "该分享链接已失效或提取码未验证"}, status=403)
                return
            project_id = rec["project_id"]
            risk_id = parse_qs(parsed.query).get("risk_id", [None])[0]
            try:
                from .guard import simulate_guard_repair_effect
                res = simulate_guard_repair_effect(project_id, risk_id=risk_id)
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
            return

        # --- 以下 API 必须通过鉴权拦截 ---
        if path.startswith("/api/"):
            token = self.get_auth_token()
            if not is_authenticated(token):
                self.send_json({"success": False, "message": "未登录或登录已失效，请重新登录！"}, status=401)
                return

            # 全域多项目商业大盘概览: /api/portfolio/summary
            if path == "/api/portfolio/summary":
                try:
                    from .portfolio import get_portfolio_summary
                    summary = get_portfolio_summary()
                    self.send_json(summary)
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 全域多项目大盘执行报告: /api/portfolio/report
            if path == "/api/portfolio/report":
                try:
                    from .portfolio import generate_portfolio_executive_report
                    rep = generate_portfolio_executive_report()
                    self.send_json(rep)
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 查询项目分享链接列表: /api/projects/{id}/share/info
            if path.startswith("/api/projects/") and path.endswith("/share/info"):
                project_id = path.split("/")[3]
                from .share import list_project_shares
            # 查询项目 3 级搜索意图矩阵: /api/projects/{id}/intent/matrix
            if path.startswith("/api/projects/") and path.endswith("/intent/matrix"):
                project_id = path.split("/")[3]
                try:
                    out_file = os.path.join(PROJECTS_DIR, project_id, "outputs", "keywords_intent_matrix.json")
                    if os.path.exists(out_file):
                        with open(out_file, "r", encoding="utf-8") as f:
                            idata = json.load(f)
                        self.send_json(idata)
                    else:
                        from .intent import build_3tier_intent_matrix
                        res = build_3tier_intent_matrix(project_id)
                        self.send_json(res)
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, status=500)
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

            # 获取通知与告警设置 API: /api/settings/notifications
            if path == "/api/settings/notifications":
                from .patrol import load_notification_settings
                settings = load_notification_settings()
                self.send_json({"success": True, "settings": settings})
                return

            # 获取项目历史巡检时序数据: /api/projects/{id}/history
            if path.startswith("/api/projects/") and path.endswith("/history"):
                project_id = path.split("/")[3]
                try:
                    from .patrol import get_project_history
                    records = get_project_history(project_id, limit=12)
                    self.send_json({"success": True, "project_id": project_id, "history": records})
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 获取客户在所属行业的对标战绩与差距报告: /api/projects/{id}/benchmark
            if path.startswith("/api/projects/") and path.endswith("/benchmark"):
                project_id = path.split("/")[3]
                try:
                    from .benchmark import evaluate_project_against_benchmark
                    report = evaluate_project_against_benchmark(project_id)
                    self.send_json(report)
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 获取词库生命周期健康度评估与快速裂变分析: /api/projects/{id}/evolution/analyze
            if path.startswith("/api/projects/") and path.endswith("/evolution/analyze"):
                project_id = path.split("/")[3]
                try:
                    from .evolution import analyze_prompt_portfolio
                    analysis = analyze_prompt_portfolio(project_id)
                    self.send_json(analysis)
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 获取所有集团矩阵配置列表: /api/groups
            if path == "/api/groups":
                from .group import load_groups_config
                cfg = load_groups_config()
                self.send_json({"success": True, "groups": list(cfg.get("groups", {}).values())})
                return

            # 获取指定集团的综合协同大盘与矩阵声量: /api/groups/{id}/matrix
            if path.startswith("/api/groups/") and path.endswith("/matrix"):
                group_id = path.split("/")[3]
                from .group import calculate_group_matrix
                try:
                    matrix = calculate_group_matrix(group_id)
                    self.send_json(matrix)
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 获取指定项目的多模态视觉资产与视频脚本: /api/projects/{id}/visual/assets
            if path.startswith("/api/projects/") and path.endswith("/visual/assets"):
                project_id = path.split("/")[3]
                from .visual import get_visual_assets
                try:
                    assets = get_visual_assets(project_id)
                    self.send_json(assets)
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

            # 获取分发渠道台账与收录状态: /api/projects/{id}/distribution/ledger
            if path.startswith("/api/projects/") and path.endswith("/distribution/ledger"):
                project_id = path.split("/")[3]
                from .dist_bot import get_distribution_ledger
                try:
                    ledger = get_distribution_ledger(project_id)
                    self.send_json(ledger)
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 获取渠道富文本剪贴板内容: /api/projects/{id}/distribution/rich-content/{channel}
            if path.startswith("/api/projects/") and "/distribution/rich-content/" in path:
                parts = path.split("/")
                project_id = parts[3]
                channel = parts[6] if len(parts) > 6 else ""
                from .dist_bot import format_rich_text_copy
                try:
                    res = format_rich_text_copy(project_id, channel)
                    self.send_json(res)
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, status=500)
            # 获取今日头条富文本长文预览接口: /api/projects/{id}/toutiao/preview
            if path.startswith("/api/projects/") and path.endswith("/toutiao/preview"):
                project_id = path.split("/")[3]
                from .publisher import build_toutiao_article_html
                try:
                    html_content = build_toutiao_article_html(project_id)
                    self.send_json({"success": True, "project_id": project_id, "html": html_content})
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 一键复制富文本接口: /api/projects/{id}/toutiao/copy
            if path.startswith("/api/projects/") and path.endswith("/toutiao/copy"):
                project_id = path.split("/")[3]
                from .publisher import get_toutiao_rich_html_for_clipboard
                try:
                    res = get_toutiao_rich_html_for_clipboard(project_id)
                    self.send_json(res)
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 获取微头条 150 字三维短动态接口: /api/projects/{id}/toutiao/micro
            if path.startswith("/api/projects/") and path.endswith("/toutiao/micro"):
                project_id = path.split("/")[3]
                from .publisher import build_toutiao_micro_post
                try:
                    micro_res = build_toutiao_micro_post(project_id)
                    self.send_json({"success": True, "project_id": project_id, "data": micro_res})
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 获取微信公众号原生内联富文本长文接口: /api/projects/{id}/wechat/preview
            if path.startswith("/api/projects/") and path.endswith("/wechat/preview"):
                project_id = path.split("/")[3]
                from .publisher import build_wechat_article_html
                try:
                    html_content = build_wechat_article_html(project_id)
                    self.send_json({"success": True, "project_id": project_id, "html": html_content})
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 一键复制微信富文本接口: /api/projects/{id}/wechat/copy
            if path.startswith("/api/projects/") and path.endswith("/wechat/copy"):
                project_id = path.split("/")[3]
                from .publisher import get_wechat_rich_html_for_clipboard
                try:
                    res = get_wechat_rich_html_for_clipboard(project_id)
                    self.send_json(res)
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 获取微信视频号 60 秒口播脚本与分镜表接口: /api/projects/{id}/wechat/video
            if path.startswith("/api/projects/") and path.endswith("/wechat/video"):
                project_id = path.split("/")[3]
                from .publisher import build_wechat_video_script
                try:
                    video_res = build_wechat_video_script(project_id)
                    self.send_json({"success": True, "project_id": project_id, "data": video_res})
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 获取 DeepSeek GitHub README 接口: /api/projects/{id}/deepseek/readme
            if path.startswith("/api/projects/") and path.endswith("/deepseek/readme"):
                project_id = path.split("/")[3]
                from .publisher import build_deepseek_github_readme
                try:
                    content = build_deepseek_github_readme(project_id)
                    self.send_json({"success": True, "project_id": project_id, "content": content})
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 获取 DeepSeek 知乎深度专栏评测长文接口: /api/projects/{id}/deepseek/zhihu
            if path.startswith("/api/projects/") and path.endswith("/deepseek/zhihu"):
                project_id = path.split("/")[3]
                from .publisher import build_deepseek_zhihu_article
                try:
                    content = build_deepseek_zhihu_article(project_id)
                    self.send_json({"success": True, "project_id": project_id, "content": content})
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 获取 DeepSeek 极简高信息密度知识底座: /api/projects/{id}/deepseek/llms
            if path.startswith("/api/projects/") and path.endswith("/deepseek/llms"):
                project_id = path.split("/")[3]
                from .publisher import build_deepseek_token_optimized_llms
                try:
                    content = build_deepseek_token_optimized_llms(project_id)
                    self.send_json({"success": True, "project_id": project_id, "content": content})
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 获取 Kimi 深度选型白皮书: /api/projects/{id}/kimi/whitepaper
            if path.startswith("/api/projects/") and path.endswith("/kimi/whitepaper"):
                project_id = path.split("/")[3]
                from .publisher import build_kimi_research_whitepaper
                try:
                    content = build_kimi_research_whitepaper(project_id)
                    self.send_json({"success": True, "project_id": project_id, "content": content})
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 获取百度百科词条草案: /api/projects/{id}/baidu/baike
            if path.startswith("/api/projects/") and path.endswith("/baidu/baike"):
                project_id = path.split("/")[3]
                from .publisher import build_baidu_baike_entry
                try:
                    content = build_baidu_baike_entry(project_id)
                    self.send_json({"success": True, "project_id": project_id, "content": content})
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 获取百度文库/知道 Q&A 对: /api/projects/{id}/baidu/qa
            if path.startswith("/api/projects/") and path.endswith("/baidu/qa"):
                project_id = path.split("/")[3]
                from .publisher import build_baidu_wenku_qa_pairs
                try:
                    content = build_baidu_wenku_qa_pairs(project_id)
                    self.send_json({"success": True, "project_id": project_id, "content": content})
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 获取分发台账执行大盘与存活汇总: /api/projects/{id}/ledger/summary
            if path.startswith("/api/projects/") and path.endswith("/ledger/summary"):
                project_id = path.split("/")[3]
                from .dist_bot import get_distribution_ledger
                try:
                    res = get_distribution_ledger(project_id)
                    self.send_json(res)
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 获取商业 ROI 测算与续约预测: /api/projects/{id}/roi/calculate
            if path.startswith("/api/projects/") and path.endswith("/roi/calculate"):
                project_id = path.split("/")[3]
                from .roi import calculate_project_roi
                try:
                    res = calculate_project_roi(project_id)
                    self.send_json(res)
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 获取真实大模型 API 评测报告: /api/projects/{id}/eval/report
            if path.startswith("/api/projects/") and path.endswith("/eval/report"):
                project_id = path.split("/")[3]
                r_path = os.path.join(PROJECTS_DIR, project_id, "outputs", "06_大模型真实API评测与Citation捕获报告.json")
                if os.path.exists(r_path):
                    try:
                        with open(r_path, "r", encoding="utf-8") as f:
                            self.send_json(json.load(f))
                    except Exception as e:
                        self.send_json({"success": False, "message": str(e)}, status=500)
                else:
                    self.send_json({
                        "success": False,
                        "message": "评测报告尚未生成，请先通过 POST /api/projects/{id}/eval/run 发起评测",
                        "hint": "use_post_eval_run"
                    }, status=404)
                return

            # 获取项目商业交付结案确认单数据: /api/projects/{id}/acceptance/data
            if path.startswith("/api/projects/") and path.endswith("/acceptance/data"):
                project_id = path.split("/")[3]
                from .acceptance import get_acceptance_data
                try:
                    res = get_acceptance_data(project_id)
                    self.send_json(res)
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 打印/导出盖章级商业结案验收单 HTML: /api/projects/{id}/acceptance/print
            if path.startswith("/api/projects/") and path.endswith("/acceptance/print"):
                project_id = path.split("/")[3]
                try:
                    from .acceptance import generate_print_acceptance_html
                    html_body = generate_print_acceptance_html(project_id)
                    body_bytes = html_body.encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(body_bytes)))
                    self.send_header("X-Robots-Tag", "noindex, nofollow, noarchive")
                    self.end_headers()
                    self.wfile.write(body_bytes)
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 查看/打印商业交付结案与数字资产移交证书 HTML: /api/projects/{id}/certificate
            if path.startswith("/api/projects/") and path.endswith("/certificate"):
                project_id = path.split("/")[3]
                try:
                    qs = parse_qs(parsed.query)
                    regenerate = qs.get("regenerate", ["0"])[0].lower() in ("1", "true", "yes")
                    cert_file = os.path.join(PROJECTS_DIR, project_id, "outputs", "09_GEO全案商业交付结案与数字资产移交证书.html")
                    if os.path.exists(cert_file) and not regenerate:
                        with open(cert_file, "r", encoding="utf-8") as cf:
                            html_body = cf.read()
                    else:
                        from .certificate import build_delivery_certificate_html
                        html_body = build_delivery_certificate_html(project_id)
                    body_bytes = html_body.encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(body_bytes)))
                    self.send_header("X-Robots-Tag", "noindex, nofollow, noarchive")
                    self.end_headers()
                    self.wfile.write(body_bytes)
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 一键下载全套交付物 ZIP 归档包: /api/projects/{id}/acceptance/download-zip
            if path.startswith("/api/projects/") and path.endswith("/acceptance/download-zip"):
                project_id = path.split("/")[3]
                try:
                    from .acceptance import export_project_archive_zip
                    zip_path = export_project_archive_zip(project_id)
                    with open(zip_path, "rb") as zf:
                        zip_bytes = zf.read()
                    fname = f"GEO_Delivery_Archive_{project_id}.zip"
                    self.send_response(200)
                    self.send_header("Content-Type", "application/zip")
                    self.send_header("Content-Disposition", f'attachment; filename="{fname}"')
                    self.send_header("Content-Length", str(len(zip_bytes)))
                    self.send_header("X-Robots-Tag", "noindex, nofollow, noarchive")
                    self.end_headers()
                    self.wfile.write(zip_bytes)
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 获取售前全案商业投标建议书数据: /api/projects/{id}/pitch/data
            if path.startswith("/api/projects/") and path.endswith("/pitch/data"):
                project_id = path.split("/")[3]
                from .pitch import get_pitch_data
                try:
                    res = get_pitch_data(project_id)
                    self.send_json(res)
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 全屏交互式售前 Pitch Deck 演示幻灯片: /api/projects/{id}/pitch/slides
            if path.startswith("/api/projects/") and path.endswith("/pitch/slides"):
                project_id = path.split("/")[3]
                try:
                    from .pitch import generate_pitch_presentation_html
                    html_body = generate_pitch_presentation_html(project_id)
                    body_bytes = html_body.encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(body_bytes)))
                    self.send_header("X-Robots-Tag", "noindex, nofollow, noarchive")
                    self.end_headers()
                    self.wfile.write(body_bytes)
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 商业投标建议书 A4 纸排版打印: /api/projects/{id}/pitch/print
            if path.startswith("/api/projects/") and path.endswith("/pitch/print"):
                project_id = path.split("/")[3]
                try:
                    from .pitch import generate_print_pitch_html
                    html_body = generate_print_pitch_html(project_id)
                    body_bytes = html_body.encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(body_bytes)))
                    self.send_header("X-Robots-Tag", "noindex, nofollow, noarchive")
                    self.end_headers()
                    self.wfile.write(body_bytes)
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 获取企业行业实体知识图谱数据: /api/projects/{id}/graph/data
            if path.startswith("/api/projects/") and path.endswith("/graph/data"):
                project_id = path.split("/")[3]
                from .graph import build_entity_knowledge_graph
                try:
                    res = build_entity_knowledge_graph(project_id)
                    self.send_json(res)
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 获取实体知识图谱高清矢量 SVG 图: /api/projects/{id}/graph/svg
            if path.startswith("/api/projects/") and path.endswith("/graph/svg"):
                project_id = path.split("/")[3]
                try:
                    from .graph import generate_graph_svg
                    svg_content = generate_graph_svg(project_id)
                    body_bytes = svg_content.encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "image/svg+xml; charset=utf-8")
                    self.send_header("Content-Length", str(len(body_bytes)))
                    self.send_header("X-Robots-Tag", "noindex, nofollow, noarchive")
                    self.end_headers()
                    self.wfile.write(body_bytes)
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 知识图谱多跳子图推理检索: /api/projects/{id}/graph/query
            if path.startswith("/api/projects/") and path.endswith("/graph/query"):
                project_id = path.split("/")[3]
                kw = parse_qs(parsed.query).get("q", [""])[0] or parse_qs(parsed.query).get("keyword", [""])[0]
                try:
                    from .graph import query_entity_subgraph
                    res = query_entity_subgraph(project_id, kw)
                    self.send_json(res)
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 大模型事实幻觉与虚假负面风险检测: /api/projects/{id}/guard/risks
            if path.startswith("/api/projects/") and path.endswith("/guard/risks"):
                project_id = path.split("/")[3]
                try:
                    from .guard import detect_factual_hallucinations
                    res = detect_factual_hallucinations(project_id)
                    self.send_json(res)
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 事实幻觉修复前后沙箱对决推演: /api/projects/{id}/guard/simulation
            if path.startswith("/api/projects/") and path.endswith("/guard/simulation"):
                project_id = path.split("/")[3]
                risk_id = parse_qs(parsed.query).get("risk_id", [None])[0]
                try:
                    from .guard import simulate_guard_repair_effect
                    res = simulate_guard_repair_effect(project_id, risk_id=risk_id)
                    self.send_json(res)
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
            # 获取 RAG 语义分块切片诊断数据: /api/projects/{id}/rag/diagnose (GET)
            if path.startswith("/api/projects/") and path.endswith("/rag/diagnose"):
                project_id = path.split("/")[3]
                diag_file = os.path.join(PROJECTS_DIR, project_id, "outputs", "rag_chunks_diagnostic.json")
                if os.path.exists(diag_file):
                    try:
                        with open(diag_file, "r", encoding="utf-8") as f:
                            self.send_json(json.load(f))
                    except Exception as e:
                        self.send_json({"success": False, "message": str(e)}, status=500)
                else:
                    try:
                        from .rag_diag import diagnose_rag_chunks
                        res = diagnose_rag_chunks(project_id)
                        self.send_json(res)
                    except Exception as e:
                        self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 获取内容合规与广告法风控审查数据: /api/projects/{id}/compliance/inspect (GET)
            if path.startswith("/api/projects/") and path.endswith("/compliance/inspect"):
                project_id = path.split("/")[3]
                comp_file = os.path.join(PROJECTS_DIR, project_id, "outputs", "compliance_inspection.json")
                if os.path.exists(comp_file):
                    try:
                        with open(comp_file, "r", encoding="utf-8") as f:
                            self.send_json(json.load(f))
                    except Exception as e:
                        self.send_json({"success": False, "message": str(e)}, status=500)
                else:
                    try:
                        from .compliance import inspect_content_compliance
                        res = inspect_content_compliance(project_id)
                        self.send_json(res)
                    except Exception as e:
                        self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 获取竞对大模型声量差距逆向与反超沙盘数据: /api/projects/{id}/competitor/gap (GET)
            if path.startswith("/api/projects/") and path.endswith("/competitor/gap"):
                project_id = path.split("/")[3]
                gap_file = os.path.join(PROJECTS_DIR, project_id, "outputs", "competitor_gap_analysis.json")
                if os.path.exists(gap_file):
                    try:
                        with open(gap_file, "r", encoding="utf-8") as f:
                            self.send_json(json.load(f))
                    except Exception as e:
                        self.send_json({"success": False, "message": str(e)}, status=500)
                else:
                    try:
                        from .competitor_gap import analyze_competitor_gap
                        res = analyze_competitor_gap(project_id)
                        self.send_json(res)
                    except Exception as e:
                        self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 获取大模型 Citation 信源权威度与外链信任度数据: /api/projects/{id}/citation/authority (GET)
            if path.startswith("/api/projects/") and path.endswith("/citation/authority"):
                project_id = path.split("/")[3]
                auth_file = os.path.join(PROJECTS_DIR, project_id, "outputs", "citation_authority_matrix.json")
                if os.path.exists(auth_file):
                    try:
                        with open(auth_file, "r", encoding="utf-8") as f:
                            self.send_json(json.load(f))
                    except Exception as e:
                        self.send_json({"success": False, "message": str(e)}, status=500)
                else:
                    try:
                        from .citation_authority import evaluate_project_citation_authority
                        res = evaluate_project_citation_authority(project_id)
                        self.send_json(res)
                    except Exception as e:
                        self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 获取提示词注入防御与品牌安全隔离数据: /api/projects/{id}/guard/injection (GET)
            if path.startswith("/api/projects/") and path.endswith("/guard/injection"):
                project_id = path.split("/")[3]
                guard_file = os.path.join(PROJECTS_DIR, project_id, "outputs", "prompt_injection_guard.json")
                if os.path.exists(guard_file):
                    try:
                        with open(guard_file, "r", encoding="utf-8") as f:
                            self.send_json(json.load(f))
                    except Exception as e:
                        self.send_json({"success": False, "message": str(e)}, status=500)
                else:
                    try:
                        from .injection_guard import evaluate_project_injection_immunity
                        res = evaluate_project_injection_immunity(project_id)
                        self.send_json(res)
                    except Exception as e:
                        self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 获取普林斯顿 9 因子全案质检报告: /api/projects/{id}/princeton/audit (GET)
            if path.startswith("/api/projects/") and path.endswith("/princeton/audit"):
                project_id = path.split("/")[3]
                audit_file = os.path.join(PROJECTS_DIR, project_id, "outputs", "princeton_audit.json")
                if os.path.exists(audit_file):
                    try:
                        with open(audit_file, "r", encoding="utf-8") as f:
                            self.send_json(json.load(f))
                    except Exception as e:
                        self.send_json({"success": False, "message": str(e)}, status=500)
                else:
                    try:
                        from .princeton import audit_project_deliverables_princeton
                        res = audit_project_deliverables_princeton(project_id)
                        self.send_json(res)
                    except Exception as e:
                        self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 获取实时探测状态与摘要: /api/projects/{id}/probing/status (GET)
            if path.startswith("/api/projects/") and path.endswith("/probing/status"):
                project_id = path.split("/")[3]
                trace_file = os.path.join(PROJECTS_DIR, project_id, "outputs", "live_probing_trace.json")
                if os.path.exists(trace_file):
                    try:
                        with open(trace_file, "r", encoding="utf-8") as f:
                            self.send_json(json.load(f))
                    except Exception as e:
                        self.send_json({"success": False, "message": str(e)}, status=500)
                else:
                    self.send_json({
                        "success": True,
                        "project_id": project_id,
                        "has_probed": False,
                        "message": "尚未执行实时探测，点击【立即启动探测】开始"
                    })
                return

            # 获取 18 号 Citation 对账公文报告: /api/projects/{id}/probing/report (GET)
            if path.startswith("/api/projects/") and path.endswith("/probing/report"):
                project_id = path.split("/")[3]
                report_file = os.path.join(PROJECTS_DIR, project_id, "outputs", "18_大模型实时联网探测与Citation信源溯源对账报告.md")
                if os.path.exists(report_file):
                    try:
                        with open(report_file, "r", encoding="utf-8") as f:
                            content = f.read()
                        self.send_json({
                            "success": True,
                            "project_id": project_id,
                            "filename": "18_大模型实时联网探测与Citation信源溯源对账报告.md",
                            "content": content
                        })
                    except Exception as e:
                        self.send_json({"success": False, "message": str(e)}, status=500)
                else:
                    try:
                        from .probing import run_live_probing
                        r = run_live_probing(project_id, query_sample_size=3, use_live=False)
                        with open(r["report_path"], "r", encoding="utf-8") as f:
                            content = f.read()
                        self.send_json({
                            "success": True,
                            "project_id": project_id,
                            "filename": "18_大模型实时联网探测与Citation信源溯源对账报告.md",
                            "content": content
                        })
                    except Exception as e:
                        self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 19 号声誉状态: GET /api/projects/{id}/sentiment/status
            if path.startswith("/api/projects/") and path.endswith("/sentiment/status"):
                project_id = path.split("/")[3]
                try:
                    from .sentiment_guard import get_sentiment_status
                    self.send_json(get_sentiment_status(project_id))
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 19 号公关报告: GET /api/projects/{id}/sentiment/report（无文件 404，禁止自动 scan）
            if path.startswith("/api/projects/") and path.endswith("/sentiment/report"):
                project_id = path.split("/")[3]
                report_file = os.path.join(
                    PROJECTS_DIR, project_id, "outputs",
                    "19_大模型品牌负面联想排查与声誉危机清洗压制公关报告.md",
                )
                if not os.path.exists(report_file):
                    self.send_json({
                        "success": False,
                        "message": "19 号报告尚未生成，请先 POST /sentiment/scan",
                    }, status=404)
                    return
                try:
                    with open(report_file, "r", encoding="utf-8") as f:
                        content = f.read()
                    self.send_json({
                        "success": True,
                        "project_id": project_id,
                        "filename": "19_大模型品牌负面联想排查与声誉危机清洗压制公关报告.md",
                        "content": content,
                    })
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 20 号知识衰减状态: GET /api/projects/{id}/decay/status
            if path.startswith("/api/projects/") and path.endswith("/decay/status"):
                project_id = path.split("/")[3]
                try:
                    from .decay_monitor import get_decay_status
                    self.send_json(get_decay_status(project_id))
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 20 号衰减公关报告: GET /api/projects/{id}/decay/report（无文件 404，禁止自动后台计算）
            if path.startswith("/api/projects/") and path.endswith("/decay/report"):
                project_id = path.split("/")[3]
                report_file = os.path.join(
                    PROJECTS_DIR, project_id, "outputs",
                    "20_大模型知识半衰期衰减监测与长效留存自愈报告.md",
                )
                if not os.path.exists(report_file):
                    self.send_json({
                        "success": False,
                        "message": "20 号报告尚未生成，请先 POST /decay/track",
                    }, status=404)
                    return
                try:
                    with open(report_file, "r", encoding="utf-8") as f:
                        content = f.read()
                    self.send_json({
                        "success": True,
                        "project_id": project_id,
                        "filename": "20_大模型知识半衰期衰减监测与长效留存自愈报告.md",
                        "content": content,
                    })
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 21 号商业心智渗透审计状态: GET /api/projects/{id}/mindshare/status
            if path.startswith("/api/projects/") and path.endswith("/mindshare/status"):
                project_id = path.split("/")[3]
                try:
                    from .mindshare_auditor import get_mindshare_status
                    self.send_json(get_mindshare_status(project_id))
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 21 号商业心智报告获取: GET /api/projects/{id}/mindshare/report
            if path.startswith("/api/projects/") and path.endswith("/mindshare/report"):
                project_id = path.split("/")[3]
                report_file = os.path.join(
                    PROJECT_ROOT, "projects", project_id, "outputs",
                    "21_大模型品牌商业心智渗透率与商业转化价值审计公文报告.md"
                )
                if not os.path.exists(report_file):
                    self.send_json({
                        "success": False,
                        "message": "21 号报告尚未生成，请先 POST /mindshare/audit",
                    }, status=404)
                    return
                try:
                    with open(report_file, "r", encoding="utf-8") as f:
                        content = f.read()
                    self.send_json({
                        "success": True,
                        "project_id": project_id,
                        "filename": "21_大模型品牌商业心智渗透率与商业转化价值审计公文报告.md",
                        "content": content,
                    })
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 22 号 RAG 重排演习状态: GET /api/projects/{id}/rerank/status
            if path.startswith("/api/projects/") and path.endswith("/rerank/status"):
                project_id = path.split("/")[3]
                try:
                    from .rerank_simulator import get_rerank_status
                    self.send_json(get_rerank_status(project_id))
                except Exception as e:
                    self.send_json({"success": False, "message": str(e)}, status=500)
                return

            # 22 号 RAG 重排演习报告获取: GET /api/projects/{id}/rerank/report
            if path.startswith("/api/projects/") and path.endswith("/rerank/report"):
                project_id = path.split("/")[3]
                report_file = os.path.join(
                    PROJECT_ROOT, "projects", project_id, "outputs",
                    "22_跨大模型RAG混合检索召回与重排序挤占演习报告.md"
                )
                if not os.path.exists(report_file):
                    self.send_json({
                        "success": False,
                        "message": "22 号报告尚未生成，请先 POST /rerank/simulate",
                    }, status=404)
                    return
                try:
                    with open(report_file, "r", encoding="utf-8") as f:
                        content = f.read()
                    self.send_json({
                        "success": True,
                        "project_id": project_id,
                        "filename": "22_跨大模型RAG混合检索召回与重排序挤占演习报告.md",
                        "content": content,
                    })
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
