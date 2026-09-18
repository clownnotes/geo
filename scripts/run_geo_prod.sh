#!/bin/bash
# 生产机（Mac mini）管理台启动脚本。
# 注意：若被复制到 /Users/ne/bin/run_geo.sh，不可用 dirname/.. 推算仓根（会变成 /Users/ne）。
# 优先：环境变量 GEO_ROOT；其次：脚本在仓内 scripts/ 时用相对路径；最后：默认 /Users/ne/apps/GEO。
set -euo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:${PATH:-}"
export GEO_BIND_HOST=0.0.0.0
if [[ -n "${GEO_ROOT:-}" ]]; then
  ROOT="$GEO_ROOT"
elif [[ -d "$(cd "$(dirname "$0")/.." && pwd)/tools/geo" ]]; then
  ROOT="$(cd "$(dirname "$0")/.." && pwd)"
else
  ROOT="/Users/ne/apps/GEO"
fi
cd "$ROOT" || exit 1
exec /usr/bin/python3 -m tools.geo web --port 8088
