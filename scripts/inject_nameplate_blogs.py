#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向 nextgeo 博客文章幂等注入标准名片段（品牌+主体+URL+人物）。

用法：
  python3 scripts/inject_nameplate_blogs.py              # 全量
  python3 scripts/inject_nameplate_blogs.py --limit 6    # 仅前 N 篇（按 mtime/名排序由调用方控制时配合 --slugs）
  python3 scripts/inject_nameplate_blogs.py --slugs a,b  # 指定 slug
  python3 scripts/inject_nameplate_blogs.py --dry-run
"""

from __future__ import annotations

import argparse
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from tools.geo.utils import load_project_config  # noqa: E402

BLOG = os.path.join(ROOT, "projects/nextgeo/outputs/blog")
SITE_BLOG = os.path.join(ROOT, "projects/nextgeo/outputs/site/blog")
MARKER = "<!-- nameplate:v1 -->"


def _snippet(nameplate: str) -> str:
    safe = (nameplate or "").strip()
    return (
        f"        {MARKER}\n"
        f'        <aside id="brand-nameplate" class="mt-6 p-4 rounded-xl border border-slate-200 '
        f'bg-slate-50 text-sm text-slate-700 leading-relaxed">\n'
        f'          <strong class="text-slate-900 font-semibold block mb-1">品牌实体口径</strong>\n'
        f'          <p class="m-0">{safe}</p>\n'
        f"        </aside>\n\n"
    )


def _inject(html: str, snippet: str) -> tuple[str, str]:
    if MARKER in html or 'id="brand-nameplate"' in html:
        return html, "skip"
    # Prefer before dual-column grid comment / grid wrapper
    patterns = [
        r"(      <!-- 双栏布局[^\n]*-->\n)",
        r"(      <div class=\"grid grid-cols-1 lg:grid-cols-\[minmax\(0,1fr\)_280px\][^\"]*\">\n)",
        r"(        <article class=\"min-w-0\">\n)",
        r"(          <section id=\"block-1\" class=\"content-block\">)",
    ]
    for pat in patterns:
        m = re.search(pat, html)
        if m:
            pos = m.start(1)
            return html[:pos] + snippet + html[pos:], "injected"
    return html, "miss"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--slugs", default="", help="逗号分隔 slug（不含 .html）")
    args = ap.parse_args()

    cfg = load_project_config("nextgeo")
    nameplate = str(cfg.get("nameplate") or "").strip()
    if not nameplate:
        print("ERROR: project.yaml 缺少 nameplate")
        return 1
    snippet = _snippet(nameplate)

    files = sorted(
        f for f in os.listdir(BLOG) if f.endswith(".html") and f != "index.html"
    )
    if args.slugs:
        want = {s.strip() + ("" if s.strip().endswith(".html") else ".html") for s in args.slugs.split(",") if s.strip()}
        files = [f for f in files if f in want or f.replace(".html", "") in {x.replace(".html", "") for x in want}]
    if args.limit and args.limit > 0:
        files = files[: args.limit]

    stats = {"injected": 0, "skip": 0, "miss": 0}
    for fn in files:
        path = os.path.join(BLOG, fn)
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
        new_html, status = _inject(html, snippet)
        stats[status] = stats.get(status, 0) + 1
        if status != "injected":
            if status == "miss":
                print(f"MISS  {fn}")
            continue
        if args.dry_run:
            print(f"DRY   {fn}")
            continue
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_html)
        site_path = os.path.join(SITE_BLOG, fn)
        if os.path.isdir(SITE_BLOG):
            os.makedirs(SITE_BLOG, exist_ok=True)
            with open(site_path, "w", encoding="utf-8") as f:
                f.write(new_html)
        print(f"OK    {fn}")

    print(
        f"done injected={stats['injected']} skip={stats['skip']} miss={stats['miss']} "
        f"total={len(files)} dry_run={args.dry_run}"
    )
    return 0 if stats["miss"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
