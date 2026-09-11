#!/usr/bin/env bash
# 生产机一键：确保 GEOZiLiao 就位 → 拉主仓 → 立刻从资料仓 restore 站点
# 用法（在 mini 上，或本机 ssh mini 执行）：
#   bash scripts/cutover_ziliao_on_mini.sh
set -euo pipefail

GEO_ROOT="${GEO_ROOT:-/Users/ne/apps/GEO}"
ZILIAO_ROOT="${ZILIAO_ROOT:-/Users/ne/apps/GEOZiLiao}"
ZILIAO_REMOTE="${ZILIAO_REMOTE:-https://git.baicl.cc/admin/GEOZiLiao.git}"

if [[ ! -d "$GEO_ROOT/.git" ]]; then
  echo "错误: 找不到主仓 $GEO_ROOT"
  exit 1
fi

echo "==> 1) 资料仓 GEOZiLiao"
if [[ ! -d "$ZILIAO_ROOT/.git" ]]; then
  echo "    克隆 $ZILIAO_REMOTE -> $ZILIAO_ROOT"
  git clone "$ZILIAO_REMOTE" "$ZILIAO_ROOT"
else
  echo "    已存在，拉取最新"
  git -C "$ZILIAO_ROOT" pull --ff-only origin main
fi

echo "==> 2) 主仓 GEO pull"
git -C "$GEO_ROOT" pull --ff-only github main || git -C "$GEO_ROOT" pull --ff-only origin main

echo "==> 3) 从资料仓恢复 site/assets（必须紧接 pull 之后）"
bash "$GEO_ROOT/scripts/restore_delivery_from_ziliao.sh"

echo "==> 4) 抽检 nextgeo"
if [[ -f "$GEO_ROOT/projects/nextgeo/outputs/site/index.html" ]]; then
  echo "OK nextgeo site 在盘"
else
  echo "FAIL: nextgeo site 缺失，请检查 GEOZiLiao 是否含 projects/nextgeo/site"
  exit 1
fi

echo "完成。线上静态站点应已从资料仓填回。"
