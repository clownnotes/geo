# -*- coding: utf-8 -*-
"""GEO 成员交付看板与企业透视模块 (tools/geo/perspective.py)

// [2026-09-20] [成员管理交付看板与企业透视改造]
面向对象抽象：
- MemberDeliveryCard: 成员交付看板卡片
- ProjectPerspectiveItem: 企业透视条目
"""

import os
import time
from .utils import load_project_config


def scan_projects_perspective(projects_dir):
    """扫描全部项目目录，抽取透视元数据并计算交付进度与最后活动时间。

    算法与 GET /api/projects 保持绝对一致：扫描 outputs/ 中的 01_~05_。
    """
    cache = {}
    if not projects_dir or not os.path.exists(projects_dir):
        return cache

    for item in os.listdir(projects_dir):
        p_dir = os.path.join(projects_dir, item)
        if not os.path.isdir(p_dir) or item.startswith("."):
            continue
        try:
            cfg = load_project_config(item, projects_dir=projects_dir)
            out_dir = cfg.get("_outputs_dir") or os.path.join(p_dir, "outputs")
            outputs = os.listdir(out_dir) if os.path.exists(out_dir) else []

            # 交付步骤与百分比计算（与现网 5 步向导同源）
            steps_done = 0
            if any("01_" in f for f in outputs): steps_done += 1
            if any("02_" in f for f in outputs) or "llms.txt" in outputs: steps_done += 1
            if any("03_" in f for f in outputs): steps_done += 1
            if any("04_" in f for f in outputs): steps_done += 1
            if any("05_" in f for f in outputs): steps_done += 1
            progress_pct = int((steps_done / 5) * 100)

            # 摸底状态枚举严格约束（仅 unprobed | baseline_ready | awaiting_retest）
            probe_status = str(cfg.get("probe_status") or "unprobed").strip() or "unprobed"
            if probe_status not in ("baseline_ready", "awaiting_retest"):
                probe_status = "unprobed"

            creator_user_id = str(cfg.get("creator_user_id") or "").strip()
            creator_name = str(cfg.get("creator_name") or "").strip()
            client_name = str(cfg.get("client_name") or cfg.get("company_name") or item)

            # 最后活动时间：取 project.yaml、outputs 目录及产出文件中的最新 mtime
            mtimes = []
            yaml_path = os.path.join(p_dir, "project.yaml")
            if os.path.exists(yaml_path):
                mtimes.append(os.path.getmtime(yaml_path))
            if os.path.exists(out_dir):
                mtimes.append(os.path.getmtime(out_dir))
                for f in outputs:
                    fp = os.path.join(out_dir, f)
                    if os.path.exists(fp):
                        mtimes.append(os.path.getmtime(fp))
            latest_mtime = max(mtimes) if mtimes else os.path.getmtime(p_dir)
            updated_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(latest_mtime))

            cache[item] = {
                "client_id": item,
                "client_name": client_name,
                "creator_user_id": creator_user_id,
                "creator_name": creator_name,
                "probe_status": probe_status,
                "steps_done": steps_done,
                "progress_pct": progress_pct,
                "updated_at": updated_at,
            }
        except Exception:
            continue

    return cache


def build_members_perspective(members, projects_dir):
    """为花名册中的运营成员富化交付看板与企业透视数据。

    自建判定铁律：
    - 仅当 p.creator_user_id 非空且等于 member.user_id 时为自建；
    - 严禁以 creator_name == m.name 判定自建；
    - 老项目无 creator_user_id 时归为老板分配。
    """
    project_cache = scan_projects_perspective(projects_dir)
    enriched = []

    for m in members or []:
        member_uid = str(m.get("user_id") or "").strip()
        allowed = list(m.get("allowed_projects") or [])

        perspective_projects = []
        self_created_count = 0
        assigned_count = 0

        for pid in allowed:
            pinfo = project_cache.get(pid)
            if pinfo:
                p_uid = pinfo.get("creator_user_id") or ""
                # 自建只认 creator_user_id
                is_self = bool(member_uid and p_uid and p_uid == member_uid)
                origin_label = "自建" if is_self else "老板分配"
                if is_self:
                    self_created_count += 1
                else:
                    assigned_count += 1

                perspective_projects.append({
                    "client_id": pid,
                    "client_name": pinfo.get("client_name") or pid,
                    "is_self_created": is_self,
                    "origin_label": origin_label,
                    "probe_status": pinfo.get("probe_status", "unprobed"),
                    "steps_done": pinfo.get("steps_done", 0),
                    "progress_pct": pinfo.get("progress_pct", 0),
                    "updated_at": pinfo.get("updated_at", ""),
                })
            else:
                assigned_count += 1
                perspective_projects.append({
                    "client_id": pid,
                    "client_name": pid,
                    "is_self_created": False,
                    "origin_label": "老板分配",
                    "probe_status": "unprobed",
                    "steps_done": 0,
                    "progress_pct": 0,
                    "updated_at": "",
                })

        card = dict(m)
        card["projects"] = perspective_projects
        card["total_count"] = len(perspective_projects)
        card["self_created_count"] = self_created_count
        card["assigned_count"] = assigned_count
        enriched.append(card)

    return enriched
