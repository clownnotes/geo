# Proposal: 中国本土 GEO 五大模型分类体系与豆包第一主战策略工程化 (Domestic GEO 5-Model Taxonomy & Doubao First Strategy)

## Why (为什么做 / 业务背景与战略聚焦)

1. **战略全面聚焦中国本土市场，彻底剔除海外无效噪声**：
   - 本项目服务对象 100% 为中国本土企业主、本地服务商与实体品牌，潜在客户从不会使用海外受限模型（如 ChatGPT / Perplexity）寻找国内供应商；
   - 过去历史规范与模版中零星残留有海外爬虫（`Google-Extended`、`Bingbot`）与海外模型描述，分散了核心资源与分发精力，必须彻底本土化收敛。
2. **确立「豆包（Doubao / 字节跳动生态）」为第一主战高地（50%+ 资源权重）**：
   - 豆包在国民级大众消费、中小微企业主、本地服务选型中拥有最高的日常活跃度与决策渗透率；
   - 豆包底层的 **Bytespider** 爬虫具备极高抓取频率（24~48h 秒级/天级生效），其 RAG 算法偏好“通俗接地气、真实价格避坑、问句对齐 Q&A、微头条短动态与本地商户三元组”；
   - 必须在分发工具、体检诊断与战略全景中将豆包确立为第一核心支柱。
3. **建立中国本土 5 大主流 AI 大模型生态分类与差异化渗透战法**：
   - 明确将国内大模型划分为：**字节系（豆包）**、**技术推理系（DeepSeek）**、**长文本全网系（Kimi）**、**社交私域系（腾讯元宝）**、**搜索政企系（百度文心一言）**；
   - 针对每种模型生态的底层爬虫机制、内容偏好、核心阵地与优化因子进行工程化定版。

---

## What Changes (改动范围)

1. **战略全景与理论中枢升级 (`docs/strategy/overview.md` & `docs/index.md`)**：
   - 定版《中国本土 AI 大模型五大生态阵营分类与差异化渗透矩阵》；
   - 确立四层架构中的本土信源矩阵（头条/知乎/微信/GitHub/百度百科）；
   - 更新首页 tagline 与大模型生态引导。
2. **站点底座与爬虫工程本土化 (`tools/geo/scaffold.py` & `docs/sop/02-scaffold-sop.md`)**：
   - `build_robots_txt` 显式置顶放行 `Bytespider`（豆包）、`Baiduspider`（文心）、`Sogouspider`（元宝）、`Yisouspider`（通义）；
   - 更新 `docs/public/robots.txt` 与 `docs/public/llms.txt`。
3. **体检诊断与售前建议书国内模型对齐 (`tools/geo/audit.py` & `tools/geo/pitch.py`)**：
   - 体检诊断自动模拟 Bytespider / Baiduspider / Sogouspider 抓取并评估本土可见度；
   - 售前 Pitch Deck 全屏幻灯片与标书文档全面对齐国内 5 大主流模型。
4. **交付手册与 SOP 映射更新 (`docs/sop/delivery-sop.md` & `docs/sop/04-distribute-sop.md`)**：
   - 完善五阶段交付程序映射与 5 大渠道分发台账回填规范。

---

## Capabilities (对外能力)

- **国内 5 大模型分类认知标准**：提供结构化表格与分类指标，供所有交付工程师与销售全案直接引用；
- **豆包专属分发与爬虫补丁**：`geo scaffold` 生成 `Bytespider` 优先的 `robots.txt`；`geo distribute` 生成头条长文+微头条专版；
- **国内本土化体检与 Pitch Deck**：`geo audit` 与 `geo pitch` 输出中国本土模型采购决策全景。

---

## Impact (影响分析)

- **完全向下兼容**：所有已有项目工作区配置无缝继承；
- **交付效率与转化率倍增**：运营与内容团队不再做无意义的海外渠道分发，100% 聚焦国内高转化信任池。

