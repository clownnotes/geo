# Design: GEO 工程体系对标评估与全网矩阵半自动化分发演进

## 1. 架构总览与分层设计

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      Web 管理工作台交互层 (web/index.html)                │
│  - Step 4 矩阵分发助手（4 阵地卡片 + 一键复制 + 直达各平台发布后台入口）   │
│  - 工业化 vs 传统手工代运营 对标透视卡片与客户沟通话术库                  │
│  - Step 5 真实 Citation 权威域名图谱与渗透分布看板                      │
└────────────────────────────────────▲────────────────────────────────────┘
                                     │ (RESTful API / JSON)
┌────────────────────────────────────┴────────────────────────────────────┐
│                      核心业务与生产引擎层 (tools/geo/)                   │
│  - distribute.py: 4 渠道格式化器（知乎/头条/微信/GitHub）+ 操作清单组装器 │
│  - monitor.py: 基于 probe_llm_live 的 Citation 域名增量聚合与加权模型   │
│  - server.py: 提供分发平台排版预览接口与对标数据接口                    │
└────────────────────────────────────▲────────────────────────────────────┘
                                     │ (Clean Markdown / Static SSG)
┌────────────────────────────────────┴────────────────────────────────────┐
│                      知识库与标准规范层 (docs/ & VitePress)             │
│  - docs/strategy/industrial-vs-manual.md: 行业对标与成熟度评估白皮书    │
│  - 单源维护 benchmark 对标矩阵数据                                      │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 核心模块与实现规范

### 2.1 分发矩阵四渠道产物规范 (`tools/geo/distribute.py`)
每个项目在 `outputs/` 下统一生成以下标准文件：

1. **`dist_zhihu_article.md`（知乎专栏版）**：
   - 格式约束：标准 GFM Markdown，嵌入对比表格、代码块语法、文末添加客观测评签名与声明；避免使用知乎 Markdown 解析器不支持的复杂 HTML 标签。
2. **`dist_toutiao_article.md`（今日头条/百家号版）**：
   - 格式约束：高易读性分段、核心量化数据用 `【加粗】` 强调、包含 3 组常见问题长文问答对与 1 条微头条精炼短动态。
3. **`dist_wechat_article.html`（微信公众号专用版）**：
   - 格式约束：采用内联 CSS 样式（如 `style="font-size: 15px; color: #333; line-height: 1.75;"`）渲染的 Clean HTML 片段，支持微信公众平台后台富文本编辑器直接无损粘贴。
4. **`dist_github_README.md`（GitHub 开源生态版）**：
   - 格式约束：包含 Shields.io 状态徽标、全套 Markdown 快速导航、/llms.txt 链接与规范开源目录索引。
5. **`dist_channels_checklist.md`（外发渠道执行清单）**：
   - 格式约束：明确 4 大平台的发布入口、建议标签、发布频率与回填落地页链接规范。

### 2.2 Citation 反向归因与权威度加权评分 (`tools/geo/monitor.py`)
在现有的 `probe_llm_live` 返回的 `citations` 数组基础上做增量聚合，无需重复解析：

```python
# 权威信源基础权重字典（0.0 ~ 1.0）
PLATFORM_AUTHORITY_WEIGHTS = {
    "zhihu.com": 1.0,      # 深度技术长文高权重
    "github.com": 0.95,    # 开源与技术代码高权重
    "toutiao.com": 0.90,   # 字节豆包核心抓取源
    "juejin.cn": 0.85,     # 开发者技术社区
    "weixin.qq.com": 0.85, # 微信生态
    "baike.baidu.com": 0.90# 百科词条
}
# 计算逻辑：
# 1. 对所有返回的 Citation URL 提取 netloc（如 www.zhihu.com -> zhihu.com）；
# 2. 统计每个域名的出现频次 count；
# 3. 计算加权得分：Score = count * PLATFORM_AUTHORITY_WEIGHTS.get(domain, 0.5)；
# 4. 输出按权重得分排序的 Top-N 权威渗透分布表。
```

### 2.3 RESTful API 契约设计 (`tools/geo/server.py`)

#### ① 分发平台排版预览接口
- **请求**：`GET /api/projects/{id}/distribute/preview?platform={zhihu|toutiao|wechat|github}`
- **鉴权**：需携带 Bearer Token
- **响应示例**：
```json
{
  "success": true,
  "platform": "wechat",
  "filename": "dist_wechat_article.html",
  "format": "html",
  "content": "<div style=\"font-family: -apple-system, BlinkMacSystemFont, ...\">...</div>"
}
```

#### ② 行业对标数据接口
- **请求**：`GET /api/benchmark/comparison`
- **鉴权**：公开接口 / 需 Token 均可
- **响应示例**：
```json
{
  "success": true,
  "dimensions": [
    {
      "dim": "技术底座能力",
      "manual": "0 代码能力，无法配置 /llms.txt 与 JSON-LD",
      "industrial": "一键生成全套底座补丁，建立官方实体身份",
      "gain": "大模型采纳率提升 +30%~+41%"
    },
    {
      "dim": "交付耗时与成本",
      "manual": "3~7 天人工写稿，按月收取高额代运营费",
      "industrial": "30 秒全套资产自动化，边际交付成本趋近于 0",
      "gain": "效率提升 90% 以上"
    }
  ]
}
```

---

## 3. Web 工作台 Step 4 直达入口映射

在前端定义各平台官方创作后台直达链接，支持一键点击跳出：
- **知乎创作中心**：`https://www.zhihu.com/creator`
- **今日头条号**：`https://mp.toutiao.com/`
- **微信公众平台**：`https://mp.weixin.qq.com/`
- **GitHub**：`https://github.com/new`
