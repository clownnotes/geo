# -*- coding: utf-8 -*-
"""
GEO Web 集中式项目与资产 API 集成测试
// [2026-09-18] [接入小毛驴统一API] 覆盖阶段 3、4、5：
// 1. 项目 CRUD + 雪花 ID + 创建者/成员溯源
// 2. 报告列表与 POST .../bundles ZIP 下载
// 3. 异步任务派发与 SSE 事件流
// 4. 项目在线更新与安全归档
"""

import os
import io
import json
import time
import zipfile
import threading
import unittest
import urllib.request
import urllib.error
from http.server import ThreadingHTTPServer

from tools.geo.server import GeoWebHandler, create_session, ACTIVE_SESSIONS
from tools.geo.utils import PROJECTS_DIR


class TestProjectsV1Api(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # 启动测试 HTTP 服务在临时端口
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), GeoWebHandler)
        cls.port = cls.server.server_address[1]
        cls.base_url = f"http://127.0.0.1:{cls.port}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

        # 创建有效登录态
        cls.token = create_session(
            username="测试产品经理",
            user_id="1768892187321049888",
            phone="13150568888",
            role="developer",
            credits=5000,
        )
        cls.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {cls.token}",
        }
        cls.test_slug = f"test_proj_{int(time.time())}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        # 清理测试可能生成的目录
        test_dir = os.path.join(PROJECTS_DIR, cls.test_slug)
        if os.path.exists(test_dir):
            import shutil
            shutil.rmtree(test_dir, ignore_errors=True)

    def _request(self, method: str, path: str, body: dict = None, custom_headers: dict = None):
        url = f"{self.base_url}{path}"
        data = json.dumps(body).encode("utf-8") if body is not None else None
        headers = dict(self.headers)
        if custom_headers:
            headers.update(custom_headers)

        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                raw = resp.read()
                ctype = resp.headers.get("Content-Type", "")
                if "application/zip" in ctype:
                    return resp.status, raw, resp.headers
                return resp.status, json.loads(raw.decode("utf-8")), resp.headers
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", errors="ignore")
            try:
                return e.code, json.loads(raw), e.headers
            except Exception:
                return e.code, {"raw": raw}, e.headers

    def test_01_create_project_with_snowflake_and_creator(self):
        """测试 3.1: 创建项目分配雪花 ID，并记录责任人"""
        payload = {
            "client_id": self.test_slug,
            "client_name": "测试协同企业",
            "official_url": "https://test-company.com",
            "industry": "工业物联网",
            "business_one_liner": "高精度工业网关与边缘智能计算设备源头厂家",
            "keywords": ["工业物联网网关", "边缘计算盒子"],
            "competitors": ["研华科技", "映翰通"],
        }
        status, res, _ = self._request("POST", "/api/v1/projects", body=payload)
        self.assertEqual(status, 200)
        self.assertEqual(res.get("code"), 0)
        self.assertEqual(res.get("project_slug"), self.test_slug)

        # 核心契约断言：雪花 ID 必须为纯数字字符串，禁止自增数字
        snowflake_id = res.get("id")
        self.assertIsInstance(snowflake_id, str)
        self.assertTrue(snowflake_id.isdigit())
        self.assertGreater(len(snowflake_id), 12)

        # 责任人溯源断言
        self.assertEqual(res.get("creator_user_id"), "1768892187321049888")
        self.assertEqual(res.get("creator_name"), "测试产品经理")

    def test_02_get_projects_list(self):
        """测试 3.1: 获取项目列表包含雪花 ID 与责任人"""
        status, res, _ = self._request("GET", "/api/v1/projects")
        self.assertEqual(status, 200)
        self.assertEqual(res.get("code"), 0)
        projects = res.get("data", [])
        self.assertIsInstance(projects, list)

        # 找到刚创建的项目
        target = next((p for p in projects if p.get("project_slug") == self.test_slug), None)
        self.assertIsNotNone(target)
        self.assertTrue(target.get("id").isdigit())
        self.assertEqual(target.get("creator_user_id"), "1768892187321049888")
        self.assertTrue(target.get("can_edit"))

    def test_03_get_project_detail_and_config(self):
        """测试 3.2: 映射宿主机 projects/{slug} 并在线读取 project.yaml"""
        status, res, _ = self._request("GET", f"/api/v1/projects/{self.test_slug}")
        self.assertEqual(status, 200)
        data = res.get("data", {})
        self.assertEqual(data.get("project_slug"), self.test_slug)
        self.assertEqual(data.get("client_name"), "测试协同企业")
        self.assertIn("config_raw", data)
        self.assertIn("client_id:", data["config_raw"])

    def test_04_put_project_update(self):
        """测试 3.2: 在线更新 project.yaml，防覆盖与备份"""
        update_payload = {
            "client_name": "测试协同企业（已升级）",
            "business_one_liner": "高精度工业网关与边缘智能计算设备领先服务商",
            "keywords": ["工业物联网网关", "边缘计算盒子", "AIoT平台"],
        }
        status, res, _ = self._request("PUT", f"/api/v1/projects/{self.test_slug}", body=update_payload)
        self.assertEqual(status, 200)
        self.assertEqual(res.get("code"), 0)

        # 验证读取最新内容
        _, detail, _ = self._request("GET", f"/api/v1/projects/{self.test_slug}")
        self.assertEqual(detail["data"]["client_name"], "测试协同企业（已升级）")

    def test_05_reports_and_bundle_zip(self):
        """测试 3.3: 报告列表查询与 POST .../bundles 打包下载（路径无动词）"""
        # 在 outputs 目录下伪造一个交付文件
        out_dir = os.path.join(PROJECTS_DIR, self.test_slug, "outputs")
        os.makedirs(out_dir, exist_ok=True)
        sample_file = os.path.join(out_dir, "01_商业体检报告.md")
        with open(sample_file, "w", encoding="utf-8") as f:
            f.write("# 诊断体检报告\n得分：88分")

        # 1. 查询报告列表
        status, res, _ = self._request("GET", f"/api/v1/projects/{self.test_slug}/reports")
        self.assertEqual(status, 200)
        reports = res.get("data", [])
        self.assertTrue(any(r["filename"] == "01_商业体检报告.md" for r in reports))

        # 2. POST .../bundles 一键打包下载
        status, zip_bytes, headers = self._request("POST", f"/api/v1/projects/{self.test_slug}/bundles")
        self.assertEqual(status, 200)
        self.assertIn("application/zip", headers.get("Content-Type", ""))

        # 验证 ZIP 内容完好
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            names = zf.namelist()
            self.assertIn("01_商业体检报告.md", names)

    def test_06_async_task_and_sse_events(self):
        """测试 4.1 ~ 4.3: 异步任务调度与 SSE 流式事件推送"""
        task_payload = {
            "task_type": "test_echo",
            "params": {"message": "API集成测试任务", "sleep": 0.05}
        }
        status, res, _ = self._request("POST", f"/api/v1/projects/{self.test_slug}/tasks", body=task_payload)
        self.assertEqual(status, 200)
        task_data = res.get("data", {})
        task_id = task_data.get("id")
        self.assertIsNotNone(task_id)

        # 验证查询单任务
        status, qres, _ = self._request("GET", f"/api/v1/tasks/{task_id}")
        self.assertEqual(status, 200)
        self.assertEqual(qres["data"]["id"], task_id)

        # 验证 SSE 事件流推送
        sse_url = f"{self.base_url}/api/v1/tasks/{task_id}/events"
        req = urllib.request.Request(sse_url, headers=self.headers, method="GET")
        with urllib.request.urlopen(req, timeout=10) as sse_resp:
            chunks = []
            for _ in range(10):
                line = sse_resp.readline().decode("utf-8")
                if not line:
                    break
                chunks.append(line)
                if '"event": "done"' in line:
                    break

        full_stream = "".join(chunks)
        self.assertIn("data: ", full_stream)
        self.assertIn('"event": "status"', full_stream)

    def test_07_safe_archive_project(self):
        """测试 3.1: 规范 RESTful DELETE 安全归档项目"""
        status, res, _ = self._request("DELETE", f"/api/v1/projects/{self.test_slug}")
        self.assertEqual(status, 200)
        self.assertEqual(res.get("code"), 0)

        # 原目录已不存在（已移入归档）
        orig_dir = os.path.join(PROJECTS_DIR, self.test_slug)
        self.assertFalse(os.path.exists(orig_dir))

        # 清理归档目录
        archived_name = res["data"]["archived_as"]
        archived_path = os.path.join(PROJECTS_DIR, archived_name)
        if os.path.exists(archived_path):
            import shutil
            shutil.rmtree(archived_path, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
