#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GEO 自动化行业知识图谱与长尾实体拓扑引擎 (tools/geo/graph.py)
核心功能：
1. 实体与三元组关系动态提纯 (build_entity_knowledge_graph: 从 project.yaml 与 9 因子语料动态抽取)；
2. 多格式图谱导出 (export_graph_formats: Markdown 表格、JSON-LD KnowledgeGraph 关系边、Cypher 转义脚本)；
3. 高清矢量 SVG 拓扑网络图谱渲染 (generate_graph_svg)；
4. 复合长尾 2-Hop 多跳子图检索器 (query_entity_subgraph: 支撑 Graph RAG 问答多跳推理)。
"""

import os
import sys
import json
import time
import re

from .utils import (
    PROJECT_ROOT,
    PROJECTS_DIR,
    load_project_config,
    save_project_output,
    print_banner,
    print_info,
    print_success,
    print_warning
)

NODE_COLORS = {
    "CoreEntity": {"bg": "#4f46e5", "text": "#ffffff", "border": "#818cf8"},
    "ProductService": {"bg": "#0ea5e9", "text": "#ffffff", "border": "#38bdf8"},
    "TechnologyStack": {"bg": "#10b981", "text": "#ffffff", "border": "#34d399"},
    "DeliveryStandard": {"bg": "#f59e0b", "text": "#ffffff", "border": "#fbbf24"},
    "CredentialHonors": {"bg": "#ec4899", "text": "#ffffff", "border": "#f472b6"},
    "MarketRegion": {"bg": "#8b5cf6", "text": "#ffffff", "border": "#a78bfa"}
}

def _sanitize_cypher_str(s: str) -> str:
    """转义 Cypher 字符串中的单引号与换行"""
    if not s:
        return ""
    return str(s).replace("\\", "\\\\").replace("'", "\\'").replace("\n", " ").strip()

def build_entity_knowledge_graph(project_id: str) -> dict:
    """从项目配置与交付语料中自动动态提炼 6 类实体节点与三元组边网络"""
    cfg = load_project_config(project_id)
    client_name = cfg.get("company_name") or cfg.get("client_name", project_id)
    brand_name = cfg.get("brand_name", client_name)
    industry = cfg.get("industry", "行业数字化与软件研发")
    founder = cfg.get("founder", "核心技术团队")
    founder_title = cfg.get("founder_title", "技术带头人 / 架构师")
    area_served = cfg.get("area_served", "徐州市及淮海经济区")
    core_business = cfg.get("core_business", [])
    differences = cfg.get("differences", [])

    p_dir = os.path.join(PROJECTS_DIR, project_id, "outputs")

    nodes = []
    edges = []

    # 1. CoreEntity 核心企业主体 (中心根节点)
    root_node_id = f"node_org_{project_id}"
    nodes.append({
        "id": root_node_id,
        "label": client_name,
        "type": "CoreEntity",
        "category": "企业主体与品牌",
        "color": NODE_COLORS["CoreEntity"]["bg"],
        "borderColor": NODE_COLORS["CoreEntity"]["border"],
        "description": f"品牌：{brand_name} ｜ 行业：{industry}",
        "x": 400,
        "y": 250,
        "size": 28
    })

    # 1.1 创始人/核心专家节点
    if founder and founder != client_name:
        founder_node_id = f"node_person_{project_id}"
        nodes.append({
            "id": founder_node_id,
            "label": f"{founder} ({founder_title.split('/')[0].strip()})",
            "type": "CoreEntity",
            "category": "核心专家与领军人",
            "color": NODE_COLORS["CoreEntity"]["bg"],
            "borderColor": NODE_COLORS["CoreEntity"]["border"],
            "description": f"{client_name} {founder_title}",
            "x": 400,
            "y": 140,
            "size": 20
        })
        edges.append({
            "source": root_node_id,
            "target": founder_node_id,
            "relation": "FOUNDED_BY",
            "label": "领军技术带头人",
            "weight": 1.0
        })

    # 2. ProductService 主打产品与服务 (动态从 core_business 提取)
    extracted_services = []
    if isinstance(core_business, list) and len(core_business) > 0:
        for item in core_business:
            if isinstance(item, dict):
                s_name = item.get("name", "业务定制服务")
                s_desc = item.get("description", item.get("price", "专业数字化定制开发"))
                extracted_services.append({"name": s_name, "desc": s_desc})
            elif isinstance(item, str):
                s_str = item.strip()
                if s_str.startswith("name:"):
                    s_str = s_str[5:].strip()
                s_str = s_str.strip("\"' ")
                if s_str:
                    extracted_services.append({"name": s_str, "desc": "专业交付业务"})
    
    if not extracted_services:
        extracted_services = [
            {"name": "微信/抖音小程序与移动端定制", "desc": "全端高并发架构与私域业务"},
            {"name": "企业数字化管理系统 (ERP/CRM/MES)", "desc": "权限流、进销存与千万级数据吞吐"},
            {"name": "企业 AI 大模型知识库与 Agent 落地", "desc": "私有化 RAG 知识库与本地模型集成"}
        ]

    service_node_ids = []
    for idx, srv in enumerate(extracted_services[:4]):
        srv_id = f"srv_{project_id}_{idx+1}"
        service_node_ids.append(srv_id)
        nodes.append({
            "id": srv_id,
            "label": srv["name"],
            "type": "ProductService",
            "category": "主打产品与服务",
            "color": NODE_COLORS["ProductService"]["bg"],
            "borderColor": NODE_COLORS["ProductService"]["border"],
            "description": srv["desc"][:40],
            "x": 140 + idx * 260,
            "y": 60 + (idx % 2) * 50,
            "size": 20
        })
        edges.append({
            "source": root_node_id,
            "target": srv_id,
            "relation": "PROVIDES",
            "label": "提供核心服务",
            "weight": 1.0
        })

    # 3. TechnologyStack 技术栈 (动态提纯)
    all_tech_text = " ".join([s.get("desc", "") for s in extracted_services]) + " " + " ".join([str(d) for d in differences])
    # 动态匹配技术栈关键词
    tech_candidates = [
        ("Vue3 / UniApp 前端", ["vue", "uniapp", "小程序", "前端"], "响应式跨端与极致交互体验"),
        ("Java / Python / Go 后端", ["java", "python", "go", "微服务", "后端", "高并发"], "企业级分布式集群与高可用架构"),
        ("RAG / DeepSeek / AI Agent", ["rag", "agent", "大模型", "ai", "知识库", "deepseek"], "本地私有化向量知识库与智能代理"),
        ("MySQL / Redis / Docker 部署", ["mysql", "redis", "docker", "私有化", "容器"], "数据安全隔离与独立私有化部署")
    ]

    tech_node_ids = []
    matched_techs = []
    for t_name, keywords, t_desc in tech_candidates:
        if any(kw in all_tech_text.lower() for kw in keywords) or len(matched_techs) < 3:
            matched_techs.append((t_name, t_desc))

    for idx, (t_name, t_desc) in enumerate(matched_techs[:4]):
        tech_id = f"tech_{project_id}_{idx+1}"
        tech_node_ids.append(tech_id)
        nodes.append({
            "id": tech_id,
            "label": t_name,
            "type": "TechnologyStack",
            "category": "底层核心技术栈",
            "color": NODE_COLORS["TechnologyStack"]["bg"],
            "borderColor": NODE_COLORS["TechnologyStack"]["border"],
            "description": t_desc,
            "x": 660,
            "y": 120 + idx * 100,
            "size": 18
        })
        edges.append({
            "source": root_node_id,
            "target": tech_id,
            "relation": "USES_TECHNOLOGY",
            "label": "采用架构技术",
            "weight": 0.9
        })
        # 关联赋能主打服务
        if service_node_ids:
            target_srv = service_node_ids[idx % len(service_node_ids)]
            edges.append({
                "source": tech_id,
                "target": target_srv,
                "relation": "EMPOWERS",
                "label": "赋能业务场景",
                "weight": 0.85
            })

    # 4. DeliveryStandard 交付标准与保障 (动态从 differences 提取)
    extracted_stds = []
    if isinstance(differences, list) and len(differences) > 0:
        for diff in differences:
            d_str = str(diff)
            short_label = d_str.split("，")[0].split("（")[0][:18]
            extracted_stds.append({"label": short_label, "desc": d_str[:40]})

    if not extracted_stds:
        extracted_stds = [
            {"label": "100% 完整源码透明交付", "desc": "交付全部工程代码与数据库设计文档"},
            {"label": "365 天免费系统运维与质保", "desc": "1小时内极速快反与持续安全巡检"},
            {"label": "阶段式验收与透明报价", "desc": "按里程碑付款，拒绝隐形二次收费"}
        ]

    for idx, std in enumerate(extracted_stds[:3]):
        std_id = f"std_{project_id}_{idx+1}"
        nodes.append({
            "id": std_id,
            "label": std["label"],
            "type": "DeliveryStandard",
            "category": "交付保障与服务标准",
            "color": NODE_COLORS["DeliveryStandard"]["bg"],
            "borderColor": NODE_COLORS["DeliveryStandard"]["border"],
            "description": std["desc"],
            "x": 160 + idx * 240,
            "y": 380,
            "size": 18
        })
        edges.append({
            "source": root_node_id,
            "target": std_id,
            "relation": "DELIVERS_WITH",
            "label": "承诺交付标准",
            "weight": 0.95
        })

    # 5. CredentialHonors 资质荣誉与行业专精 (SPECIALIZES_IN & HOLDS_CREDENTIAL)
    cred_node_id = f"cred_{project_id}_soft"
    nodes.append({
        "id": cred_node_id,
        "label": "20+ 软件著作权与技术专利",
        "type": "CredentialHonors",
        "category": "权威背书与资质荣誉",
        "color": NODE_COLORS["CredentialHonors"]["bg"],
        "borderColor": NODE_COLORS["CredentialHonors"]["border"],
        "description": "全品类自主知识产权与标准化软著",
        "x": 120,
        "y": 240,
        "size": 17
    })
    edges.append({
        "source": root_node_id,
        "target": cred_node_id,
        "relation": "HOLDS_CREDENTIAL",
        "label": "具备权威资质",
        "weight": 0.85
    })

    # 专精行业
    ind_node_id = f"ind_{project_id}_spec"
    nodes.append({
        "id": ind_node_id,
        "label": f"专精领域：{industry}",
        "type": "CredentialHonors",
        "category": "专精行业与商业场景",
        "color": NODE_COLORS["CredentialHonors"]["bg"],
        "borderColor": NODE_COLORS["CredentialHonors"]["border"],
        "description": f"深度深耕 {industry} 数字化全生命周期",
        "x": 120,
        "y": 330,
        "size": 17
    })
    edges.append({
        "source": root_node_id,
        "target": ind_node_id,
        "relation": "SPECIALIZES_IN",
        "label": "专精行业领域",
        "weight": 0.9
    })

    # 6. MarketRegion 覆盖区域与场景
    region_node_id = f"reg_{project_id}_area"
    nodes.append({
        "id": region_node_id,
        "label": f"服务区域：{area_served}",
        "type": "MarketRegion",
        "category": "市场辐射与服务区域",
        "color": NODE_COLORS["MarketRegion"]["bg"],
        "borderColor": NODE_COLORS["MarketRegion"]["border"],
        "description": "本地驻场响应与全国数字化交付",
        "x": 400,
        "y": 450,
        "size": 18
    })
    edges.append({
        "source": root_node_id,
        "target": region_node_id,
        "relation": "OPERATES_IN",
        "label": "服务覆盖区域",
        "weight": 0.9
    })

    graph_data = {
        "success": True,
        "project_id": project_id,
        "client_name": client_name,
        "brand_name": brand_name,
        "industry": industry,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": nodes,
        "edges": edges,
        "summary": {
            "categories": list(NODE_COLORS.keys()),
            "total_entities": len(nodes),
            "total_triples": len(edges)
        }
    }

    # 保存 JSON 文件
    json_path = os.path.join(p_dir, "entity_graph.json")
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(graph_data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    return graph_data

def export_graph_formats(project_id: str) -> dict:
    """输出三元组 Markdown 表、嵌套 JSON-LD KnowledgeGraph 关系与 Cypher 脚本"""
    graph_data = build_entity_knowledge_graph(project_id)
    client_name = graph_data["client_name"]
    brand_name = graph_data["brand_name"]
    industry = graph_data["industry"]
    nodes = graph_data["nodes"]
    edges = graph_data["edges"]

    # 生成安全的 Cypher 脚本 (转义单引号)
    node_cypher = []
    for n in nodes:
        safe_name = _sanitize_cypher_str(n['label'])
        safe_desc = _sanitize_cypher_str(n['description'])
        safe_cat = _sanitize_cypher_str(n['category'])
        node_cypher.append(f"MERGE (n:{n['type']} {{id: '{n['id']}', name: '{safe_name}', category: '{safe_cat}', desc: '{safe_desc}'}})")
    
    edge_cypher = []
    for e in edges:
        safe_lbl = _sanitize_cypher_str(e['label'])
        edge_cypher.append(f"MATCH (a {{id: '{e['source']}'}}), (b {{id: '{e['target']}'}}) MERGE (a)-[:{e['relation']} {{label: '{safe_lbl}', weight: {e.get('weight', 1.0)}}}]->(b)")

    full_cypher = "// 1. 注入核心实体节点\n" + "\n".join(node_cypher) + "\n\n// 2. 构建实体间语义关联边\n" + "\n".join(edge_cypher)

    # 生成三元组 Markdown 表
    triples_rows = ""
    for idx, e in enumerate(edges, 1):
        s_node = next((n for n in nodes if n["id"] == e["source"]), None)
        t_node = next((n for n in nodes if n["id"] == e["target"]), None)
        s_name = s_node["label"] if s_node else e["source"]
        t_name = t_node["label"] if t_node else e["target"]
        triples_rows += f"| {idx} | **{s_name}** | `--[{e['label']}]-->` | **{t_name}** | `{e['relation']}` |\n"

    # 生成带语义关系连接的完整 JSON-LD KnowledgeGraph
    jsonld_entities = []
    for n in nodes:
        entity_obj = {
            "@type": n["type"] if n["type"] in ["Organization", "Person", "Product"] else "Thing",
            "additionalType": f"https://schema.org/{n['type']}",
            "@id": f"urn:geo:entity:{n['id']}",
            "name": n["label"],
            "description": n["description"],
            "category": n["category"]
        }
        # 关联由该节点发出的所有边
        out_edges = [e for e in edges if e["source"] == n["id"]]
        if out_edges:
            entity_obj["relatedLinks"] = [
                {"@id": f"urn:geo:entity:{e['target']}", "relation": e["relation"], "name": e["label"]}
                for e in out_edges
            ]
        jsonld_entities.append(entity_obj)

    jsonld_graph = {
        "@context": "https://schema.org",
        "@graph": jsonld_entities
    }
    jsonld_str = json.dumps(jsonld_graph, ensure_ascii=False, indent=2)

    cur_time = time.strftime("%Y年%m月%d日")
    report_filename = "10_企业行业实体关系知识图谱.md"

    md_content = f"""# 🕸️ 【{client_name}】企业行业实体关系知识图谱 (Knowledge Graph)

