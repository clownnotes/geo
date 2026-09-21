# Design: 阶段一帮助提示剥离与连点封禁逻辑废除

## 一、系统架构与交互解耦设计

### 1. 阶段一问号帮助触发器物理分离（UI 交互层）

**问题根源**：
此前问号图标 `<i data-lucide="help-circle">` 被作为内联子节点放入 `<button>` 内，导致点击冒泡触发布局外层整个运行事件。

**设计方案**：
将主操作按钮与帮助按钮重构为兄弟节点布局，封装为复合按钮组：

```html
<div class="inline-flex items-center gap-1.5">
  <!-- 主操作按钮：点击执行流水线 -->
  <button type="button" onclick="runStep1Audit(event, 'crawl')" id="btn-step-1-boss-crawl" class="...">
    <span>① 真抓网络与底座指标</span>
  </button>
  
  <!-- 独立帮助触发器：点击查看说明，阻止事件穿透 -->
  <button type="button" onclick="showStepHelp(event, 'crawl')" class="p-2 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition" title="查看本步说明">
    <i data-lucide="help-circle" class="w-4 h-4"></i>
  </button>
</div>
```

### 2. 帮助说明统一字典与弹窗机制

前端维护标准帮助说明字典 `STEP_HELP_DEFINITIONS`：

弹层给运营看，用白话，不要写 SSR、Schema、幻觉、端口号。

| 模式标识 (Key) | 标题 | 这一步做什么 | 开始前要有什么 | 做完会多出什么 |
| :--- | :--- | :--- | :--- | :--- |
| `crawl` | 先去客户官网看一看 | 真的打开客户官网，检查大模型爬虫能不能读到页面，再把结果存进这个项目。 | 客户官网打得开。 | 一份「网站摸底结果」（`audit_metrics.json`） |
| `boss_direct` | 写成给老板看的诊断 | 用刚才存下来的摸底结果，算客户现在丢了多少机会，写成一份给老板看的说明。 | 必须先做过「先去客户官网看一看」。 | 给老板看的诊断稿 |
| `tech_direct` | 写成给做网站的人看的清单 | 用刚才的摸底结果，列出网站要改的地方和改法。 | 必须先做过「先去客户官网看一看」。 | 给做网站的人看的改造清单 |
| `interpret` | 再补一段更好懂的说法 | 在诊断上面再补一段销售时更好讲的话。这一句现在没有问号，不必新做按钮；字典里留着，方便以后用。 | 必须先做过摸底，并且小毛驴服务是通的。 | 诊断稿里多一段说法 |

阶段一有两套页签（老板版、工程师版），一共 4 个问号，都在主按钮里面。4 个都要拆成旁边的独立按钮。老板版和工程师版的「先去看官网」共用 `crawl`。

点击帮助触发器时，调用通用帮助浮层组件：
- 阻止事件冒泡：`event.stopPropagation()`；
- 弹出轻量模态卡片，展示当前步骤的“目的、前置条件、产出物”，附带“我知道了 / 关闭”按钮；
- 支持点击遮罩或按下 ESC 键秒关。

---

## 二、前端防重提与防抖机制 (Debounce & Lock)

1. **执行状态互斥锁 (`isAuditRunning`)**：
   - 锁必须写在函数最前面、任何 `await` 之前。现在「直出」会先去问有没有摸底结果，这段等待里连点仍会发出第二次。
   - 已经在跑：直接 `showToast('上一步还在做，请稍等', 'warning')` 并返回。
   - 刚进入：立刻 `isAuditRunning = true`，再把当前按钮设为 `disabled` 并换成「正在处理」文案。
2. **安全退出保证**：
   - 已经在跑时只提示并返回，**不要把锁放开**（放开就会把正在做的那一次拆掉）。
   - 还没选项目：在上锁之前就返回。
   - 上锁之后才发现还没做摸底、请求失败或超时：在 `finally` 里放开锁，并恢复按钮原来的文字。

---

## 三、后端风控护栏重构（废除连点自动停用账号）

### 1. 只废除「频控升级成封号」

`check()` 里现在有 4 处：次数超了先 429，`denied` 超过 `TOO_MANY_429_PER_HOUR` 再 `_auto_disable` 并返回 403「账号已被安全策略停用」。这 4 处的停用调用删掉。超限仍返回 429，并 `logger.warning` 记一笔。不改花名册。

下面这条**留下**：

- `record_sensitive_denial()`：短时间反复去碰敏感产出（语料、整包、配方一类），仍调用 `_auto_disable`。
- 现有测试 `test_sensitive_asset_denials_auto_disable` 必须继续通过。

`TOO_MANY_429_PER_HOUR` 不再用来封号。可以留着只做日志计数，也可以删掉常量；不能再写花名册。

### 2. 护栏阈值

- `REQ_PER_MINUTE`：120 → **300**
- `OUTPUT_READ_PER_HOUR`：120 → **600**
- `DISTINCT_PROJECT_PER_HOUR`、`DISTINCT_FILENAME_PER_HOUR`、`SENSITIVE_DENIALS_PER_HOUR` 不改。

### 3. 数据恢复

- 把 `13805206070` 的 `status` 从 `disabled` 改回 `active`（现码 `data/rbac_members.json` 已核实是停用）。
- 改的是花名册文件。本地 `:8088` 若还在跑，改完重启一次，避免进程里还记着旧的停用状态。

### 4. 既有测试必须改预期

`tests/test_operator_anti_scrape.py` 的 `test_distinct_filename_sweep_rate_limited_first_then_disabled` 现在断言：反复 429 之后账号变成 `disabled` 且返回 403。本期改为：反复超限仍然是 429，账号保持 `active`。不新增一套跟旧测试打架的断言却留着旧测试。
