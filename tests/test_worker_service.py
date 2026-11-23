# -*- coding: utf-8 -*-
"""
自动化测试：GEO 后厂无状态异步 Worker 服务契约与安全门禁 (tests/test_worker_service.py)
覆盖 9 类合法任务状态机流转、凭证拦截、路径穿越防御、MySQL DSN 拒绝与 0.0.0.0 绑定禁止。
"""

import os
import json
import time
import urllib.request
import urllib.error
import threading
import unittest

from tools.worker.app import create_server, validate_bind_host
from tools.worker.auth import ENV_INTERNAL_TOKEN, HEADER_INTERNAL_TOKEN
from tools.worker.store import get_job_store, VALID_JOB_TYPES

TEST_TOKEN = "geo-worker-test-token-20261123"


class TestWorkerService(unittest.TestCase):
    """Worker 服务端到端接口与安全自动化测试集"""

    @classmethod
    def setUpClass(cls):
        cls._orig_token = os.environ.get(ENV_INTERNAL_TOKEN)
        os.environ[ENV_INTERNAL_TOKEN] = TEST_TOKEN

        # 启动绑定到 127.0.0.1 临时随机端口的真实 HTTP 服务
        cls.server = create_server(host="127.0.0.1", port=0)
        cls.port = cls.server.server_address[1]
        cls.base_url = f"http://127.0.0.1:{cls.port}"

        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        if cls._orig_token is not None:
            os.environ[ENV_INTERNAL_TOKEN] = cls._orig_token
        else:
            os.environ.pop(ENV_INTERNAL_TOKEN, None)

    def _request(self, method: str, path: str, body: dict = None, headers: dict = None) -> tuple[int, dict]:
        """统一辅助请求函数"""
        url = f"{self.base_url}{path}"
        req_headers = {"Content-Type": "application/json"}
        if headers:
            req_headers.update(headers)

        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(url, data=data, headers=req_headers, method=method)

        try:
            with urllib.request.urlopen(req) as resp:
                status = resp.status
                payload = json.loads(resp.read().decode("utf-8"))
                return status, payload
        except urllib.error.HTTPError as err:
            err_body = {}
            try:
                err_body = json.loads(err.read().decode("utf-8"))
            except Exception:
                pass
            return err.code, err_body

    def test_01_health_check(self):
        """测试 GET /health 探活接口"""
        status, res = self._request("GET", "/health")
        self.assertEqual(status, 200)
        self.assertEqual(res.get("status"), "ok")
        self.assertEqual(res.get("service"), "geo-worker")

    def test_02_auth_negative_scenarios(self):
        """反向用例：缺失 Token、错误 Token 与 Bearer 请求头统一返回 401"""
        valid_body = {"job_type": "build_blog", "project_id": "demo_corp"}

        # 1. 缺凭据
        status, res = self._request("POST", "/worker/jobs", body=valid_body)
        self.assertEqual(status, 401)
        self.assertIn("error", res)

        # 2. 错误凭据
        status, res = self._request(
            "POST",
            "/worker/jobs",
            body=valid_body,
            headers={HEADER_INTERNAL_TOKEN: "wrong-token"},
        )
        self.assertEqual(status, 401)

        # 3. 违规使用 Authorization: Bearer
        status, res = self._request(
            "POST",
            "/worker/jobs",
            body=valid_body,
            headers={"Authorization": f"Bearer {TEST_TOKEN}"},
        )
        self.assertEqual(status, 401)
        self.assertIn("Authorization Bearer", res.get("error", ""))

    def test_03_invalid_parameters_negative_scenarios(self):
        """反向用例：非法 job_type、缺失参数或非法路径穿越返回 400"""
        auth_hdr = {HEADER_INTERNAL_TOKEN: TEST_TOKEN}

        # 1. 非法任务类型
        status, res = self._request(
            "POST",
            "/worker/jobs",
            body={"job_type": "invalid_job", "project_id": "demo_corp"},
            headers=auth_hdr,
        )
        self.assertEqual(status, 400)
        self.assertIn("Invalid or missing job_type", res.get("error", ""))

        # 2. 缺失 project_id
        status, res = self._request(
            "POST",
            "/worker/jobs",
            body={"job_type": "diagnose"},
            headers=auth_hdr,
        )
        self.assertEqual(status, 400)

        # 3. project_id 路径穿越攻击
        for bad_id in ["../demo_corp", "demo/corp", "demo\\corp", ""]:
            status, res = self._request(
                "POST",
                "/worker/jobs",
                body={"job_type": "diagnose", "project_id": bad_id},
                headers=auth_hdr,
            )
            self.assertEqual(status, 400, f"Expected 400 for bad project_id: {bad_id}")

    def test_04_job_not_found_negative(self):
        """反向用例：查询不存在的 job_id 返回 404"""
        status, res = self._request(
            "GET",
            "/worker/jobs/job_non_existent_99999",
            headers={HEADER_INTERNAL_TOKEN: TEST_TOKEN},
        )
        self.assertEqual(status, 404)
        self.assertIn("Job not found", res.get("error", ""))

    def test_05_illegal_mysql_dsn_injection_negative(self):
        """反向用例：显式注入 MySQL DSN 断言立即拒绝并返回 400"""
        auth_hdr = {HEADER_INTERNAL_TOKEN: TEST_TOKEN}
        payload = {
            "job_type": "diagnose",
            "project_id": "demo_corp",
            "params": {
                "dsn": "mysql://root:secret@Leishen-DB:3306/nextdoor",
            },
        }
        status, res = self._request("POST", "/worker/jobs", body=payload, headers=auth_hdr)
        self.assertEqual(status, 400)
        self.assertIn("MySQL parameter detected", res.get("error", ""))

    def test_06_bind_wildcard_forbidden_negative(self):
        """反向用例：尝试绑定 0.0.0.0 启动断言拒绝报错"""
        with self.assertRaises(ValueError) as ctx:
            validate_bind_host("0.0.0.0")
        self.assertIn("0.0.0.0", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx2:
            create_server(host="0.0.0.0", port=18092)
        self.assertIn("0.0.0.0", str(ctx2.exception))

    def _poll_job_until_done(self, job_id: str, timeout_sec: float = 10.0) -> dict:
        """轮询任务直到完成或超时"""
        deadline = time.time() + timeout_sec
        auth_hdr = {HEADER_INTERNAL_TOKEN: TEST_TOKEN}
        while time.time() < deadline:
            status, res = self._request("GET", f"/worker/jobs/{job_id}", headers=auth_hdr)
            self.assertEqual(status, 200)
            job_status = res.get("status")
            self.assertIn(job_status, ["queued", "running", "succeeded", "failed"])
            if job_status in ("succeeded", "failed"):
                return res
            time.sleep(0.05)
        self.fail(f"Job {job_id} did not finish within {timeout_sec}s")

    def test_07_nine_job_types_full_lifecycle_positive(self):
        """正向用例：9 类合法 job_type 提交返 202 并轮询验证状态机与 outputs 产物"""
        auth_hdr = {HEADER_INTERNAL_TOKEN: TEST_TOKEN}
        self.assertEqual(len(VALID_JOB_TYPES), 9)

        job_configs = {
            "diagnose": {"mode": "full"},
            "probe": {"use_live": False, "query_sample_size": 2},
            "build_site": {},
            "build_blog": {"mode": "incremental"},
            "boss_report": {},
            "share_portal": {"expire_days": 7},
            "distribute_pack": {},
            "acceptance_report": {},
            "pitch_roi": {"target_tier": "starter"},
        }

        for jtype, params in job_configs.items():
            # 1. 提交任务
            submit_body = {
                "job_type": jtype,
                "project_id": "demo_corp",
                "params": params,
            }
            status, res = self._request("POST", "/worker/jobs", body=submit_body, headers=auth_hdr)
            self.assertEqual(status, 202, f"Expected 202 for job_type={jtype}, got {status}")
            self.assertIn("job_id", res)
            self.assertEqual(res.get("status"), "queued")

            # 2. 轮询至完成
            job_id = res["job_id"]
            final_job = self._poll_job_until_done(job_id)
            self.assertEqual(
                final_job.get("status"),
                "succeeded",
                f"Job {jtype} failed with: {final_job.get('error_message')}",
            )

            # 3. 产物校验：所有产物必须严格落在 demo_corp/outputs/ 下
            output_paths = final_job.get("output_paths", [])
            for p in output_paths:
                self.assertIn("projects/demo_corp/outputs", p)
                self.assertFalse(p.endswith(".zip"), "Strict Rule: No ZIP deliverable allowed!")

            # 4. 专项断言
            if jtype == "acceptance_report":
                filenames = [os.path.basename(p) for p in output_paths]
                self.assertIn("00_GEO商业交付验收结案确认单.md", filenames)
                self.assertIn("09_GEO全案商业交付结案与数字资产移交证书.html", filenames)
                self.assertNotIn("demo_corp_geo_delivery_archive.zip", filenames)

    def test_08_job_failure_transparent_error_propagation(self):
        """反向用例：任务内部执行异常完整透传至 error_message 并置 status 为 failed"""
        auth_hdr = {HEADER_INTERNAL_TOKEN: TEST_TOKEN}
        # 使用合法格式但磁盘不存在的项目 ID，会抛出 FileNotFoundError
        submit_body = {
            "job_type": "build_site",
            "project_id": "non_existent_project_999",
            "params": {},
        }
        status, res = self._request("POST", "/worker/jobs", body=submit_body, headers=auth_hdr)
        self.assertEqual(status, 202)
        job_id = res["job_id"]

        final_job = self._poll_job_until_done(job_id)
        self.assertEqual(final_job.get("status"), "failed")
        err_msg = final_job.get("error_message") or ""
        self.assertIn("FileNotFoundError", err_msg)
        self.assertIn("non_existent_project_999", err_msg)

