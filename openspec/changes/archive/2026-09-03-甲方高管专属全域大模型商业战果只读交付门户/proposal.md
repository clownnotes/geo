# Proposal: 甲方高管专属全域大模型商业战果只读交付门户 (第 28 维·修订版)

## Why (背景与业务痛点)

在 GEO 项目前期 1~27 维度的工业化底座建设中，系统已在后端沉淀了极其深厚的大模型推演算法与攻防资产（包括普林斯顿 9 因子质检、大模型爬虫高保真排版、商业心智渗透率 MPI、因果边际贡献、竞品截流沙盘、全网分发存活台账等）。

然而在商业化落地与代运营服务交付中，存在一个**关键的“最后一公里”痛点**：
1. **控制台面向工程师，甲方高管无法直视**：现有的 Web 控制台（8088 端口）充斥着 30 多个操作按钮、流水线调度配置、底层运行日志与敏感调试信息。若将其直接提供给甲方企业的董事长、总经理或 CMO，不仅操作门槛极高，更存在敏感配置被误触或泄露的安全风险；
2. **传统 PDF/PPT 汇报周期长、缺乏科技代差**：一线代运营团队过去往往需要耗费 1~2 天人工整理 Word/PDF 汇报周报，数据静态滞后、无法交互、毫无高科技质感，难以体现工业化 GEO 相比传统搜索引擎代运营的技术代差；
3. **商业核心价值无法秒级感知**：甲方出资人真正关心的三大核心问题——**“大模型到底首推我们没有？”、“帮我们拦截了多少竞品客户？”、“相比传统广告相当于省了多少钱？”**，散落在各后台 JSON 与 Markdown 文件中，缺乏一个免密沉浸、移动端自适应的高管战略战果大屏。

因此，亟需在第 28 维建设**《甲方高管专属全域大模型商业战果只读交付门户 (Executive GEO Delivery Portal)》**，让代运营团队能够 3 秒生成专属安全链接，发给甲方老板在微信中免密即开，用直观量化的商业 ROI、主流大模型推荐雷达、真实信源证据链与数字结案证书，直接驱动客户高满意度结案与大额季度续约。

---

## What (核心改动与交付功能)

本变更遵循“三大价值过滤铁律”中**【铁律 3: 商业交付更具代差】**与**【铁律 2: SOP 生产大幅提效】**，在现有架构上进行纵向升级，**坚决不搞平行烟囱**：

1. **高管商业交付数据聚合引擎 (`tools/geo/share.py` 纵向升级)**：
   - 打破 16 维历史局限，打通 17~27 维高阶商业资产，严格对齐真实 JSON 字段，坚决杜绝假数据：
     - **商业心智渗透率 (MPI)**：基于 `mindshare_conversion_audit.json` 读取真实的 `summary.mpi`、年化广告节省 `summary.annual_aev_yuan`、实测模型探针的首推率（基于 `probe_records.is_top1` 真实统计）；
     - **实测模型推荐心智雷达**：对齐实测探针（豆包、DeepSeek、Kimi），杜绝无探针模型的假打分；对微信/元宝生态在分发台账中真实标注「渠道覆盖代理·微信搜一搜独占」；
     - **竞对攻防实战**：基于 `competitor_gap_analysis.json` 真实提取对手列表、声量领先差距与反制突破点；
     - **普林斯顿 9 因子 & 爬虫保真度**：呈现 `princeton_audit.json` 的实测均分，并聚合 `outputs/*_pack/fidelity_report.json` 的真实无托底保真度评分；
     - **全网分发存活台账**：真实提取 `dist_ledger.json` 中各渠道 URL、收录状态与探活结果，区分「已收录·探活正常」、「已填报·待探活」与「待分发」；
     - **商业结案数字证书**：复用既有 `tools/geo/certificate.py` 编译的 A4 打印证书，呈现 SHA256 密码学防伪指纹。
2. **专属高管沉浸式只读大屏 (原地升级 `web/share.html`)**：
   - **单文件收敛原则**：坚决不新建平行 `portal.html`，原地重构升级 `web/share.html`，确保历史 `/share/{token}` 与新别名 `/portal/{token}` 统一享受现代高管大屏；
   - 采用深邃科技暗黑商务风格（Deep Navy / Slate Dark Theme），移动端微信与 iPad 极致自适应；
   - 向后兼容：保留旧版交付物查看能力（通过折叠抽屉优雅嵌入），新增 Hero KPI 四宫格、模型首推雷达、竞对攻防表、信源证据链与证书查验 Modal。
3. **高熵安全鉴权与生命周期管理**：
   - 密码学高熵安全 Token（$2^{192}$ 穷举空间），支持可选 4 位加盐哈希提取码保护（PIN Code）；
   - 提供 `--refresh` 强制重置生命周期功能：作废当前项目所有历史活跃 Token，生成唯一单活新链接。
4. **CLI 一键调度与离线单文件导出 (`tools/geo/cli.py`)**：
   - 挂载 `geo portal <project_id>` 子命令（兼容保留 `geo share`）；
   - 支持 `--days`、`--pin`、`--refresh`、`--export <file.html>`（离线导出单文件 HTML，内联全部关键 CSS/JS 资源，保证内网断网零 CDN 依赖打开）；
   - 终端彩色打印高管交付专享卡片与一键发送给甲方老板的微信格式文案模板。

---

## Capabilities (对外能力规范)

### 1. 命令行 CLI 接口
```bash
# 生成 30 天免密高管专属交付大屏链接与微信战报模版
./geo portal xuzhou_xuanyuan

# 生成带 4 位访问提取码的专属门户（有效期 90 天）
./geo portal xuzhou_xuanyuan --days 90 --pin 8888

# 强制作废历史链接并生成全新专属 Token (单活轮转)
./geo portal xuzhou_xuanyuan --refresh

# 导出离线独立单文件 HTML 交付大屏 (无外部 CDN 依赖，内网即开即用)
./geo portal xuzhou_xuanyuan --export ./executive_portal_xuzhou.html
```

### 2. HTTP Web API 接口
- `GET /portal/{token}` 与 `GET /share/{token}`：统一指向升级后的 `web/share.html`；
- `GET /api/share/{token}/data`：只读沙箱数据聚合 API（向后兼容既有键，追加高管战报键）；
- `GET /api/share/{token}/certificate`：复用既有接口，直取 A4 打印级交付结案证书；
- `GET /api/share/{token}/download-zip`：复用既有接口，安全下载数字资产全包。

---

## Impact (影响范围分析)

1. **改动模块**：
   - `tools/geo/share.py`：升级数据聚合器，增补字段映射与 `--refresh`、`--export` 逻辑；
   - `tools/geo/cli.py`：挂载 `geo portal` 子命令及参数解析；
   - `tools/geo/server.py`：复用既有 handler，仅增设 `/portal/{token}` 别名路由；
   - `web/share.html`：原地升级为高管沉浸式深色大屏，不创建平行文件；
   - `tests/test_delivery_portal.py`：新增全套覆盖与断言单测。
2. **兼容性与安全红线**：
   - 100% 兼容历史 `/share/{token}` 链接与 `data/shares.json`；
   - 强制保持 `X-Robots-Tag: noindex, nofollow, noarchive` 防爬虫索引；
   - 全库现有 133 组单元测试必须 100% 保持秒绿通过。
