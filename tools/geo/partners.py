#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""合作方 / 业务员名册（代理归属分类，非登录账号）。"""

from __future__ import annotations

import os
import re
import secrets
import time
from datetime import date
from typing import Any

from .utils import PROJECT_ROOT, PROJECTS_DIR, load_project_config

PARTNERS_FILE = os.path.join(PROJECT_ROOT, "config", "geo_partners.yaml")


def _ensure_file() -> None:
    os.makedirs(os.path.dirname(PARTNERS_FILE), exist_ok=True)
    if not os.path.exists(PARTNERS_FILE):
        with open(PARTNERS_FILE, "w", encoding="utf-8") as f:
            f.write("partners: []\n")


def _escape_yaml_str(value: Any) -> str:
    """双引号标量转义，避免名称含引号/换行破坏回读（仓库未引入 PyYAML）。"""
    s = str(value if value is not None else "")
    s = s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "")
    return f'"{s}"'


def _unescape_yaml_str(raw: str) -> str:
    s = (raw or "").strip()
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        body = s[1:-1]
        out: list[str] = []
        i = 0
        while i < len(body):
            if body[i] == "\\" and i + 1 < len(body):
                nxt = body[i + 1]
                if nxt == "n":
                    out.append("\n")
                elif nxt == '"':
                    out.append('"')
                elif nxt == "\\":
                    out.append("\\")
                else:
                    out.append(nxt)
                i += 2
                continue
            out.append(body[i])
            i += 1
        return "".join(out)
    if len(s) >= 2 and s[0] == "'" and s[-1] == "'":
        return s[1:-1]
    return s


def _parse_partners_yaml(content: str) -> list[dict]:
    """极简解析 config/geo_partners.yaml（单层 list of dict）。"""
    partners: list[dict] = []
    current: dict | None = None
    in_list = False
    for raw in content.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("partners:"):
            in_list = True
            continue
        if not in_list:
            continue
        if stripped.startswith("- "):
            if current:
                partners.append(current)
            current = {}
            rest = stripped[2:].strip()
            if ":" in rest and not rest.startswith("{"):
                k, v = rest.split(":", 1)
                current[k.strip()] = _unescape_yaml_str(v)
            continue
        if current is not None and ":" in stripped and line.startswith(" "):
            k, v = stripped.split(":", 1)
            current[k.strip()] = _unescape_yaml_str(v)
    if current:
        partners.append(current)
    return partners


def _dump_partners_yaml(partners: list[dict]) -> str:
    lines = ["partners:"]
    if not partners:
        lines.append("  []")
        return "\n".join(lines) + "\n"
    for p in partners:
        lines.append(f"  - id: {_escape_yaml_str(p.get('id', ''))}")
        lines.append(f"    name: {_escape_yaml_str(p.get('name', ''))}")
        lines.append(f"    status: {_escape_yaml_str(p.get('status', 'active'))}")
        lines.append(f"    created_at: {_escape_yaml_str(p.get('created_at', ''))}")
    return "\n".join(lines) + "\n"


def load_partners(include_archived: bool = True) -> list[dict]:
    _ensure_file()
    try:
        with open(PARTNERS_FILE, "r", encoding="utf-8") as f:
            partners = _parse_partners_yaml(f.read())
    except Exception:
        return []
    if include_archived:
        return partners
    return [p for p in partners if p.get("status", "active") != "archived"]


def save_partners(partners: list[dict]) -> None:
    _ensure_file()
    with open(PARTNERS_FILE, "w", encoding="utf-8") as f:
        f.write(_dump_partners_yaml(partners))


def partner_map(include_archived: bool = True) -> dict[str, str]:
    return {p["id"]: p.get("name", p["id"]) for p in load_partners(include_archived) if p.get("id")}


