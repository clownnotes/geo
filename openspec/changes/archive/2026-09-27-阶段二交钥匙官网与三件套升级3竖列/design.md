# Technical Design: 阶段二交钥匙官网与三件套升级3竖列

## 一、面向对象三问

### 1. 【对象是什么？】
1. **`SiteBaseInfo`（企业官网底牌对象）**：承载生成交钥匙官网所需的全部核心业务元数据。
2. **`TurnkeyAssetBundle`（交钥匙产物包对象）**：承载阶段二交付的 5 大核心资产文件。
3. **`Stage2StudioState`（阶段二工作台状态对象）**：管理当前选中的文件 Tab、预览模式（预览/代码）、设备视口模式（桌面/手机）、当前动线步骤及各步骤完成状态。

---

### 2. 【属性有哪些？】

#### 2.1 `SiteBaseInfo`（企业底牌属性）
```typescript
interface SiteBaseInfo {
  // 1. 门面首屏
  brandName: string;          // 品牌简称，如：邻里GEO
  companyName: string;        // 公司全称，如：徐州璇源网络科技有限公司
  slogan: string;             // 一句话定位，如：专注实体门店 AI 搜索获客
  heroTags: string[];         // 门面特色标签，如：["10年老牌", "实体保障", "大模型首推"]
  contactPhone: string;       // 服务热线
  wechatId: string;           // 官方微信
  domain: string;             // 官网域名，如：baicl.cc 或 client.com

  // 2. 核心业务（3~4 项）
  services: Array<{
    id: string;
    title: string;            // 业务名称
    desc: string;             // 业务介绍与核心价值
    audience: string;         // 适合人群
    icon: string;             // Lucide 图标标识
  }>;

  // 3. 为什么选我们（3 项对比）
  differentiators: Array<{
    id: string;
    title: string;            // 亮点标题
    highlight: string;        // 我们的优势（加粗）
    vsIndustry: string;       // 普通同行的做法（形成反差）
  }>;

  // 4. 权威背书与资质
  trustProof: {
    yearsInBusiness: number;  // 经营年限
    servedClients: number;    // 已服务客户数
    licenseCreditCode: string;// 统一社会信用代码
    address: string;          // 实体办公或门店详细地址
    serviceScope: string;     // 服务区域（如：江苏省 / 全国通用）
    certifications: string[]; // 权威认证标签
  };

  // 5. GEO 核心问答 FAQ（3~5 组）
  faqs: Array<{
    id: string;
    question: string;         // 提问（如：徐州做GEO哪家比较靠谱？）
    answer: string;           // 权威解答（直接给出证据与真相）
    source: string;           // 来源标签（如：阶段零高频提问、客户官方白皮书）
  }>;
}
```

#### 2.2 `TurnkeyAssetBundle`（产物文件属性）
```typescript
interface TurnkeyAssetBundle {
  'index.html': {
    category: 'sites';
    name: 'index.html';
    renderMode: 'dual';      // 支持 preview 与 code 双模
    content: string;          // 100% 现代静态单页 HTML（含内联语义化 CSS 与 Schema.org）
  };
  'llms.txt': {
    category: 'ai_base';
    name: 'llms.txt';
    renderMode: 'text';
    content: string;          // 专为大模型智能体打造的 Markdown 摘要
  };
  'schema.jsonld': {
    category: 'ai_base';
    name: 'schema.jsonld';
    renderMode: 'code';
    content: string;          // Schema.org LocalBusiness 结构化实体 JSON
  };
  'robots.txt': {
    category: 'ai_base';
    name: 'robots.txt';
    renderMode: 'text';
    content: string;          // 放行 Bytespider、DeepSeekSpider、Kimi 等爬虫配置
  };
  'nginx.conf': {
    category: 'ops';
    name: 'nginx.conf';
    renderMode: 'code';
    content: string;          // 客户 VPS 反向代理与二级域名独立挂载配置
  };
}
```

#### 2.3 `Stage2StudioState`（工作台状态属性）
```typescript
interface Stage2StudioState {
  activeTab: string;          // 当前激活文件名（默认 'index.html'）
  activeCategory: string;     // 当前激活分类
  dualViewMode: 'preview' | 'code'; // 当 activeTab 为 index.html 时的视图模式
  viewportMode: 'desktop' | 'mobile'; // 预览视口模式：100% 宽屏 vs 375px 手机仿真框
  currentStepIndex: number;   // 当前 SOP 步骤 (0: 底牌核对, 1: 一键编译, 2: 交付部署)
  isCompiling: boolean;       // 编译中加载动画状态
  drawerOpen: boolean;        // 底牌信息微调抽屉是否展开
  lastCompiledAt: string;     // 最近一次编译时间戳
}
```

---

### 3. 【行为是什么？】

