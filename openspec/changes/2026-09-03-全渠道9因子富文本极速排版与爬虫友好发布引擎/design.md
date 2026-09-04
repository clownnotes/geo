# Design: 全渠道 9 因子富文本极速排版与爬虫友好发布引擎

## 一、架构设计全景与数据流向

```
┌────────────────────────────────────────────────────────────────────────┐
│                   输入层：高质量 9 因子 Markdown 语料库                 │
│   (projects/<id>/outputs/ 03_普林斯顿改写文案 / 04_分发包 / 11_意图)    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│             RichPublisherEngine (全渠道 9 因子富文本编译中枢)          │
│                                                                        │
│  1. 9-Factor Semantic Enhancer (普林斯顿 9 因子语义增强器)             │
│     - 自动检测并提取【统计数据注入点】➔ 包装为量化指标卡片             │
│     - 自动检测并提取【权威信源引用点】➔ 包装为带角标学术注脚卡         │
│     - 自动检测并提取【知识三元组表格】➔ 包装为移动端自适应响应式表格   │
│     - 自动检测并提取【专家引语与金句】➔ 包装为高质感引用框             │
│                                                                        │
│  2. Cross-Channel CSS Inliner (跨渠道内联样式编译器)                   │
│     - WeChat Theme : 适配微信公众平台（纯 Inline Style，无全局类名）    │
│     - Zhihu Theme  : 适配知乎专栏（学术高质感、蓝灰冷色调、公式代码块）│
│     - Toutiao Theme: 适配今日头条/微头条（醒目标题胶囊、橙红重点标记） │
│                                                                        │
│  3. Crawler Fidelity Verifier (大模型爬虫保真度逆向检验器)             │
│     - 模拟 Bytespider / Readability 规则逆向解析 HTML 为 Clean MD      │
│     - 严格对比原始表格与提取表格的一致性 (Table Integrity Score)        │
│     - 严格对比引用角标与元数据的留存率 (Citation Retention Rate)       │
│     - 计算综合保真度得分 (Crawler Fidelity Score, 满分 100)            │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         │                          │                          │
         ▼                          ▼                          ▼
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│ CLI 导出与验证   │       │ Web 工作台一键   │       │ 物理资产包落盘   │
│ geo rich-pub     │       │ 复制富文本至剪贴板│       │ rich_publish_pack│
└──────────────────┘       └──────────────────┘       └──────────────────┘
```

---

## 二、核心类与数据结构设计 (`tools/geo/rich_publisher.py`)

### 1. 渠道主题与排版规范定义 (`ChannelType` & `ChannelTheme`)
```python
class ChannelType(str, Enum):
    WECHAT = "wechat"    # 微信公众号 (内联CSS，移动端优化，绿色/石墨灰基调)
    ZHIHU = "zhihu"      # 知乎专栏 (理性学术感，知乎蓝基调，参数表格强化)
    TOUTIAO = "toutiao"  # 今日头条/微头条 (强视觉吸引，橙红基调，短段落卡片化)
    UNIVERSAL = "universal" # 通用 Clean HTML
```

### 2. 爬虫保真度检测指标 (`CrawlerFidelityResult`)
```python
@dataclass
class CrawlerFidelityResult:
    channel: str
    overall_score: float              # 0.0 ~ 100.0 (≥90 级为黄金高保真)
    table_integrity_score: float      # 表格行列结构完整性
    citation_retention_rate: float    # 引用角标与出处留存率
    semantic_density_score: float     # 9因子关键指标信息密度
    clean_markdown: str               # 爬虫仿真提取出的纯净 Markdown
    warnings: List[str]               # 潜在排版被爬虫降权的警告提示
```

