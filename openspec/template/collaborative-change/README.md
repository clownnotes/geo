# 多 IDE 协同 OpenSpec 模板

支持 Antigravity（开发）+ Windsurf / Claude Code（审核/对齐）的双端协作工作流。

## 用法

### 1. 创建新变更
```bash
./opsx propose <需求名称>
```
会自动生成中文变更目录，并预置 `proposal.md`、`design.md`、`tasks.md`、`review-log.md`。

### 2. 检查状态
```bash
./opsx status
```

### 3. 归档变更
```bash
./opsx archive
```
