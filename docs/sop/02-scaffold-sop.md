# SOP-02 站点底座技术改造交付

> **阶段目标**：让客户官网在 30 分钟内具备"AI 可读、AI 可信、AI 可引用"的底座。  
> **执行人**：交付工程师 + 客户站务 ｜ **周期**：签约后第 1 周 ｜ **对应程序**：`geo scaffold`

---

## 一、一键生成底座补丁

```bash
python3 -m tools.geo scaffold --project <client_id>
```

产物（`projects/<client_id>/outputs/scaffold/`）：

| 文件 | 挂载位置 | 作用 |
| :--- | :--- | :--- |
| `llms.txt` | 网站根目录 | AI 爬虫毫秒级站点索引（Answer.AI 规范） |
| `llms-full.txt` | 网站根目录 | 完整版索引，rewrite 语料产出后回填 |
| `robots.txt` | 网站根目录 | 放行 Bytespider（豆包）/ Baiduspider / Sogouspider / Yisouspider / DeepSeekBot 等本土 AI 爬虫 |
| `json-ld.html` | 全站 `<head>` | WebSite + Organization（含 founder/telephone/areaServed）+ FAQPage 三块实体声明 |
| `README-挂载说明.md` | 交付给客户技术 | 三步挂载指引 |

## 二、技术交接 checklist（发给客户技术的工单）

- [ ] 三个静态文件放入站点根目录（Nginx `root` 或静态托管 `public/`），`curl https://域名/llms.txt` 返回 200 且非空；
- [ ] `json-ld.html` 内容粘贴进全站 `<head>`（SSR/SSG 项目改模板一次生效；纯 CSR 项目必须先解决服务端渲染，否则一切白做）；
- [ ] 若客户站为纯 Vue/React CSR：本阶段升级为"改造立项"，输出预渲染方案与工期评估，**不可**直接跳到 SOP-03。

## 三、复检与验收（硬标准）

```bash
python3 -m tools.geo audit --project <client_id>   # 复检
```

| 验收项 | 标准 |
| :--- | :--- |
| 底座体检得分 | **4/4 全部通过** |
| FAQPage 结构化问答 | 与客户确认过的口径逐字一致 |
| 实体署名 | 公司名/人名/电话与 project.yaml 完全一致（多信源一致 = AI 可信） |

## 四、企业行业实体知识图谱与 Graph RAG 拓扑构建

```bash
# 生成三元组知识图谱与高清矢量拓扑图
python3 -m tools.geo graph <client_id>

# 导出特定格式 (cypher / jsonld / svg)
python3 -m tools.geo graph <client_id> --export svg
```

| 交付产物 | 格式 | 商业与大模型价值 |
| :--- | :--- | :--- |
| `10_企业行业实体关系知识图谱.md` | Markdown | 三元组拓扑清单与 Graph RAG 多跳推理示例 |
| `entity_graph.json` | JSON | 6 类实体节点与 6 种谓词关联边数据 |
| `10_实体知识图谱拓扑图.svg` | SVG | 800×520 高清矢量拓扑网络图，支持嵌入官网技术架构页 |

> ⚠️ **合规红线**：JSON-LD 与 FAQ 中不得写入无法验证的绝对化承诺（"第一""最强"等广告法禁用语），entity.person 头衔需客户书面授权。

> 上一步 [SOP-01 诊断](/sop/01-audit-sop) ｜ 下一步 ➔ [SOP-03 内容重构](/sop/03-rewrite-sop)
