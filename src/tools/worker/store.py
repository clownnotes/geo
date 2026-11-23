# -*- coding: utf-8 -*-
"""
GEO Worker 内存任务存储与安全路径校验模块 (tools/worker/store.py)
无状态、线程安全、绝对不连 MySQL、输出路径严格锁死在 projects/{id}/outputs/。
"""

import os
import re
import time
import uuid
import threading
from typing import Dict, Any, List, Optional
from tools.geo.utils import PROJECTS_DIR

VALID_JOB_TYPES = {
    "diagnose",
    "probe",
    "build_site",
    "build_blog",
    "boss_report",
    "share_portal",
    "distribute_pack",
    "acceptance_report",
    "pitch_roi",
}

PROJECT_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-]+$")
FORBIDDEN_DB_KEYWORDS = ("mysql://", "leishen-db", "dsn=", "mysql_")


def validate_project_id(project_id: str) -> None:
    """校验项目标识合法性，禁止路径穿越字符。"""
    if not project_id or not isinstance(project_id, str):
        raise ValueError("Invalid project_id: must be a non-empty string")
    if not PROJECT_ID_PATTERN.match(project_id):
        raise ValueError(f"Invalid project_id: '{project_id}' contains illegal characters")


def validate_output_path(project_id: str, path: str) -> str:
    """校验产物路径必须严格位于指定项目的 outputs 目录内。"""
    validate_project_id(project_id)
    allowed_base = os.path.realpath(os.path.join(PROJECTS_DIR, project_id, "outputs"))
    target = os.path.realpath(path)
    if not (target == allowed_base or target.startswith(allowed_base + os.sep)):
        raise ValueError(f"Path traversal detected: {path} is outside {allowed_base}")
    return target


def check_no_mysql_dsn(data: Any) -> None:
    """严格递归检测参数中是否存在非法 MySQL / DSN 连接参数。"""
    if isinstance(data, str):
        lowered = data.lower()
        for kw in FORBIDDEN_DB_KEYWORDS:
            if kw in lowered:
                raise ValueError(f"Security Violation: MySQL parameter detected ('{kw}')")
    elif isinstance(data, dict):
        for k, v in data.items():
            check_no_mysql_dsn(k)
            check_no_mysql_dsn(v)
    elif isinstance(data, (list, tuple, set)):
        for item in data:
            check_no_mysql_dsn(item)


class Job:
    """内存异步任务模型"""

    def __init__(self, job_id: str, project_id: str, job_type: str, params: Optional[Dict[str, Any]] = None):
        self.job_id = job_id
        self.project_id = project_id
        self.job_type = job_type
        self.params = params or {}
        self.status = "queued"
        self.result: Dict[str, Any] = {}
        self.output_paths: List[str] = []
        self.error_message: Optional[str] = None
        self.created_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self.started_at: Optional[str] = None
        self.finished_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """序列化为对外规范字典"""
        return {
            "job_id": self.job_id,
            "project_id": self.project_id,
            "job_type": self.job_type,
            "status": self.status,
            "result": self.result,
            "output_paths": self.output_paths,
            "error_message": self.error_message,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }


class JobStore:
    """线程安全的内存任务存储表"""

    def __init__(self):
        self._jobs: Dict[str, Job] = {}
        self._lock = threading.Lock()

    def create_job(self, project_id: str, job_type: str, params: Optional[Dict[str, Any]] = None) -> Job:
        """创建并记录新任务"""
        validate_project_id(project_id)
        if job_type not in VALID_JOB_TYPES:
            raise ValueError(f"Unsupported job_type: '{job_type}'")
        check_no_mysql_dsn(params)

        job_id = f"job_{uuid.uuid4().hex}"
        job = Job(job_id=job_id, project_id=project_id, job_type=job_type, params=params)
        with self._lock:
            self._jobs[job_id] = job
        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        """获取指定任务"""
        with self._lock:
            return self._jobs.get(job_id)

    def update_job(
        self,
        job_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        output_paths: Optional[List[str]] = None,
        error_message: Optional[str] = None,
    ) -> Optional[Job]:
        """更新任务执行状态与产出结果"""
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            job.status = status
            now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            if status == "running" and not job.started_at:
                job.started_at = now_iso
            elif status in ("succeeded", "failed"):
                job.finished_at = now_iso
            if result is not None:
                job.result = result
            if output_paths is not None:
                job.output_paths = output_paths
            if error_message is not None:
                job.error_message = error_message
            return job


_GLOBAL_STORE: Optional[JobStore] = None


def get_job_store() -> JobStore:
    """获取单例内存任务存储"""
    global _GLOBAL_STORE
    if _GLOBAL_STORE is None:
        _GLOBAL_STORE = JobStore()
    return _GLOBAL_STORE