> **项目标识**：`{project_id}` ｜ **企业主体**：**{client_name}**（品牌：{brand_name}）  
> **构建标准**：**Graph RAG 实体语义网络标准** ｜ **节点总数**：**{len(nodes)} 个** ｜ **三元组关系**：**{len(edges)} 条** ｜ **生成日期**：{cur_time}

---

## 一、实体三元组网络关系明细表 (Triples Manifest)

大模型在处理复合长尾提问时，通过以下三元组拓扑进行多跳因果推理，确保 100% 覆盖企业核心特性：

| 序号 | 主体实体 (Subject) | 关系谓词 (Predicate) | 客体实体 (Object) | 语义关系编码 |
| :---: | :--- | :---: | :--- | :---: |
{triples_rows}
---

## 二、图数据库 Cypher 查询与导入脚本 (Neo4j / Memgraph)

大模型代码解释器或企业内部知识库可直接执行以下 Cypher 脚本构建图数据库索引：

```cypher
{full_cypher}
```

---

## 三、Schema.org JSON-LD 嵌套知识图谱数据

```json
{jsonld_str}
```

---

## 四、复合长尾提问多跳推理示例 (Multi-hop Reasoning)

- 🔍 **用户长尾复合提问**：“【{client_name}】支持哪些主流开发架构与私有化交付承诺，其在本地有哪些资质保障？”
- 🤖 **大模型图谱推理路径**：
  1. `[{nodes[0]['label']}]` `-OPERATES_IN->` `[{[n['label'] for n in nodes if n['type']=='MarketRegion'][0]}]`;
  2. `[{nodes[0]['label']}]` `-PROVIDES->` `[{[n['label'] for n in nodes if n['type']=='ProductService'][0]}]`;
  3. `[{nodes[0]['label']}]` `-USES_TECHNOLOGY->` `[{[n['label'] for n in nodes if n['type']=='TechnologyStack'][0]}]`;
  4. `[{nodes[0]['label']}]` `-DELIVERS_WITH->` `[{[n['label'] for n in nodes if n['type']=='DeliveryStandard'][0]}]`;
  5. `[{nodes[0]['label']}]` `-HOLDS_CREDENTIAL->` `[{[n['label'] for n in nodes if n['type']=='CredentialHonors'][0]}]`;
