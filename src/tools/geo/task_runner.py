# -*- coding: utf-8 -*-
"""
GEO 异步任务调度与项目级并发互斥队列锁 (tools/geo/task_runner.py)
// [2026-09-18] [接入小毛驴统一API] 遵循 AGENTS.md 与设计规范：
// 1. 采用雪花 ID 字符串作为全系统唯一主键；
// 2. 项目级并发互斥队列锁（Project Task Mutex），防多电脑同时写入 outputs 踩踏；
// 3. 逐行捕获任务执行日志，提供 SSE 实时推流订阅；
// 4. 持久化任务历史到 data/tasks.json。
"""

import os
import sys
import json
import time
import io
import queue
import threading
import contextlib
from typing import Dict, List, Optional, Generator

from .idgen import new_id
from .utils import PROJECT_ROOT


class TaskStatus:
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class GeoTask:
    """GEO 异步任务对象"""

    def __init__(
        self,
        task_id: str,
        project_id: str,
        task_type: str,
        created_by_user_id: str = "",
        created_by_name: str = "",
        params: dict = None,
        status: str = TaskStatus.PENDING,
        progress: int = 0,
        log_output: str = "",
        duration_ms: int = 0,
        error_message: str = "",
        created_at: float = None,
        started_at: float = None,
        completed_at: float = None,
    ):
        self.task_id = str(task_id)
        self.project_id = str(project_id)
        self.task_type = str(task_type)
        self.created_by_user_id = str(created_by_user_id or "")
        self.created_by_name = str(created_by_name or "")
        self.params = params or {}
        self.status = status
        self.progress = progress
        self.log_output = log_output
        self.duration_ms = duration_ms
        self.error_message = error_message
        self.created_at = created_at or time.time()
        self.started_at = started_at
        self.completed_at = completed_at

    def to_dict(self) -> dict:
        return {
            "id": self.task_id,
            "project_id": self.project_id,
            "task_type": self.task_type,
            "created_by_user_id": self.created_by_user_id,
            "created_by_name": self.created_by_name,
            "params": self.params,
            "status": self.status,
            "progress": self.progress,
            "log_output": self.log_output,
            "duration_ms": self.duration_ms,
            "error_message": self.error_message,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "GeoTask":
        return cls(
            task_id=str(d.get("id") or d.get("task_id", "")),
            project_id=str(d.get("project_id", "")),
            task_type=str(d.get("task_type", "")),
            created_by_user_id=str(d.get("created_by_user_id", "")),
            created_by_name=str(d.get("created_by_name", "")),
            params=d.get("params") or {},
            status=d.get("status", TaskStatus.PENDING),
            progress=d.get("progress", 0),
            log_output=d.get("log_output", ""),
            duration_ms=d.get("duration_ms", 0),
            error_message=d.get("error_message", ""),
            created_at=d.get("created_at"),
            started_at=d.get("started_at"),
            completed_at=d.get("completed_at"),
        )


class _StreamCapture(io.TextIOBase):
    """拦截 stdout/stderr 并实时推送至任务通道"""

    def __init__(self, task_id: str, original_stream, manager: "TaskManager"):
        self.task_id = task_id
        self.original_stream = original_stream
        self.manager = manager
        self.buffer = ""

    def write(self, s: str):
        if self.original_stream:
            try:
                self.original_stream.write(s)
                self.original_stream.flush()
            except Exception:
                pass

        self.buffer += s
        while "\n" in self.buffer:
            line, self.buffer = self.buffer.split("\n", 1)
            line = line.strip("\r")
            if line:
                self.manager.append_task_log(self.task_id, line)
        return len(s)

    def flush(self):
        if self.original_stream:
            try:
                self.original_stream.flush()
            except Exception:
                pass
        if self.buffer.strip():
            line = self.buffer.strip("\r\n")
            self.buffer = ""
            if line:
                self.manager.append_task_log(self.task_id, line)


class TaskManager:
    """
    单例任务管理器
    具备项目级并发互斥队列锁：同一个 project_id 同一时刻仅允许一个任务处于 RUNNING 状态，
    其他并发提交的任务自动进入 PENDING 队列，并在前序任务完成后按序唤醒。
    """

    def __init__(self, data_file: str = None):
        self.data_file = data_file or os.path.join(PROJECT_ROOT, "data", "tasks.json")
        self._lock = threading.RLock()
        self._tasks: Dict[str, GeoTask] = {}
        self._project_queues: Dict[str, List[GeoTask]] = {}
        self._running_projects: Dict[str, str] = {}  # project_id -> task_id
        self._subscribers: Dict[str, List[queue.Queue]] = {}  # task_id -> list of Queues
        self._load_tasks()

    def _load_tasks(self):
        """从磁盘持久化文件加载任务列表"""
        if not os.path.exists(self.data_file):
            return
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            for t_dict in data:
                task = GeoTask.from_dict(t_dict)
                # 若加载时发现之前进程意外崩溃处于 running，重置为 failed
                if task.status == TaskStatus.RUNNING:
                    task.status = TaskStatus.FAILED
                    task.error_message = "服务重启中断未完成"
                self._tasks[task.task_id] = task
        except Exception:
            pass

    def _save_tasks(self):
        """持久化保存任务到磁盘"""
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            # 仅保留最近 200 条记录防止过大
            all_tasks = sorted(self._tasks.values(), key=lambda t: t.created_at, reverse=True)[:200]
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump([t.to_dict() for t in all_tasks], f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def submit_task(
        self,
        project_id: str,
        task_type: str,
        created_by_user_id: str = "",
        created_by_name: str = "",
        params: dict = None,
    ) -> GeoTask:
        """
        提交一个异步任务：
        若该项目当前无 running 任务，立即执行；
        若已有任务在 running，放入互斥队列 pending 排队。
        """
        task_id = new_id()
        task = GeoTask(
            task_id=task_id,
            project_id=project_id,
            task_type=task_type,
            created_by_user_id=created_by_user_id,
            created_by_name=created_by_name,
            params=params or {},
            status=TaskStatus.PENDING,
            progress=0,
            log_output="",
            created_at=time.time(),
        )

        with self._lock:
            self._tasks[task_id] = task
            self._save_tasks()

            # 判断互斥锁
            if project_id in self._running_projects:
                # 已有任务在运行，加入该项目的排队队列
                if project_id not in self._project_queues:
                    self._project_queues[project_id] = []
                self._project_queues[project_id].append(task)
                self.append_task_log(
                    task_id,
                    f"[排队中] 项目 [{project_id}] 正在执行前序任务，当前任务已进入互斥队列等待...",
                )
            else:
                # 无任务运行，直接启动
                self._start_task_locked(task)

        return task

    def _start_task_locked(self, task: GeoTask):
        """在持有 _lock 条件下标记任务为 RUNNING 并启动后台线程"""
        task.status = TaskStatus.RUNNING
        task.started_at = time.time()
        task.progress = 5
        self._running_projects[task.project_id] = task.task_id
        self._save_tasks()

        self._broadcast_event(
            task.task_id,
            {"event": "status", "status": task.status, "progress": task.progress},
        )
        self.append_task_log(
            task.task_id,
            f"[开始执行] 任务 ID: {task.task_id} | 项目: {task.project_id} | 类型: {task.task_type}",
        )

        # 启动工作线程执行
        thread = threading.Thread(
            target=self._execute_task_wrapper,
            args=(task,),
            name=f"task-{task.task_id}",
            daemon=True,
        )
        thread.start()

    def _execute_task_wrapper(self, task: GeoTask):
        """工作线程执行主体与异常防护"""
        start_time = time.time()
        success = False
        error_msg = ""

        # 接管该任务执行期间的输出
        capture_out = _StreamCapture(task.task_id, sys.stdout, self)
        capture_err = _StreamCapture(task.task_id, sys.stderr, self)

        try:
            with contextlib.redirect_stdout(capture_out), contextlib.redirect_stderr(capture_err):
                self._run_task_logic(task)
            success = True
            task.progress = 100
        except Exception as e:
            error_msg = str(e)
            self.append_task_log(task.task_id, f"[错误] 任务执行异常: {error_msg}")
        finally:
            capture_out.flush()
            capture_err.flush()

        # 任务结束收尾
        completed_at = time.time()
        duration_ms = int((completed_at - start_time) * 1000)

        with self._lock:
            task.completed_at = completed_at
            task.duration_ms = duration_ms
            task.status = TaskStatus.SUCCESS if success else TaskStatus.FAILED
            task.error_message = error_msg
            self._save_tasks()

            # 释放该项目的运行锁
            if self._running_projects.get(task.project_id) == task.task_id:
                del self._running_projects[task.project_id]

            # 广播完成事件
            self._broadcast_event(
                task.task_id,
                {
                    "event": "done",
                    "status": task.status,
                    "progress": task.progress,
                    "duration_ms": duration_ms,
                    "error": error_msg,
                },
            )

            # 唤醒该项目的下一个排队任务
            if task.project_id in self._project_queues and self._project_queues[task.project_id]:
                next_task = self._project_queues[task.project_id].pop(0)
                self._start_task_locked(next_task)

    def _run_task_logic(self, task: GeoTask):
        """派发具体 SOP 业务逻辑"""
        project_id = task.project_id
        step = task.task_type
        params = task.params or {}

        if step == "audit":
            mode = params.get("mode", "crawl")
            from .audit import (
                run_audit_crawl,
                run_audit_interpret,
                run_audit_boss_direct,
                run_audit_tech_direct,
                run_audit,
            )
            if mode == "crawl":
                run_audit_crawl(project_id)
            elif mode == "interpret":
                run_audit_interpret(project_id)
            elif mode == "boss_direct":
                run_audit_boss_direct(project_id)
            elif mode == "tech_direct":
                run_audit_tech_direct(project_id)
            else:
                run_audit(project_id, mode="full")
        elif step == "scaffold":
            from .scaffold import run_scaffold
            run_scaffold(project_id)
        elif step == "rewrite":
            from .rewrite import run_rewrite
            rmode = params.get("mode", "incremental")
            run_rewrite(project_id, mode=rmode)
        elif step == "distribute":
            from .distribute import run_distribute
            run_distribute(project_id)
        elif step == "monitor":
            from .monitor import run_monitor
            run_monitor(project_id)
        elif step == "probe":
            from .probing import generate_probing_script
            generate_probing_script(project_id)
        elif step == "evolution":
            from .evolution import run_evolution_pipeline
            run_evolution_pipeline(project_id)
        elif step == "test_echo":
            # 测试用模拟任务
            echo_msg = params.get("message", "Hello Task")
            sleep_sec = params.get("sleep", 0)
            print(f"Task echo: {echo_msg}")
            if sleep_sec > 0:
                time.sleep(sleep_sec)
            print("Task echo finished")
        else:
            raise ValueError(f"不支持的 GEO 任务类型: {step}")

    def append_task_log(self, task_id: str, line: str):
        """向任务追加一行日志，并广播给 SSE 客户端"""
        timestamp_str = datetime_now_str()
        formatted_line = f"[{timestamp_str}] {line}"

        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                if task.log_output:
                    task.log_output += "\n" + formatted_line
                else:
                    task.log_output = formatted_line

        self._broadcast_event(
            task_id,
            {"event": "log", "line": formatted_line},
        )

    def _broadcast_event(self, task_id: str, event_data: dict):
        """广播事件给所有订阅该任务的 Queue"""
        with self._lock:
            subs = self._subscribers.get(task_id, [])
            dead_queues = []
            for q in subs:
                try:
                    q.put_nowait(event_data)
                except queue.Full:
                    dead_queues.append(q)
            for dq in dead_queues:
                subs.remove(dq)

    def subscribe_events(self, task_id: str) -> Generator[str, None, None]:
        """
        订阅指定任务的 SSE 事件流生成器
        1. 先推送历史状态与已有日志
        2. 再实时监听队列并 yield SSE 帧
        """
        q = queue.Queue(maxsize=1000)
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                yield f"data: {json.dumps({'event': 'error', 'msg': '任务不存在'})}\n\n"
                return

            if task_id not in self._subscribers:
                self._subscribers[task_id] = []
            self._subscribers[task_id].append(q)

            # 先推送初始状态
            yield f"data: {json.dumps({'event': 'status', 'status': task.status, 'progress': task.progress})}\n\n"

            # 补发历史日志
            if task.log_output:
                for line in task.log_output.split("\n"):
                    if line:
                        yield f"data: {json.dumps({'event': 'log', 'line': line})}\n\n"

            # 如果任务已结束，补发 done 事件并退出
            if task.status in (TaskStatus.SUCCESS, TaskStatus.FAILED):
                yield f"data: {json.dumps({'event': 'done', 'status': task.status, 'progress': task.progress, 'duration_ms': task.duration_ms, 'error': task.error_message})}\n\n"
                return

        # 任务运行中，持续监听新事件
        try:
            while True:
                try:
                    event = q.get(timeout=30)  # 30s 心跳防断开
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                    if event.get("event") == "done":
                        break
                except queue.Empty:
                    # 心跳保持
                    yield ": ping\n\n"
        finally:
            with self._lock:
                if task_id in self._subscribers and q in self._subscribers[task_id]:
                    self._subscribers[task_id].remove(q)

    def get_task(self, task_id: str) -> Optional[GeoTask]:
        with self._lock:
            return self._tasks.get(task_id)

    def list_project_tasks(self, project_id: str) -> List[GeoTask]:
        with self._lock:
            tasks = [t for t in self._tasks.values() if t.project_id == project_id]
            tasks.sort(key=lambda t: t.created_at, reverse=True)
            return tasks

    def is_project_busy(self, project_id: str) -> bool:
        with self._lock:
            return project_id in self._running_projects


def datetime_now_str() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


# 单例全局任务管理器
_DEFAULT_TASK_MANAGER = TaskManager()


def get_task_manager() -> TaskManager:
    return _DEFAULT_TASK_MANAGER
