# -*- coding: utf-8 -*-
"""
雪花 ID 生成器测试
"""

import unittest
import threading
from tools.geo.idgen import SnowflakeGenerator, new_id, new_id_int


class TestSnowflakeIdGen(unittest.TestCase):

    def test_single_id_format(self):
        sf_str = new_id()
        self.assertIsInstance(sf_str, str)
        self.assertTrue(sf_str.isdigit())
        self.assertGreater(len(sf_str), 10)

        sf_int = new_id_int()
        self.assertIsInstance(sf_int, int)
        self.assertGreater(sf_int, 0)

    def test_monotonic_increasing(self):
        ids = [new_id_int() for _ in range(100)]
        for i in range(len(ids) - 1):
            self.assertLess(ids[i], ids[i + 1])

    def test_concurrent_uniqueness(self):
        generated = set()
        lock = threading.Lock()
        threads = []

        def worker():
            for _ in range(200):
                val = new_id()
                with lock:
                    generated.add(val)

        for _ in range(10):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # 10 线程 * 200 = 2000 个 ID 无任何重复
        self.assertEqual(len(generated), 2000)


if __name__ == "__main__":
    unittest.main()
