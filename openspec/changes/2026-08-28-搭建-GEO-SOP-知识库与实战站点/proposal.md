# Proposal: 搭建 GEO SOP 知识库与实战站点

## Why (为什么做)
- 当前我们已经完成了 GEO 核心战略、徐州本地标杆规划和客户交付 SOP 的全套理论文档，但缺乏一个结构化、交互式、可对外展示和供大模型/客户秒级浏览的 Web 载体。
- 构建基于 VitePress 的高性能 SSG 静态知识库站点，一方面作为自身对外输出 GEO 标准与客户交付 SOP 的平台，另一方面作为大模型（DeepSeek、豆包、Kimi）抓取的标杆站点，验证 `/llms.txt`、JSON-LD 与普林斯顿标准样式的实际生效情况。

## What Changes (改动了什么)
1. **初始化 Node.js / VitePress 基础工程**：配置 `package.json`、`vitepress` 依赖与打包脚本。
2. **构建知识库与实战站点结构**：
   - 首页：GEO 核心价值、普林斯顿标准体系、四步交付漏斗看板与快捷入口；
   - 战略指南栏目：包含从 SEO 到 GEO、大模型双通道机理、四层技术体系；
   - 客户交付 SOP 栏目：包含 5 大阶段交付细则、可交互勾选的验收清单（CheckList）；
   - 标杆实战库：包含徐州本地软件开发实操方案、25 个意图词库与《2026 选型白皮书》；
   - 模版与工具中心：包含一键复制的 `/llms.txt`、JSON-LD 代码、对比表格与自动化巡检脚本。
3. **注入 GEO 核心技术底座**：
   - 静态编译自动生成根目录 `/llms.txt` 与 `/robots.txt`；
   - 在 HTML head 中全局注入 Schema.org (JSON-LD) 结构化元数据；
   - 配置高对比度、大模型清洗友好的 Markdown 样式。

## Capabilities (对外能力)
- 🖥️ **本地交互式站点**：支持全局搜索、暗色模式、响应式布局、交互式任务勾选；
- 🤖 **大模型秒级抓取 (GEO-Ready)**：100% 纯静态预渲染 HTML + 结构化 `/llms.txt`；
- 📦 **一键打包与极简部署**：`npm run build` 生成 `dist` 产物，直接上传云服务器 Nginx 即可上线。

## Impact (受影响的部分)
- 新增 `package.json`, `.vitepress/config.mts`, `docs/index.md`, `docs/guide/`, `docs/sop/`, `docs/templates/`。
- 本地开发支持 `npm run dev` 启动端口 5173 预览。
