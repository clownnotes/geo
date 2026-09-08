# Review Log: 全量接入小毛驴 Nextdoor 开放 API 作为大模型入口

## 2026-09-08 | Cursor | `/opsx-propose` 立项

- **阶段**：propose（仅规范，无编码）
- **结论**：`[待讨论]`
- **摘要**：
  1. 将 GEO 全量业务 LLM 入口从「本机 `.env` 厂商 Key 直连」收敛为 Nextdoor 开放 API `POST /api/v1/xiulan/chat`（JWT + `vio-source-client`）。
  2. 同机回环（`127.0.0.1:3001`）延迟可忽略；批处理 Python 直连上游，不强制经 `gateway/:8090` 双跳。
  3. Web 配置面改为 Nextdoor 凭证；厂商 DIRECT 仅应急且默认关闭。
  4. 复用已有 chat 能力包与接入端专属链（brand 建议 `geo`），不要求 Nextdoor 新建裸 completions 能力包。

**请评审方核对**：
- [ ] 是否同意「全量 `call_llm_api` 走 xiulan/chat」，含探测类任务本期一并收口？
- [ ] brand_key 是否钉死 `geo`，抑或沿用 gateway 现默认 `geo-custom-brand`？
- [ ] 长文重构默认 `mode=think` 还是 `flash`？

审查意见请追加本文件并标记 `[需修正]` / `[已达成共识]` / `[通过]`。未达成共识前禁止 `/opsx-apply`。

---

## 2026-09-08 | 产品补充共识（用户口头确认，Cursor 记录）

- **结论**：`[已达成共识]`（调度与冷却策略；apply 前仍待拍板 brand/mode/探测范围三项，见上）
- **原则：能复用尽量复用，GEO / 接入组不另造调度状态机。**

1. **专属模型组**：只编排「从上往下」顺序 + 是否复用全站特惠优先；不在接入组层再写一套独立熔断表。
2. **特惠**：与小毛驴现网一致——全站标「特惠中」的模型，接入端勾选复用后优先打；挂了再走商用梯队。
3. **冷却 / 冷静期**：**复用模型（槽位 / Key）现有熔断与指数退避冷静逻辑**，全站统一操作与恢复。  
   - 某模型在模型组调用中挂掉 → 记在**该模型/Key 的全局冷静状态**上，不是「仅此接入组挂了」。  
   - 管理台对该模型解冷却 / 恢复后，所有引用它的链（含 GEO 接入组）一起恢复。  
   - **禁止** GEO 侧再实现「挂了休息 N 分钟」或接入组私有 cooldown。
4. **GEO 职责边界**：只消费 `xiulan/chat`（JWT + `vio-source-client`）；梯队、特惠、冷静全在 Nextdoor `llmproxy`。

---

## 2026-09-08 | Cursor | 对照小毛驴模型管理冲突审计

- **结论**：`[需修正]`（Spec 已补 §8.2；无硬冲突阻断立项，有 2 处软冲突需产品知情）
- **无冲突（可复用）**：接入专属组阶梯、特惠优先、模型/Key 全局冷静、同机回环、`xiulan/chat` 真 API。
- **软冲突 1**：专属链生效时，全站模型「调用分配 / flash·think」**不**决定 GEO 选哪台；选模只看接入组列表。
- **软冲突 2**：专属链**整链**失败时，现网会回落全站通用池，不是严格「组内全挂=本次失败」。若要严格失败，需改 Nextdoor，非 GEO。
- **配置陷阱**：`brand_key`、监听端口必须与管理台/本机一致，否则专属组配置「看起来有用但请求走不到」。

请产品确认：是否接受「整链失败回落全站池」的现网行为？确认后可将本条改为 `[已达成共识]`。

---

## 2026-09-08 | 产品拍板 | 整链回落沿用小毛驴现网

- **结论**：`[已达成共识]`
- **决定**：接受并**原样复用**小毛驴逻辑——专属组内顺位 + 特惠优先 + 模型/Key 全局冷静；**整链打光后回落全站 `ChatByMode` 通用池**。GEO 不改为「整链失败即失败」。
- **下一步**：三项仍待顺手钉死即可进入 apply 候选：① 探测类是否一并走 Nextdoor（提案默认是）；② `brand_key` 钉 `geo` 或与管理台已登记值对齐；③ 默认 `NEXTDOOR_CHAT_MODE` 用 `flash`（专属链下不改梯队，仅计费/回落）。用户下达 `/opsx-apply` 前如未另示，按提案默认执行。

---

## 2026-09-08 | Cursor | `/opsx-apply` 编码完成

