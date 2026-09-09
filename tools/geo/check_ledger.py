#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""运维检测台账：真机逾期判定 + append-only JSONL 检测日志。"""

from __future__ import annotations

import json
import os
import re
import secrets
import time
from datetime import datetime, timezone, timedelta
from typing import Any

from .utils import PROJECT_ROOT, PROJECTS_DIR, load_project_config
from .patrol import load_notification_settings

DATA_DIR = os.path.join(PROJECT_ROOT, "data")
LOG_FILE = os.path.join(DATA_DIR, "ops_check_logs.jsonl")

STATUS_ORDER = {"never": 0, "overdue": 1, "warn": 2, "ok": 3}


def _ensure_log_file() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write("")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_at_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    s = str(value).strip()
    if not s:
        return None
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def days_since_utc(at_iso: str | None, now: datetime | None = None) -> float | None:
    dt = parse_at_utc(at_iso)
    if not dt:
        return None
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    else:
        now = now.astimezone(timezone.utc)
    return max(0.0, (now - dt).total_seconds() / 86400.0)


def append_check_log(
    *,
    project_id: str,
    mode: str,
    operator: str = "system",
    keywords: list | None = None,
    sov_pct: float | None = None,
    summary: str = "",
    source_ref: str = "",
    at: str | None = None,
) -> dict:
    """追加一条检测日志。at 必须为 UTC ISO（缺省自动生成）。"""
    _ensure_log_file()
    kws = [str(k).strip() for k in (keywords or []) if str(k).strip()]
    row = {
        "id": f"chk_{int(time.time())}_{secrets.token_hex(3)}",
        "project_id": project_id,
        "at": at or utc_now_iso(),
        "operator": operator or "system",
        "mode": mode,
        "keywords": kws,
        "keyword_count": len(kws),
        "sov_pct": float(sov_pct) if sov_pct is not None else None,
        "summary": summary or "",
        "source_ref": source_ref
        or (f"projects/{project_id}/outputs/05_manual_probes.json" if mode == "manual_probe" else ""),
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def list_check_logs(project_id: str | None = None, limit: int = 100) -> list[dict]:
    _ensure_log_file()
    rows: list[dict] = []
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                if project_id and obj.get("project_id") != project_id:
                    continue
                rows.append(obj)
    except FileNotFoundError:
        return []
    rows.reverse()  # 新→旧
    return rows[: max(1, int(limit or 100))]


def _policy_from_settings(settings: dict | None = None) -> dict:
    s = settings if settings is not None else load_notification_settings()
    return {
        "warn_days": float(s.get("warn_days", 7) or 7),
        "overdue_days": float(s.get("overdue_days", 14) or 14),
        "min_manual_keywords": int(s.get("min_manual_keywords", 1) or 1),
        "overdue_webhook_enabled": bool(s.get("overdue_webhook_enabled", False)),
    }


def _latest_valid_manual(logs: list[dict], min_kw: int) -> dict | None:
    for row in logs:  # already new→old
        if row.get("mode") != "manual_probe":
            continue
        if int(row.get("keyword_count") or len(row.get("keywords") or [])) >= min_kw:
            return row
    return None


def _count_manual_keywords_unique(project_id: str, logs: list[dict]) -> int:
    seen = set()
    for row in logs:
        if row.get("mode") != "manual_probe":
            continue
        for k in row.get("keywords") or []:
            if k:
                seen.add(str(k).strip())
    # 兜底读 05_manual_probes.json
    try:
        cfg = load_project_config(project_id)
        path = os.path.join(cfg.get("_outputs_dir", ""), "05_manual_probes.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                for key, val in data.items():
                    if isinstance(val, dict) and val.get("keyword"):
                        seen.add(str(val["keyword"]).strip())
                    elif isinstance(key, str) and "|" in key:
                        # model|keyword
                        seen.add(key.split("|", 1)[-1].strip())
    except Exception:
        pass
    return len({x for x in seen if x})


def classify_status(days: float | None, policy: dict, has_manual: bool) -> str:
    if not has_manual or days is None:
        return "never"
    if days >= policy["overdue_days"]:
        return "overdue"
    if days >= policy["warn_days"]:
        return "warn"
    return "ok"


def build_check_ledger(now: datetime | None = None) -> dict:
    """聚合全部项目台账行。"""
    policy = _policy_from_settings()
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    all_logs = list_check_logs(limit=5000)
    by_project: dict[str, list] = {}
    for row in all_logs:
        pid = row.get("project_id")
        if not pid:
            continue
        by_project.setdefault(pid, []).append(row)

    rows = []
    if os.path.isdir(PROJECTS_DIR):
        for item in sorted(os.listdir(PROJECTS_DIR)):
            if item.startswith(".") or item == "_template":
                continue
            p_dir = os.path.join(PROJECTS_DIR, item)
            if not os.path.isdir(p_dir):
                continue
            try:
                cfg = load_project_config(item)
            except Exception:
                continue
            plogs = by_project.get(item, [])
            valid = _latest_valid_manual(plogs, policy["min_manual_keywords"])
            days = days_since_utc(valid.get("at") if valid else None, now=now)
            status = classify_status(days, policy, bool(valid))
            kw_count = int(valid.get("keyword_count") or 0) if valid else 0
            unique_kw = _count_manual_keywords_unique(item, plogs)
            sov = valid.get("sov_pct") if valid else None
            sample_note = ""
            if valid and kw_count <= 1:
                sample_note = "样本量小，仅供参考"
            rows.append({
                "project_id": item,
                "client_name": cfg.get("client_name") or cfg.get("company_name") or item,
                "status": status,
                "last_manual_at": valid.get("at") if valid else None,
                "manual_keyword_count": unique_kw,
                "last_event_keyword_count": kw_count,
                "last_sov_pct": sov,
                "sample_note": sample_note,
                "days_since": round(days, 2) if days is not None else None,
            })

    rows.sort(key=lambda r: (STATUS_ORDER.get(r["status"], 9), -(r["days_since"] or 0), r["client_name"]))

    summary = {
        "never": sum(1 for r in rows if r["status"] == "never"),
        "overdue": sum(1 for r in rows if r["status"] == "overdue"),
        "warn": sum(1 for r in rows if r["status"] == "warn"),
        "ok": sum(1 for r in rows if r["status"] == "ok"),
        "total": len(rows),
    }
    return {
        "success": True,
        "policy": policy,
        "summary": summary,
        "rows": rows,
        "generated_at": utc_now_iso(),
    }


def log_manual_ingest(
    project_id: str,
    *,
    keyword: str,
    operator: str,
    metrics: dict | None = None,
) -> dict:
    sov = None
    if metrics and isinstance(metrics, dict):
        sov = metrics.get("sov_pct")
    return append_check_log(
        project_id=project_id,
        mode="manual_probe",
        operator=operator or "system",
        keywords=[keyword] if keyword else [],
        sov_pct=sov,
        summary=f"真机回填 1 词；SOV={sov if sov is not None else '—'}",
        source_ref=f"projects/{project_id}/outputs/05_manual_probes.json",
    )
