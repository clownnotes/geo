#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GEO 定时自动化巡检与企微/飞书异动告警中枢 (tools/geo/patrol.py)
核心功能：
1. 自动遍历活跃客户项目，并发探测主流大模型并沉淀 SQLite 时序历史；
2. 实时监测 SOV 暴跌与竞品拦截态势；
3. 发现异常时自动组装并向企业微信/飞书/钉钉群机器人发送富文本告警卡片。
"""

import os
import sys
import json
import time
import sqlite3
import datetime
import urllib.request
import urllib.error
import ssl

from .utils import (
    load_project_config,
    print_banner,
    print_info,
    print_success,
    print_warning,
    PROJECTS_DIR
)
from .monitor import run_monitor, extract_monitor_metrics

DATA_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
SETTINGS_FILE = os.path.join(DATA_DIR, "notifications.json")

def load_notification_settings() -> dict:
    """读取全局通知与告警配置"""
    default_settings = {
        "enabled": False,
        "webhook_type": "auto",  # auto / wecom / feishu / dingtalk
        "webhook_url": "",
        "min_sov_threshold": 50.0,
        "notify_on_sov_drop": True,
        "notify_on_intercept": True,
        "drop_threshold_pct": 10.0,
        "last_patrol_time": None
    }
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                default_settings.update(data)
        except Exception:
            pass
    return default_settings

def save_notification_settings(settings: dict) -> bool:
    """保存全局通知与告警配置 (自动 Merge 现有配置)"""
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        current = load_notification_settings()
        current.update(settings)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(current, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存通知配置失败: {e}")
        return False

# ==========================================
# SQLite 历史声量时序库
# ==========================================

def get_history_db_path(project_id: str) -> str:
    """获取项目的 history.db 绝对路径"""
    cfg = load_project_config(project_id)
    return os.path.join(cfg["_project_dir"], "history.db")

def init_history_db(db_path: str):
    """初始化 SQLite 历史表结构"""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS monitor_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                check_date TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                is_offline INTEGER DEFAULT 0,
                sov_pct REAL NOT NULL,
                top3_pct REAL NOT NULL,
                authority_score REAL NOT NULL,
                total_prompts INTEGER NOT NULL,
                hit_count INTEGER NOT NULL,
                intercept_count INTEGER NOT NULL,
                lost_count INTEGER NOT NULL,
                details_json TEXT
            )
        """)
        conn.commit()

def record_project_history(project_id: str, metrics: dict) -> int:
    """将单次巡检指标存入项目的 history.db"""
    db_path = get_history_db_path(project_id)
    init_history_db(db_path)
    
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    now_ts = int(time.time())
    
    p_stats = metrics.get("prompt_stats", {})
    details_str = json.dumps({
        "citations": metrics.get("citations", []),
        "is_offline": metrics.get("is_offline", False)
    }, ensure_ascii=False)

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO monitor_history 
            (check_date, timestamp, is_offline, sov_pct, top3_pct, authority_score, 
             total_prompts, hit_count, intercept_count, lost_count, details_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            today_str,
            now_ts,
            1 if metrics.get("is_offline") else 0,
            metrics.get("sov_pct", 0.0),
            metrics.get("top3_pct", 0.0),
            metrics.get("authority_score", 0.0),
            p_stats.get("total", 0),
            p_stats.get("hit_count", 0),
            p_stats.get("intercept_count", 0),
            p_stats.get("lost_count", 0),
            details_str
        ))
        conn.commit()
        return cursor.lastrowid

