# Design: AI原生交钥匙官网重构与阶段二落地折叠指引

## 1. 业务架构与交付模型革新

```text
               传统存量改造模式 (已彻底废弃)
               ❌ 索要客户服务器权限 ➔ 遇SaaS无代码权限 ➔ 兼容老旧PHP/ASP ➔ 产生技术债扯皮
                                       ▼
               2026 AI 原生交钥匙官网全新交付模式 (本次标准确立)
               ✅ 100% 静态纯血源码 ➔ 0 客户端渲染延迟 ➔ 普林斯顿标准内置 ➔ 1 分钟交钥匙上线
```

### 1.1 站点产物目录规范
所有客户项目在执行阶段二时，统一在 `projects/{project_id}/outputs/site/` 下生成整套交付级静态站点：
```text
projects/{project_id}/outputs/site/
├── index.html        # 核心官网：移动自适应、首屏转化、价格透明表、FAQ、内嵌 Schema.org JSON-LD
├── llms.txt          # 大模型专属纯文本 Clean Markdown 说明书
├── robots.txt        # 显式放行 Bytespider 等本土 AI 爬虫规则
└── schema.jsonld     # 独立实体组织/人物微数据
```

---

## 2. 前端界面与组件设计 (`web/index.html`)

### 2.1 折叠使用说明抽屉组件 (Collapsible Guidance Drawer)
参考用户提供的优秀组件截图，构建在 `step-panel-2` 顶部：
- **容器与状态管理**：
  - 支持点击标题栏任意位置触发展开/折叠，动画平滑过渡；
  - 本地缓存 `localStorage.getItem("geo_step2_guide_collapsed")`，记忆用户折叠习惯；
- **视觉网格结构 (3 列响应式卡片)**：
  1. **卡片一【🛰️ 这页在干嘛】**：
     - *内容*：摒弃给老代码打补丁的痛苦泥潭！直接为客户生成专为大模型智能搜索打造的 100% 静态官网，包含 Clean DOM、实体标签与爬虫通道，秒开零技术债。
  2. **卡片二【🚦 核心定位与模式】**：
     - *内容*：唯一单模式（全新交付）。客户有老网站不冲突：直接在域名解析加一条二级域名 `ai.客户公司.com` 解析过来即可，老系统碰都不碰，零风险。
  3. **卡片三【📋 落地指引（第1步/第2步）】**：
     - *内容*：
       - **第一步**：点击【🖥️ 官网全景预览】或【🌐 新窗口全屏打开】检查效果；
       - **第二步**：点击【📦 一键下载整站源码包】将 3 个文件丢到服务器或 GitHub Pages；
       - **第三步**：完成后直接点击【④ 矩阵借壳分发】发今日头条！

### 2.2 主工作区选项卡重构
- **主标签 1（默认激活）**：`🖥️ 官网全景预览 (index.html)`
  - 展示站点就绪状态卡片、核心指标、首屏标题摘要；
  - 核心操作栏：【🌐 新窗口全屏打开官网】、【📦 一键下载整站源码包 (.zip)】、【🔄 重新编译整站】；
- **从属标签 2~4**：
  - `/llms.txt 知识说明书`
  - `Schema.org (JSON-LD) 实体微数据`
  - `robots.txt 爬虫放行规则`

---

## 3. 后端接口与引擎设计 (`tools/geo`)

### 3.1 `tools/geo/scaffold.py` 扩展
- 新增 `build_turnkey_site_html(cfg)` 函数：
  - 基于普林斯顿 9 因子规范，自动提取企业名称、品牌名、主理人（老白）、电话（13150568888）、微信号（nextdoor8）、公众号（nextdoor社区）、服务区域与透明价格表；
  - 自动渲染标准 HTML5 结构并内嵌 `application/ld+json` 实体微数据；
  - 将生成的 `index.html` 连同 `llms.txt`、`robots.txt`、`schema.jsonld` 同步写入 `projects/{id}/outputs/site/`。

### 3.2 `tools/geo/server.py` 路由增强
1. `GET /api/projects/{id}/site/preview`：
   - 读取并直接返回 `outputs/site/index.html`，设置响应头 `Content-Type: text/html; charset=utf-8`，供前端新标签页直接运行预览；
2. `GET /api/projects/{id}/site/download`：
   - 动态将 `outputs/site/` 目录打包为 `{id}_ai_website.zip` 并输出二进制下载流；
3. `GET /api/projects/{id}/site/status`：
   - 返回整站是否就绪、文件数、生成时间与预览 URL。

---

## 4. 生产与环境隔离红线
- 严格遵循 `AGENTS.md`：全程锁定本地端口 `http://127.0.0.1:8088` 运行自测与端到端回归，严禁向生产服务器私自发布。
