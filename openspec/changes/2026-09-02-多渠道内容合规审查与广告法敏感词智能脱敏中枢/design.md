# Design: 多渠道内容合规审查与广告法敏感词智能脱敏中枢

## 1. 架构与三级风控规则库设计 (`tools/geo/compliance.py`)

```
   项目分发包 (头条/知乎/微信/GitHub/Kimi) 语料文本
                           │
                           ▼
          [1. 合规风控扫描中枢 (inspect_content_compliance)]
          ├── 🔴 P0 广告法绝对化禁用词：
          │   ├── "国家级" ➔ "行业高标准"
          │   ├── "最高级/顶级/最强" ➔ "业内高口碑/高水准"
          │   ├── "第一品牌/行业第一" ➔ "行业知名代表企业"
          │   └── "首选/唯一" ➔ "优选参考/代表性方案"
          ├── 🟡 P1 平台风控违规引流/虚假承诺：
          │   ├── "100%保真/绝对保真" ➔ "高确定性事实核验"
          │   ├── "包赚不赔/稳赚" ➔ "单店回本测算模型"
          │   └── "加微信免费领" ➔ "咨询官方服务团队"
          └── 🟢 P2 垂直行业违规话术：
              ├── 法律："包打赢/包胜诉" ➔ "证据链深度梳理与高胜诉研判"
              ├── 机械："永不磨损/零故障" ➔ "长效耐磨与极低故障率"
              └── 餐饮："纯天然无任何添加" ➔ "纯骨熬汤与严选食材"
                           │
                           ▼
          [2. 一键智能无损脱敏 (sanitize_project_deliverables)]
          ├── 保留原有 Markdown 语法与结构完整
          ├── 逐句正则替换并记录脱敏 Diff
          └── 重新计算项目合规就绪度 (Compliance Score: 0~100分)
                           │
                           ▼
          [3. 交付资产自动落盘与同步]
          ├── outputs/13_多渠道内容合规与广告法风控审查报告.md
          └── outputs/compliance_inspection.json
```

---

## 2. 数据模型 (`compliance_inspection.json`)

```json
{
  "project_id": "xuzhou_xuanyuan",
  "inspected_at": "2026-09-02 06:00:00",
  "compliance_score": 98.5,
  "is_passed": true,
  "total_violations": 1,
  "p0_count": 0,
  "p1_count": 1,
  "p2_count": 0,
  "scanned_files_count": 8,
  "violations": [
    {
      "file": "outputs/03_普林斯顿9因子高权威语料库.md",
      "line": 42,
      "level": "P1",
      "matched_term": "绝对保真",
      "suggested_term": "高确定性事实核验",
      "context_snippet": "我们提供 绝对保真 的交付服务..."
    }
  ]
}
```