def _slug_id(name: str, existing_ids: set[str] | None = None) -> str:
    """生成合作方 ID；纯中文名用时间戳+随机后缀，避免同秒冲突。"""
    existing = existing_ids or set()
    raw = re.sub(r"[^a-zA-Z0-9_\u4e00-\u9fff]+", "_", name.strip())
    raw = re.sub(r"_+", "_", raw).strip("_").lower()
    if not raw or re.search(r"[\u4e00-\u9fff]", raw):
        raw = f"agent_{int(time.time())}_{secrets.token_hex(3)}"
    elif not raw.startswith("agent_"):
        raw = f"agent_{raw}"
    candidate = raw[:48]
    if candidate not in existing:
        return candidate
    for _ in range(8):
        suffix = secrets.token_hex(2)
        trial = f"{candidate[:40].rstrip('_')}_{suffix}"
        if trial not in existing:
            return trial
    return f"agent_{secrets.token_hex(6)}"


def create_partner(name: str, partner_id: str | None = None) -> dict:
    name = (name or "").strip()
    if not name:
        raise ValueError("合作方名称不能为空")
    partners = load_partners(include_archived=True)
    existing_ids = {p.get("id") for p in partners if p.get("id")}
    pid = (partner_id or "").strip() or _slug_id(name, existing_ids)
    pid = re.sub(r"[^a-zA-Z0-9_\-]", "_", pid)
    if pid in existing_ids:
        raise ValueError(f"合作方 ID [{pid}] 已存在")
    row = {
        "id": pid,
        "name": name,
        "status": "active",
        "created_at": date.today().isoformat(),
    }
    partners.append(row)
    save_partners(partners)
    return row


def update_partner(partner_id: str, *, name: str | None = None, status: str | None = None) -> dict:
    partners = load_partners(include_archived=True)
    target = None
    for p in partners:
        if p.get("id") == partner_id:
            target = p
            break
    if not target:
        raise ValueError(f"合作方 [{partner_id}] 不存在")
    if name is not None:
        name = name.strip()
        if not name:
            raise ValueError("合作方名称不能为空")
        target["name"] = name
    if status is not None:
        if status not in ("active", "archived"):
            raise ValueError("status 仅支持 active / archived")
        target["status"] = status
        if status == "archived":
            clear_partner_from_projects(partner_id)
    save_partners(partners)
    return target


def clear_partner_from_projects(partner_id: str) -> int:
    """归档时清空挂在该合作方下的项目归属。"""
    cleared = 0
    if not os.path.exists(PROJECTS_DIR):
        return 0
    for item in os.listdir(PROJECTS_DIR):
        if item.startswith(".") or item == "_template":
            continue
        p_dir = os.path.join(PROJECTS_DIR, item)
        if not os.path.isdir(p_dir):
            continue
        try:
            cfg = load_project_config(item)
            if (cfg.get("partner_id") or "") == partner_id:
                set_project_partner_id(item, "")
                cleared += 1
        except Exception:
            continue
    return cleared


def set_project_partner_id(project_id: str, partner_id: str | None) -> str:
    """写入或清空 project.yaml 的 partner_id。返回最终值（空串表示未分配）。"""
    cfg = load_project_config(project_id)
    yaml_path = os.path.join(cfg["_project_dir"], "project.yaml")
    value = (partner_id or "").strip()
    with open(yaml_path, "r", encoding="utf-8") as f:
        content = f.read()

    quoted = _escape_yaml_str(value)
    if re.search(r"(?m)^partner_id\s*:", content):
        content = re.sub(
            r"(?m)^partner_id\s*:.*$",
            f"partner_id: {quoted}",
            content,
            count=1,
        )
    else:
        content = content.rstrip() + f"\n\n# 代理合作归属（可选；空=未分配）\npartner_id: {quoted}\n"

    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write(content)
    return value


def resolve_partner_name(partner_id: str | None, pmap: dict[str, str] | None = None) -> str:
    pid = (partner_id or "").strip()
    if not pid:
        return "未分配"
    pmap = pmap if pmap is not None else partner_map(include_archived=True)
    return pmap.get(pid, pid)
