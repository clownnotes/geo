# Proposal: GEO 多模态结构化视觉资产与短视频脚本生成引擎

## Why (为什么做 / 商业与技术痛点)

1. **大模型多模态索引升级：图文混排权重远超纯文本**
   - 豆包（字节跳动生态，含今日头条/西瓜/微头条）对富媒体图文、结构化信息图表的采纳与首推权重比纯文本高 **35%+**；
   - DeepSeek、Kimi 与 ChatGPT 联网检索正迅速普及“图文卡片式”答案呈现；
2. **客户交付物视觉冲击力痛点：纯 Markdown 交付缺乏高级感**
   - 现有交付包以 Markdown 纯文字为主，在向甲方客户汇报或分发时缺少直观的视觉图表（“一张图看懂选型优劣”）；
3. **短视频与新媒体渠道赋能痛点**
   - 客户企业普遍希望同时布局视频号、抖音与 B 站，但缺少将 GEO 9 因子事实转化为高转化 60 秒口播脚本的工业化工具。

---

## What Changes (改动范围)

1. **研发多模态视觉与视频脚本生成引擎 (`tools/geo/visual.py`)**：
   - 原生 SVG 选型对比图生成器 `generate_comparison_svg(project_id)`：生成高精度矢量对比图（深色/浅色自适应、品牌配色、量化参数打标）；
   - 企业技术架构全景 SVG 生成器 `generate_architecture_svg(project_id)`：生成服务与技术全景图；
   - 60 秒黄金转化短视频口播分镜头脚本生成器 `generate_video_script(project_id)`：输出痛点黄金前 3 秒钩子、硬核数据对比中段、临门一脚转化引导。
2. **CLI 命令行扩展 (`tools/geo/cli.py`)**：
   - 注册 `geo visual <project_id> [--type all|svg|video]` 子命令。
3. **后端 RESTful API 扩展 (`tools/geo/server.py`)**：
   - `GET /api/projects/{id}/visual/assets`：获取项目全量多模态资产列表（含 SVG 代码与短视频脚本）；
   - `POST /api/projects/{id}/visual/generate`：一键推演生成或重新生成视觉资产包。
4. **Web 管理工作台与专属交付门户升级 (`web/index.html` & `web/share.html`)**：
   - Step 3/Step 4 增加「🎨 多模态视觉资产与视频脚本」抽屉，支持 SVG 实时矢量预览与一键下载；
   - 专属客户门户 `web/share.html` 嵌入原生 SVG 对比图与视频脚本，交付体验跃升。
5. **SOP 知识库更新 (`docs/sop/03-rewrite-sop.md` & `04-distribute-sop.md`)**：
   - 规范多模态图片在知乎与今日头条等图文平台的分发规范。

---

## Capabilities (对外能力)

- `GET /api/projects/{id}/visual/assets`
- `POST /api/projects/{id}/visual/generate`
- CLI: `python3 -m tools.geo visual <project_id>`
- 交付产物：
  - `outputs/07_选型差异化对比图.svg`
  - `outputs/08_企业技术全景架构图.svg`
  - `outputs/09_60秒短视频高转化口播脚本.md`

---

## Impact (影响分析)

- **纯标准库与 SVG 实现**：无需庞大的第三方绘图依赖（如 Playwright/Pillow 等），轻量级高性能；
- **交付体验跃升**：全面覆盖图文、信息图、视频号脚本三位一体的现代 GEO 交付矩阵。
