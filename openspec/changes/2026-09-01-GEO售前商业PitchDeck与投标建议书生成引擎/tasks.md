## 1. 售前 Pitch Deck 与投标建议书核心引擎 (`tools/geo/pitch.py`)

- [x] 1.1 编写阶梯商业报价与能力对比模型（`calculate_pitch_quote`，输出基础版、专业版、集团旗舰版 3 档配置与报价）。
- [x] 1.2 编写全案商业服务投标建议书生成器（`generate_pitch_deck`，输出《00_GEO全案商业服务投标建议书与PitchDeck.md》）。
- [x] 1.3 编写 10 页全屏交互式幻灯片生成器（`generate_pitch_presentation_html`，支持深色科技风全屏放映、键盘翻页与沙箱推演演示）。
- [x] 1.4 编写 A4 排版商业标书打印生成器（`generate_print_pitch_html`，支持直接打印或存为 PDF）。

## 2. CLI 命令行与工具库集成

- [x] 2.1 在 `tools/geo/__init__.py` 中导出 `generate_pitch_deck`、`generate_pitch_presentation_html` 与 `calculate_pitch_quote`。
- [x] 2.2 在 `tools/geo/cli.py` 中注册 `geo pitch <project_id> [--tier standard] [--slides]` 子命令。

## 3. 后端 RESTful API 扩展 (`tools/geo/server.py` & `share.py`)

- [x] 3.1 实现 `GET /api/projects/{id}/pitch/data` 接口（返回 Pitch 建议书与阶梯报价）。
- [x] 3.2 实现 `GET /api/projects/{id}/pitch/slides` 接口（交互式幻灯片放映页）。
- [x] 3.3 实现 `GET /api/projects/{id}/pitch/print` 接口（商业建议书 A4 打印页）。
- [x] 3.4 在专属交付门户 `tools/geo/share.py` 注入售前提案与放映入口。

## 4. Web 管理工作台与专属交付门户前端升级 (`web/index.html` & `web/share.html`)

- [x] 4.1 在向导 Step 1（调研审计）及顶部增加「🎯 售前 Pitch Deck」与「🖥️ 放映幻灯片」操作按钮与弹窗。
- [x] 4.2 在专属交付门户 `web/share.html` 呈现「🎯 商业全案投标建议书」查验与全屏幻灯片放映卡片。

## 5. SOP 文档更新与本地全流程实测

- [x] 5.1 更新 `docs/sop/delivery-sop.md` 与 `01-audit-sop.md`，规范化售前勘测、投标比选与 Pitch 演示 SOP。
- [x] 5.2 在本地开发端（8088）进行全流程端到端实测：建议书生成、全屏幻灯片翻页、打印与门户交互。
- [x] 5.3 严格遵循规范：仅在开发端测试，正常执行 Git 提交推送，在 `review-log.md` 记录审查结论。
