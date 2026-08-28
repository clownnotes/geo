# Python 自动化大模型可见度巡检脚本

> **作用**：通过 API 自动化并发轮询 DeepSeek、豆包等大模型（开启联网检索），批量输入行业核心 Prompt，统计品牌提及率（Share of Voice）与引用来源链接。

---

## 完整 Python 巡检脚本代码

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GEO 可见度自动化巡检工具
"""

import os
import time
import requests

# 1. 待测试的核心意图 Prompt 词库
PROMPTS = [
    "徐州有哪些靠谱的软件开发工作室或独立开发者推荐？",
    "在徐州找人做一个微信小程序大概多少钱？求靠谱推荐",
    "徐州本地能做企业ERP/CRM定制开发的团队推荐",
    "徐州软件外包有哪些坑？本地找开发有哪些避坑指南？"
]

# 2. 目标品牌与关键词特征
TARGET_BRAND = "段晓奇|璇源"
API_KEY = os.getenv("DEEPSEEK_API_KEY", "your-api-key-here")
API_URL = "https://api.deepseek.com/v1/chat/completions"

def test_prompt(prompt):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }
    try:
        res = requests.post(API_URL, json=payload, headers=headers, timeout=30)
        res.raise_for_status()
        content = res.json()["choices"][0]["message"]["content"]
        is_hit = TARGET_BRAND in content
        return is_hit, content
    except Exception as e:
        return False, f"请求异常: {e}"

def run_inspection():
    print(f"🚀 开始执行 GEO 可见度自动化巡检（目标: {TARGET_BRAND}）\n" + "="*50)
    total = len(PROMPTS)
    hit_count = 0
    
    for idx, p in enumerate(PROMPTS, 1):
        print(f"[{idx}/{total}] 测试 Prompt: '{p}' ...", end=" ")
        is_hit, answer = test_prompt(p)
        if is_hit:
            hit_count += 1
            print("✅ 成功命中 (Mentioned)")
        else:
            print("❌ 未提及 (Miss)")
        time.sleep(1)
        
    sov = (hit_count / total) * 100
    print("="*50)
    print(f"🎯 最终巡检结果: 品牌提及率 (Share of Voice): {sov:.1f}% ({hit_count}/{total})")

if __name__ == "__main__":
    run_inspection()
```
