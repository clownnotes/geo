# 设计

## 安全模型

复用 `shares.json` Token + 可选 PIN + 可作废；公开路由仅：
- `GET /share/{token}?view=audit` → `share.html` 报告阅读态
- `GET /api/share/{token}/audit-report` → Markdown JSON
- `GET /api/share/{token}/audit-html` → 自包含 HTML

管理端：
- `POST /api/projects/{id}/export-audit-html` → 落盘客户版 HTML

## 数据

仅读取 `outputs/01_企业AI可见度现状体检与商业诊断报告.md`。

## 签发

模板与客户页抬头：`邻里 GEO 工业级商业交付中心`。
