# Tasks: 平台统一托管与VPS反代交钥匙建站架构

## 1. 后端服务与路由扩展 (含安全与鉴权契约)
- [x] 1.1 扩展 `tools/geo/server.py`：实现生产级纯净静态路由 `GET /sites/{project_id}/` 及其静态子文件路由：
  - 强制加入安全沙箱：`project_id` 正则 `^[a-zA-Z0-9_-]+$` 校验，`os.path.commonpath` 严格锁定在 `outputs/site/`；
  - 拦截任意包含 `..` 或越界读取 `project.yaml`/源码的操作（返回 403/404）；
  - 未就绪/未编译项目（缺少 `outputs/site/index.html`）返回 404；
  - 本地预览态响应头统一注入 `Cache-Control: no-cache, no-store, must-revalidate`。
- [x] 1.2 扩展 `tools/geo/server.py`：实现 `GET /api/projects/{id}/site/nginx-conf` 接口：
  - 必须经过 `require_auth` Bearer Token 强鉴权（未登录返回 401）；
  - 动态注入回源物理机地址（默认占位符 `http://<YOUR_PHYSICAL_MAC_IP_OR_DDNS>:8088`，支持 `?origin=` 参数覆盖）；
  - 输出带 `proxy_cache` 7 天容灾缓存的 Nginx 配置，附带腾讯云 CDN 命令行刷新 (Purge Cache) 指引。

## 2. 前端阶段二交互与中控台改造
- [x] 2.1 升级 `web/index.html` 阶段二发布卡片：整合【🟢 在线托管运行中】指示器、【🌐 独立站点新窗口直访】、【⚡ 查看/复制 VPS 反代配置】与【📦 源码离线备份导出】。
- [x] 2.2 增加 VPS Nginx 反代配置查看模态框与一键复制功能，明确提示“公网回源 IP 替换”与“腾讯云 CDN 缓存刷新命令”。
- [x] 2.3 更新阶段二顶部折叠使用说明文案，清晰说明物理机+VPS转发的落地流程。

## 3. 本地安全防护与功能回归测试
- [x] 3.1 本地测试 `curl -I http://127.0.0.1:8088/sites/xuzhou_clownCoder_studio/`，验证纯净单页加载正常且包含 `no-cache` 头。
- [x] 3.2 安全测试路径穿越：`curl http://127.0.0.1:8088/sites/..%2f..%2fproject.yaml` 验证被有效拦截（返回 400 或 404）。
- [x] 3.3 安全测试鉴权：未带 Token 访问 `GET /api/projects/{id}/site/nginx-conf` 验证返回 401；带 Token 验证返回 200 及正确的 upstream 占位符与 CDN 刷新命令。
- [x] 3.4 检查 Git 状态与生产隔离红线（严禁推生产 `mini`）。

