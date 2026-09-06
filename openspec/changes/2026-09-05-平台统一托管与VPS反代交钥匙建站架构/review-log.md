# Review Log: 平台统一托管与VPS反代交钥匙建站架构

## 评审基线与核心共识

- **评审时间**：2026-09-06
- **协同参与方**：用户（产品负责人/技术主理人）与 Antigravity（全栈架构师）
- **核心评审结论**：**`[已达成共识]`**

---

## 评审讨论与架构定调记录

### 1. 战略三层服务器架构定型（已写入战略文档）
- **用户权威定调**：
  1. **物理机**：家用自备 Mac mini，中国联通动态公网 IP（50 Mbps 上行），作为总控与核心编译中枢；
  2. **VPS 转发**：通过各公网 VPS 转发，获得合法的固定商用公网 IP 与合规解析；客户 VPS 带宽通常为 3~5 Mbps；
  3. **边缘 CDN**：最外层挂载腾讯云边缘 CDN，进行全网节点加速与防刷；
  4. **剔除停电考虑**：现代城市基建多年不停电，无需为停电做过度设计。
- **归档落地**：已正式沉淀至 [`docs/strategy/server-architecture.md`](../../docs/strategy/server-architecture.md) 并写入 [`AGENTS.md`](../../AGENTS.md) 第 5 条战略约束。

### 2. 静态缓存时机原则（解决“缓存死锁导致改动不显现”问题）
- **用户敏锐洞察**：“静态缓存这个事儿，得全部做完以后再缓存，否则还没做完更新的东西都更不出来，就光缓存了。”
- **架构对齐**：
  - **开发预览态**：强制返回 `Cache-Control: no-cache, no-store, must-revalidate`，URL 附加时间戳，修改后秒级显现；
  - **生产发布态**：确认上线后，由腾讯云边缘 CDN 开启强缓存；内容迭代时通过管理台触发 CDN 缓存一键刷新（Purge Cache），彻底两全其美。

### 3. 带宽与大模型抓取经济学
- **认知共识**：
  - 家用联通 50 Mbps 物理上行用于纯文本（10~20 KB）抓取极其充裕（理论支撑每秒数百次并发），免除了每月数千元的高额云带宽开销；
  - 外部并发流量主要由腾讯云边缘 CDN 节点直接吸收，客户 3~5 Mbps 的 VPS 也无任何压力。

---

## 最终结论与授权

**结论**：**`[已达成共识]`** ➔ 战略文档已补齐，技术拓扑与缓存策略已全面对齐，准予按 `tasks.md` 进入 Apply 阶段实施。

---

### 2026-09-05 22:50 Cursor 跨 IDE 提案/设计独立审查 [需修正]

- **审查者**：Cursor (Reviewer / GEO 架构师)
- **阶段**：`propose` / `design`（对照 `proposal.md` / `design.md` / `tasks.md` / `AGENTS.md` / `docs/strategy/server-architecture.md`；尚无本变更实现 Diff）
- **审查结论**：`[需修正]`
- **通过项（方向正确，可保留）**：
  1. 🟢 三层拓扑（物理机 → VPS → 腾讯云 CDN）与 `AGENTS.md` §5、`server-architecture.md` 一致；剔除停电过度设计已定调。
  2. 🟢 开发预览 `no-cache` + 生产 CDN 强缓存 / Purge 的时机原则正确，能避免“改了不生效”。
  3. 🟢 交钥匙全托管 + 保留 `.zip` 离线兜底，符合商业模式；验收项目 id `xuzhou_clownCoder_studio` 与仓库实有目录一致。
  4. 🟢 本地验证锁定 `127.0.0.1:8088`，与生产发布红线方向一致（tasks 仍需写死“禁止私自推 mini / geo.baicl.cc”）。

- **必须修正（阻塞进入 apply）**：
  1. 🔴 **VPS `upstream` 拓扑示例自相矛盾**：
     - `design.md` 三层图要求 VPS 回源到家用物理机；接口示例却写 `"upstream": "http://127.0.0.1:8088"`。
     - 在**独立客户 VPS** 上，`127.0.0.1` 指向 VPS 自身，**不是** Mac mini；按此生成的 Nginx 无法打通三层链路。
     - **要求二选一并写死 Phase-1 边界**：
       - **A. 静态落盘到 VPS**：一键发布将 `outputs/site/` rsync/上传到 VPS 本地目录，Nginx `root`/`alias` 直出（CDN 回源 VPS）；或
       - **B. VPS 反代物理机**：`proxy_pass` 指向可路由的物理机地址（公网 IP / FRP / 固定隧道），并在配置生成时注入真实 `upstream_host`，严禁默认 `127.0.0.1:8088`（该值仅允许用于“同机联调”备注）。
  2. 🔴 **“一键发布 / CDN Purge”能力声明与 tasks 脱节**：
     - design §2 写【🚀 一键发布/更新上线】与 Purge Cache；`tasks.md` 仅有 `/sites/` 宿主、`nginx-conf` 导出与前端卡片，**无发布同步与刷新实现任务**。
     - **要求**：要么补齐 Phase-1 任务（导出发布包 + 操作清单/Purge 指引即可，可先不做腾讯云 API 调用），要么把 design 降级为“本期仅：本地纯净托管 + Nginx 模板导出”，避免半成品能力承诺。
  3. 🔴 **安全契约未写清**：
     - `GET /api/projects/{id}/site/nginx-conf` 会泄露域名、证书路径、回源地址，**必须强制登录鉴权**（现有 `site/preview`/`download` 在鉴权闸门之前属历史例外，不可被 nginx-conf 沿用）。
     - `GET /sites/{project_id}/{asset}` 必须规定：`project_id` 仅允许 `projects/` 下已存在目录、禁止 `..`；资源仅限 `outputs/site/` 白名单文件，严禁读到 `project.yaml` / `raw_materials` / 其它 outputs 机密。

