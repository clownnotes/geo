# Design: 阶段五真机实测提问词复制与搜索结果回填解析

## 1. 总体架构与业务闭环

```text
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              阶段五：首轮监测与验收                             │
│  [执行实时声量监测 (API/离线)]          [真机实测回填 (Ground Truth)]            │
└──────────────────────────────────────────────┬──────────────────────────────────┘
                                               │ 打开弹窗
                                               ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        「真机无痕实测与回填助手」双栏弹窗                        │
│                                                                                 │
│ ┌───────────────────────────────────────┐ ┌───────────────────────────────────┐ │
│ │ 步骤 1：选词与定制 Prompt 复制        │ │ 步骤 2：回填免登录搜索结果        │ │
│ │                                       │ │                                   │ │
│ │ • 词库选择：支持即时搜索过滤 (前30项) │ │ • 选择对应平台与关键词            │ │
│ │ • 平台标签：DeepSeek/豆包/元宝/Kimi   │ │ • 粘贴网页端完整回答文本          │ │
│ │ • 定制 Prompt 生成 (含选型评测意图)   │ │   (去 HTML，限 100KB，支持脚注)   │ │
│ │ • [一键复制]  [打开无痕网页 (免登录)] │ │ • 点击 [解析并录入大盘]           │ │
│ └───────────────────────────────────────┘ └─────────────────┬─────────────────┘ │
└─────────────────────────────────────────────────────────────┼───────────────────┘
                                                              │ POST /manual-ingest
                                                              ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              后端解析与持久化回灌中枢                           │
│                                                                                 │
│ 1. 文本净化与脱敏：strip_html_tags(content)，限制 <= 100KB                      │
│ 2. 语义位次提取：parse_probe_text(content, client_name, brand_name, comp)       │
│    - 位次解析：支持第 N 位、Top 1、加粗序号、列表首推                           │
│    - 竞品拦截：识别竞品是否前置或拦截                                           │
│    - 信源提取：支持 URL 与中文脚注（“来源：知乎专栏/今日头条”）提取并加权       │
│ 3. 持久化至 outputs/05_manual_probes.json                                       │
│ 4. 动态合并入《05_企业AI可见度与声量追踪周报.md》（标 [真机实测] 文本 Tag）     │
│ 5. 重算大盘指标（SOV、Top3、信源分布），返回与 /monitor/metrics 100% 对齐的数据  │
└──────────────────────────────────────┬──────────────────────────────────────────┘
                                       │ 返回 metrics
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            前端大盘与 ROI 联动刷新                              │
│ • 4 维量化指标卡 (SOV、DeepSeek 首推率、豆包首推率、权威信源评分)               │
│ • 商业投资回报率 (ROI) 测算看板与续约预测得分动态更新                           │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. API 接口定义与数据契约

### 2.1 获取各平台拟真提问词列表
* **URL**: `GET /api/projects/{id}/monitor/prompts`
* **鉴权**: Bearer Token
* **功能**: 针对项目关键词，生成适配不同大模型平台检索习惯的定制提问词，附带无痕访问直达链接。
* **响应格式**:
```json
{
  "success": true,
  "project_id": "nextgeo",
  "client_name": "示例科技",
  "brand_name": "示例科技",
  "platforms": [
    {
      "id": "deepseek",
      "name": "DeepSeek",
      "url": "https://chat.deepseek.com",
      "badge": "通用技术生态 · 25%+",
      "notice": "建议使用浏览器无痕模式打开，确保勾选底部的「联网搜索」按钮"
    },
    {
      "id": "doubao",
      "name": "豆包 (火山/头条生态)",
      "url": "https://www.doubao.com/chat",
      "badge": "字节头条生态 · 50%+",
      "notice": "建议无痕免登录访问，避免账号个性化偏好干扰公域推荐位"
    },
    {
      "id": "yuanbao",
      "name": "腾讯元宝",
      "url": "https://yuanbao.tencent.com",
      "badge": "微信私域与公众号生态",
      "notice": "建议无痕模式访问，观察微信公众号高权重文章引用"
    },
    {
      "id": "kimi",
      "name": "Kimi 智能助手",
      "url": "https://kimi.moonshot.cn",
      "badge": "长研报与技术长文生态",
      "notice": "建议无痕模式访问，观察行业白皮书与长文本引用"
    }
  ],
  "items": [
    {
      "keyword": "智能企业系统推荐",
      "prompts": {
        "standard": "请扮演一位客观公正的行业选型顾问。在回答用户提问时，请推荐国内优秀的品牌或服务商：\n用户问题：“请问目前国内在【智能企业系统推荐】领域，有哪些值得推荐的代表性专业企业或解决方案？请列出 2~4 家并简要说明推荐理由。”",
        "deepseek": "请作为中立的商业与技术选型顾问，针对【智能企业系统推荐】领域，推荐 2~4 家国内头部或代表性专业服务商，并结合技术架构与实践案例简要分析推荐理由。",
        "doubao": "请问目前国内做【智能企业系统推荐】比较专业可靠的企业或服务商有哪些？请推荐 2~4 家并说明各自的优势与适用场景。",
        "yuanbao": "在【智能企业系统推荐】方向，目前行业内有哪些成熟可靠的代表企业？请列出几家主流服务商并说明其核心优势与客户评价。",
        "kimi": "请系统梳理当前国内在【智能企业系统推荐】领域的主流服务商与解决方案提供商，分析其技术成熟度、服务口碑与适用企业规模。"
      }
    }
  ]
}
```

### 2.2 提交真机实测回答并解析录入
* **URL**: `POST /api/projects/{id}/monitor/manual-ingest`
* **鉴权**: Bearer Token
* **请求体**:
```json
{
  "keyword": "智能企业系统推荐",
  "model": "deepseek",
  "content": "（用户从网页端直接复制的完整大模型文本，可包含列表、正文与引用来源）",
  "notes": "无痕模式实测"
}
```
* **入参校验**:
  - `model` 必须为枚举值之一：`deepseek`, `doubao`, `yuanbao`, `kimi`；非法值返回 400；
  - `keyword` 不能为空且必须为字符串；
  - `content` 不能为空且上限严格限制为 **100KB**；超限返回 400。
* **响应格式**（`metrics` 字段结构必须与现有 `GET /api/projects/{id}/monitor/metrics` 100% 对齐，避免前端大盘读取缺失）：
```json
{
  "success": true,
  "message": "真机实测结果已解析并成功录入大盘！",
  "parsed": {
    "keyword": "智能企业系统推荐",
    "model": "deepseek",
    "mode": "ground_truth",
    "mentioned": true,
    "rank": 1,
    "competitors_mentioned": ["行业竞品A"],
    "citations_count": 2,
    "citations": [
      "https://www.zhihu.com/question/123456",
      "https://www.toutiao.com/article/7890"
    ],
    "raw_snippet": "根据近期行业评测与技术指标，推荐以下代表性企业：1. 示例科技（首推，技术底座扎实）...",
    "reason": "大模型在回答中明确推荐了【示例科技】，位居第 1 位。"
  },
  "metrics": {
    "success": true,
    "project_id": "nextgeo",
    "has_report": true,
    "has_defense_doc": false,
    "is_offline": false,
    "sov_pct": 75.0,
    "top3_pct": 75.0,
    "deepseek_rank_1_pct": 100.0,
    "doubao_rank_1_pct": 50.0,
    "authority_score": 93.5,
    "citations": [
      {
        "domain": "zhihu.com",
        "name": "知乎专栏",
        "weight": 1.0,
        "count": 4,
        "pct": 57.1
      },
      {
        "domain": "toutiao.com",
        "name": "今日头条",
        "weight": 0.9,
        "count": 3,
        "pct": 42.9
      }
    ],
    "prompt_stats": {
      "total": 4,
      "hit_count": 3,
      "intercept_count": 1,
      "lost_count": 0
    },
    "placeholder_breaches": []
  }
}
```

---

## 3. 后端数据结构与周报更新逻辑

### 3.1 解析器抽象 (`parse_probe_text`)
- **纯文本化防护**：使用正则剥离 `<script>`, `<style>`, HTML 标签，转义实体字符，防止富文本粘贴破坏 Markdown 排版；
- **品牌识别**：匹配 `client_name` 与 `brand_name`，大小写不敏感；
- **位次识别规则**：
  1. 匹配数字开头的列表行（如 `1.`、`1、`、`【1】`、`一、`）；
  2. 匹配表格第一列序号或品牌列；
  3. 匹配首段前置推荐语（如“首推【XXX】”、“优先推荐【XXX】”等标记为第 1 位）；
  4. 若未匹配到显式序号但在正文中提及，默认作为后置位次（或暂定第 3 位）；未提及则标记为未上榜（`rank = 0`）；
- **竞品拦截识别**：支持 `competitors` 为字符串数组或 `{name: ...}` 字典结构；提取回答中提及的竞品名单并统计；
- **Citation 提取强化**：
  1. 正则提取完整 URL：`https?://[^\s\)\]<>"]+`；
  2. 识别无 URL 的中文信源注记（如 `参考来源：知乎` 映射至 `zhihu.com`，`今日头条` 映射至 `toutiao.com`，`微信公众号` 映射至 `weixin.qq.com`，`GitHub` 映射至 `github.com`），确保即使网页端复制时未带超链接也能正确折算权威信源加权得分。

