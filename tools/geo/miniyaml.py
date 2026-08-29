"""极简 YAML 子集解析器（零依赖）。

仅支持本项目 project.yaml 所需的结构：
- 顶层 `key: value` 标量
- `key:` 后跟 `- item` 列表
- `key:` 后跟更深缩进的嵌套字典
不追求通用 YAML 兼容性，遇到不支持的语法直接抛错，避免静默出错数据。
"""
from __future__ import annotations

import re
from typing import Any


class MiniYamlError(ValueError):
    pass


_NUM_RE = re.compile(r"^-?\d+(\.\d+)?$")


def _parse_scalar(raw: str) -> Any:
    text = raw.strip()
    if text == "":
        return ""
    if text[0] in "\"'" and text[-1] == text[0] and len(text) >= 2:
        return text[1:-1]
    lowered = text.lower()
    if lowered in ("true", "yes"):
        return True
    if lowered in ("false", "no"):
        return False
    if lowered in ("null", "~"):
        return None
    if _NUM_RE.match(text):
        return float(text) if "." in text else int(text)
    return text


def _strip_comment(line: str) -> str:
    """去掉行尾注释（跳过引号内的 # 号）。"""
    quote = ""
    for idx, ch in enumerate(line):
        if quote:
            if ch == quote:
                quote = ""
        elif ch in "\"'":
            quote = ch
        elif ch == "#" and (idx == 0 or line[idx - 1] in " \t"):
            return line[:idx]
    return line


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _parse_block(lines: list, pos: int, indent: int) -> tuple[Any, int]:
    """解析同一缩进层级的块，返回 (值, 新行号)。"""
    result: Any = None
    while pos < len(lines):
        raw = _strip_comment(lines[pos])
        if not raw.strip():
            pos += 1
            continue
        cur = _indent(raw)
        if cur < indent:
            break
        if cur > indent:
            raise MiniYamlError(f"缩进异常: {lines[pos]!r}")
        stripped = raw.strip()
        if stripped.startswith("- "):
            if result is None:
                result = []
            if not isinstance(result, list):
                raise MiniYamlError(f"列表与键值混用: {lines[pos]!r}")
            result.append(_parse_scalar(stripped[2:]))
            pos += 1
            continue
        if ":" in stripped:
            if result is None:
                result = {}
            if not isinstance(result, dict):
                raise MiniYamlError(f"字典与列表混用: {lines[pos]!r}")
            key, _, value = stripped.partition(":")
            key = key.strip()
            if value.strip():
                result[key] = _parse_scalar(value)
                pos += 1
            else:
                # 查看子块缩进，决定是列表/字典还是空值
                child_indent, child_pos = _peek_child(lines, pos + 1)
                if child_indent is None:
                    result[key] = {}
                    pos += 1
                else:
                    child, pos = _parse_block(lines, child_pos, child_indent)
                    result[key] = child
            continue
        raise MiniYamlError(f"无法解析的行: {lines[pos]!r}")
    return (result if result is not None else {}), pos


def _peek_child(lines: list, pos: int) -> tuple[Any, int]:
    for idx in range(pos, len(lines)):
        raw = _strip_comment(lines[idx])
        if not raw.strip():
            continue
        return _indent(raw), idx
    return None, pos


def load(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    data, _ = _parse_block(lines, 0, 0)
    if not isinstance(data, dict):
        raise MiniYamlError("顶层必须是键值字典")
    return data
