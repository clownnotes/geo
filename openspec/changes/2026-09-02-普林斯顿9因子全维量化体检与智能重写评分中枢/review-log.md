# 跨 IDE 联合评审日志 (Review Log)

---

### 2026-09-02 Antigravity [发起提案：普林斯顿9因子全维量化体检与智能重写评分中枢] [待讨论]

- **阶段**：Proposal & Design Initial Submission
- **需求范围**：
  1. 研发 `tools/geo/princeton.py`，实现普林斯顿 9 大优化因子的特征捕获、加权打分（0~100）与预期采纳提升率计算（+0%~+41%）；
  2. 实现纯关键词堆砌负惩罚与主观浮夸词严厉扣分机制；
  3. 实现低分营销文案一键普林斯顿 9 因子高权威重构与 Before/After Diff；
  4. 支持项目全案 16 维交付物普林斯顿因子批量审计；
  5. 扩展 CLI `geo score` 与后端 RESTful API；
  6. 升级 `web/index.html`，新增「🔬 普林斯顿体检仪」模态与双栏即时交互；
  7. 新建 `tests/test_princeton.py` 自动化测试。
- **协同约束声明**：
  - 本端（Antigravity）负责方案设计与后续代码研发；
  - 严格遵守红线：**本地 8088 端口测试、禁私自推生产；最终归档严格交由另一个 IDE（Cursor）在独立复审后执行！**

- **状态结论**：`[待讨论]`，提请跨 IDE（Cursor 等）进行独立审查对齐。
