## 1. 分享链接与安全沙箱引擎 (`tools/geo/share.py`)

- [x] 1.1 编写高熵安全 Token 生成与 PIN 加盐哈希存储模块（`create_share_link`、`list_project_shares`、`revoke_share_link`，持久化至 `data/shares.json`）。
- [x] 1.2 编写只读沙箱数据组装器（`get_share_portal_data`，严格校验过期时间、PIN 提取码，仅提取交付 Markdown 与声量时序指标，物理隔离内部信息）。

## 2. CLI 命令行与工具库集成

- [x] 2.1 在 `tools/geo/__init__.py` 中导出 `create_share_link` 与 `get_share_portal_data`。
- [x] 2.2 在 `tools/geo/cli.py` 中注册 `geo share <project_id>` 子命令（支持 `--days` 与 `--pin` 参数并打印复制卡片）。

## 3. 后端 RESTful API 与页面路由 (`tools/geo/server.py`)

- [x] 3.1 实现 `POST /api/projects/{id}/share/create` 接口（生成分享 Token 并返回标准复制话术）。
- [x] 3.2 实现 `GET /api/projects/{id}/share/info` 与 `DELETE /api/share/{token}` 接口（管理端查询与一键作废）。
- [x] 3.3 实现 `GET /api/share/{token}/data` 公开只读沙箱数据接口（带 PIN 校验与 `X-Robots-Tag: noindex`）。
- [x] 3.4 实现 `GET /share/{token}` 路由（返回专属客户端单页应用 `web/share.html`）。

## 4. 专属甲方只读交付门户前端 (`web/share.html`)

- [x] 4.1 构建移动端与桌面端自适应的只读交付界面（含客户抬头、GEO 认证徽标、SEO 禁爬 Meta）。
- [x] 4.2 实现 PIN 提取码解锁弹窗（支持 SessionStorage 记住密码，解锁后平滑展现内容）。
- [x] 4.3 实现 5 步交付物 Tab 切换渲染（体检、底座、普林斯顿语料、四平台排版、声量周报与 Citation 图谱、竞品包抄）。
- [x] 4.4 接入一键打包下载交付 ZIP 与一键打印美化周报按钮。

## 5. Web 管理端交互升级 (`web/index.html`)

- [x] 5.1 在向导页顶部操作栏增加「🔗 客户专属交付链接」按钮。
- [x] 5.2 编写分享链接配置与生成弹窗（支持设置有效天数、可选 PIN 码、一键复制微信话术与查看已有链接）。

## 6. 知识库更新与全流程实测

- [x] 6.1 更新 `docs/sop/delivery-sop.md`，纳入甲方专属免密分享交付动作规范。
- [x] 6.2 进行全流程端到端实测：生成免密链接与带 PIN 链接，测试移动端排版、数据隔离、作废与过期拦截。
- [x] 6.3 在 `review-log.md` 记录审查与实测结论。
