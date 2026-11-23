# -*- coding: utf-8 -*-
"""
GEO Worker 核心 HTTP 服务模块 (tools/worker/app.py)
仅允许监听 127.0.0.1 回环地址，严格拒绝 0.0.0.0。
提供 /health、POST /worker/jobs 与 GET /worker/jobs/{job_id}。
"""

import json
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from typing import Tuple
from tools.worker.auth import verify_auth
from tools.worker.store import (
    get_job_store,
    validate_project_id,
    check_no_mysql_dsn,
    VALID_JOB_TYPES,
)
from tools.worker.runner import get_worker_runner

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 18092


def validate_bind_host(host: str) -> str:
    """严格校验绑定地址，绝对禁止绑定 0.0.0.0。"""
    cleaned = (host or "").strip()
    if cleaned in ("0.0.0.0", "::", ""):
        raise ValueError("Security Violation: GEO Worker is strictly forbidden from binding to 0.0.0.0 or any public wildcard.")
    return cleaned


class WorkerHTTPHandler(BaseHTTPRequestHandler):
    """Worker 请求分发处理器"""

    def send_json(self, status: int, data: dict) -> None:
        """输出 JSON 格式响应"""
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def read_json_body(self) -> Tuple[bool, dict, str]:
        """读取并解析请求体 JSON"""
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length <= 0:
                return False, {}, "Request body is empty"
            raw = self.rfile.read(length).decode("utf-8")
            return True, json.loads(raw), ""
        except Exception as exc:
            return False, {}, f"Invalid JSON body: {str(exc)}"

    def do_GET(self) -> None:
        """处理 GET 路由"""
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        if path == "/health":
            self.send_json(200, {"status": "ok", "service": "geo-worker"})
            return

        if path.startswith("/worker/jobs/"):
            job_id = path[len("/worker/jobs/"):]
            self.handle_get_job(job_id)
            return

        self.send_json(404, {"error": "Not Found"})

    def handle_get_job(self, job_id: str) -> None:
        """处理任务查询"""
        ok, msg, code = verify_auth(self.headers)
        if not ok:
            self.send_json(code, {"error": msg})
            return

        job = get_job_store().get_job(job_id)
        if not job:
            self.send_json(404, {"error": f"Job not found: {job_id}"})
            return

        self.send_json(200, job.to_dict())

    def do_POST(self) -> None:
        """处理 POST 路由"""
        parsed = urlparse(self.path)
        if parsed.path.rstrip("/") != "/worker/jobs":
            self.send_json(404, {"error": "Not Found"})
            return

        ok, msg, code = verify_auth(self.headers)
        if not ok:
            self.send_json(code, {"error": msg})
            return

        success, body, err = self.read_json_body()
        if not success:
            self.send_json(400, {"error": err})
            return

        self.handle_create_job(body)

    def handle_create_job(self, body: dict) -> None:
        """校验并创建异步任务"""
        job_type = body.get("job_type")
        project_id = body.get("project_id")
        params = body.get("params") or {}

        if not job_type or job_type not in VALID_JOB_TYPES:
            self.send_json(400, {"error": f"Invalid or missing job_type: '{job_type}'"})
            return

        try:
            validate_project_id(project_id)
            check_no_mysql_dsn(body)
        except ValueError as val_err:
            self.send_json(400, {"error": str(val_err)})
            return

        store = get_job_store()
        job = store.create_job(project_id=project_id, job_type=job_type, params=params)
        get_worker_runner().submit(job.job_id)

        self.send_json(202, {"job_id": job.job_id, "status": "queued"})


def create_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> ThreadingHTTPServer:
    """构建 Worker HTTP 服务实例"""
    valid_host = validate_bind_host(host)
    server = ThreadingHTTPServer((valid_host, port), WorkerHTTPHandler)
    server.daemon_threads = True
    return server
