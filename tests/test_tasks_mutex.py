# -*- coding: utf-8 -*-
"""
GeoTask 与项目级并发互斥队列锁单测
验证多电脑并发防踩踏机制、任务排队与状态流转
"""

import os
import time
import unittest
import tempfile
from tools.geo.task_runner import TaskManager, TaskStatus


class TestTaskManagerMutex(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_file = os.path.join(self.temp_dir.name, "tasks_test.json")
        self.mgr = TaskManager(data_file=self.data_file)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_single_task_execution_and_log_capture(self):
        task = self.mgr.submit_task(
            project_id="test_proj_single",
            task_type="test_echo",
            created_by_user_id="1768892187321049001",
            created_by_name="李工",
            params={"message": "单任务测试执行", "sleep": 0.05},
        )
        self.assertIsNotNone(task.task_id)
        self.assertTrue(task.task_id.isdigit())

        # 等待其执行完成
        max_wait = 20
        while max_wait > 0 and task.status != TaskStatus.SUCCESS:
            time.sleep(0.05)
            max_wait -= 1

        self.assertEqual(task.status, TaskStatus.SUCCESS)
        self.assertIn("Task echo: 单任务测试执行", task.log_output)
        self.assertGreater(task.duration_ms, 0)
        self.assertFalse(self.mgr.is_project_busy("test_proj_single"))

    def test_project_task_mutex_queue(self):
        """
        核心防御性测试：
        模拟两位同事在各自电脑上同时对同一项目点击运行，
        task1 耗时 0.2s，task2 必须自动进入 pending 队列排队，
        task1 完成后，task2 自动被唤醒并完成，防止文件并发写入损坏 outputs。
        """
        proj_id = "test_proj_mutex"

        # 1. 提交长任务 1
        t1 = self.mgr.submit_task(
            project_id=proj_id,
            task_type="test_echo",
            created_by_user_id="1001",
            created_by_name="张三",
            params={"message": "张三的任务", "sleep": 0.2},
        )

        # 立即提交任务 2
        t2 = self.mgr.submit_task(
            project_id=proj_id,
            task_type="test_echo",
            created_by_user_id="1002",
            created_by_name="李四",
            params={"message": "李四的任务", "sleep": 0.05},
        )

        # 此时 t1 必定是 running，t2 必定处于 pending 排队中！
        self.assertEqual(t1.status, TaskStatus.RUNNING)
        self.assertEqual(t2.status, TaskStatus.PENDING)
        self.assertTrue(self.mgr.is_project_busy(proj_id))

        # 等待 t1 完成并触发 t2
        for _ in range(40):
            if t1.status == TaskStatus.SUCCESS and t2.status == TaskStatus.SUCCESS:
                break
            time.sleep(0.05)

        self.assertEqual(t1.status, TaskStatus.SUCCESS)
        self.assertEqual(t2.status, TaskStatus.SUCCESS)
        self.assertFalse(self.mgr.is_project_busy(proj_id))
        self.assertIn("张三的任务", t1.log_output)
        self.assertIn("李四的任务", t2.log_output)

    def test_sse_event_subscription(self):
        """测试 SSE 事件订阅输出格式"""
        t = self.mgr.submit_task(
            project_id="test_proj_sse",
            task_type="test_echo",
            created_by_user_id="1003",
            created_by_name="王五",
            params={"message": "SSE 推流测试", "sleep": 0.05},
        )

        events = []
        for chunk in self.mgr.subscribe_events(t.task_id):
            events.append(chunk)
            if '"event": "done"' in chunk:
                break

        full_stream = "".join(events)
        self.assertIn("data: ", full_stream)
        self.assertIn('"event": "status"', full_stream)
        self.assertIn('"event": "done"', full_stream)


if __name__ == "__main__":
    unittest.main()
