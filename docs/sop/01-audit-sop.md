# SOP-01 售前获客与现状诊断

> **阶段目标**：用一份《企业 AI 可见度诊断报告》让客户看见"自己在 AI 眼里有多透明"，以数据驱动签单。  
> **执行人**：售前顾问 ｜ **周期**：签约前 1~3 天 ｜ **对应程序**：`geo audit`

---

## 一、执行步骤

1. **建立客户工作区与意图挖掘**（客户档案、5 维意图词库、竞品清单隔离在 `projects/<client_id>/`）：
   ```bash
   # 1. 初始化项目
   python3 -m tools.geo init <client_id> --name "客户全称" --url https://client.com --industry "行业"
   
   # 2. 意图词 / 侦察回填（阶段零）优先完成，体检可见度表会引用 probe
   python3 -m tools.geo intent <client_id>
   ```
2. **执行站点底座体检**（分两步，管理台同序）：
   ```bash
   # ① 仅 Python 真抓 → audit_metrics.json + 技术报告
   python3 -m tools.geo audit <client_id> --mode crawl

   # ② 小毛驴商业解读（需已有 metrics；需 NEXTDOOR_API_KEY；同机 Base=http://127.0.0.1:3001）
   python3 -m tools.geo audit <client_id> --mode interpret

   # 或一条龙：先抓再解读
   python3 -m tools.geo audit <client_id> --mode full
   ```
   - **技术真源**：`projects/<client_id>/outputs/audit_metrics.json`（硬指标，不经大模型改写）
   - **客户报告**：`projects/<client_id>/outputs/01_企业AI可见度现状体检与商业诊断报告.md`
   - **商业解读**：若已配置小毛驴 / Nextdoor（优先 `NEXTDOOR_API_KEY`；同机 `NEXTDOOR_BASE_URL=http://127.0.0.1:3001`），点「② 小毛驴解读」写结论与建议；未配置或失败时降级为规则稿。外部调用方才走公网 `https://nextdoor.baicl.cc`，管理面与同机互调禁止绕 VPS。
3. **管理台**：阶段一按钮 **① 真抓指标** → **② 小毛驴解读**；「一键复制给 IDE」用于旗舰客户二次精修。
4. **一键生成售前商业 Pitch Deck**（可选）：
   ```bash
   python3 -m tools.geo pitch <client_id> --tier pro
   ```

## 二、分层原则（必读）

| 层 | 谁做 | 禁止 |
| :--- | :--- | :--- |
| 技术指标 | Python `urllib` 真抓 | 大模型不得伪造 has_llms_txt / SSR 等 |
| 商业解读 | 小毛驴 LLM（可选） | 不得编造关键词假排名；可见度引用阶段零 probe |
| 二次精修 | Cursor / IDE（可选） | 不得覆盖 `audit_metrics.json` 真值 |

## 三、报价与立项话术（诊断报告 → 合同的转化钩子）

| 服务档位 | 客户现状判读 | 核心权益清单 | 参考报价 |
| :---: | :--- | :--- | :--- |
| **基础版 (Standard)** | 初创与小微企业首发占位 | 3 件套底座 + 9 因子语料 + 2 平台矩阵分发 + 月度巡检 | ¥19,800/年 |
| **专业进阶版 (Pro · 推荐)** | 成长型企业全域垄断与获客 | 全套 5 步交付 + 5 大全渠道 + 实时沙箱 + 企微告警 + ROI 战报 | **¥35,000/年** |
| **集团旗舰版 (Enterprise)** | 集团母子品牌与全网护城河 | 集团协同矩阵 + 30 动态词演进 + 短视频脚本 + 1对1 专家 | ¥68,000/年 |

## 四、质检打分表（售前自查，满分 10）

| 检查项 | 分值 | 达标线 |
| :--- | :---: | :---: |
| project.yaml 必填字段完整（client_id/name/url/keywords） | 2 | 缺一不立项 |
| 意图词库 ≥ 40 个且覆盖 5 维分类（选型/价格/避坑/场景/品牌占位） | 3 | 少于 40 或未覆盖 5 维退回补充 |
| 竞品清单 ≥ 2 家 | 1 | monitor 位次计算依赖 |
| 诊断报告已发送客户并获确认回执；`audit_metrics.json` 与报告技术表一致 | 3 | 无回执或不一致不进 Stage 2 |

## 五、验收标准

- [ ] 客户在诊断报告上签字/微信确认"现状判读无异议"；
- [ ] `audit_metrics.json` 已留档；有 probe 时可见度表引用真机结果；
- [ ] 合同明确验收线：底座复检 4/4 通过 + 核心词 SOV 提升幅度。

> 下一步 ➔ [SOP-02 站点底座改造](/sop/02-scaffold-sop)
