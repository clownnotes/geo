# -*- coding: utf-8 -*-
"""
雪花 ID (Snowflake ID) 全局唯一标识符生成器
// [2026-09-18] [接入小毛驴统一API] 遵循全局协作规则 4.11，全系统禁止自增 ID，统一采用雪花 ID，出网统一为字符串
"""

import time
import threading

# 纪元时间戳：2026-01-01 00:00:00 UTC (1767225600000 ms)
DEFAULT_EPOCH = 1767225600000

# 位分配
WORKER_ID_BITS = 10
SEQUENCE_BITS = 12

MAX_WORKER_ID = (1 << WORKER_ID_BITS) - 1   # 1023
MAX_SEQUENCE = (1 << SEQUENCE_BITS) - 1     # 4095

WORKER_ID_SHIFT = SEQUENCE_BITS
TIMESTAMP_SHIFT = SEQUENCE_BITS + WORKER_ID_BITS


class SnowflakeGenerator:
    """线程安全的雪花 ID 生成器"""

    def __init__(self, worker_id: int = 1, epoch: int = DEFAULT_EPOCH):
        if worker_id < 0 or worker_id > MAX_WORKER_ID:
            raise ValueError(f"worker_id 必须在 0 到 {MAX_WORKER_ID} 之间，收到: {worker_id}")
        self.worker_id = worker_id
        self.epoch = epoch
        self.sequence = 0
        self.last_timestamp = -1
        self.lock = threading.Lock()

    def _current_millis(self) -> int:
        return int(time.time() * 1000)

    def next_id(self) -> int:
        """生成下一个 64 位雪花 ID 整数"""
        with self.lock:
            timestamp = self._current_millis()

            # 处理时钟回拨
            if timestamp < self.last_timestamp:
                offset = self.last_timestamp - timestamp
                if offset <= 5:
                    # 微小回拨，休眠等待
                    time.sleep(offset / 1000.0)
                    timestamp = self._current_millis()
                else:
                    raise RuntimeError(f"检测到系统时钟回拨 {offset}ms，雪花生成器拒绝生成 ID")

            if timestamp == self.last_timestamp:
                self.sequence = (self.sequence + 1) & MAX_SEQUENCE
                if self.sequence == 0:
                    # 当前毫秒序列号耗尽，等待下一毫秒
                    while timestamp <= self.last_timestamp:
                        timestamp = self._current_millis()
            else:
                self.sequence = 0

            self.last_timestamp = timestamp

            sf_id = ((timestamp - self.epoch) << TIMESTAMP_SHIFT) | \
                    (self.worker_id << WORKER_ID_SHIFT) | \
                    self.sequence
            return sf_id

    def next_id_str(self) -> str:
        """生成雪花 ID 字符串（出网契约）"""
        return str(self.next_id())


# 全局单例生成器
_DEFAULT_GENERATOR = SnowflakeGenerator(worker_id=1)


def new_id() -> str:
    """生成全局唯一的雪花 ID 纯数字字符串"""
    return _DEFAULT_GENERATOR.next_id_str()


def new_id_int() -> int:
    """生成全局唯一的雪花 ID uint64 整数"""
    return _DEFAULT_GENERATOR.next_id()