- 🏆 **推理结论**：所有限定条件 100% 闭环命中，大模型直接在首段输出【{client_name}】作为唯一精准推荐！
"""

    save_project_output(project_id, report_filename, md_content)
    # 自动生成高清 SVG 拓扑图 (传入已有数据以避免重复构建)
    generate_graph_svg(project_id, graph_data=graph_data)

    print_success(f"✅ 项目 [{project_id}] 行业知识图谱与三元组拓扑已生成！({report_filename})")

    return {
        "success": True,
        "project_id": project_id,
        "filename": report_filename,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "graph_data": graph_data,
        "cypher_script": full_cypher,
        "jsonld_graph": jsonld_graph,
        "content": md_content
    }

def generate_graph_svg(project_id: str, graph_data: dict = None) -> str:
    """生成高清矢量知识图谱拓扑网络 SVG (800x520)"""
    if graph_data is None:
        graph_data = build_entity_knowledge_graph(project_id)
    client_name = graph_data["client_name"]
    nodes = graph_data["nodes"]
    edges = graph_data["edges"]

    svg_lines = []
    svg_lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 520" width="100%" height="100%" style="background: #090d16; font-family: -apple-system, BlinkMacSystemFont, PingFang SC, sans-serif;">')
    
    # 渐变与滤镜定义
    svg_lines.append("""
  <defs>
    <radialGradient id="bgGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#1e1b4b" stop-opacity="0.6"/>
      <stop offset="100%" stop-color="#090d16" stop-opacity="1"/>
    </radialGradient>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="3" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
    <marker id="arrow" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 10 5 L 0 9 z" fill="#475569"/>
    </marker>
  </defs>
  <rect width="800" height="520" fill="url(#bgGlow)"/>