def get_project_history(project_id: str, limit: int = 12) -> list:
    """获取项目的多周巡检历史时序记录（最近 N 条）"""
    db_path = get_history_db_path(project_id)
    if not os.path.exists(db_path):
        return []
    
    records = []
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM monitor_history 
                ORDER BY timestamp ASC
            """)
            rows = cursor.fetchall()
            for r in rows[-limit:]:
                d = dict(r)
                if d.get("details_json"):
                    try:
                        d["details"] = json.loads(d["details_json"])
                    except Exception:
                        d["details"] = {}
                records.append(d)
    except Exception as e:
        print(f"读取历史数据异常: {e}")
    return records

# ==========================================
# 异动告警检测与 Webhook 发送
# ==========================================

def check_alert_conditions(current_metrics: dict, history_records: list, settings: dict, cfg: dict = None) -> tuple:
    """
    检查当前声量是否触发告警规则
    返回: (should_alert, reasons_summary, details_list)
    """
    reasons = []
    curr_sov = current_metrics.get("sov_pct", 0.0)
    curr_intercept = current_metrics.get("prompt_stats", {}).get("intercept_count", 0)
    is_offline = current_metrics.get("is_offline", False)
    
    # 规则 1: 绝对值跌破健康线
    min_threshold = settings.get("min_sov_threshold", 50.0)
    if curr_sov < min_threshold and not is_offline:
        reasons.append(f"当前 SOV ({curr_sov}%) 低于预警安全线 ({min_threshold}%)")

    # 规则 2: 环比上周断崖下跌
    if len(history_records) >= 2 and settings.get("notify_on_sov_drop", True):
        last_rec = history_records[-2]  # 上一次记录
        last_sov = last_rec.get("sov_pct", 0.0)
        drop_limit = settings.get("drop_threshold_pct", 10.0)
        if last_sov - curr_sov >= drop_limit:
            reasons.append(f"SOV 环比突降 {round(last_sov - curr_sov, 1)}%（上周: {last_sov}% ➔ 本周: {curr_sov}%）")

    # 规则 3: 发现竞品拦截激增
    if curr_intercept > 0 and settings.get("notify_on_intercept", True):
        last_intercept = history_records[-2].get("intercept_count", 0) if len(history_records) >= 2 else 0
        if curr_intercept > last_intercept:
            reasons.append(f"发现新增竞品拦截词（当前 {curr_intercept} 组意图词被竞品占位）")

    # 规则 4: 品牌核心占位词失守识别 (Brand Anchor Loss)
    if cfg and not is_offline:
        brand_name = cfg.get("brand_name", "")
        founder = cfg.get("founder", "")
        # 查找包含品牌名或创始人的核心占位词
        anchor_words = [w for w in [brand_name, founder] if w and len(w) >= 2]
        # 如果项目 outputs 中存在周报，检查占位词是否未获首推
        out_dir = cfg.get("_outputs_dir", "")
        rep_file = os.path.join(out_dir, "05_企业AI可见度与声量追踪周报.md") if out_dir else ""
        if rep_file and os.path.exists(rep_file):
            try:
                with open(rep_file, "r", encoding="utf-8", errors="ignore") as fp:
                    rep_content = fp.read()
                for aw in anchor_words:
                    # 匹配格式: | **...{aw}...** | `...` | ❌ 暂未上榜 | ...
                    if f"| **{aw}**" in rep_content and "❌ 暂未上榜" in rep_content:
                        reasons.append(f"核心品牌占位词【{aw}】未获第一提及（处于失守风险）")
                        break
            except Exception:
                pass

    should_alert = len(reasons) > 0
    summary = "；".join(reasons) if should_alert else "各项指标平稳处于健康区间"
    return should_alert, summary, reasons

def send_webhook_alert(webhook_url: str, project_name: str, reasons_summary: str, metrics: dict, webhook_type: str = "auto", is_test: bool = False) -> tuple:
    """发送 Webhook 告警卡片（支持企微 / 飞书 / 钉钉）"""
    if not webhook_url:
        return False, "未配置 Webhook URL"

    # 自动识别渠道类型
    wtype = webhook_type
    if wtype == "auto":
        if "qyapi.weixin.qq.com" in webhook_url:
            wtype = "wecom"
        elif "open.feishu.cn" in webhook_url:
            wtype = "feishu"
        elif "dingtalk.com" in webhook_url:
            wtype = "dingtalk"
        else:
            wtype = "wecom"

    sov = metrics.get("sov_pct", 0.0)
    top3 = metrics.get("top3_pct", 0.0)
    hit_cnt = metrics.get("prompt_stats", {}).get("hit_count", 0)
    intercept_cnt = metrics.get("prompt_stats", {}).get("intercept_count", 0)
    tag_test = "【测试演练】" if is_test else "【声量异动告警】"

    if wtype == "wecom":
        # 企业微信 Markdown 卡片
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "content": f"""### 🚨 GEO 商业声量监测{tag_test}
> **企业主体**：<font color="info">{project_name}</font>
> **当前 SOV**：<font color="warning">{sov}%</font> ｜ **Top3 推荐率**：{top3}%
> **探测状态**：命中首推 **{hit_cnt}** 组 ｜ 竞品拦截 **{intercept_cnt}** 组
> **异动详情**：<font color="comment">{reasons_summary}</font>

