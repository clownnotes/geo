# Review Log: 对照苍何诊断与答题卡母盘的交付提升探讨

## 2026-09-16 Cursor（propose 初稿）

- 曾误把共识写到 `docs/specs/*` 旁路文件；产品要求：**只认 OpenSpec**。

## 2026-09-16 产品纠正 + 收口

- **指令**：规范进 OpenSpec；自建 specs 有料的并进来，文件夹清理掉，避免歧义。  
- **已做**：
  - 全部已定共识并入本目录 `design.md`（§A～§G）
  - IDE 深化提示词：`prompts/diag-deepen-report-ide.md`
  - 删除旁路：`answer-card-vs-master.md`、`master-and-keywords-two-systems.md`、`baseline-probe-vs-stage1-audit.md`、`diag-report-fast-and-deep.md`、`keyword-list-first-vs-maintain.md`、`console-nav-ia.md`、`docs/specs/prompts/diag-deepen-report-ide.md`、`docs/strategy/geo-flow-benchmark-canghe.md`
  - SOP / roadmap / 发帖运维页脚改为引用本 `design.md`
- **保留不动**（原有工程规范，非本轮旁路）：`answer-source-writing.md`、`llm-browser-probe-sop.md`、站点/文章模板等  
- **侧栏落地**仍有效（首次交付 + 四类运维）  
- 状态：`[已达成共识]` — 探讨真源 = 本 OpenSpec；实现欠账见 design §G。

## 2026-09-16 Cursor（/opsx-apply 3.1–3.3）

- **已做**：
  - 3.1 `copyDiagDeepenPrompt` → `GET /diag/deepen-prompt`；阶段一旁提示 `refreshDiagDeepenProbeHint`
  - 3.2 关键词页门闩 UI + `confirmKeywordsWithClient` 写 `project.yaml`；发帖运维页 `ops-publish-kw-gate` 横幅
  - 3.3 `diag_deepen.audit_probe_answer_coverage` + 阶段零收工/实战提示强制 `answer_full`；单测 `tests/test_diag_deepen.py`
- 状态：`[已修正]` — 3.x 编码完成，待产品验收（tasks 4.1）；**未归档**

## 2026-09-16 产品确认（规范真源）

- **口令**：只要提「开规范」= OpenSpec；规范只留这一处；禁止再造易歧义的 `*spec*` 旁路文件夹。
- **已写入全局规则**：`~/.cursor/rules/openspec-only.mdc`；本仓 `/.cursor/rules/openspec.mdc` §0。
- 状态：`[已达成共识]` — tasks 4.1 已勾；归档仍须用户显式下达。

## 2026-09-16 产品指令归档

- 用户明确要求：归档本变更 + git 推远程，再继续「关键词语义」探讨。
- 状态：`[通过]` — 准许 `./opsx archive`
- **已归档路径**：`openspec/changes/archive/2026-09-16-对照苍何诊断与答题卡母盘的交付提升探讨/`
