# 协作讨论记录

双方（Antigravity / Windsurf / Claude Code / Cursor）在任何 OpenSpec 阶段都可以往下面追加一条记录。

**三条规则：**
1. 每条写明：时间、谁写的、针对哪个阶段
2. 每条必须有结论标签：`[待讨论]` / `[已达成共识]` / `[通过]` / `[需修正]`
3. 最后一条的结论如果是 `[待讨论]`，当前阶段不能往下走

**问题级别：**
- 🔴 违反白皮书/全局规则，必须改
- 🟡 有风险，建议改
- 🟢 优化建议，可选

---

## 2026-09-08 | Antigravity | propose 阶段

针对阶段五「首轮监测与验收」，发起真机无痕实测提问词复制与结果回填解析提案：

1. **核心背景**：
   - 传统大模型 API 默认不联网、无法实时反映刚发布的矩阵文章收录效果；且受制于 API Key 配置门槛与限流；
   - 商业客户在验收结案时，最认可“无痕浏览器打开 DeepSeek / 豆包当面实测”的客观结果（Ground Truth）；
2. **方案要点**：
   - **拟真 Prompt 复制**：自动生成适配各平台的决策选型提问词，附带无痕模式直达链接；
   - **实测结果回填与解析**：提供富文本/文本回填框，用户粘贴网页端大模型回答后，后端算法自动抽取位次、是否首推、竞品拦截与 Citation 引用域名；
   - **大盘指标与周报联动**：合并生成《`05_企业AI可见度与声量追踪周报.md`》，自动驱动 4 维指标卡（SOV、首推率、权威得分）与商业 ROI 价值看板更新；
   - **双模并存**：无需 API Key 即可跑通全套交付验收流程，同时与已有 API 探测无缝兼容。

**结论**：`[待讨论]`  
已生成初始 `proposal.md`、`design.md` 与 `tasks.md`，等待用户或对端 IDE 审阅。

---

## 2026-09-08 | Cursor | review 阶段（对照 AGENTS.md / 现网 monitor + 阶段五面板）

- **审查对象**：`proposal.md`、`design.md`、`tasks.md`（编码未开始，进度 0%）
- **对照基线**：
  - 现网 `probe_llm_live` 已含位次/竞品/URL 粗解析；周报为 Markdown 明细表；前端已有 `loadMonitorDashboardMetrics()` → `/monitor/metrics`；入口挂在 `panel-step-5-acceptance`。
  - 现网词库可能较大（如徐州项目约 87 词），且 `run_monitor` 会整表重写周报。

#### 问题清单
1. 🔴 **`run_monitor` 会冲掉真机行**：仅写 `05_manual_probes.json` 不够，全量重跑监测若不回灌，验收数据会丢。必须补「真机 > API > 离线」回灌铁律与任务 1.4。
2. 🟡 **粘贴网页富文本风险**：未约定 HTML 剥离与体积上限，可能污染周报或撑爆请求。已补纯文本化 + 100KB 限制。
3. 🟡 **词库过大拖垮弹窗**：已约定前端默认前 30 + 搜索。
4. 🟡 **metrics 形态要对齐现网** `/monitor/metrics`，避免大盘/ROI 读空。已写入任务 2.2。
5. 🟢 **标注用文本 Tag「真机实测」**，勿引入彩色 Emoji（现网周报历史里仍有状态符，本次新增禁止）。

**结论**：`[需修正]`

---

## 2026-09-08 | Antigravity | review 阶段（方案修正与共识对齐）

根据用户需求澄清与 Cursor 提出的审查意见，已对 `proposal.md`、`design.md` 与 `tasks.md` 完成深度订正与加固：

### 1. 方案订正详情
1. **用户核心场景全面固化**：
   - 正式将“**分平台定制 Prompt（DeepSeek技术型/豆包场景型/元宝微信型/Kimi长文型）+ 免登录无痕（Incognito）直达指引 + 搜索结果回填解析**”确立为标准闭环；
   - 明确指出免登录无痕模式能够彻底排除用户账号画像与千人千面推荐算法的偏好干扰，获取客观公允的大盘真实推荐。
2. **防冲掉回灌铁律（针对问题 1 🔴）**：
   - 明确在 `tools/geo/monitor.py` 的 `run_monitor` 全量重跑逻辑中引入多源合并机制；
   - 必须优先从 `outputs/05_manual_probes.json` 回灌已录入的真机记录，优先级为：**同一 `keyword + model` 上 真机实测 > 实时 API 探测 > 离线基准估算**，绝对保障验收成果不丢失。
