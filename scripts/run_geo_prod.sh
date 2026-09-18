#!/bin/bash
# 生产机（Mac mini）管理台启动脚本。
# 必须绑定 0.0.0.0，否则 VPS / EdgeOne 经 Tailscale 反代打不到本机，域名会 502。
# 开发本机请直接：python3 -m tools.geo web --port 8088（默认只听 127.0.0.1）
set -euo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:${PATH:-}"
export GEO_BIND_HOST=0.0.0.0
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
exec /usr/bin/python3 -m tools.geo web --port 8088