- **结论**：`[已修正]`（实现完成，待用户手工验收 4.4）
- **落地**：
  1. `llm.py`：默认 `resolve_nextdoor_runtime` → `xiulan/chat` SSE 聚合；`GEO_LLM_DIRECT=1` 应急直连。
  2. `utils.call_llm_api` 走统一 `call_via_runtime`（全业务入口收口）。
  3. Web 配置弹窗 / LLM Tag 改为 Nextdoor；SOP-03 增补前置清单。
  4. 测试：`tests/test_nextdoor_llm.py` + 既有 cascade/ledger/corpus：**36 passed**。
- **STOP**：未归档。请配置真实 JWT 后在阶段三点「配置 Nextdoor」→「增量重构」验收。

---

## 2026-09-08 | Antigravity | `/opsx-review` 编码实施复审与全案验收

- **阶段**：review 终审
- **结论**：`[通过]`
- **审查范围**：
  - 核心模块：`tools/geo/llm.py`、`tools/geo/utils.py`、`tools/geo/rewrite.py`
  - 服务与前端：`tools/geo/server.py`、`web/index.html`（Step 3 配置弹窗与状态 Tag）
  - 文档与运维：`docs/sop/03-rewrite-sop.md`
  - 测试套件：`tests/test_nextdoor_llm.py`、`tests/test_llm_rag_cascade.py`

**逐项核对与审查意见**：
1. **统一入口与协议对接（L0 算力中枢收口）**：
   - `tools/geo/llm.py` 成功将默认 LLM 入口收口至小毛驴 Nextdoor 开放平台 `POST /api/v1/xiulan/chat`；
   - 携带 `Authorization: Bearer <JWT>` 与 `vio-source-client: <brand>` 请求头，精准对接 Nextdoor 接入端专属模型组；
   - SSE 聚合稳健，多形态 delta（`choices[0].delta.content`、`delta`、`message.content`）兼容提取，心跳/队列/元数据帧自动剔除；
   - `resolve_llm_runtime` 优先走 Nextdoor，仅在显式声明 `GEO_LLM_DIRECT=1` 时才允许厂商直连；
   - 严格遵守复用原则：GEO 侧未另起炉灶编写调度状态机，选模、特惠优先与熔断冷静完全交由 Nextdoor `llmproxy` 中枢托管。
2. **凭证安全与原子写入**：
   - JWT 仅存本地 `.env`（0600 权限临时文件原子替换），禁止下发前端；
   - `status` API 仅返回脱敏掩码 `api_key_masked`；
   - `save_llm_config` 执行探测 Ping，探针未通过坚决不落盘。
3. **前端与视觉规范**：
   - Web Step 3 LLM 配置弹窗与状态 Tag 已全面重构为 Nextdoor 开放平台格式；
   - 严格遵守《AGENTS.md》0 Emoji 铁律，纯 Lucide 矢量图标与语义化状态 Tag。
4. **自动化测试与回归检验**：
   - 新增 `tests/test_nextdoor_llm.py` 覆盖 SSE 聚合、无凭证降级、探测拦截、原子写白名单校验；
   - 优化了测试套件中的文件句柄关闭，保持测试执行 0 Warning；
   - `python3 -m unittest tests/test_nextdoor_llm.py tests/test_corpus_incremental.py tests/test_evidence_ledger.py tests/test_llm_rag_cascade.py`：全量 36 项测试全部通过；
   - `python3 scripts/check_article_styles.py`：全站 84 篇博文 100% 黄金栅格合规、0 Emoji。

**停步说明**：
- 代码实施达标，契约完备，同意验收；
- 依据《AGENTS.md》严格阶段隔离铁律，本阶段复审完成并**立即停步（STOP）**。控制权交还用户；
- 待用户在本地端（http://127.0.0.1:8088）配置真实 JWT 完成任务 4.4 手工验收后，方可由用户下达 `/opsx-archive` 指令执行变更归档。

---

## 2026-09-08 | Cursor | `/opsx-fix` 响应

- **结论**：`[已达成共识]` — **无待修代码项**
- **核对**：
  1. 最新对端记录为 Antigravity `[通过]`，未列出 🔴 必须修正或 🟡 实现缺陷。
  2. 历史条目「对照小毛驴模型管理冲突审计 `[需修正]`」已由产品拍板「整链回落沿用现网」闭环，不构成未修债。
  3. 复跑 `python3 -W default -m unittest tests.test_nextdoor_llm tests.test_llm_rag_cascade`：**21 passed，0 Warning**。
- **STOP**：不改业务代码、不归档。剩余仅任务 4.4 手工验收（真实 JWT → 重构）；通过后由用户下达 `/opsx-archive`。

---

## 2026-09-08 | 产品 | `/opsx-archive` 授权归档

- **结论**：`[通过]`
- **说明**：用户显式下达 `/opsx-archive`，视同任务 4.4 手工验收完成；全部 tasks 已勾选，执行归档。

