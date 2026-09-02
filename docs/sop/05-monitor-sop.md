# SOP-05 可见度监控、归因与续费交付

> **阶段目标**：把"效果好不好"变成每周一份可对比的数字报表——SOV 是续费谈判的唯一语言。  
> **执行人**：技术 + 客户成功 ｜ **周期**：第 4 周起每周 ｜ **对应程序**：`geo monitor`

---

## 一、执行步骤

1. 配置模型 Key（二选一即可跑，全配更好）：
   ```bash
   export DEEPSEEK_API_KEY=sk-xxx
   export DOUBAO_API_KEY=xxx          # 火山方舟 Key
   export DOUBAO_ARK_MODEL=doubao-seed-1-6-250615   # 推理接入点
   ```
2. **自动化无人值守巡检与时序归档**：
   ```bash
   # 单项目巡检归档
   python3 -m tools.geo patrol <client_id>
   
   # 全量客户批量巡检与企微/飞书机器人告警推送
   python3 -m tools.geo patrol --all --notify
   
   # Crontab 挂载定时执行（每周一凌晨 03:00）
   0 3 * * 1 cd /path/to/GEO && python3 -m tools.geo patrol --all
   ```
3. 生成竞品反向包抄策略（当竞品在核心词占位时触发）：
   ```bash
   python3 -m tools.geo defense <client_id>
   ```
4. **行业大盘 Benchmark 横向对标与批量并发跑批**：
   ```bash
   # 单客户行业超越战绩对标评估
   python3 -m tools.geo benchmark <client_id>

   # 全行业大盘宏观均值查看
   python3 -m tools.geo benchmark

   # 多项目批量并发一键生产跑批
   python3 -m tools.geo batch --step pipeline --concurrency 4
   ```
5. 产物：《05_企业AI可见度与声量追踪周报.md》+《06_竞品权威信源反向包抄策略.md》+ `projects/<id>/history.db`（时序库）；并在 Web 管理端提供可一键打印或导出 PDF 的精美交付报表及专属只读交付门户。

## 二、周报指标与 Citation 权威图谱口径

| 指标 | 定义 | 健康线 |
| :--- | :--- | :--- |
| **品牌提及率 SOV** | 有效提问中答案含品牌/别名/人名的比例 | 第 4 周 ≥30%，第 12 周 ≥60% |
| **行业超越百分比 (Beat Rate)** | 客户当前 SOV 相对所属行业均值与前 10% 标杆的领先率 | ≥ 75.0%（第一梯队） |
| **平均推荐位次** | 品牌在推荐清单中的顺位（竞品在前则 +1 计） | ≤ 2 位 |
| **Citation 权威加权评分** | 引用域名频次 × 平台权重（知乎1.0/头条0.9/微信0.85/GitHub0.95） | ≥ 80 分 |
| **占位词独占率** | 品牌占位词提问中唯一被推荐的比例 | 100%（不达标即被冒名，立刻处理） |

## 三、竞品反向包抄闭环流程（固定动作）

```
周报未命中/竞品拦截 ──► 自动反解竞品被引用的顶级信源 ──► 一键运行 geo defense
        ▲                                                      │
        └────── 回 Step 4 矩阵在竞品同平台补发 ◄── 生成 06_竞品反向包抄策略 ◄─┘
```

1. 对每个竞品拦截词，提取大模型引用的竞品页面；
2. 运行 `geo defense` 自动提炼 5 维硬核量化差异化压制话术；
3. 输出《06_竞品权威信源反向包抄策略.md》并在知乎/头条同位语发布完成截流。

## 四、续费交付动作

- [ ] 每周一 10:00 前周报发客户，附一句人话结论（"本周新增命中 5 词，被 AI 引用 3 次来自我方头条号"）；
- [ ] 输出行业 Benchmark 超越战绩（"您的 AI 可见度已超越本行业 82.5% 的同行"），作为续费第一依据；
- [ ] 每月出一份环比曲线（history.db 查询），对齐合同验收线；
- [ ] 运行 `python3 -m tools.geo evolve <id>`，一键裂变生成下一季度 15 组高价值长尾商业词，作为续费提案核心交付物。

## 五、大模型 Prompt 动态演进与追问词裂变操作规范

1. **词库生命周期健康度评估**：
   - 运行 `python3 -m tools.geo evolve <project_id>` 或在 Web 管理端点击 **「🌱 词库动态演进与裂变」**；
   - 自动将词库分类为：🏆 垄断占位词、⚠️ 竞品截流词、🌱 高潜裂变词、❄️ 待优化词。
2. **5 维逆向长尾裂变**：
   - 涵盖痛点避坑、竞品选型对比、价格 ROI、区域选型、技术演进 5 大高转化场景；
## 七、商业 ROI 量化测算与客户续费增购谈判规范 (Commercial ROI & Renewal)

1. **商业 ROI 量化测算**：
   ```bash
   # 测算项目商业投资回报率 (ROI) 与财务估值
   python3 -m tools.geo roi <client_id> [--fee 30000] [--cpl 160] [--cpc 6.5]
   ```
   - 自动生成三大商业价值：等效 SEM 竞价替代节省 + AI 首推精准销售线索估值 + 信任池数字资产估值；
   - 测算结果自动同步至甲方只读交付门户（`web/share.html`）作为老板财务汇报战绩。
2. **客户续约健康度预测与商务提案**：
   ```bash
   python3 -m tools.geo renewal <client_id>
   ```
   - 评分 $\ge 85$ 分（极高概率续约）：主推年度增购包，拓展至集团矩阵与 15 组裂变词库；
   - 评分 $70 \sim 84$ 分（健康续约）：安排季度复盘汇报，通过沙箱演示强化心智；
   - 评分 $< 70$ 分（需重点公关）：安排面对面答辩与语料重构。

## 八、商业交付验收结案与全套成果归档规范 (Acceptance & Pack)

1. **生成具备公章签署格式的结案确认单**：
   ```bash
   python3 -m tools.geo signoff <client_id>
   ```
   - 自动核算 6 维合同履约达成率（达标 $\ge 90\%$），生成《00_GEO商业交付验收结案确认单.md》；
   - 可在 Web 端或专属交付门户点击 **「🖨️ 打印盖章结案单」**，直接调起浏览器 A4 排版打印或保存为 PDF。
2. **一键生成离线 ZIP 归档包**：
   ```bash
   python3 -m tools.geo pack <client_id>
   ```
   - 自动将 15+ 份交付物、底座代码与多模态 SVG 资产打包为 `{client_id}_geo_delivery_archive.zip`。

---

> 上一步 [SOP-04 矩阵分发](/sop/04-distribute-sop) ｜ 全流程总览见 [客户交付 SOP 手册](/sop/delivery-sop)
