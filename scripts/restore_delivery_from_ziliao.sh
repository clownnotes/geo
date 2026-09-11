#!/usr/bin/env bash
# 将并列目录 GEOZiLiao 中的交付站/媒体资产恢复到主仓 GEO（本地拷贝，不改 git index）
set -euo pipefail

GEO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ZILIAO_ROOT="$(cd "$GEO_ROOT/../GEOZiLiao" && pwd)"

if [[ ! -d "$ZILIAO_ROOT/.git" ]]; then
  echo "错误: 未找到资料仓 $ZILIAO_ROOT"
  exit 1
fi

restore_one() {
  local id="$1"
  local src="$ZILIAO_ROOT/projects/$id"
  local dst_site="$GEO_ROOT/projects/$id/outputs/site"
  local dst_assets="$GEO_ROOT/projects/$id/outputs/assets"
  local dst_out="$GEO_ROOT/projects/$id/outputs"
  local did=0

  if [[ ! -d "$src" ]]; then
    echo "  skip $id （资料仓无此客户目录）"
    return 0
  fi
  mkdir -p "$dst_out"

  if [[ -d "$src/site" ]]; then
    mkdir -p "$dst_site"
    rsync -a --delete "$src/site/" "$dst_site/"
    echo "  restored site  -> projects/$id/outputs/site"
    did=1
  fi
  if [[ -d "$src/assets" ]]; then
    mkdir -p "$dst_assets"
    rsync -a --delete "$src/assets/" "$dst_assets/"
    echo "  restored assets -> projects/$id/outputs/assets"
    did=1
  fi
  if [[ -d "$src/archives" ]]; then
    shopt -s nullglob
    local z
    for z in "$src/archives/"*; do
      [[ -f "$z" ]] || continue
      cp -f "$z" "$dst_out/"
      echo "  restored $(basename "$z") -> outputs/"
      did=1
    done
    shopt -u nullglob
  fi
  if [[ "$did" -eq 0 ]]; then
    echo "  skip $id （无 site/assets/archives）"
  else
    echo "OK $id"
  fi
}

echo "GEO       = $GEO_ROOT"
echo "GEOZiLiao = $ZILIAO_ROOT"

if [[ $# -ge 1 ]]; then
  for id in "$@"; do
    restore_one "$id"
  done
else
  for dir in "$ZILIAO_ROOT"/projects/*/; do
    id="$(basename "$dir")"
    [[ "$id" == _template ]] && continue
    [[ -d "$dir" ]] || continue
    restore_one "$id"
  done
fi

echo ""
echo "说明: 恢复仅写本地磁盘；主仓若已 gitignore site/assets，不会自动进双推。"
