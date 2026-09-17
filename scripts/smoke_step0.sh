#!/usr/bin/env bash
# 阶段零 Vue3 组件岛一键冒烟（改 step0 后必须通过才可宣称完成）
set -eo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

echo "=================================================="
echo "  [GEO 阶段零冒烟] smoke:step0"
echo "=================================================="

echo ">> 1/4 build:step0"
BUILD_LOG="$(mktemp)"
if ! npm run build:step0 >"$BUILD_LOG" 2>&1; then
  echo "FAIL: npm run build:step0"
  tail -n 40 "$BUILD_LOG" || true
  rm -f "$BUILD_LOG"
  exit 1
fi
rm -f "$BUILD_LOG"
echo "   OK build"

echo ">> 2/4 产物体积"
BUNDLE_FILE="$REPO_ROOT/web/assets/step0/step0.js"
if [ ! -f "$BUNDLE_FILE" ]; then
  echo "FAIL: 缺少 $BUNDLE_FILE"
  exit 1
fi
FILE_SIZE=$(wc -c < "$BUNDLE_FILE" | tr -d ' ')
if [ "$FILE_SIZE" -lt 50000 ]; then
  echo "FAIL: 产物过小 (${FILE_SIZE} bytes, 需要 > 50000)"
  exit 1
fi
echo "   OK web/assets/step0/step0.js ($((FILE_SIZE / 1024)) KB)"

echo ">> 3/4 /assets 路由（8088 可选）"
if curl -s --connect-timeout 1 "http://127.0.0.1:8088/" > /dev/null 2>&1; then
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8088/assets/step0/step0.js")
  if [ "$HTTP_CODE" != "200" ]; then
    echo "FAIL: /assets/step0/step0.js HTTP $HTTP_CODE (期望 200)"
    exit 1
  fi
  NOT_FOUND_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8088/assets/step0/non_existent_test.js")
  if [ "$NOT_FOUND_CODE" != "404" ]; then
    echo "FAIL: 缺文件应 404，实际 HTTP $NOT_FOUND_CODE"
    exit 1
  fi
  echo "   OK 8088 静态映射 (200 / 404)"
else
  echo "   SKIP 8088 未运行（构建与产物已通过）"
fi

echo ">> 4/4 扫盘 probe_script_*.json"
OUT_DIR="$REPO_ROOT/projects/nextgeo/outputs"
if [ ! -d "$OUT_DIR" ]; then
  echo "FAIL: 缺少目录 $OUT_DIR"
  exit 1
fi
SCRIPT_COUNT=$(find "$OUT_DIR" -maxdepth 1 -name "probe_script_*.json" 2>/dev/null | wc -l | tr -d ' ')
echo "   OK nextgeo 清单份数: $SCRIPT_COUNT"

echo "=================================================="
echo "  smoke:step0 PASS"
echo "=================================================="
exit 0
