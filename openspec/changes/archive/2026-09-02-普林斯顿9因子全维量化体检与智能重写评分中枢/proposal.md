# Proposal: 普林斯顿9因子全维量化体检与智能重写评分中枢 (Princeton 9-Factor Diagnostic Scorer & Rewriter Hub)

## Why (为什么做 / 商业痛点与理论落地)

1. **普林斯顿 9 因子缺乏开箱即用的客观量化体检工具**：
   - 普林斯顿大学与佐治亚理工学院的开山论文《GEO: Generative Engine Optimization》指出了决定大模型引用采纳的核心 9 大因子（统计数据、信源引用、专家引语、逻辑顺畅度、术语精确度、简明通俗度、权威语调、独特性词汇，以及纯关键词堆砌的负惩罚）；
   - 但在真实商业交付中，企业客户拿出自己的宣传文案、官网介绍或产品资料时，系统缺乏一个立即可用的“量化体检仪”，无法客观、精准地为客户现有文案打出 9 维具体得分。

2. **售前签约现场“降维打击”与价值证明（Live Proof）**：
   - 销售与商务团队需要一个即测即评的现场体验工具：客户输入现有官网的一段话（约 500~2000 字），系统 3 秒内输出 9 维雷达图与诊断报告，显示当前得分仅 35~45 分（营销词泛滥、缺乏统计数据与权威引用）；
   - 一键生成“普林斯顿 9 因子重构版本”，得分跃升至 90+ 分（AAA 级），预估大模型采纳率提升上限达 +35% 以上，相对原文跃迁 +20%+，商业价值对比立竿见影。

3. **交付内容全生命周期质检与持续优化闭环**：
   - 交付团队在编写或审核知乎、头条、GitHub、官网白皮书等资产时，需要自动化的 CI/CD 质检中枢，确保每一份对外分发的材料在 9 因子各维度均达到及格线（>=80分），防止劣质水文损害品牌声量。

---

## What Changes (改动范围)

1. **研发普林斯顿 9 因子量化评分与重构引擎 (`tools/geo/princeton.py`)**：
   - `score_text_princeton_factors(text: str, industry: str = None) -> dict`：
     - 深度扫描 9 大因子特征，各维度加权严格归一化为 100%（F1 统计数据 25%，信源 15%，其余各 10%）；
     - 输出综合加权总分 (Overall Princeton Score, 0~100)、评级分档（AAA/AA/A/B/C）、理论采纳上限 `est_visibility_ceiling` 与净增益 `est_boost_vs_baseline`；
     - 复用 `compliance.py` 的极限营销词典，精准捕获浮夸营销词与单词频 $>5\%$ 堆砌负惩罚；
   - `rewrite_text_princeton_factors(text: str, project_id: str = None, industry: str = None) -> dict`：
     - 遵守事实真实性红线：有 `project_id` 时仅绑定已登记真实事实（缺项输出 `[待客户提供确认]`）；无 `project_id` 时结构重构、数值与信源附带 `[示例待核实]` 显式标示；
     - 输出 Before / After 文本对比 Diff 及前后评分跃迁数据；
   - `audit_project_deliverables_princeton(project_id: str) -> dict`：
     - 批量扫描项目 16 维已生成交付物（排除自身与 `.compliance_backup`），输出规范编号成果：`outputs/17_普林斯顿9因子全案质检报告.md` 与 `outputs/princeton_audit.json`。

2. **CLI 命令行扩展 (`tools/geo/cli.py`)**：
   - 注册 `geo score` 子命令（三文档契约严格统一）：
     - `geo score <file_or_text> [--industry X] [--rewrite]`：对单文件或输入文本执行 9 因子打分，可选重构；
     - `geo score --project <id> [--audit]`：对指定项目交付物执行全案 17 号质检审计。

3. **后端 RESTful API 扩展 (`tools/geo/server.py`)**：
   - `POST /api/princeton/score`：提交文本打分；
   - `POST /api/princeton/rewrite`：提交文本一键普林斯顿重构；
   - `GET /api/projects/{id}/princeton/audit`：获取项目全案 17 号质检报告。

4. **Web 管理工作台交互升级 (`web/index.html`)**：
   - 顶部导航栏新增「🔬 普林斯顿体检仪」入口；
   - 模态内提供双栏交互：左侧文案输入，右侧即时渲染 9 因子雷达图、各项得分细目、一键重构按钮与优化前后 Diff 视窗。

5. **自动化测试套件 (`tests/test_princeton.py`)**：
   - 覆盖权重和严格归一化等于 100 断言、标杆高分、营销水文低分、堆砌扣分、事实防伪标记与 17 号报告输出。

---

## Capabilities (对外能力)

- **任意企业商业文案 9 因子秒级量化体检与雷达图生成**；
- **大模型采纳率预期提升幅度（+0% ~ +41%）科学量化模型**；
- **严格遵循真实性红线的一键普林斯顿智能重写与对比 Diff**；
- **项目 17 号全案交付物普林斯顿因子批量 CI 质检报告**。

---

## Impact (影响分析)

- **纯增量开发**：完全基于纯文本与现有项目实体配置做特征分析，不侵入现有数据管道；
- **售前与交付双重赋能**：极大提升客户信任度与交付成果的理论严谨度；
- **严格遵循规范**：本地 8088 端口测试，严禁私自向生产服务器发布；归档严格由 Cursor 审查通过后执行。
