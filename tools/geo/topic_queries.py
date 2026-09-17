# -*- coding: utf-8 -*-
"""选题长问合格判定（OpenSpec：创建与阶段零先探活再长问选题 §C）。"""

from __future__ import annotations

import re
from typing import Iterable, List, Sequence, Tuple

# 像「会问出口」的痕迹
_QUESTIONISH = re.compile(
    r"[？?]|哪家|哪个|怎么|如何|什么|谁|靠谱|有没有|多少钱|区别|坑|推荐|找谁|"
    r"该不该|能不能|是否|为何|为什么|怎么样|好不好|值不值|适不适合"
)

# 明显短标签 / SEO 渣
_SHORT_LABEL = re.compile(r"^[\w\u4e00-\u9fff]{1,12}$")


def is_qualifying_long_query(text: str) -> bool:
    """是否可作为选题长问写入清单 / 写稿主路径。"""
    t = (text or "").strip()
    if not t:
        return False
    if t in ("行业核心推荐词", "好用方案对比"):
        return False
    q = bool(_QUESTIONISH.search(t))
    # 过短纯标签
    if len(t) < 10:
        return False
    # 纯短标签（无问句痕迹）
    if _SHORT_LABEL.match(t) and not q and len(t) <= 12:
        return False
    if q and len(t) >= 10:
        return True
    if len(t) >= 20:
        return True
    if len(t) >= 15 and (" " in t or "，" in t or "。" in t or "、" in t):
        return True
    return False


def filter_long_queries(items: Iterable) -> Tuple[List[str], List[str]]:
    """返回 (合格长问, 被拒短词/不合格)。"""
    ok: List[str] = []
    rejected: List[str] = []
    seen = set()
    for item in items or []:
        text = item.get("prompt") if isinstance(item, dict) else str(item)
        text = (text or "").strip()
        if not text:
            continue
        if text in seen:
            continue
        seen.add(text)
        if is_qualifying_long_query(text):
            ok.append(text)
        else:
            rejected.append(text)
    return ok, rejected


def qualifying_from_list(items: Sequence) -> List[str]:
    ok, _ = filter_long_queries(items)
    return ok