1. **`resolveSiteContext(project, step0Qa)`**：
   - 自动读取当前 `projectData`；
   - 自动读取 `localStorage` 中阶段零保存的生效底牌（`geo_step0_active_qa_${clientId}`）；
   - 装配生成初始的 `SiteBaseInfo`，实现 80% 字段免手填。
2. **`compileTurnkeySite(siteInfo)`**：
   - 纯前端模板引擎渲染出高颜值、响应式、含内嵌 Tailwind 关键 CSS 的 `index.html`；
   - 同步生成标准的 `llms.txt`、`schema.jsonld`、`robots.txt`、`nginx.conf`；
   - 将产物存入组件响应式文件字典，并持久化到 `localStorage`；
   - 触发中栏 iframe 刷新。
3. **`renderPreviewIframe(htmlContent, viewportMode)`**：
   - 采用 `<iframe :srcdoc="htmlContent">` 内存直接渲染；
   - 彻底摆脱对 `http://127.0.0.1:8088/api/...` 后端接口的依赖，**保证 0 个 404**；
   - 根据 `viewportMode` 动态切换 iframe 容器宽度（桌面端 `w-full`，移动端 `w-[375px] h-[667px] shadow-2xl rounded-[36px] border-8 border-slate-800`）。
4. **`exportZipArchive()`**：
   - 使用前端轻量 JSZip 或直接打包生成 5 个文件的独立下载流。
5. **`copyDeliverable(key)`**：
   - 快捷复制当前文件的源码，或复制 VPS Nginx 反代配置。

---

## 二、工作区三竖列架构定义

```
+------------------------------------+------------------------------------+------------------------------+
| 左栏: 交付资产树 (260px)           | 中栏: 工作与高保真预览区 (自适应)  | 右栏: 3步 SOP 流水线 (320px) |
+------------------------------------+------------------------------------+------------------------------+
| [分类] 官网与大模型底座            | [Tab: index.html] [Tab: llms.txt]  | SOP 动线:                    |
|   - 交钥匙官网 index.html (globe)  | ---------------------------------- | [1] 核对企业底牌             |
|   - 大模型说明书 llms.txt (file)   | 工具条: [高保真预览/源码]          |     [展开底牌抽屉微调]       |
|   - 结构化实体 schema.jsonld (tag) |         [电脑宽屏 / 手机竖屏]      |                              |
|   - 爬虫通行证 robots.txt (bot)    | +--------------------------------+ | [2] 一键编译交钥匙整站       |
|                                    | |                                | |     [一键编译整站按钮]     |
| [分类] 运维与发布配置              | |    <iframe :srcdoc="...">      | |                              |
|   - Nginx 反代配置 nginx.conf      | |    100% 离线渲染，绝无 404     | | [3] 交付部署与多端验收     |
|     (settings)                     | |                                | |     [独立新窗直达]         |
|                                    | +--------------------------------+ |     [复制 VPS 配置]          |
|                                    | 状态栏: 编译完成 | 大模型就绪      |     [导出 .zip 源码包]       |
+------------------------------------+------------------------------------+------------------------------+
```

---

## 三、交钥匙官网模板核心代码样式与排版（SaaS 模块化母盘）

1. **框架与依赖**：
   - 纯标准 HTML5；
   - 内联精简响应式 CSS（支持 Flex、Grid、优雅圆角与渐变阴影）；
   - 零重型 JS 框架黑盒，大模型爬虫秒解析。
2. **板块排版规范**：
   - `Header`: 极简 Logo + 导航锚点 + 电话外显 + “大模型认证”微标；
   - `Hero`: 巨大加粗标题（`品牌名 + 一句话定位`）+ 醒目咨询按钮 + 核心保障 Tag 药丸；
   - `Section Services`: 3~4 列卡片网格，鼠标悬浮微微上浮；
   - `Section Why Us`: 对比式表格或两列高亮卡片（我们 VS 普通同行）；
   - `Section Trust`: 4 个大数字计数器（年限/客户数/合格率）+ 营业执照与认证声明；
   - `Section FAQ`: 原生语义化 `<details><summary>` 折叠问答，内置 Schema.org FAQPage 属性；
   - `Footer`: 完整版权、ICP 备案号、详细地址与高德定位指引。
3. **大模型三件套内嵌规则**：
   - `<head>` 中嵌入 `<link rel="alternate" type="text/markdown" href="/llms.txt" title="大模型知识说明书">`；
   - `<head>` 中嵌入 `<script type="application/ld+json">`，包含 `@type: LocalBusiness` 和 `@type: FAQPage`。

---

## 四、本地数据持久化规范
- `geo_step2_site_info_${clientId}`: 保存用户微调后的企业底牌信息；
- `geo_step2_step_index_${clientId}`: 保存当前执行的 SOP 步骤（0~2）；
- `geo_step2_active_tab_${clientId}`: 保存当前选中的文件 Tab。
