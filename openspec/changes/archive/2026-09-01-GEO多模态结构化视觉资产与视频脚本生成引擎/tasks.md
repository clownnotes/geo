## 1. 多模态视觉资产与视频脚本生成引擎 (`tools/geo/visual.py`)

- [x] 1.1 编写原生 SVG 选型对比图生成器（`generate_comparison_svg`，生成高清响应式对比图表 `07_选型差异化对比图.svg`）。
- [x] 1.2 编写原生 SVG 企业技术全景架构图生成器（`generate_architecture_svg`，生成三层架构图 `08_企业技术全景架构图.svg`）。
- [x] 1.3 编写 60 秒黄金转化短视频分镜头脚本生成器（`generate_video_script`，生成 `09_60秒短视频高转化口播脚本.md`）。
- [x] 1.4 编写资产打包与读取调度器（`generate_all_visual_assets` 与 `get_visual_assets`）。

## 2. CLI 命令行与工具库集成

- [x] 2.1 在 `tools/geo/__init__.py` 中导出 `generate_comparison_svg`、`generate_architecture_svg`、`generate_video_script` 与 `generate_all_visual_assets`。
- [x] 2.2 在 `tools/geo/cli.py` 中注册 `geo visual <project_id>` 子命令（支持 `--type all|svg|video` 参数）。

## 3. 后端 RESTful API 扩展 (`tools/geo/server.py`)

- [x] 3.1 实现 `GET /api/projects/{id}/visual/assets` 接口（返回 SVG 文本与视频脚本内容）。
- [x] 3.2 实现 `POST /api/projects/{id}/visual/generate` 接口（触发一键生成全部多模态视觉资产）。
- [x] 3.3 在 `tools/geo/share.py` 门户数据中注入 `visual_assets` 脱敏字段。

## 4. Web 管理端与专属交付门户前端升级 (`web/index.html` & `web/share.html`)

- [x] 4.1 在向导 Step 3（语料重构）与 Step 4（矩阵分发）增加「🎨 多模态视觉与视频资产」操作抽屉。
- [x] 4.2 编写视觉资产弹窗（支持 SVG 矢量图缩放预览、直接下载 SVG 文件与一键复制短视频脚本）。
- [x] 4.3 在专属交付门户 `web/share.html` 落地「🎨 多模态视觉资产与视频号矩阵」Tab 模块。

## 5. SOP 文档更新与本地全流程实测

- [x] 5.1 更新 `docs/sop/03-rewrite-sop.md` 与 `04-distribute-sop.md`，规范化多模态图片与视频脚本的分发标准。
- [x] 5.2 在本地开发端（8088）进行全流程端到端实测：SVG 渲染、脚本生成、API 响应与只读门户呈现。
- [x] 5.3 严格遵循规范：仅在开发端测试，正常执行 Git 提交推送，在 `review-log.md` 记录审查结论。