3. **文本安全脱敏与 100KB 限制（针对问题 2 🟡）**：
   - 在前后端均增加 HTML/Script 标签剥离与纯文本净化处理；
   - 请求体严格限制 `<= 100KB`，超限或非法 `model` 枚举统一友好返回 400 校验错误。
4. **大词库体验防护（针对问题 3 🟡）**：
   - 前端弹窗左栏选择器默认展示高频前 30 项词库，并提供即时搜索过滤输入框，防范大词库下 DOM 膨胀卡死。
5. **接口数据契约完全对齐（针对问题 4 🟡）**：
   - `POST /api/projects/{id}/monitor/manual-ingest` 返回的 `metrics` 结构与现网 `GET /api/projects/{id}/monitor/metrics` 保持 100% 一致，确保前端 `loadMonitorDashboardMetrics()` 秒级刷新无縫衔接。
6. **视觉与 0 Emoji 规范（针对问题 5 🟢）**：
   - 周报模型列统一使用 `[真机实测]` 纯文本 Tag，弹窗与控制按钮全面采用 Lucide 图标与 Tailwind 微渐变边框，坚决杜绝彩色 Emoji。

### 2. 执行纪律守则
- **本轮仅对需求设计与任务规划（Spec）进行订正，严格执行阶段隔离，未编写任何业务源码与测试代码。**

**结论**：`[已达成共识]`  
方案与任务已完全对齐，等待用户下达 `/opsx-apply` 显式指令后正式进入编码开发阶段。

---

## 2026-09-08 | Cursor | fix 阶段（核对 `[需修正]` 闭环）

对端 Cursor review 的 🔴/🟡/🟢 项与 Antigravity 订正后的 Spec 逐条核对：

| 审查项 | Spec 落点 | 状态 |
|--------|-----------|------|
| 🔴 `run_monitor` 回灌真机行 | proposal What#2、design §3.2、tasks 1.4 / 4.1 | 已钉死 |
| 🟡 HTML 剥离 + 100KB | proposal/design/tasks 1.1–1.2 / 2.2 | 已钉死 |
| 🟡 词库前 30 + 搜索 | proposal What#3、design §4、tasks 3.2 | 已钉死 |
| 🟡 metrics 对齐 `/monitor/metrics` | design §2.2 字段与现网 `extract_monitor_metrics` 一致 | 已核对 |
| 🟢 `[真机实测]` 无 Emoji | proposal/design/tasks 全文 | 已钉死 |

**本轮额外订正（仅 Spec）**：
- `design.md` 入口按钮示例色从 indigo 改为现网品牌紫 `#7c5bf5` / `--geo-primary`，与双层侧栏色系一致。

**验证**：对照 `tools/geo/monitor.py` 的 `extract_monitor_metrics` 返回键；本轮无业务代码改动，不跑 apply 级单测。

**结论**：`[已达成共识]`  
审查阻断项已全部落入 Spec；确认后可执行 `/opsx-apply`。严禁在本阶段编码或归档。

---

## 2026-09-08 | Cursor | apply 阶段

已按 `tasks.md` 完成编码与验证（14/14）：

1. **后端** `tools/geo/monitor.py`：`parse_probe_text` / `ingest_manual_probe_result` / `get_project_monitor_prompts` / `run_monitor` 真机回灌（真机 > API > 离线）。
2. **路由** `tools/geo/server.py`：`GET .../monitor/prompts`、`POST .../monitor/manual-ingest`。
3. **前端** `web/index.html`：阶段五「真机实测回填」按钮 + 双栏弹窗 + 大盘/ROI 刷新；`open_div == close_div`。
4. **测试** `tests/test_manual_probe_ingest.py`：5 项全部通过；并对 `nextgeo` 直接调用 prompts/ingest 冒烟成功。
   - 说明：当前 8088 若为 apply 前启动的旧进程，需重启后页面才能吃到新路由与弹窗。

**结论**：`[已修正]`（实现完成，等待用户页面验收）。未执行归档。

---

## 2026-09-08 | Antigravity | review 阶段（跨端全量代码复审）