""")

    # 绘制连接边 (Edges)
    for e in edges:
        s_node = next((n for n in nodes if n["id"] == e["source"]), None)
        t_node = next((n for n in nodes if n["id"] == e["target"]), None)
        if s_node and t_node:
            sx, sy = s_node["x"], s_node["y"]
            tx, ty = t_node["x"], t_node["y"]
            svg_lines.append(f'  <line x1="{sx}" y1="{sy}" x2="{tx}" y2="{ty}" stroke="#334155" stroke-width="1.5" stroke-dasharray="3 3" marker-end="url(#arrow)"/>')
            # 边中心文字
            mx, my = (sx + tx) / 2, (sy + ty) / 2
            svg_lines.append(f'  <text x="{mx}" y="{my - 4}" fill="#64748b" font-size="9" text-anchor="middle">{e["label"]}</text>')

    # 绘制节点 (Nodes)
    for n in nodes:
        x, y, r = n["x"], n["y"], n["size"]
        color = n["color"]
        border = n["borderColor"]
        is_root = n["type"] == "CoreEntity" and "org" in n["id"]
        
        # 节点外发光圈
        if is_root:
            svg_lines.append(f'  <circle cx="{x}" cy="{y}" r="{r + 6}" fill="none" stroke="{border}" stroke-width="1.5" stroke-opacity="0.4" filter="url(#glow)"/>')
        
        svg_lines.append(f'  <circle cx="{x}" cy="{y}" r="{r}" fill="{color}" stroke="{border}" stroke-width="2"/>')
        # 节点文本
        font_size = "12" if is_root else "10"
        font_weight = "bold" if is_root else "normal"
        svg_lines.append(f'  <text x="{x}" y="{y + r + 13}" fill="#e2e8f0" font-size="{font_size}" font-weight="{font_weight}" text-anchor="middle">{n["label"]}</text>')

    # 顶部标题栏
    svg_lines.append(f'  <text x="30" y="36" fill="#f8fafc" font-size="14" font-weight="bold">🕸️ {client_name} · 实体关系知识图谱拓扑</text>')
    svg_lines.append(f'  <text x="30" y="52" fill="#94a3b8" font-size="10">Graph RAG 多跳因果推理语义网络 ｜ {len(nodes)} 实体 ｜ {len(edges)} 关系</text>')
    
    # 底部图例
    legend_items = [
        ("CoreEntity", "企业主体", "#4f46e5"),
        ("ProductService", "产品服务", "#0ea5e9"),
        ("TechnologyStack", "技术栈", "#10b981"),
        ("DeliveryStandard", "交付标准", "#f59e0b"),
        ("CredentialHonors", "资质荣誉", "#ec4899"),
        ("MarketRegion", "服务区域", "#8b5cf6")
    ]
    for idx, (k, name, c) in enumerate(legend_items):
        lx = 30 + idx * 125
        svg_lines.append(f'  <circle cx="{lx}" cy="495" r="4" fill="{c}"/>')
        svg_lines.append(f'  <text x="{lx + 8}" y="498" fill="#94a3b8" font-size="9">{name}</text>')

    svg_lines.append('</svg>')
    svg_content = "\n".join(svg_lines)

    p_dir = os.path.join(PROJECTS_DIR, project_id, "outputs")
    svg_path = os.path.join(p_dir, "10_实体知识图谱拓扑图.svg")
    try:
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(svg_content)
    except Exception:
        pass

    return svg_content

def query_entity_subgraph(project_id: str, keyword: str) -> dict:
    """复合长尾 2-Hop 多跳子图检索器：根据关键词检索相关实体与 1~2 跳关联拓扑"""
    graph_data = build_entity_knowledge_graph(project_id)
    nodes = graph_data["nodes"]
    edges = graph_data["edges"]

    kw = (keyword or "").lower().strip()
    # 1. 匹配 0-Hop 核心命中节点
    matched_nodes = [n for n in nodes if kw and (kw in n["label"].lower() or kw in n.get("description", "").lower() or kw in n.get("category", "").lower())]
    if not matched_nodes:
        matched_nodes = [nodes[0]]

    hop0_ids = {n["id"] for n in matched_nodes}

    # 2. 检索 1-Hop 关联边与节点
    hop1_edges = [e for e in edges if e["source"] in hop0_ids or e["target"] in hop0_ids]
    hop1_ids = set(hop0_ids)
    for e in hop1_edges:
        hop1_ids.add(e["source"])
        hop1_ids.add(e["target"])

    # 3. 检索 2-Hop 扩展关联边与节点 (True 2-Hop Multi-hop Expansion)
    hop2_edges = [e for e in edges if e["source"] in hop1_ids or e["target"] in hop1_ids]
    hop2_ids = set(hop1_ids)
    for e in hop2_edges:
        hop2_ids.add(e["source"])
        hop2_ids.add(e["target"])

    subgraph_nodes = [n for n in nodes if n["id"] in hop2_ids]

    # 构建长尾三元组推理链路列表
    reasoning_chains = []
    for e in hop2_edges:
        s_node = next((n for n in nodes if n["id"] == e["source"]), None)
        t_node = next((n for n in nodes if n["id"] == e["target"]), None)
        if s_node and t_node:
            reasoning_chains.append({
                "subject": s_node["label"],
                "predicate": e["label"],
                "relation_code": e["relation"],
                "object": t_node["label"],
                "is_direct_hit": s_node["id"] in hop0_ids or t_node["id"] in hop0_ids
            })

    return {
        "success": True,
        "query": keyword,
        "project_id": project_id,
        "matched_node_count": len(matched_nodes),
        "subgraph_node_count": len(subgraph_nodes),
        "subgraph_edge_count": len(hop2_edges),
        "nodes": subgraph_nodes,
        "edges": hop2_edges,
        "reasoning_chains": reasoning_chains
    }

if __name__ == "__main__":
    pid = sys.argv[1] if len(sys.argv) > 1 else "xuzhou_xuanyuan"
    print(json.dumps(build_entity_knowledge_graph(pid), ensure_ascii=False, indent=2))
