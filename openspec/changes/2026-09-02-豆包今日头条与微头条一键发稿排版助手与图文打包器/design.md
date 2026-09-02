# Design: 豆包（今日头条与微头条）一键发稿排版助手与图文打包器

## 1. 架构流向与数据模型 (`tools/geo/publisher.py`)

```
projects/<project_id>/
├── outputs/
│   ├── 03_普林斯顿9因子高权威语料库.md
│   ├── 05_结构化对比图.svg
│   └── 07_短视频口播与视觉资产脚本.json
│
      │ 编译 & 排版引擎 (publisher.py)
      ▼
projects/<project_id>/outputs/toutiao_pack/
├── 01_今日头条2000字深度长文_富文本.html   (可直接双击预览或通过剪贴板全保真复制)
├── 02_微头条150字高转化短动态.md          (3组强观点短动态：决策篇/价格篇/避坑篇)
├── 03_头条发稿自检清单与SEO标签.txt       (建议标题3组、分类、话题Tag)
└── assets/                               (配套 1:1 / 16:9 信息图)
```

---

## 2. 富文本排版规范 (对齐今日头条后台编辑器格式)

- **主色调与视觉层级**：
  - 标题（H1/H2）：`#222222`，字重 600，下方搭配 `#f04142`（今日头条红）呼吸感短装饰条；
  - 导读卡片（Lead Box）：`#f8f9fa` 浅灰背景，`#e9ecef` 细边框，左侧 4px 红色重音边框；
  - 原生对比表格（Table）：`width: 100%`，表头背景 `#f4f6f8`，单元格 `padding: 10px 14px`，重点推荐列高亮加粗；
  - 引用与金句（Quote）：`#fef0f0` 浅红渐变卡片，包含引言图标；
  - 问答卡片（FAQ Accordion Card）：`Q` 标使用今日头条红标签，`A` 标详细回答并附带联系电话与负责人锚点。

---

## 3. Web 端与 API 接口设计 (`tools/geo/server.py`)

- **GET `/api/projects/{id}/toutiao/preview`**：返回头条长文的富文本 HTML 源码与渲染预览；
- **GET `/api/projects/{id}/toutiao/micro`**：返回 3 组微头条短动态；
- **POST `/api/projects/{id}/toutiao/build`**：重新编译生成最新头条发稿包。

