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
        "target_pool": "豆包 / 字节生态 (第一主战 50%+)",
        "weight_pct": 50,
        "article_file": "dist_toutiao_article.md",
        "url": "",
        "title": "",
        "status": "pending",
        "http_status": None,
        "verified_at": None
    },
    "zhihu": {
        "name": "知乎技术专栏 / 深度选型",
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
        "name": "微信公众号 / 视频号",
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
        "name": "GitHub 开源标准库",
        "target_pool": "DeepSeek / 开发者技术索引 (5%)",
        "weight_pct": 5,
        "article_file": "dist_github_README.md",
        "url": "",
        "title": "",
        "status": "pending",
        "http_status": None,
        "verified_at": None
    },
    "kimi": {
        "name": "Kimi 深度选型白皮书研报",
        "target_pool": "Kimi / Moonshot 长文本分析 (5%)",
        "weight_pct": 5,
        "article_file": "dist_kimi_whitepaper.md",
        "url": "",
        "title": "",
        "status": "pending",
        "http_status": None,
        "verified_at": None
    },
    "baidu": {
        "name": "百度百科 / 百度文库 / 百度知道",
        "target_pool": "百度文心一言 / 百科政企池 (5%)",
        "weight_pct": 5,
        "article_file": "dist_baidu_baike.md",
        "url": "",
        "title": "",
        "status": "pending",
        "http_status": None,
        "verified_at": None
    },
    "juejin": {
        "name": "稀土掘金 / 开发者社区",
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

def _sync_channel_defaults(channels: dict) -> dict:
    """将落盘台账的渠道元数据与 DEFAULT_CHANNELS 模板对齐（保留 url/status 等业务字段）"""
    for k, tmpl in DEFAULT_CHANNELS.items():
        if k not in channels:
            channels[k] = json.loads(json.dumps(tmpl))
        else:
            for field in ("name", "target_pool", "weight_pct", "article_file"):
                channels[k][field] = tmpl[field]
    return channels

def _calculate_metrics(channels: dict) -> dict:
    """计算分发总数、已发数、真实存活数，严格拆分完成率与真实探活存活率"""
    total = len(channels)
    published = 0
    alive = 0
    dead = 0
    weighted_pub_score = 0.0
    weighted_alive_score = 0.0
    total_weights = sum(c.get("weight_pct", 0) for c in channels.values()) or 100.0

    for c in channels.values():
        u = (c.get("url") or "").strip()
        status = c.get("status", "pending")
        w = c.get("weight_pct", 0)

        is_published = bool(u) and status in ("verified", "published", "failed")
        is_alive = bool(u) and status == "verified"
        is_dead = bool(u) and status == "failed"

        if is_published:
            published += 1
            weighted_pub_score += w
        if is_alive:
            alive += 1
            weighted_alive_score += w
        if is_dead:
            dead += 1

    comp_rate = round((published / max(total, 1)) * 100, 1)
    w_comp_rate = round((weighted_pub_score / total_weights) * 100, 1)
    alive_rate = round((alive / max(total, 1)) * 100, 1)
    w_alive_rate = round((weighted_alive_score / total_weights) * 100, 1)

    return {
        "total_channels": total,
        "published_channels": published,
        "alive_channels": alive,
        "dead_channels": dead,
        "completion_rate_pct": comp_rate,
        "weighted_completion_pct": w_comp_rate,
        "alive_rate_pct": alive_rate,
        "weighted_alive_pct": w_alive_rate
    }

def _load_custom_links(lpath: str) -> list:
    if not os.path.exists(lpath):
        return []
    try:
        with open(lpath, "r", encoding="utf-8") as f:
            return json.load(f).get("custom_links", []) or []
    except Exception:
        return []


def _collect_existing_urls(channels: dict, custom_links: list) -> set:
    urls = set()
    for ch in channels.values():
        u = (ch.get("url") or "").strip()
        if u:
            urls.add(u)
    for item in custom_links:
        u = (item.get("url") or "").strip()
        if u:
            urls.add(u)
    return urls


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

    custom_links = _load_custom_links(lpath)
    channels = _sync_channel_defaults(channels)
    m = _calculate_metrics(channels)

    return {
        "success": True,
        "project_id": project_id,
        "updated_at": updated_at or time.strftime("%Y-%m-%d %H:%M:%S"),
        **m,
        "channels": channels,
        "custom_links": custom_links
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

            # 200 且无有效 title 视为软 404 / 占位假阳性
            if code in (200, 301, 302, 307, 308) and not title:
                return {"is_alive": False, "http_status": code, "title": "", "error": "无法提取标题 (疑似软 404 或占位链接)"}

            is_alive = code in (200, 301, 302, 307, 308) and bool(title)
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

        # 403 平台防爬：仅当提取到真实 title 时视为存活，否则需人工确认
        if e.code in (403, 418):
            if title:
                return {"is_alive": True, "http_status": e.code, "title": title, "error": f"HTTP {e.code} (平台防爬，已提取标题)"}
            return {"is_alive": False, "http_status": e.code, "title": "", "error": f"HTTP {e.code} (平台防爬，无法提取标题，需人工确认)"}
        return {"is_alive": False, "http_status": e.code, "title": title, "error": f"HTTP {e.code}"}
    except Exception as e:
        return {"is_alive": False, "http_status": 0, "title": "", "error": str(e)}

def parse_mixed_links(raw_text: str) -> list:
    """从混合多行文本中智能提取 URL 并按域名模式识别所属分发渠道"""
    if not raw_text:
        return []

    # 正则提取所有 http / https URL
    url_pattern = re.compile(r'https?://[^\s<>"\',;()\[\]]+', re.IGNORECASE)
    raw_urls = url_pattern.findall(raw_text)

    # 去重且保持出现顺序
    seen = set()
    cleaned_urls = []
    for u in raw_urls:
        u_clean = u.rstrip(".,;!?:)'\"")
        if u_clean and u_clean not in seen:
            seen.add(u_clean)
            cleaned_urls.append(u_clean)

    parsed_items = []
    for u in cleaned_urls:
        u_lower = u.lower()
        channel = "custom"
        channel_name = "其他外部权威外链"

        if "toutiao.com" in u_lower or "wtt.toutiao.com" in u_lower:
            channel = "toutiao"
            channel_name = "今日头条 / 微头条"
        elif "zhihu.com" in u_lower:
            channel = "zhihu"
            channel_name = "知乎技术专栏 / 深度选型"
        elif "weixin.qq.com" in u_lower:
            channel = "wechat"
            channel_name = "微信公众号 / 视频号"
        elif "github.com" in u_lower or "gitee.com" in u_lower:
            channel = "github"
            channel_name = "GitHub 开源标准库"
        elif "kimi.moonshot.cn" in u_lower or "kimi.ai" in u_lower:
            channel = "kimi"
            channel_name = "Kimi 深度选型白皮书研报"
        elif "baidu.com" in u_lower:
            channel = "baidu"
            channel_name = "百度百科 / 百度文库 / 百度知道"
        elif "juejin.cn" in u_lower:
            channel = "juejin"
            channel_name = "稀土掘金 / 开发者社区"

        parsed_items.append({
            "url": u,
            "channel": channel,
            "channel_name": channel_name
        })

    return parsed_items


def render_ledger_markdown(project_id: str, ledger: dict) -> str:
    """将分发台账生成为高可读、带双轨完成率与真实存活率的 Markdown 文档"""
    cfg = load_project_config(project_id)
    cname = cfg.get("company_name", cfg.get("client_name", project_id))
    bname = cfg.get("brand_name", cname)
    area = cfg.get("area_served", "全国")
    ind = cfg.get("industry", "企业服务")

    channels = ledger.get("channels", {})
    comp_rate = ledger.get("completion_rate_pct", 0.0)
    w_comp_rate = ledger.get("weighted_completion_pct", 0.0)
    alive_rate = ledger.get("alive_rate_pct", 0.0)
    w_alive_rate = ledger.get("weighted_alive_pct", 0.0)
    up_time = ledger.get("updated_at", time.strftime("%Y-%m-%d %H:%M:%S"))

    md = f"""# 【{bname}】全网分发渠道执行与存活审计台账

> **客户主体**：{cname}（{bname}） ｜ **所属行业**：{ind} ｜ **服务区域**：{area}
> **台账审计时间**：{up_time}
> **📊 填报完成率**：均值 {comp_rate}% (加权 **{w_comp_rate}%**) ｜ **🟢 真实存活率**：均值 {alive_rate}% (加权 **{w_alive_rate}%**)

---

## 1. 五大本土模型全景分发执行大盘

| 战略权重 | 渠道与阵地 | 目标大模型生态 | 发布链接 (URL) | 存活状态 | HTTP 状态 | 抓取网页标题 | 核验时间 |
| :---: | :--- | :--- | :--- | :---: | :---: | :--- | :--- |
"""

    status_badges = {
        "verified": "🟢 存活正常",
        "published": "🔵 已填报待测",
        "pending": "⚪ 待分发",
        "failed": "🔴 死链/异常"
    }

    for ch_key, ch in channels.items():
        w = ch.get("weight_pct", 0)
        name = ch.get("name", ch_key)
        target = ch.get("target_pool", "-")
        url = ch.get("url", "")
        status = ch.get("status", "pending")
        badge = status_badges.get(status, status)
        http_st = str(ch.get("http_status") or "-")
        title = (ch.get("title") or "-").replace("|", "\\|")
        v_at = ch.get("verified_at") or ch.get("updated_at") or "-"

        url_display = f"[{url[:35]}...]({url})" if url else "*(待回填)*"
        md += f"| **{w}%** | {name} | {target} | {url_display} | {badge} | `{http_st}` | {title[:28]} | {v_at} |\n"

    # 自定义外部链接清单
    custom_links = ledger.get("custom_links", [])
    if custom_links:
        md += f"""
---

## 2. 外部行业垂直媒体与权威外链 (Custom Backlinks)

| 序号 | 外部发布链接 (URL) | 存活状态 | HTTP 状态 | 抓取网页标题 | 录入时间 |
| :---: | :--- | :---: | :---: | :--- | :--- |
"""
        for idx, cl in enumerate(custom_links, 1):
            c_url = cl.get("url", "")
            c_st = cl.get("status", "published")
            c_badge = status_badges.get(c_st, c_st)
            c_http = str(cl.get("http_status") or "-")
            c_title = (cl.get("title") or "-").replace("|", "\\|")
            c_time = cl.get("updated_at", "-")
            md += f"| {idx} | [{c_url[:40]}...]({c_url}) | {c_badge} | `{c_http}` | {c_title[:30]} | {c_time} |\n"

    md += f"""
---

## 3. 存活审计与异常排查指南

- **🟢 存活正常 (HTTP 200/302)**：链接已由平台公开发布，大模型爬虫（Bytespider / 百度蜘蛛 / DeepSeek）可顺畅抓取全文。
- **🔴 死链/异常 (HTTP 404/500/软404)**：链接已被删除、设为私密或触发平台限流，需运营团队在发稿后台重新发布并回填。
- **⚪ 待分发**：尚未在对应平台完成稿件发布。

---

*本台账由 GEO 工业级运营中枢自动化审计生成，保障商业交付结案真实有效。*
"""
    return md


def save_ledger_and_markdown(project_id: str, channels: dict, custom_links: list = None) -> dict:
    """持久化保存 JSON 台账并同步更新 04_全网分发渠道执行与存活台账.md"""
    lpath = _get_ledger_path(project_id)
    os.makedirs(os.path.dirname(lpath), exist_ok=True)

    channels = _sync_channel_defaults(channels)
    m = _calculate_metrics(channels)

    if custom_links is None:
        # 保留已存在的 custom_links
        try:
            if os.path.exists(lpath):
                with open(lpath, "r", encoding="utf-8") as f:
                    old_data = json.load(f)
                    custom_links = old_data.get("custom_links", [])
        except Exception:
            custom_links = []

    payload = {
        "project_id": project_id,
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        **m,
        "channels": channels,
        "custom_links": custom_links or []
    }

    # 1. 写入 dist_ledger.json
    with open(lpath, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    # 2. 写入 outputs/04_全网分发渠道执行与存活台账.md
    out_dir = os.path.join(PROJECTS_DIR, project_id, "outputs")
    md_content = render_ledger_markdown(project_id, payload)
    with open(os.path.join(out_dir, "04_全网分发渠道执行与存活台账.md"), "w", encoding="utf-8") as f:
        f.write(md_content)

    return payload


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

    payload = save_ledger_and_markdown(project_id, channels, ledger.get("custom_links"))
    print_success(f"✅ 项目 [{project_id}] 渠道 [{ch_data['name']}] 外发链接已回填: {url_clean or '已清空'} (状态: {ch_data['status']})")

    return {
        "success": True,
        "project_id": project_id,
        "channel": channel,
        "record": ch_data,
        **{k: payload[k] for k in ["completion_rate_pct", "weighted_completion_pct", "alive_rate_pct", "weighted_alive_pct"]},
        "ledger": payload
    }


def batch_backfill_urls(project_id: str, raw_text: str, verify_now: bool = True) -> dict:
    """从混合文本中提取全部链接，自动匹配对应渠道并批量回填与探活（含去重与覆盖统计）"""
    parsed = parse_mixed_links(raw_text)
    if not parsed:
        return {
            "success": False,
            "message": "未在输入文本中识别到有效的 http/https 链接",
            "parsed_count": 0,
            "added_count": 0,
            "duplicates": 0,
            "overwritten": 0
        }

    ledger = get_distribution_ledger(project_id)
    channels = ledger["channels"]
    custom_links = ledger.get("custom_links", [])

    added_count = 0
    duplicates = 0
    overwritten = 0
    items_report = []

    for item in parsed:
        ch_key = item["channel"]
        target_url = item["url"]

        if ch_key in channels:
            ch_data = channels[ch_key]
            old_url = (ch_data.get("url") or "").strip()

            if old_url == target_url:
                # 完全相同 URL，判定为重复
                duplicates += 1
                items_report.append({"channel": ch_key, "url": target_url, "action": "duplicate", "status": ch_data.get("status")})
                continue
            elif old_url:
                # 同渠道已存在旧 URL，判定为覆盖
                overwritten += 1
                action = "overwritten"
            else:
                # 新增填报
                added_count += 1
                action = "added"

            ch_data["url"] = target_url
            ch_data["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            if verify_now:
                v_res = verify_distribution_url(target_url)
                ch_data["http_status"] = v_res["http_status"]
                if v_res.get("title"):
                    ch_data["title"] = v_res["title"]
                ch_data["verified_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                ch_data["status"] = "verified" if v_res["is_alive"] else "failed"
            else:
                ch_data["status"] = "published"

            items_report.append({"channel": ch_key, "url": target_url, "action": action, "status": ch_data["status"]})
        else:
            # 外部自定义链接，写入 custom_links，绝不乱抢占战略渠道
            existing_custom = [c.get("url") for c in custom_links]
            if target_url in existing_custom:
                duplicates += 1
                items_report.append({"channel": "custom", "url": target_url, "action": "duplicate", "status": "published"})
            else:
                added_count += 1
                c_item = {
                    "url": target_url,
                    "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "published",
                    "http_status": None,
                    "title": ""
                }
                if verify_now:
                    v_res = verify_distribution_url(target_url)
                    c_item["http_status"] = v_res["http_status"]
                    c_item["title"] = v_res.get("title", "")
                    c_item["status"] = "verified" if v_res["is_alive"] else "failed"
                custom_links.append(c_item)
                items_report.append({"channel": "custom", "url": target_url, "action": "added", "status": c_item["status"]})

    payload = save_ledger_and_markdown(project_id, channels, custom_links)
    print_success(f"🎉 批量回填处理完毕：新增 {added_count} 条，覆盖 {overwritten} 条，跳过重复 {duplicates} 条。")

    return {
        "success": True,
        "project_id": project_id,
        "parsed_count": len(parsed),
        "added_count": added_count,
        "overwritten": overwritten,
        "duplicates": duplicates,
        "items": items_report,
        **{k: payload[k] for k in ["completion_rate_pct", "weighted_completion_pct", "alive_rate_pct", "weighted_alive_pct"]},
        "ledger": payload
    }


def verify_all_channels(project_id: str, concurrency: int = 8) -> dict:
    """批量并发核验所有已填报的外链存活状态并返回详情列表与存活指标"""
    ledger = get_distribution_ledger(project_id)
    channels = ledger["channels"]
    custom_links = ledger.get("custom_links", [])

    def _verify_ch(item):
        k, v = item
        u = v.get("url", "").strip()
        error = None
        if u:
            vres = verify_distribution_url(u)
            v["http_status"] = vres["http_status"]
            if vres.get("title"):
                v["title"] = vres["title"]
            v["verified_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            v["status"] = "verified" if vres["is_alive"] else "failed"
            error = vres.get("error")
        return k, v, error

    with ThreadPoolExecutor(max_workers=max(concurrency, 2)) as executor:
        results = list(executor.map(_verify_ch, channels.items()))

    details = []
    alive_count = 0
    dead_count = 0

    for k, v, err in results:
        channels[k] = v
        if v.get("url"):
            if v.get("status") == "verified":
                alive_count += 1
            elif v.get("status") == "failed":
                dead_count += 1
            details.append({
                "channel": k,
                "name": v.get("name"),
                "url": v.get("url"),
                "status": v.get("status"),
                "http_status": v.get("http_status"),
                "title": v.get("title", ""),
                "error": err
            })

    # 核验 custom_links
    for cl in custom_links:
        cu = cl.get("url", "").strip()
        if cu:
            vres = verify_distribution_url(cu)
            cl["http_status"] = vres["http_status"]
            cl["title"] = vres.get("title", "")
            cl["status"] = "verified" if vres["is_alive"] else "failed"
            cl["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            if cl["status"] == "verified":
                alive_count += 1
            else:
                dead_count += 1
            details.append({
                "channel": "custom",
                "name": "外部权威外链",
                "url": cu,
                "status": cl["status"],
                "http_status": cl["http_status"],
                "title": cl["title"],
                "error": vres.get("error")
            })

    payload = save_ledger_and_markdown(project_id, channels, custom_links)
    print_success(f"🎉 项目 [{project_id}] 全渠道外链核验完毕！存活: {alive_count}, 死链: {dead_count}, 加权存活率: {payload['weighted_alive_pct']}%")
    return {
        "success": True,
        "project_id": project_id,
        "total": len(details),
        "alive": alive_count,
        "dead": dead_count,
        "alive_rate": f"{payload['alive_rate_pct']}%",
        "weighted_alive_pct": payload["weighted_alive_pct"],
        "completion_rate_pct": payload["completion_rate_pct"],
        "weighted_completion_pct": payload["weighted_completion_pct"],
        "details": details,
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