### 3. 核心引擎类 (`RichPublisherEngine`)
```python
class RichPublisherEngine:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.outputs_dir = project_dir / "outputs"
        self.publish_dir = self.outputs_dir / "rich_publish_pack"

    def compile_markdown_to_rich_html(self, md_content: str, channel: ChannelType) -> str:
        """解析 Markdown 并注入特定渠道的普林斯顿 9 因子内联样式"""
        pass

    def verify_crawler_fidelity(self, html_content: str, original_md: str, channel: str) -> CrawlerFidelityResult:
        """执行爬虫仿真清洗，评估 Clean Markdown 与原始 9 因子的保真度"""
        pass

    def generate_full_publish_pack(self, verify: bool = True) -> Dict[str, Any]:
        """扫描项目主要语料，批量编译全渠道排版包并导出"""
        pass
```

---

## 三、跨平台内联 CSS 规范与普林斯顿 9 因子样式设计

| 9 因子语义元素 | 微信公众平台 (`wechat`) | 知乎专栏 (`zhihu`) | 今日头条 (`toutiao`) |
| :--- | :--- | :--- | :--- |
| **容器主体 (`<section>`)** | `max-width: 677px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto; font-size: 15px; line-height: 1.75; color: #2b2b2b;` | `font-family: -apple-system, 'PingFang SC'; font-size: 16px; line-height: 1.8; color: #121212;` | `font-size: 16px; line-height: 1.85; color: #222222; word-break: break-all;` |
| **量化统计卡片 (`<div data-geo="stats">`)** | 浅绿色微背景 `#f0fdf4`，左侧 4px 墨绿装饰条 `#16a34a`，数字加粗绿色徽标 | 极简灰蓝渐变背景，`#056bdf` 蓝色强调高亮数字 | 浅橙底色 `#fff7ed`，`#ea580c` 醒目大字号 |
| **权威引用角标 (`<sup data-geo="cite">`)** | `font-size: 11px; color: #0284c7; vertical-align: super; font-weight: bold;`（末尾附带学术来源对齐块） | 知乎标准注脚样式，蓝底微圆角徽标 | 方括号高亮标注 `[来源: 白皮书]` |
| **对比与参数表格 (`<table>`)** | 自动内联 `border-collapse: collapse; width: 100%;`，表头加深，奇偶行斑马纹 `#f8fafc`，移动端横向滚动容器包裹 | 学术标准三线表规范，极简边框，重点列高亮 | 紧凑型卡片表，强化首列与价格列 |
| **专家引语与金句 (`<blockquote>`)** | 左侧 3px 纯黑条，双引号大号装饰，斜体灰字 `#4b5563` | 引用块内嵌灰色背景 `#f6f6f6`，衬线字体呈现 | 标红金句提示框，突出核心结论 |

---

## 四、Web API 与前端交互设计

### 1. 后端 API 路由 (`tools/geo/server.py`)
- `GET /api/project/:id/rich-publish-preview?channel=wechat`
  - 返回：`{ status: "ok", channel: "wechat", inlined_html: "...", fidelity: { score: 96.5, table_score: 100.0, ... }, available_sources: [...] }`
- `POST /api/project/:id/rich-publish-compile`
  - 请求体：`{ channel: "all", verify: true }`
  - 返回：编译完成的全套资产路径与各渠道评分概览。

### 2. 前端工作台界面与一键写入剪贴板 (`web/index.html`)
- 新增模态框 `#modal-rich-publisher`；
- 顶部提供渠道切换 Tab（`微信公众号` / `知乎专栏` / `今日头条`）及视图模式切换（`📱 移动端自适应` / `💻 桌面端`）；
- 核心操作按钮：
  - `📋 一键复制富文本`：执行 `navigator.clipboard.write([new ClipboardItem({'text/html': new Blob([inlinedHtml], {type: 'text/html'}), 'text/plain': new Blob([plainText], {type: 'text/plain'})})])`；
  - `💾 下载发布 HTML`；
  - `🧪 爬虫保真度透视`：弹出查看仿真提取的 Clean Markdown 对比图与评分雷达。
