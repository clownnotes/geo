# Tasks: AI原生交钥匙官网重构与阶段二落地折叠指引

## 1. 后端与静态建站引擎扩展
- [x] 1.1 升级 `tools/geo/scaffold.py`：实现 `build_turnkey_site_html(cfg)` 自动化编译逻辑，将生成的普林斯顿标准极速单页 `index.html` 以及 `llms.txt`、`robots.txt`、`schema.jsonld` 规范输出至 `projects/{id}/outputs/site/` 目录。
- [x] 1.2 升级 `tools/geo/server.py`：新增 `/api/projects/{id}/site/preview`（直接以 text/html 形式预览官网）与 `/api/projects/{id}/site/download`（打包 outputs/site 为 zip 并下载）接口。

## 2. 前端界面重构与折叠指引组件
- [x] 2.1 在 `web/index.html` 阶段二面板顶部构建模块化折叠使用说明抽屉组件（Collapsible Guidance Drawer），严格还原参考截图风格，包含标题、收起/展开切换以及 3 张横向高质卡片（这页在干嘛、核心定位模式、第一步第二步操作指引），并支持 `localStorage` 记住收起偏好。
- [x] 2.2 重构阶段二主工作区选项卡：将默认第一标签置换为【🖥️ 官网全景预览 (index.html)】，提供“一键新窗口打开预览”与“一键下载整站源码包”双核心行动按钮，保留底层三项技术协议代码作为专业支撑。

## 3. 端到端测试与真实项目回归
- [x] 3.1 针对标杆项目 `xuzhou_clownCoder_studio`（徐州邻里社区·老白）执行 `scaffold`，验证 `outputs/site/` 生成的完整度。
- [x] 3.2 在本地开发端 `http://127.0.0.1:8088` 验证界面渲染：折叠说明展开/收起是否丝滑，点击新窗口预览是否秒开并完美呈现，整站 zip 下载解压后是否完整可用。
