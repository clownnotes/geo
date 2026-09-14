#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""官网双栈自检：解析 A/AAAA，并分别探测 443 TLS。

用法:
  python3 scripts/check_site_dualstack.py https://www.baicl.cc

说明:
  - 本机若只有链路本地 IPv6（无公网 IPv6），AAAA 探测失败不代表 CDN 挂了。
  - www.baicl.cc 走 EdgeOne（*.eo.dnse0.com）。请在腾讯云 EdgeOne 控制台确认：
      站点加速 → 网络优化 → 「IPv6 访问」= 开启
  - 有公网 IPv6 的网络（部分手机蜂窝）上应看到 AAAA 探测为 ok。
"""
from __future__ import annotations

import json
import sys
from urllib.parse import urlparse

sys.path.insert(0, ".")
from tools.geo.audit import _probe_ip, _resolve_dualstack, fetch_url_content  # noqa: E402


def main() -> int:
    url = (sys.argv[1] if len(sys.argv) > 1 else "https://www.baicl.cc").strip()
    if not url.startswith("http"):
        url = "https://" + url
    host = urlparse(url).hostname or ""
    dual = _resolve_dualstack(host)
    probe = {
        "a": {ip: _probe_ip(host, ip) for ip in dual["a"]},
        "aaaa": {ip: _probe_ip(host, ip) for ip in dual["aaaa"]},
    }
    status, body, _ = fetch_url_content(url)
    out = {
        "url": url,
        "host": host,
        "dns": dual,
        "probe_443": probe,
        "urllib_fetch_status": status,
        "urllib_fetch_hint": (body[:160] if status != 200 else f"ok bytes≈{len(body)}"),
        "edgeone_checklist": [
            "打开 https://console.cloud.tencent.com/edgeone",
            "进入站点 baicl.cc → 站点加速 → 网络优化",
            "确认「IPv6 访问」已开启（开启后 DNS 才会稳定返回可用 AAAA）",
            "用手机蜂窝等有公网 IPv6 的网络再跑本脚本，AAAA 应为 ok",
        ],
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    aaaa = dual["aaaa"]
    if not aaaa:
        print("\n结论: 无 AAAA。请到 EdgeOne 开启 IPv6 访问，或检查 DNS。", file=sys.stderr)
        return 2
    if all(v != "ok" for v in probe["aaaa"].values()):
        print(
            "\n结论: 有 AAAA 但本机 IPv6 连不上。"
            "若本机无公网 IPv6，请换网络复核；同时确认 EdgeOne IPv6 开关已开。",
            file=sys.stderr,
        )
        return 1
    print("\n结论: 本机 IPv6 探测通过。", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
