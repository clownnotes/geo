#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GEO 自动化分发台账回填与收录核验中枢 (tools/geo/dist_bot.py)
核心功能：
1. 管理 5 大信任池渠道（今日头条/知乎/掘金/GitHub/微信公众号）外发台账 (outputs/dist_ledger.json)；
2. 记录与更新外发 URL，并自动化发起轻量 HTTP 存活与收录连通性探测及页面标题抓取；
3. 计算项目全渠道分发完成率 (0~100%) 与收录状态；
4. 生成适配公众号/知乎带样式的富文本 HTML 剪贴板内容。
"""

import os
import sys
import json
import time
import re
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
        "name": "今日头条 / 微头条",
        "target_pool": "豆包 / 字节生态 (第一主攻 50%+)",
        "weight_pct": 50,
        "article_file": "dist_toutiao_article.md",
        "url": "",
        "title": "",
        "status": "pending",
        "http_status": None,
        "verified_at": None
    },
    "zhihu": {
        "name": "知乎专栏 / 问答",
        "target_pool": "DeepSeek / 技术决策池 (25%)",
        "weight_pct": 25,
        "article_file": "dist_zhihu_article.md",
        "url": "",
        "title": "",
        "status": "pending",
        "http_status": None,
        "verified_at": None
    },
    "wechat": {
        "name": "微信公众号",
        "target_pool": "腾讯元宝 / 微信搜一搜 (10%)",
        "weight_pct": 10,
        "article_file": "dist_wechat_article.html",
        "url": "",
        "title": "",
        "status": "pending",
        "http_status": None,
        "verified_at": None
    },
    "github": {
        "name": "GitHub / 选型研报",
        "target_pool": "DeepSeek / Kimi 深度研报池 (10%)",
        "weight_pct": 10,
        "article_file": "dist_github_README.md",
        "url": "",
        "title": "",
        "status": "pending",
        "http_status": None,
        "verified_at": None
    },
    "baidu": {
        "name": "百度百科 / 百家号",
        "target_pool": "百度文心一言 / 百科政企池 (5%)",
        "weight_pct": 5,
        "article_file": "03_普林斯顿9因子高权威语料库.md",
        "url": "",
        "title": "",
        "status": "pending",
        "http_status": None,
        "verified_at": None
    },
    "juejin": {
        "name": "稀土掘金",
        "target_pool": "豆包 / 开发者技术检索池",
        "weight_pct": 0,
        "article_file": "dist_juejin_article.md",
        "url": "",
        "title": "",
        "status": "pending",
        "http_status": None,
        "verified_at": None
    }
}

def _get_ledger_path(project_id: str) -> str:
    return os.path.join(PROJECTS_DIR, project_id, "outputs", "dist_ledger.json")

def _find_channel_file(project_id: str, channel: str) -> tuple:
    """定位渠道文章文件路径与文件名"""
    p_dir = os.path.join(PROJECTS_DIR, project_id, "outputs")
    dist_dir = os.path.join(p_dir, "distribute")
    ch_info = DEFAULT_CHANNELS.get(channel, {})
    default_fname = ch_info.get("article_file", "")
    
    # 检查 outputs/distribute/ 子目录下的命名
    if os.path.exists(dist_dir):
        for f in os.listdir(dist_dir):
            if f.endswith(f"_{channel}.md") or f.endswith(f"_{channel}.html") or f.endswith(f"--{channel}.md"):
                return os.path.join(dist_dir, f), f

    # 兼容回退候选
    candidate_files = [default_fname]
    if channel in ("juejin", "baidu"):
        candidate_files.append("03_普林斯顿9因子高权威语料库.md")
        candidate_files.append("03_普林斯顿9因子企业语料库.md")

    for f in candidate_files:
        fpath = os.path.join(p_dir, f)
        if os.path.exists(fpath):
            return fpath, f

    return os.path.join(p_dir, default_fname), default_fname

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

def _calculate_metrics(channels: dict) -> tuple:
    """计算分发总数、已发数、均值完成率与加权战略完成率"""
    total = len(channels)
    published = 0
    weighted_score = 0.0
    total_weights = sum(c.get("weight_pct", 0) for c in channels.values()) or 100.0

    for c in channels.values():
        is_ok = bool(c.get("url")) and c.get("status") in ("verified", "published")
        if is_ok:
            published += 1
            weighted_score += c.get("weight_pct", 0)

    rate = round((published / max(total, 1)) * 100, 1)
    weighted_rate = round((weighted_score / total_weights) * 100, 1)
    return total, published, rate, weighted_rate

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

    total, published, rate, weighted_rate = _calculate_metrics(channels)

    return {
        "success": True,
        "project_id": project_id,
        "updated_at": updated_at or time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_channels": total,
        "published_channels": published,
        "completion_rate_pct": rate,
        "weighted_completion_pct": weighted_rate,
        "channels": channels
    }

def verify_distribution_url(url: str) -> dict:
    """轻量探测外发 URL 是否真实存活、抓取网页标题并过滤软 404"""
    if not url or not url.startswith("http"):
        return {"is_alive": False, "http_status": None, "title": "", "error": "无效的 URL"}

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 GEOBot/2.2",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
        }
    )
    
    soft_404_keywords = [
        "页面不存在", "404 not found", "内容已被删除", "抱歉，出错了", 
        "该内容已被发布者删除", "page not found", "404", "无法找到页面"
    ]

    try:
        with urllib.request.urlopen(req, timeout=6) as response:
            code = response.getcode()
            title = ""
            try:
                chunk = response.read(32768).decode("utf-8", errors="ignore")
                t_match = re.search(r"<title>(.*?)</title>", chunk, re.IGNORECASE | re.DOTALL)
                if t_match:
                    title = re.sub(r"\s+", " ", t_match.group(1)).strip()
            except Exception:
                pass
            
            # 软 404 校验
            if title and any(k in title.lower() for k in soft_404_keywords):
                return {"is_alive": False, "http_status": code, "title": title, "error": "软 404 (页面已失效或删除)"}

            # 200/301/302 存活
            is_alive = code in (200, 301, 302, 307, 308)
            return {"is_alive": is_alive, "http_status": code, "title": title, "error": None}

    except urllib.error.HTTPError as e:
        title = ""
        try:
            chunk = e.read(4096).decode("utf-8", errors="ignore")
            t_match = re.search(r"<title>(.*?)</title>", chunk, re.IGNORECASE | re.DOTALL)
            if t_match:
                title = re.sub(r"\s+", " ", t_match.group(1)).strip()
        except Exception:
            pass

        # 403 平台防爬（知乎/头条/微信平台）
        if e.code in (403, 418):
            return {"is_alive": True, "http_status": e.code, "title": title or "平台安全网关防护中", "error": f"HTTP {e.code} (平台防爬校验)"}
        return {"is_alive": False, "http_status": e.code, "title": title, "error": f"HTTP {e.code}"}
    except Exception as e:
        return {"is_alive": False, "http_status": 0, "title": "", "error": str(e)}

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
        ch_data["title"] = ""
        ch_data["verified_at"] = None
    else:
        if verify_now:
            v_res = verify_distribution_url(url_clean)
            ch_data["http_status"] = v_res["http_status"]
            if v_res.get("title"):
                ch_data["title"] = v_res["title"]
            ch_data["verified_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            ch_data["status"] = "verified" if v_res["is_alive"] else "failed"
        else:
            ch_data["status"] = "published"

    # 保存文件
    lpath = _get_ledger_path(project_id)
    os.makedirs(os.path.dirname(lpath), exist_ok=True)
    
    total, published, completion_rate, weighted_rate = _calculate_metrics(channels)

    payload = {
        "project_id": project_id,
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "completion_rate_pct": completion_rate,
        "weighted_completion_pct": weighted_rate,
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
        "weighted_completion_pct": weighted_rate,
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
            if vres.get("title"):
                v["title"] = vres["title"]
            v["verified_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            v["status"] = "verified" if vres["is_alive"] else "failed"
        return k, v

    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(_verify_ch, channels.items()))

    for k, v in results:
        channels[k] = v

    lpath = _get_ledger_path(project_id)
    total, published, completion_rate, weighted_rate = _calculate_metrics(channels)

    payload = {
        "project_id": project_id,
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "completion_rate_pct": completion_rate,
        "weighted_completion_pct": weighted_rate,
        "channels": channels
    }

    with open(lpath, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print_success(f"🎉 项目 [{project_id}] 全渠道外链核验完毕！均值完成率: {completion_rate}% (战略加权完成率: {weighted_rate}%)")
    return {
        "success": True,
        "project_id": project_id,
        "completion_rate_pct": completion_rate,
        "weighted_completion_pct": weighted_rate,
        "channels": channels
    }

def markdown_to_styled_html(md_text: str, title: str = "") -> str:
    """将 Markdown 转换为适合直接粘贴到公众号/知乎的内联带样式 HTML"""
    if not md_text:
        return ""
    
    # 简易而优雅的 HTML 转换器（带内联样式）
    lines = md_text.split("\n")
    html_out = []
    html_out.append('<div style="font-family: -apple-system, BlinkMacSystemFont, \'PingFang SC\', \'Hiragino Sans GB\', \'Microsoft YaHei\', sans-serif; font-size: 15px; line-height: 1.75; color: #333333; word-break: break-word;">')
    
    in_table = False
    table_rows = []
    
    def _flush_table():
        nonlocal in_table, table_rows
        if table_rows:
            html_out.append('<table style="width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 13.5px;">')
            for idx, r in enumerate(table_rows):
                cols = [c.strip() for c in r.split("|")[1:-1]]
                if idx == 0:
                    html_out.append('<tr style="background-color: #f3f4f6; font-weight: bold;">')
                    for c in cols:
                        html_out.append(f'<th style="border: 1px solid #e5e7eb; padding: 8px 10px; text-align: left;">{c}</th>')
                    html_out.append('</tr>')
                elif idx == 1 and all(set(c).issubset({"-", ":"}) for c in cols):
                    continue
                else:
                    bg = "#ffffff" if idx % 2 == 0 else "#f9fafb"
                    html_out.append(f'<tr style="background-color: {bg};">')
                    for c in cols:
                        html_out.append(f'<td style="border: 1px solid #e5e7eb; padding: 8px 10px;">{c}</td>')
                    html_out.append('</tr>')
            html_out.append('</table>')
            table_rows = []
        in_table = False

    for line in lines:
        s_line = line.strip()
        if s_line.startswith("|") and s_line.endswith("|"):
            in_table = True
            table_rows.append(s_line)
            continue
        else:
            if in_table:
                _flush_table()

        if s_line.startswith("# "):
            h1_text = s_line[2:].strip()
            html_out.append(f'<h1 style="font-size: 22px; font-weight: 800; color: #1e1b4b; border-bottom: 2px solid #4f46e5; padding-bottom: 8px; margin-top: 24px; margin-bottom: 16px;">{h1_text}</h1>')
        elif s_line.startswith("## "):
            h2_text = s_line[3:].strip()
            html_out.append(f'<h2 style="font-size: 18px; font-weight: 700; color: #312e81; border-left: 4px solid #6366f1; padding-left: 10px; margin-top: 20px; margin-bottom: 12px;">{h2_text}</h2>')
        elif s_line.startswith("### "):
            h3_text = s_line[4:].strip()
            html_out.append(f'<h3 style="font-size: 16px; font-weight: 600; color: #4338ca; margin-top: 16px; margin-bottom: 8px;">{h3_text}</h3>')
        elif s_line.startswith("> "):
            q_text = s_line[2:].strip()
            html_out.append(f'<blockquote style="margin: 12px 0; padding: 10px 14px; background-color: #f5f3ff; border-left: 3px solid #8b5cf6; color: #5b21b6; font-size: 14px; border-radius: 4px;">{q_text}</blockquote>')
        elif s_line.startswith("- ") or s_line.startswith("* "):
            li_text = s_line[2:].strip()
            # 替换 **粗体**
            li_text = re.sub(r"\*\*(.*?)\*\*", r'<strong style="color: #1e1b4b;">\1</strong>', li_text)
            html_out.append(f'<p style="margin: 4px 0; padding-left: 14px; text-indent: -14px;">• {li_text}</p>')
        elif s_line:
            p_text = re.sub(r"\*\*(.*?)\*\*", r'<strong style="color: #1e1b4b;">\1</strong>', s_line)
            html_out.append(f'<p style="margin: 10px 0; line-height: 1.8;">{p_text}</p>')
        else:
            html_out.append('<div style="height: 6px;"></div>')

    if in_table:
        _flush_table()

    html_out.append('</div>')
    return "\n".join(html_out)

def format_rich_text_copy(project_id: str, channel: str) -> dict:
    """获取指定渠道的文章内容，并输出预编译带样式的富文本 HTML"""
    fpath, fname = _find_channel_file(project_id, channel)

    raw_content = ""
    if os.path.exists(fpath):
        with open(fpath, "r", encoding="utf-8") as f:
            raw_content = f.read()

    # 提取文章主标题
    title = ""
    t_match = re.search(r"^#\s+(.+)$", raw_content, re.MULTILINE)
    if t_match:
        title = t_match.group(1).strip()
    elif "<title>" in raw_content:
        t_html = re.search(r"<title>(.*?)</title>", raw_content, re.IGNORECASE)
        if t_html:
            title = t_html.group(1).strip()

    # 转换为内联样式富文本 HTML
    if fpath.endswith(".html"):
        html_content = raw_content
    else:
        html_content = markdown_to_styled_html(raw_content, title=title)

    return {
        "success": True,
        "project_id": project_id,
        "channel": channel,
        "filename": fname,
        "title": title,
        "raw_content": raw_content,
        "html_content": html_content,
        "length": len(raw_content)
    }

if __name__ == "__main__":
    pid = sys.argv[1] if len(sys.argv) > 1 else "xuzhou_xuanyuan"
    print(json.dumps(get_distribution_ledger(pid), ensure_ascii=False, indent=2))