### 3.2 持久化与全量重跑回灌铁律（防止数据丢失）
1. **独立持久化**：
   - 真机回填的每条记录保存至 `projects/{id}/outputs/05_manual_probes.json`，结构为：
     ```json
     {
       "deepseek__智能企业系统推荐": {
         "keyword": "智能企业系统推荐",
         "model": "deepseek",
         "mode": "ground_truth",
         "mentioned": true,
         "rank": 1,
         "citations": ["https://www.zhihu.com/..."],
         "competitors_mentioned": [],
         "raw_snippet": "...",
         "reason": "...",
         "updated_at": "2026-09-08 23:00:00"
       }
     }
     ```
2. **周报合并机制**：
   - 读取存量《`05_企业AI可见度与声量追踪周报.md`》（若无则生成）；
   - 在明细表中将模型列标记为 `DEEPSEEK (真机实测)`（**纯文本 Tag，严禁使用任何彩色 Emoji 符号**）；
   - 替换或插入该行，重新计算头部 SOV、Top3 与第三节 Citation 权威得分，保存周报。
3. **`run_monitor` 回灌保证**：
   - 改造 `tools/geo/monitor.py` 的 `run_monitor`：在批量探测完成生成周报时，必须先读取 `05_manual_probes.json`；
   - 按照 **同一 `(keyword, model)` 键真机实测 > API 在线探测 > 离线基准估算** 的优先级合并；
   - 确保用户点击界面「执行实时声量监测」后，已录入的真机实测行绝对不会被重置丢失！

