# Tasks: 平台统一托管与VPS反代交钥匙建站架构

## 1. 后端服务与路由扩展
- [ ] 1.1 扩展 `tools/geo/server.py`：实现生产级纯净静态路由 `GET /sites/{project_id}/` 及其静态子文件路由（`robots.txt`、`llms.txt`、`schema.jsonld`），实现无向导框架独立运行。
- [ ] 1.2 扩展 `tools/geo/server.py`：实现 `GET /api/projects/{id}/site/nginx-conf` 接口，根据项目域名与回源信息自动生成带 `proxy_cache` 容灾机制的生产级 Nginx 配置。

## 2. 前端阶段二交互与中控台改造
- [ ] 2.1 升级 `web/index.html` 阶段二发布卡片：整合【🟢 在线托管运行中】指示器、【🌐 独立站点新窗口直访】、【⚡ 查看/复制 VPS 反代配置】与【📦 源码离线备份导出】。
- [ ] 2.2 增加 VPS Nginx 反代配置查看弹窗与一键复制功能，配置说明中包含 SSL 挂载与防断网缓存参数。
- [ ] 2.3 更新阶段二顶部折叠使用说明文案，明确标明“集中全托管”与“VPS反代零运维”的落地方式。

## 3. 本地验证与端到端测试
- [ ] 3.1 本地测试 `curl http://127.0.0.1:8088/sites/xuzhou_clownCoder_studio/`，验证纯净单页加载正常。
- [ ] 3.2 本地测试 Nginx 反代配置生成接口，确认包含长效容灾缓存指令。
- [ ] 3.3 检查 Git 状态并在本地控制台完成全链路点击验收。
