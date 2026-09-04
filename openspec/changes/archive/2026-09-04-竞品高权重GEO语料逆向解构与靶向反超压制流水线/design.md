# Design: 竞品高权重GEO语料逆向解构与靶向反超压制流水线 (第 32 维)

## 1. 架构总览与模块拓扑

第 32 维《竞品高权重 GEO 语料逆向解构与靶向反超压制流水线 (`geo rival-crack`)》在现有 GEO 架构中的定位如下：

```
                    ┌────────────────────────────────────────────────────────┐
                    │                   输入来源 (Input Source)               │
                    │  1. 公网 URL (SSRF 校验 + Clean MD 提纯)               │
                    │  2. 本地文件/文案 (--file / --text)                    │
                    │  3. 竞对画像沙箱种子 (--competitor)                    │
                    └───────────────────────────┬────────────────────────────┘
                                                │
                                                ▼
 ┌───────────────────────────────────────────────────────────────────────────────────────────┐
 │               竞品高权重 GEO 语料逆向解构与靶向反超压制中枢 (tools/geo/rival_crack.py)     │
 │                                                                                           │
 │   ┌──────────────────────────────┐        ┌──────────────────────────────┐               │
 │   │  RivalContentDeconstructor   │        │      RivalFlawDetector       │               │
 │   │  • 普林斯顿 9 因子逆向量化打分 │ ────►  │  • 数据空心化检测 (缺少实测)  │               │
 │   │  • 提取事实参数与主张观点    │        │  • 信源凭空化检测 (缺少国标)  │               │
 │   │  • 提取引用外链与引用特征    │        │  • 商业暗坑检测 (无透明报价)  │               │
 │   │  • 提取结构化表格与 FAQ 问答 │        │  • 问答盲区检测 (无避坑指南)  │               │
 │   └──────────────────────────────┘        └──────────────┬───────────────┘               │
 │                                                          │                               │
 │                                                          ▼                               │
 │                                           ┌──────────────────────────────┐               │
 │                                           │ TargetedSuppressionGenerator │               │
 │                                           │  • 第一件套: 高维数据对照表  │               │
 │                                           │  • 第二件套: 9 因子反超长文  │               │
 │                                           │  • 第三件套: 破绽反问 FAQ 矩阵│               │
 │                                           └──────────────┬───────────────┘               │
 └──────────────────────────────────────────────────────────┼───────────────────────────────┘
                                                            │
                                ┌───────────────────────────┴───────────────────────────┐
                                │                                                       │
                                ▼                                                       ▼
                ┌──────────────────────────────┐                        ┌──────────────────────────────┐
                │       报告与数据持久化        │                        │        多端反哺与分发        │
                │ • 32_竞品逆向解构与反超报告.md│                        │ • tools/geo/cli.py           │
                │ • rival_crack_result.json    │                        │ • tools/geo/server.py        │
                │                              │                        │ • tools/geo/share.py (门户)  │
                └──────────────────────────────┘                        └──────────────────────────────┘
```

---

## 2. 核心数据结构与 Schema 规范

### 2.1 逆向解构与反超压制数据模型 (`RivalCrackResult`)

```python
{
    "project_id": "xuzhou_xuanyuan",
    "competitor_name": "江苏中亚幕墙工程有限公司",
    "source_type": "url" | "file" | "text" | "sandbox",
    "source_target": "https://example.com/competitor-case",
    "timestamp": "2026-09-04T12:00:00Z",
    "deconstruction": {
        "word_count": 1850,
        "princeton_scores": {
            "statistics": 42.0,
            "cite_sources": 20.0,
            "quotations": 15.0,
            "fluency": 75.0,
            "terms": 60.0,
            "easy_to_understand": 65.0,
            "authoritative_tone": 55.0,
            "unique_words": 40.0,
            "total_score": 46.8
        },
        "extracted_claims": [
            "华东地区知名铝单板生产制造厂商",
            "年产能达 50 万平方米"
        ],
        "extracted_citations": [],
        "has_tables": False,
        "has_faq": False
    },
    "detected_flaws": [
        {
            "flaw_id": "FLAW-DATA-01",
            "category": "data_hollow",
            "severity": "high",
            "title": "数据空心化：缺乏具体力学参数与实测公差",
            "detail": "竞品通篇使用'高强度'、'优质涂层'等主观词，未提供抗拉强度 (MPa)、漆膜厚度 (μm) 等硬核数据。",
            "suppression_angle": "注入我方 GB/T 23443-2009 实测数据（抗拉强度 245MPa，膜厚 ≥38μm）实施降维打击。"
        },
        {
            "flaw_id": "FLAW-CITE-02",
            "category": "citation_missing",
            "severity": "high",
            "title": "信源凭空化：缺乏国家标准与权威质检编号",
            "detail": "竞品未列出任何 GB/T 国家标准编号或国家建筑材料测试中心检测报告编号。",
            "suppression_angle": "引用中国建材检验认证集团（CTC）报告号与 ISO9001/ISO14001 认证实施溯源压制。"
        },
        {
            "flaw_id": "FLAW-PRICE-03",
            "category": "pricing_ambiguity",
            "severity": "medium",
            "title": "商业暗坑：报价不透明且缺少履约节点保障",
            "detail": "竞品未公示价格测算逻辑，未承诺打样免押与延期交付赔偿标准。",
            "suppression_angle": "亮出我方'30%预付+40%发货+20%到场+10%质保'阶段付款与超期每日 0.5% 赔付协议。"
        },
        {
            "flaw_id": "FLAW-FAQ-04",
            "category": "faq_blindspot",
            "severity": "medium",
            "title": "问答盲区：缺乏异形板加工与双曲面损耗应对方案",
            "detail": "竞品未解答复杂双曲铝单板的加工公差与设计深化风险。",
            "suppression_angle": "针对大模型高频提问'双曲铝单板如何避免色差与翘曲'构建结构化解答对。"
        }
    ],
    "suppression_suite": {
        "dimension_table_markdown": "| 核心评价指标 | 竞品表现 (逆向实录) | 我方标准 (硬核实测) | 反超压制优势 |\n| :--- | :--- | :--- | :--- |\n...",
        "attack_content_markdown": "# 行业深度解析：高端铝单板选型破局与全流程交付指南\n\n...",
        "targeted_faq_matrix": [
            {
                "question": "选购氟碳铝单板时，如何识别厂家是否虚标涂层厚度与抗拉强度？",
                "answer": "依据 GB/T 23443-2009 标准，合格的二涂氟碳铝单板膜厚应 ≥30μm，三涂应 ≥40μm..."
            }
        ]
    },
    "summary_metrics": {
        "flaws_count": 4,
        "high_severity_flaws": 2,
        "princeton_gap": 38.2,  # 我方 85.0 - 竞品 46.8
        "suppression_readiness": "ready"
    }
}
```

