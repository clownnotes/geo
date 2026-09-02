# Proposal: GEO 商业交付结案证书与数字资产移交生成器 (GEO Delivery Certificate & Digital Asset Handover Generator Engine)

## Why (为什么做 / 商业背景与终局闭环诉求)

1. **商业交付与尾款结算的核心痛点**：
   - 在向政企客户、制造业实体、本地生活及连锁品牌交付 GEO 全案时，甲方财务、法务与决策人需要一份具有正式公信力、防伪存证与知识产权移交的**正式结案证书**；
   - 之前系统虽然输出了 Markdown 结案单，但在 A4 纸质盖章签署、PDF 打印留档以及防伪溯源上缺少公文级、防伪级的高保真排版工具；
2. **数字资产移交与法律责任界定**：
   - 结案证书需要将交付的技术底座（`/llms.txt`, `schema.jsonld`）、45 组三层意图词库、9 因子精修语料、多平台存活台账（`dist_ledger.json`）与 5 维幻觉纠偏补丁形成明确的资产清单与数字哈希，明确知识产权 100% 移交甲方，并附带 365 天质保服务承诺。

---

## What Changes (改动范围)

1. **新增商业结案证书生成引擎 (`tools/geo/certificate.py`)**：
   - `build_delivery_certificate_html(project_id)`：生成公文级防伪 A4 打印优化的结案移交证书；
   - 支持防伪水印、数字资产 SHA256 哈希存证、甲乙双方签字盖章区、365 天质保承诺与防伪验真二维码；
   - 输出标准物：`projects/<project_id>/outputs/09_GEO全案商业交付结案与数字资产移交证书.html`；
2. **CLI 命令行与 Web 端集成**：
   - CLI 新增 `geo certificate <project_id>` 子命令；
   - Web 端与甲方分享门户（`/api/share/{token}/certificate`）提供一键打印/存为 PDF 入口。

---

## Capabilities (对外能力)

- **`geo certificate <project_id>`**：一键生成公文级结案证书；
- **A4 打印优化**：支持在浏览器中直接 `Ctrl+P / Cmd+P` 一键存为标准 A4 结案证书；
- **防伪与哈希存证**：自动对交付物文件计算 SHA256 指纹，确保资产移交的法律不可篡改性。

---

## Impact (影响分析)

- **极大加速客户结算回款**：提供盖章级正式公文，消除甲方法务与财务疑虑；
- **全案闭环终局**：【商业定价 ➔ 语料母版 ➔ 渠道分发 ➔ 存活台账 ➔ 真机评测 ➔ 结案移交证书】形成 100% 商业与技术终极闭环。

