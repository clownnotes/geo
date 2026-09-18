# -*- coding: utf-8 -*-
"""
小毛驴统一知识库 (KB) 与素材上传 (Uploads) 客户端
// [2026-09-18] [接入小毛驴统一API] 复用小毛驴 KB 与 community/uploads 能力包，禁止 GEO 重复自建
"""

import os
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

from .auth_sso import DEFAULT_NEXTDOOR_BASE_URL, DEFAULT_SOURCE_CLIENT


class NextdoorKBClient:
    """小毛驴知识库与公共素材上传客户端"""

    def __init__(self, base_url: str = None, source_client: str = None):
        self.base_url = (base_url or os.getenv("NEXTDOOR_BASE_URL") or DEFAULT_NEXTDOOR_BASE_URL).rstrip("/")
        self.source_client = source_client or os.getenv("NEXTDOOR_SOURCE_CLIENT") or DEFAULT_SOURCE_CLIENT

    def _make_headers(self, token: str = "", content_type: str = "application/json") -> dict:
        headers = {
            "Content-Type": content_type,
            "vio-source-client": self.source_client,
            "Accept": "application/json",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}" if not token.startswith("Bearer ") else token
        return headers

    def upload_file(self, token: str, file_bytes: bytes, filename: str, content_type: str = "application/octet-stream") -> Dict[str, Any]:
        """
        调用小毛驴公共上传接口 (POST /api/v1/community/uploads)
        构造 multipart/form-data 协议上传图片或资料
        """
        boundary = "----NextdoorGeoBoundary" + str(int(os.getpid()))
        target_url = f"{self.base_url}/api/v1/community/uploads"

        # 组装 multipart 数据
        body = []
        body.append(f"--{boundary}".encode("utf-8"))
        body.append(f'Content-Disposition: form-data; name="file"; filename="{filename}"'.encode("utf-8"))
        body.append(f"Content-Type: {content_type}\r\n".encode("utf-8"))
        body.append(file_bytes)
        body.append(f"\r\n--{boundary}--\r\n".encode("utf-8"))
        payload = b"\r\n".join(body[:-1]) + body[-1]

        headers = self._make_headers(token, content_type=f"multipart/form-data; boundary={boundary}")
        headers["Content-Length"] = str(len(payload))

        req = urllib.request.Request(target_url, data=payload, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            try:
                return json.loads(err_body)
            except Exception:
                return {"code": e.code, "msg": f"上游上传服务异常: {err_body}", "data": None}
        except Exception as ex:
            return {"code": 502, "msg": f"连接上传服务失败: {str(ex)}", "data": None}

    def add_document(
        self,
        token: str,
        title: str,
        content: str,
        doc_type: str = "markdown",
        project_id: str = "",
    ) -> Dict[str, Any]:
        """
        调用小毛驴文档入库 (POST /api/kb/documents)
        """
        target_url = f"{self.base_url}/api/kb/documents"
        payload = {
            "title": title,
            "content": content,
            "doc_type": doc_type,
            "project_id": project_id,
        }
        data_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = self._make_headers(token, content_type="application/json")

        req = urllib.request.Request(target_url, data=data_bytes, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            try:
                return json.loads(err_body)
            except Exception:
                return {"code": e.code, "msg": f"上游知识库异常: {err_body}", "data": None}
        except Exception as ex:
            return {"code": 502, "msg": f"连接知识库服务失败: {str(ex)}", "data": None}

    def chat_kb(
        self,
        token: str,
        query: str,
        project_id: str = "",
        history: list = None,
    ) -> Dict[str, Any]:
        """
        调用小毛驴知识库问答 (POST /api/kb/chat)
        """
        target_url = f"{self.base_url}/api/kb/chat"
        payload = {
            "query": query,
            "project_id": project_id,
            "history": history or [],
        }
        data_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = self._make_headers(token, content_type="application/json")

        req = urllib.request.Request(target_url, data=data_bytes, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            try:
                return json.loads(err_body)
            except Exception:
                return {"code": e.code, "msg": f"上游知识库异常: {err_body}", "data": None}
        except Exception as ex:
            return {"code": 502, "msg": f"连接知识库问答失败: {str(ex)}", "data": None}


_DEFAULT_KB_CLIENT = NextdoorKBClient()


def get_kb_client() -> NextdoorKBClient:
    return _DEFAULT_KB_CLIENT
