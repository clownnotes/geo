#!/usr/bin/env bash
# [2026-10-07] [跨仓朋友协作] 将纯源码独立仓库中朋友合并的 PR 代码对位合入主工程
set -euo pipefail

GEO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SOURCE_ROOT="${1:-$(cd "$GEO_ROOT/.." && pwd)/GEO-Core}"

if [[ ! -d "$SOURCE_ROOT" ]]; then
  echo "错误: 未找到纯源码仓库目录: $SOURCE_ROOT"
  echo "使用方法: ./scripts/sync_pull_from_core_repo.sh [纯源码仓库绝对路径]"
  exit 1
fi

echo "============================================================================="
echo "  [GEO 协作代码合流入主仓工具]"
echo "  源纯源码仓: $SOURCE_ROOT"
echo "  目标主工程: $GEO_ROOT"
echo "============================================================================="

# 1. 对位同步前端 (web/)
if [[ -d "$SOURCE_ROOT/web" ]]; then
  echo ">>> 正在合入前端业务代码 (web/)..."
  rsync -av \
    --exclude="node_modules" \
    --exclude=".DS_Store" \
    --exclude="dist" \
    "$SOURCE_ROOT/web/" "$GEO_ROOT/web/"
fi

# 2. 对位同步后端 (tools/)
if [[ -d "$SOURCE_ROOT/tools" ]]; then
  echo ">>> 正在合入后端业务代码 (tools/)..."
  rsync -av \
    --exclude="__pycache__" \
    --exclude="*.pyc" \
    --exclude=".DS_Store" \
    "$SOURCE_ROOT/tools/" "$GEO_ROOT/tools/"
fi

# 3. 对位同步网关 (gateway/)
if [[ -d "$SOURCE_ROOT/gateway" ]]; then
  echo ">>> 正在合入网关代码 (gateway/)..."
  rsync -av \
    --exclude="__pycache__" \
    --exclude="*.pyc" \
    --exclude=".DS_Store" \
    "$SOURCE_ROOT/gateway/" "$GEO_ROOT/gateway/"
fi

# 4. 同步依赖变更 (若朋友新增了依赖)
if [[ -f "$SOURCE_ROOT/package.json" ]]; then
  cp -f "$SOURCE_ROOT/package.json" "$GEO_ROOT/package.json"
fi
if [[ -f "$SOURCE_ROOT/requirements.txt" ]]; then
  cp -f "$SOURCE_ROOT/requirements.txt" "$GEO_ROOT/requirements.txt"
fi

echo "============================================================================="
echo "  [SUCCESS] 协作者代码已成功合流入主工程！"
echo "  下一步建议:"
echo "    1. 运行 git status 和 git diff 检查合并差异是否清晰可读"
echo "    2. 运行 node tests/smoke_studio_artifacts.mjs 验证自动化冒烟断言"
echo "============================================================================="