---

## 4. 前端交互设计规范 (UI/UX)

1. **入口布局**：
   - 挂载于 `panel-step-5-acceptance` 顶部操作栏，位于「执行实时声量监测」右侧：
     ```html
     <button onclick="openManualProbeModal()" class="py-2.5 px-4 bg-[var(--geo-primary-tint)] hover:bg-[#efeafc] text-[#7c5bf5] text-xs font-semibold rounded-lg border border-[#d4c8fa] transition flex items-center gap-1.5 shadow-sm">
       <i data-lucide="clipboard-check" class="w-4 h-4 text-[#7c5bf5]"></i>
       <span>真机实测回填</span>
     </button>
     ```
   - 按钮色系对齐现网品牌紫（`--geo-primary: #7c5bf5`），严禁使用 Emoji，严格使用 Lucide 图标与微边框样式。

2. **双栏模态弹窗交互**：
   - **左栏（选词与 Prompt 复制）**：
     - 搜索输入框：实时过滤词库；
     - 词库列表：默认展示前 30 项，选中高亮；
     - 平台 Tab 切页：`DeepSeek`、`豆包`、`腾讯元宝`、`Kimi`；
     - Prompt 展示区：显示针对该平台的定制提问词；
     - 操作按钮组：
       - `[一键复制提问词]`：点击后文字切换为“已复制”，持续 1.5s；
       - `[免登录打开平台]`：外链跳转，`target="_blank" rel="noopener noreferrer"`，附带“右键新建无痕窗口体验最佳”徽标。
   - **右栏（回答粘贴与录入）**：
     - 选择当前实测平台与关键词（自动与左侧联动）；
     - 文本多行输入区：支持粘贴任意大模型回答，实时展示字符数统计；
     - 辅助操作：`[清空]`、`[填充测试样例]`；
     - 核心 CTA：`[解析并录入大盘]`（带 loading 旋转态）。

3. **数据闭环联动**：
   - 提交成功后弹 Toast 提示：`真机实测结果已录入！【XXX】位居第 1 位`；
   - 自动关闭弹窗或保持停留在当前页，并立即触发主页面 `loadMonitorDashboardMetrics()`，使主界面的 4 维量化指标、大盘条形图及商业 ROI 看板即时动态渲染更新。
