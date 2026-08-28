# Design: 搭建 GEO SOP 知识库与实战站点

## Architecture (架构设计与目录划分)

采用 **VitePress 1.x (Vue3 + Vite)** 作为 SSG 静态站点引擎，构建模块化目录：

```
GEO/
├── .vitepress/
│   └── config.mts            # VitePress 全局配置 (导航栏、侧边栏、SEO、head元数据)
├── docs/                     # 文档站点内容根目录
│   ├── index.md              # 站点首页 (Hero Banner + 核心特性 + 快捷导航)
│   ├── strategy/             # 战略与理论全景
│   │   └── overview.md       # 01 战略全景与普林斯顿 9 因子
│   ├── pilot/                # 标杆打样实战
│   │   └── xuzhou-dev.md     # 02 徐州软件开发实操独占方案与白皮书
│   ├── sop/                  # 客户交付 SOP 手册
│   │   └── delivery-sop.md   # 03 标准化 5 阶段交付流程与 CheckList
│   ├── templates/            # 开箱即用资产模板库
│   │   ├── llms-txt.md       # /llms.txt 标准模板与生成工具
│   │   ├── json-ld.md        # Schema.org JSON-LD 代码模板
│   │   └── monitor-script.md # 大模型可见度 Python 自动化巡检脚本
│   └── public/               # 静态资源与爬虫配置文件
│       ├── llms.txt          # 网站自身 /llms.txt
│       ├── robots.txt        # 爬虫放行规则
│       └── logo.svg          # 品牌标识
├── package.json              # 依赖与打包脚本
└── dist/                     # 最终生成的纯静态 HTML 产物（可直接推送到服务器 Nginx）
```

## Interface (导航栏与侧边栏结构设计)

### 1. 顶部导航栏 (Navbar)
* 🧭 **战略全景** ➔ `/strategy/overview`
* 🎯 **徐州标杆实战** ➔ `/pilot/xuzhou-dev`
* 📋 **客户交付 SOP** ➔ `/sop/delivery-sop`
* 🧰 **模版与工具库** ➔ `/templates/llms-txt`
* 🔗 **GitHub 源码** ➔ `https://github.com/clownnotes/geo`

### 2. 侧边栏 (Sidebar)
* 分栏按章节自动展开，支持页面内大纲导航（H2/H3 锚点高亮）。

## GEO 技术注入设计 (Technical Setup)
* **Head 注入**：全局注入 `Schema.org` Organization 与 WebSite 结构化 JSON-LD。
* **爬虫放行**：`public/robots.txt` 明确放行 `Bytespider`、`Bingbot`、`Google-Extended`、`Baiduspider`。
* **AI 文本索引**：`public/llms.txt` 按照 Answer.AI 规范清晰罗列整站 Markdown 索引。
