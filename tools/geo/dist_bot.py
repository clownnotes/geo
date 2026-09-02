#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GEO 自动化分发台账回填与收录核验中枢 (tools/geo/dist_bot.py)
核心功能：
1. 管理 5 大信任池渠道（今日头条/知乎/掘金/GitHub/微信公众号）外发台账 (outputs/dist_ledger.json)；
2. 记录与更新外发 URL，并自动化发起轻量 HTTP 存活与收录连通性探测；
3. 计算项目全渠道分发完成率 (0~100%) 与收录状态；
4. 生成适配公众号/知乎带样式的富文本 HTML 剪贴板内容。
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor

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

DEFAULT_CHANNELS = {
    "toutiao": {
        "name": "今日头条",
        "target_pool": "豆包 / 字节系信任池",
        "article_file": "dist_toutiao_article.md",
        "url": "",
        "status": "pending",
        "http_status": None,
        "verified_at": None
    },
    "zhihu": {
        "name": "知乎专栏",
        "target_pool": "DeepSeek / 通用检索池",
        "article_file": "dist_zhihu_article.md",
        "url": "",
        "status": "pending",
        "http_status": None,
        "verified_at": None
    },
    "juejin": {
        "name": "稀土掘金",
        "target_pool": "豆包 / 技术检索池",
        "article_file": "03_普林斯顿9因子高权威语料库.md",
        "url": "",
        "status": "pending",
        "http_status": None,
        "verified_at": None
    },
    "github": {
        "name": "GitHub Wiki/README",
        "target_pool": "DeepSeek / 开源信任池",
        "article_file": "dist_github_README.md",
        "url": "",
        "status": "pending",
        "http_status": None,
        "verified_at": None
    },
    "wechat": {
        "name": "微信公众号",
        "target_pool": "微信 / 全网信任池",
        "article_file": "dist_wechat_article.html",
        "url": "",
        "status": "pending",
        "http_status": None,
        "verified_at": None
    }
}

def _get_ledger_path(project_id: str) -> str:
    return os.path.join(PROJECTS_DIR, project_id, "outputs", "dist_ledger.json")

def get_distribution_ledger(project_id: str) -> dict:
    """读取指定项目的分发台账"""
    lpath = _get_ledger_path(project_id)
    channels = json.loads(json.dumps(DEFAULT_CHANNELS))
    updated_at = None

    if os.path.exists(lpath):
        try:
            with open(lpath, "r", encoding="utf-8") as f:
                saved = json.load(f)
                updated_at = saved.get("updated_at")
                for k, v in saved.get("channels", {}).items():
                    if k in channels:
                        channels[k].update(v)
        except Exception:
            pass

    # 计算完成率
    total = len(channels)
    published = sum(1 for c in channels.values() if c.get("url") and c.get("status") in ("verified", "published"))
    rate = round((published / max(total, 1)) * 100, 1)

    return {
        "success": True,
        "project_id": project_id,
        "updated_at": updated_at or time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_channels": total,
        "published_channels": published,
        "completion_rate_pct": rate,
        "channels": channels
    }

def verify_distribution_url(url: str) -> dict:
    """轻量探测外发 URL 是否可访问"""
    if not url or not url.startswith("http"):
        return {"is_alive": False, "http_status": None, "error": "无效的 URL"}

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 GEOBot/2.0"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=4) as response:
            code = response.getcode()
            return {"is_alive": code in (200, 301, 302, 307, 308), "http_status": code, "error": None}
    except urllib.error.HTTPError as e:
        # 部分平台返回 403 但实际内容存在
        return {"is_alive": e.code in (200, 403, 302), "http_status": e.code, "error": f"HTTP {e.code}"}
    except Exception as e:
        return {"is_alive": False, "http_status": 0, "error": str(e)}

def record_distributed_url(project_id: str, channel: str, url: str, verify_now: bool = True) -> dict:
    """记录并回填指定渠道的发布链接"""
    url_clean = (url or "").strip()
    ledger = get_distribution_ledger(project_id)
    channels = ledger["channels"]

    if channel not in channels:
        return {"success": False, "message": f"不支持的渠道: {channel}"}

    ch_data = channels[channel]
    ch_data["url"] = url_clean
    ch_data["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")

    if not url_clean:
        ch_data["status"] = "pending"
        ch_data["http_status"] = None
        ch_data["verified_at"] = None
    else:
        if verify_now:
            v_res = verify_distribution_url(url_clean)
            ch_data["http_status"] = v_res["http_status"]
            ch_data["verified_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            ch_data["status"] = "verified" if v_res["is_alive"] else "failed"
        else:
            ch_data["status"] = "published"

    # 保存文件
    lpath = _get_ledger_path(project_id)
    os.makedirs(os.path.dirname(lpath), exist_ok=True)
    
    total = len(channels)
    published = sum(1 for c in channels.values() if c.get("url") and c.get("status") in ("verified", "published"))
    completion_rate = round((published / max(total, 1)) * 100, 1)

    payload = {
        "project_id": project_id,
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "completion_rate_pct": completion_rate,
        "channels": channels
    }

    with open(lpath, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print_success(f"✅ 项目 [{project_id}] 渠道 [{ch_data['name']}] 外发链接已回填: {url_clean or '已清空'} (状态: {ch_data['status']})")

    return {
        "success": True,
        "project_id": project_id,
        "channel": channel,
        "record": ch_data,
        "completion_rate_pct": completion_rate,
        "ledger": payload
    }

def verify_all_channels(project_id: str) -> dict:
    """批量并发核验所有已填报的外链存活状态"""
    ledger = get_distribution_ledger(project_id)
    channels = ledger["channels"]

    def _verify_ch(item):
        k, v = item
        u = v.get("url", "").strip()
        if u:
            vres = verify_distribution_url(u)
            v["http_status"] = vres["http_status"]
            v["verified_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            v["status"] = "verified" if vres["is_alive"] else "failed"
        return k, v

    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(_verify_ch, channels.items()))

    for k, v in results:
        channels[k] = v

    lpath = _get_ledger_path(project_id)
    total = len(channels)
    published = sum(1 for c in channels.values() if c.get("url") and c.get("status") in ("verified", "published"))
    completion_rate = round((published / max(total, 1)) * 100, 1)

    payload = {
        "project_id": project_id,
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "completion_rate_pct": completion_rate,
        "channels": channels
    }

    with open(lpath, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print_success(f"🎉 项目 [{project_id}] 全渠道外链核验完毕！完成率: {completion_rate}%")
    return {
        "success": True,
        "project_id": project_id,
        "completion_rate_pct": completion_rate,
        "channels": channels
    }

def format_rich_text_copy(project_id: str, channel: str) -> dict:
    """获取指定渠道的文章内容，并格式化为适合富文本剪贴板粘贴的 HTML"""
    p_dir = os.path.join(PROJECTS_DIR, project_id, "outputs")
    ch_info = DEFAULT_CHANNELS.get(channel, {})
    fname = ch_info.get("article_file", "")
    fpath = os.path.join(p_dir, fname)

    raw_content = ""
    if os.path.exists(fpath):
        with open(fpath, "r", encoding="utf-8") as f:
            raw_content = f.read()

    return {
        "success": True,
        "project_id": project_id,
        "channel": channel,
        "filename": fname,
        "raw_content": raw_content,
        "length": len(raw_content)
    }

if __name__ == "__main__":
    pid = sys.argv[1] if len(sys.argv) > 1 else "xuzhou_xuanyuan"
    print(json.dumps(get_distribution_ledger(pid), ensure_ascii=False, indent=2))
