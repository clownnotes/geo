#!/usr/bin/env bash
# 开发本机 → mini 小毛驴/管理端隧道自检（与 LaunchAgent com.xiulan.tunnel-mini 配套）
# 用法：./scripts/ensure_mini_tunnel.sh
set -euo pipefail
LABEL="gui/$(id -u)/com.xiulan.tunnel-mini"
PLIST="${HOME}/Library/LaunchAgents/com.xiulan.tunnel-mini.plist"

if [[ ! -f "$PLIST" ]]; then
  echo "缺少 $PLIST — 请先按团队模板安装 LaunchAgent"
  exit 1
fi

launchctl kickstart -k "$LABEL" 2>/dev/null || {
  launchctl bootstrap "gui/$(id -u)" "$PLIST" 2>/dev/null || launchctl load "$PLIST"
  launchctl kickstart -k "$LABEL" || true
}

echo -n "探测 127.0.0.1:3001 "
for i in $(seq 1 15); do
  if curl -sS -m 2 "http://127.0.0.1:3001/api/health" 2>/dev/null | grep -q '"status"'; then
    echo "OK ($i)"
    exit 0
  fi
  echo -n "."
  sleep 1
done
echo
echo "失败。看 /tmp/tunnel-mini.log ；确认 ~/.ssh/config 里 Host mini 使用 ProxyJump vps"
exit 1