> 💡 **建议处置**：请登录 GEO 控制台查看周报并生成《竞品反向包抄策略》在同位语平台补发截流。
👉 [点击直达 GEO 商业交付工作台](https://geo.baicl.cc)"""
            }
        }
    elif wtype == "feishu":
        # 飞书富文本消息
        payload = {
            "msg_type": "post",
            "content": {
                "post": {
                    "zh_cn": {
                        "title": f"🚨 GEO 商业声量监测{tag_test} - {project_name}",
                        "content": [
                            [{"tag": "text", "text": f"当前 SOV 提及率：{sov}% ｜ Top 3 推荐率：{top3}%\n"}],
                            [{"tag": "text", "text": f"实测态势：命中首推 {hit_cnt} 组 ｜ 竞品拦截 {intercept_cnt} 组\n"}],
                            [{"tag": "text", "text": f"异动详情：{reasons_summary}\n\n"}],
                            [{"tag": "a", "text": "👉 点击直达 GEO 商业交付控制台", "href": "https://geo.baicl.cc"}]
                        ]
                    }
                }
            }
        }
    else:
        # 钉钉 / 通用 Markdown
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "title": f"GEO 声量监测{tag_test}",
                "text": f"### 🚨 GEO 商业声量监测{tag_test}\n**企业**：{project_name}\n**SOV**：{sov}%\n**详情**：{reasons_summary}\n\n[直达工作台](https://geo.baicl.cc)"
            }
        }

    try:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            webhook_url,
            data=body,
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
            res_body = resp.read().decode("utf-8", errors="ignore")
            return True, f"推送成功: {res_body[:100]}"
    except Exception as e:
        return False, f"Webhook 推送失败: {str(e)}"

# ==========================================
# 巡检调度主流程
# ==========================================

def run_patrol_project(project_id: str, notify: bool = True) -> dict:
    """对指定项目执行自动化巡检"""
    print_info(f"⏰ 开始执行项目自动化巡检: [{project_id}]")
    cfg = load_project_config(project_id)
    client_name = cfg.get("client_name", project_id)

    # 1. 运行 Step 5 声量探测与周报生成
    run_monitor(project_id)

    # 2. 提取量化指标
    metrics = extract_monitor_metrics(project_id)

    # 3. 写入历史 SQLite 库
    record_project_history(project_id, metrics)
    history_records = get_project_history(project_id, limit=12)

    # 4. 检查是否触发告警
    settings = load_notification_settings()
    should_alert, summary, _ = check_alert_conditions(metrics, history_records, settings, cfg=cfg)

    alert_sent = False
    alert_msg = ""
    if notify and settings.get("enabled") and settings.get("webhook_url") and should_alert:
        print_warning(f"🚨 项目 [{client_name}] 触发声量异动预警: {summary}")
        ok, msg = send_webhook_alert(
            settings["webhook_url"],
            client_name,
            summary,
            metrics,
            webhook_type=settings.get("webhook_type", "auto")
        )
        alert_sent = ok
        alert_msg = msg
        if ok:
            print_success(f"✅ 已成功向群机器人推送异动告警卡片")
        else:
            print_warning(f"⚠️ 告警卡片推送失败: {msg}")

    return {
        "project_id": project_id,
        "client_name": client_name,
        "sov_pct": metrics.get("sov_pct", 0.0),
        "should_alert": should_alert,
        "alert_summary": summary,
        "alert_sent": alert_sent,
        "alert_msg": alert_msg,
        "timestamp": int(time.time())
    }

def run_patrol_all(notify: bool = True) -> list:
    """全量项目自动化巡检"""
    print_banner("启动全项目无人值守自动化巡检中枢")
    results = []
    if os.path.exists(PROJECTS_DIR):
        for item in sorted(os.listdir(PROJECTS_DIR)):
            if item.startswith(".") or item == "_template":
                continue
            p_dir = os.path.join(PROJECTS_DIR, item)
            if os.path.isdir(p_dir):
                try:
                    res = run_patrol_project(item, notify=notify)
                    results.append(res)
                except Exception as e:
                    print_warning(f"项目 [{item}] 巡检异常: {e}")

    # 更新最近巡检时间
    settings = load_notification_settings()
    settings["last_patrol_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_notification_settings(settings)

    print_success(f"🎉 全项目自动化巡检完成！共巡检 {len(results)} 个活跃项目。")
    return results

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != "--all":
        run_patrol_project(sys.argv[1], notify=True)
    else:
        run_patrol_all(notify=True)