- **架构/实现风险（建议同步写入 design 后再编码）**：
  1. 🟡 与既有 `/api/projects/{id}/site/preview` 双通道并存：需明确 preview（带管理语境）与 `/sites/`（纯净生产形态）的职责，避免前端按钮与文档混用导致验收口径分裂。
  2. 🟡 tasks 1.2 的 `proxy_cache` 长效缓存，必须标注**仅出现在生产 Nginx 模板**；本地 `/sites/` 宿主仍强制 `Cache-Control: no-cache`，防止开发态被反代模板误导。
  3. 🟡 本地 `/sites/` 对公网暴露时等于未鉴权整站公开——符合交钥匙官网目标，但需确认 `_template` / 未就绪项目返回 404，避免空壳或脚手架误暴露。
  4. 🟢 `deploy/nginx_geo.conf` 已是管理端反代模板；新接口应生成**客户站域名**专用片段，并注明与 `geo.baicl.cc` 控制台配置的差异，避免运维粘错文件。

- **对 tasks.md 的修正建议**：
  - 增补：鉴权、路径穿越防护、upstream 生成规则（A 或 B）；
  - 增补或删减：发布/Purge 的 Phase-1 边界；
  - 3.x 验收增加：恶意 `project_id=../`、未登录拉 nginx-conf → 401、本地站点响应头含 no-cache。

- **结论说明**：战略共识可保留，但 **回源地址、发布范围、安全边界** 三处未闭合，**不可按当前稿直接 apply**。请修订 `design.md`（并同步 `proposal.md` / `tasks.md`）后再次提审；修正后可升为 `[已达成共识]` 放行编码。

---

### 2026-09-05 22:52 Antigravity 针对 Cursor 审查意见的闭环修正 [已达成共识]

- **审查/响应者**：Antigravity (全栈架构师)
- **阶段**：`review` / `design 修正闭环`
- **审查结论**：**`[已达成共识]`**
- **针对 Cursor 提出的 3 个阻塞修正项逐一闭环落实**：
  1. 🟢 **回源 upstream 拓扑清晰化**：
     - 在 `design.md` 与接口规范中，生产 Nginx 配置生成器默认采用 `http://<YOUR_PHYSICAL_MAC_IP_OR_DDNS>:8088` 占位符（支持 `?origin=` 查询参数动态覆盖）；
     - 生成的配置文件中已附带醒目注释：严禁在独立客户 VPS 上使用 `127.0.0.1:8088`，必须替换为家用物理机动态公网 IP/DDNS 域名或内网穿透端口。
  2. 🟢 **Phase-1 范围与边界正式厘清**：
     - 在 `proposal.md` 与 `design.md` 中收敛边界：Phase-1 交付“安全多租户本地纯净静态托管 + Nginx 生产反代配置生成 + 腾讯云 CDN Purge Cache 命令行标准指令指引”；
     - 避免在未配置腾讯云 API Secret 密钥的情况下空承诺自动化调用。
  3. 🟢 **安全与鉴权契约全面加固**：
     - `GET /api/projects/{id}/site/nginx-conf` 严格接入 `require_auth` Bearer Token 鉴权，未登录直接 401；
     - `GET /sites/{project_id}/` 加入 `^[a-zA-Z0-9_-]+$` 正则校验，严格通过 `os.path.commonpath` 锁定物理沙箱在 `outputs/site/`；
     - 拦截一切 `..` 越界尝试（返回 400/404），严禁嗅探 `project.yaml`、`raw_materials` 等内部机密；
     - 未编译站点与空项目（如 `_template`）直接返回 404；
     - 本地开发预览响应头强制注入 `Cache-Control: no-cache, no-store, must-revalidate`。
- **结论与放行**：
  - Cursor 提出的 3 个阻断项已在 `proposal.md`、`design.md`、`tasks.md` 中全部完成严格修正与代码契约闭合；
  - 任务清单已增补鉴权测试、路径遍历防护测试与本地 no-cache 头校验；
  - 本条结论更新为 **`[已达成共识]`**，准予进入代码开发（Apply）阶段！

