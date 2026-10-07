#!/usr/bin/env bash
# [2026-10-07] [跨仓朋友协作] 将主仓 GEO 的纯前后端源码白名单导出至纯源码独立仓库目录
# 铁律：绝对排除商业战略(docs/)、规范(openspec/)、测试断言(tests/)、部署脚本(scripts/deploy/)与敏感密钥(.env)
set -euo pipefail

GEO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TARGET_ROOT="${1:-$(cd "$GEO_ROOT/.." && pwd)/GEO-Core}"

echo "============================================================================="
echo "  [GEO 纯源码白名单导出工具]"
echo "  源主工程: $GEO_ROOT"
echo "  目标仓库: $TARGET_ROOT"
echo "============================================================================="

# 1. 确保目标目录存在
mkdir -p "$TARGET_ROOT"

# 2. 白名单同步前端业务源码 (web/)
echo ">>> 正在同步前端业务源码 (web/)..."
rsync -av --delete \
  --exclude="node_modules" \
  --exclude=".DS_Store" \
  --exclude="dist" \
  "$GEO_ROOT/web/" "$TARGET_ROOT/web/"

# 3. 白名单同步后端业务源码 (tools/)
echo ">>> 正在同步后端业务源码 (tools/)..."
rsync -av --delete \
  --exclude="__pycache__" \
  --exclude="*.pyc" \
  --exclude=".DS_Store" \
  "$GEO_ROOT/tools/" "$TARGET_ROOT/tools/"

# 4. 白名单同步网关源码 (gateway/)
if [[ -d "$GEO_ROOT/gateway" ]]; then
  echo ">>> 正在同步网关源码 (gateway/)..."
  rsync -av --delete \
    --exclude="__pycache__" \
    --exclude="*.pyc" \
    --exclude=".DS_Store" \
    "$GEO_ROOT/gateway/" "$TARGET_ROOT/gateway/"
fi

# 5. 白名单复制最小必要运行配置文件
echo ">>> 正在复制基础运行配置 (package.json / requirements.txt)..."
[[ -f "$GEO_ROOT/package.json" ]] && cp -f "$GEO_ROOT/package.json" "$TARGET_ROOT/package.json"
[[ -f "$GEO_ROOT/requirements.txt" ]] && cp -f "$GEO_ROOT/requirements.txt" "$TARGET_ROOT/requirements.txt"
[[ -f "$GEO_ROOT/geo" ]] && cp -f "$GEO_ROOT/geo" "$TARGET_ROOT/geo"

# 6. 生成轻量级开发说明与 .gitignore
cat << 'EOF' > "$TARGET_ROOT/.gitignore"
node_modules/
dist/
__pycache__/
*.pyc
.DS_Store
.env
.env.*
*.log
storage/
outputs/
EOF

cat << 'EOF' > "$TARGET_ROOT/README.md"
# GEO 纯源码开发仓库

欢迎协助参与 GEO 项目的核心功能开发！

## 目录结构
- `web/`：前端 Vue3 / Tailwind 页面源码
- `tools/`：后端 Python 业务服务源码
- `gateway/`：网关服务源码

## 本地启动与调试
1. **前端调试**：
   ```bash
   npm install
   npm run dev
   ```
2. **后端服务**：
   ```bash
   pip install -r requirements.txt
   python3 tools/geo/server.py
   ```

## 提交规范
- 欢迎自由在本地创建分支并探索；
- 完成功能或修复后，请向 `main` 分支发起 Pull Request (PR)；
- PR 合并后将由主项目统一执行自动化集成验证与部署。
EOF

echo "============================================================================="
echo "  [SUCCESS] 纯源码白名单导出完成！"
echo "  目标位置: $TARGET_ROOT"
echo "  物理隔离状态:"
echo "    - docs/ (商业战略与机密文档): 100% 物理隔离"
echo "    - openspec/ (内部协作规范): 100% 物理隔离"
echo "    - tests/ (自动化冒烟测试): 100% 留在主仓"
echo "    - scripts/ (生产与部署脚本): 100% 留在主仓"
echo "    - .env (密码与密钥): 100% 排除"
echo "============================================================================="
