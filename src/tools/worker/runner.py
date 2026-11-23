# -*- coding: utf-8 -*-
"""
GEO Worker 异步任务执行器模块 (tools/worker/runner.py)
基于 ThreadPoolExecutor 异步并发执行，异常完整透传至 error_message，绝不吞错。
"""

import traceback
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
from tools.worker.store import get_job_store
from tools.worker.handlers import dispatch_job


class WorkerRunner:
    """异步任务运行管理器"""

    def __init__(self, max_workers: int = 4):
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="geo_worker")

    def _execute_job(self, job_id: str) -> None:
        """子线程中执行任务逻辑"""
        store = get_job_store()
        job = store.get_job(job_id)
        if not job:
            return

        store.update_job(job_id, status="running")
        try:
            result, output_paths = dispatch_job(job.job_type, job.project_id, job.params)
            store.update_job(
                job_id=job_id,
                status="succeeded",
                result=result,
                output_paths=output_paths,
            )
        except Exception as exc:
            err_msg = f"{type(exc).__name__}: {str(exc)}"
            tb = traceback.format_exc()
            store.update_job(
                job_id=job_id,
                status="failed",
                error_message=f"{err_msg}\n{tb}".strip(),
            )

    def submit(self, job_id: str) -> None:
        """提交任务异步执行"""
        self._executor.submit(self._execute_job, job_id)

    def shutdown(self, wait: bool = True) -> None:
        """关闭线程池"""
        self._executor.shutdown(wait=wait)


_GLOBAL_RUNNER: Optional[WorkerRunner] = None


def get_worker_runner() -> WorkerRunner:
    """获取单例执行器"""
    global _GLOBAL_RUNNER
    if _GLOBAL_RUNNER is None:
        _GLOBAL_RUNNER = WorkerRunner()
    return _GLOBAL_RUNNER
