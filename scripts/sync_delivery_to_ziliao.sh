#!/usr/bin/env bash
# 将主仓 GEO 中的交付站/媒体资产同步到并列目录 GEOZiLiao（仅本地拷贝，需再 git push）
set -euo pipefail

GEO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ZILIAO_ROOT="$(cd "$GEO_ROOT/../GEOZiLiao" && pwd)"

if [[ ! -d "$ZILIAO_ROOT/.git" ]]; then
  echo "错误: 未找到资料仓 $ZILIAO_ROOT （请先初始化并 clone GEOZiLiao）"
  exit 1
fi

sync_one() {
  local id="$1"
  local src_site="$GEO_ROOT/projects/$id/outputs/site"
  local src_assets="$GEO_ROOT/projects/$id/outputs/assets"
  local dst="$ZILIAO_ROOT/projects/$id"
  mkdir -p "$dst"
  local did=0
  if [[ -d "$src_site" ]]; then
    mkdir -p "$dst/site"
    rsync -a --delete "$src_site/" "$dst/site/"
    echo "  synced site  <- projects/$id/outputs/site"
    did=1
  fi
  if [[ -d "$src_assets" ]]; then
    mkdir -p "$dst/assets"
    rsync -a --delete "$src_assets/" "$dst/assets/"
    echo "  synced assets <- projects/$id/outputs/assets"
    did=1
  fi
  # 大 ZIP（若存在）
  local zip
  shopt -s nullglob
  for zip in "$GEO_ROOT/projects/$id/outputs/"*_geo_delivery_archive.zip "$GEO_ROOT/projects/$id/outputs/"*delivery*.zip; do
    mkdir -p "$dst/archives"
    cp -f "$zip" "$dst/archives/"
    echo "  copied $(basename "$zip") -> archives/"
    did=1
  done
  shopt -u nullglob
  if [[ "$did" -eq 0 ]]; then
    echo "  skip $id （无 site/assets/zip）"
  else
    echo "OK $id -> $dst"
  fi
}

echo "GEO     = $GEO_ROOT"
echo "GEOZiLiao = $ZILIAO_ROOT"

if [[ $# -ge 1 ]]; then
  for id in "$@"; do
    sync_one "$id"
  done
else
  for dir in "$GEO_ROOT"/projects/*/; do
    id="$(basename "$dir")"
    [[ "$id" == _template ]] && continue
    [[ -d "$dir" ]] || continue
    sync_one "$id"
  done
fi

echo ""
echo "下一步（备份生效必须 push）："
echo "  cd \"$ZILIAO_ROOT\""
echo "  git add -A && git status"
echo "  git commit -m \"chore(sites): sync delivery assets\""
echo "  git push origin main"
