# 客户体检报告只读静态页

## Why

企业管理端的 01 体检报告需要发给客户快速打开；客户不应接触管理端登录与写接口。现有专属交付门户偏全案大屏，缺少「打开就是报告正文」的轻量入口。

## What

1. 在现有分享 Token 上增加 `?view=audit` 报告专页与 `/api/share/{token}/audit-html` 自包含 HTML。
2. 管理端可导出 `01_企业AI可见度现状体检报告_客户版.html`，并可复制报告链接。
3. 签发主体统一为「邻里 GEO 工业级商业交付中心」；nextgeo 去掉「淮海经济区」服务腹地表述。

## Capabilities

- 客户凭 Token（可选 PIN）只读查看 01 报告。
- 链接可作废；响应 `noindex`。
- 不暴露管理端与其它项目数据。

## Impact

- `tools/geo/share.py`、`tools/geo/server.py`、`web/share.html`、`web/index.html`
- `tools/geo/audit.py` 报告模板抬头
- `projects/nextgeo/project.yaml` 与 01 报告页眉