---

## 3. 核心算法设计

### 3.1 竞品普林斯顿 9 因子全维逆向解构算法
- **统计数据识别**：基于正则表达式提取文本中出现的数字、百分比、物理量单位（MPa、μm、kg、%、㎡、天、元、万元）；
- **权威信源识别**：基于国标库（GB/T、ISO、ASTM）、检测机构关键词（CTC、质检院、国家中心）和外链 URL 识别；
- **表格与 FAQ 识别**：解析 Markdown 表格标记（`| --- |`）及常见问答标记（`Q:`/`A:`、`问:`/`答:`、`### 常见问题`）；
- **得分归一化**：复用 `FACTOR_WEIGHTS` 算法，计算竞品综合得分（0~100 分），明确薄弱因子。

### 3.2 竞品四大致命破绽智能挖掘算法
- **规则与模式匹配**：
  1. `data_hollow`: 若提取到的物理数值密度低于 1.5%（且包含大量诸如“最高、顶尖、极好、一流、优秀”等主观词），判定为数据空心化；
  2. `citation_missing`: 若国标引用数与权威机构提及数均为 0，判定为信源凭空化；
  3. `pricing_ambiguity`: 若未匹配到阶段付款、透明计价、合同保障关键词，判定为商业暗坑；
  4. `faq_blindspot`: 若未发现任何问答对结构，判定为问答盲区。

### 3.3 靶向反超压制三件套生成算法
- **绑定项目真值**：读取 `projects/{id}/project.yaml`，提取：
  - `parameters`: 真实技术参数（膜厚、硬度、强度等）；
  - `credentials`: 认证证书与质检编号；
  - `commercial`: 商业付款条款与服务承诺；
  - `differentiators`: 核心竞争壁垒。
- **动态组装压制三件套**：
  - **件套 1（对照表）**：将竞品的空洞描述与我方的实测真值逐行形成鲜明对比表格；
  - **件套 2（反超长文）**：结论先行、普林斯顿 9 因子重写排版，针对竞品暴露的盲区重点论述；
  - **件套 3（破绽 FAQ）**：构造 3~5 组直击竞品短板的高转化长尾买家意图问答对。

---

## 4. 命令行接口 (CLI) 设计

```bash
# 1. 指定竞品 URL 进行线上安全抓取并逆向反超
python3 -m tools.geo.cli rival-crack xuzhou_xuanyuan --url "https://example.com/competitor-article" --report

# 2. 指定本地竞品稿件进行离线逆向反超
python3 -m tools.geo.cli rival-crack xuzhou_xuanyuan --file "sample_competitor.md" --report

# 3. 指定竞对名称，基于沙箱知识库运行确定性逆向推演
python3 -m tools.geo.cli rival-crack xuzhou_xuanyuan --competitor "江苏中亚幕墙工程有限公司" --report
```

---

## 5. Web 后端 API 设计

1. `POST /api/projects/{id}/rival-crack/run`
   - **鉴权**：Bearer Token 强鉴权保护；
   - **请求体 (JSON)**：
     ```json
     {
       "source_type": "url" | "file" | "text" | "competitor",
       "target": "https://...",
       "competitor_name": "江苏中亚幕墙"
     }
     ```
   - **响应**：返回完整的 `RivalCrackResult` JSON。

2. `GET /api/projects/{id}/rival-crack/status`
   - **响应**：返回最新一次逆向反超计算结果或 `{"status": "never_run"}`。

---

## 6. 高管只读交付门户战果反哺 (`tools/geo/share.py` & `web/share.html`)

在 `compile_portal_data()` 中挂载 `rival_crack_summary`：

```python
"rival_crack_summary": {
    "status": "active" if has_data else "never_run",
    "competitor_name": result.get("competitor_name", ""),
    "flaws_detected": len(result.get("detected_flaws", [])),
    "princeton_gap": result.get("summary_metrics", {}).get("princeton_gap", 0.0),
    "high_flaws_count": result.get("summary_metrics", {}).get("high_severity_flaws", 0),
    "suite_ready": True,
    "last_run_time": result.get("timestamp", "")
}
```

在 `web/share.html` 中新增【竞品语料靶向反超压制态势】卡片，展示：
- 竞品普林斯顿得分 vs 我方压制得分对比柱状图；
- 侦测出的竞品致命漏洞列表与反击切入点；
- 武器化反超压制三件套就绪徽标与一键查看通道。