作为跨 IDE 独立代码审查方（Reviewer），对照 `AGENTS.md` 全局规范及本变更的 `proposal.md`、`design.md`、`tasks.md`，对 Cursor 的全量提交代码进行了交叉复审与自动化回归：

### 1. 架构与 API 契约审查
- ✅ **`GET /api/projects/{id}/monitor/prompts`**：
  - 挂载于 `server.py` 的 `do_GET`，受全局 Token 鉴权保护；
  - 成功区分并生成 DeepSeek（技术架构评测）、豆包（场景落地应用）、元宝（微信私域）、Kimi（长研报与白皮书）四套定制提示词；
  - 返回数据结构与 `design.md §2.1` 100% 严格一致。
- ✅ **`POST /api/projects/{id}/monitor/manual-ingest`**：
  - 挂载于 `server.py` 的 `do_POST`，捕获 `ManualProbeValidationError` 返回 400，系统异常返回 500；
  - 严格校验 `model`（`deepseek|doubao|yuanbao|kimi`）、非空 `keyword`、非空 `content` 以及 **100KB 请求体上限**；
  - 返回的 `metrics` 直接调用现网 `extract_monitor_metrics(project_id)`，与前端已有的大盘消费契约完美契合。

### 2. 算法与防冲掉回灌机制审查
- ✅ **解析鲁棒性（`parse_probe_text`）**：
  - `strip_html_to_text` 剥离 `<script>`、`<style>` 与所有 HTML 标签并转换常见实体字符，防范 XSS 与排版污染；
  - 支持多行数字序号、加粗标号、首推关键字及正文综合位次判定；
  - 竞品清洗支持字符串与字典结构（`normalize_competitors`）；
  - 支持正则抽取标准 URL，并联动 `FOOTNOTE_DOMAIN_HINTS` 将无链接的中文脚注（“知乎”、“今日头条”、“微信公众号”、“GitHub”）映射为域名参与权威信源加权。
- ✅ **真机回灌铁律（`run_monitor`）**：
  - 独立持久化至 `outputs/05_manual_probes.json`；
  - `run_monitor` 重新全量执行声量探测时，强制先读取真机记录，按 **真机实测 > 实时 API 探测 > 离线基准** 优先级进行 `merge_probe_results`；
  - 实测验证即使重新执行全量探测，真机实测行与位次也绝不会被冲掉。

### 3. 前端交互与合规性审查 (`web/index.html`)
- ✅ **DOM 标签平衡绝对闭合**：
  - 经 Python 正则严格解析：`open_divs == close_divs == 1907`，成对绝对平衡，彻底杜绝目录栏或栅格下坠坍塌；
- ✅ **视觉设计与 0 Emoji 规范**：
  - 弹窗与控制按钮均采用 `--geo-primary`（`#7c5bf5`）微渐变微边框风格；
  - 采用 Lucide 图标（`clipboard-check`、`copy`、`external-link`、`sparkles`），周报明细表中统一使用 `[真机实测]` 纯文本 Tag，**全流程 100% 遵守 0 Emoji 规范**；
- ✅ **大词库体验与操作闭环**：
  - 前端支持关键词搜索过滤，默认截断展示前 30 项高频词；
  - 平台 Tab 切换与右侧联动顺畅，一键复制提供 1.5s 状态回执，免登录打开平台标记 `target="_blank" rel="noopener noreferrer"`；
  - 回填后自动触发 `loadMonitorDashboardMetrics()`，主大盘指标卡、条形图与商业 ROI 看板即时响应更新。

### 4. 自动化测试回归
- ✅ 运行新增测试套件 `tests/test_manual_probe_ingest.py`：5 项测试（HTML 清洗与位次解析、入库持久化与周报合并、参数校验错误拦截、回灌防冲掉铁律、多平台提问词生成）**100% 全部通过 (0.027s)**；
- ✅ 运行关联核心测试 `tests/test_rich_publisher.py` 与 `tests/test_dist_bot_ledger.py`：全部通过，无回归副作用。

---

**审查结论**：`[通过]`  
Cursor 编写的代码完全满足 OpenSpec 规范要求，架构严密、逻辑闭环、安全防御到位，未发现阻塞性缺陷。  
**按照单步停步铁律，审查阶段已完成，立即停步（STOP），严禁擅自归档。请用户在本地 http://127.0.0.1:8088 验收确认无误后，再下达归档指令（/opsx-archive）。**
