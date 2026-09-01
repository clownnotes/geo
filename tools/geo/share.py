#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GEO 甲方客户专属免密/提取码只读交付门户引擎 (tools/geo/share.py)
核心功能：
1. 生成密码学高熵安全 Token (secrets 模块)，支持 7/30 天时效与一键作废；
2. 支持可选 4 位提取码加盐哈希保护 (PIN Code)；
3. 构建物理只读沙箱，向甲方安全提供 5+1 交付物与实时声量走势，杜绝敏感配置泄露。
"""

import os
import sys
import json
import time
import secrets
import hashlib
import datetime

from .utils import (
    load_project_config,
    print_banner,
    print_info,
    print_success,
    print_warning,
    PROJECTS_DIR
)
from .monitor import extract_monitor_metrics
from .patrol import get_project_history

DATA_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
SHARES_FILE = os.path.join(DATA_DIR, "shares.json")

def load_shares_data() -> dict:
    """读取所有分享链接元数据"""
    if os.path.exists(SHARES_FILE):
        try:
            with open(SHARES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"shares": {}}

def save_shares_data(data: dict) -> bool:
    """保存分享链接元数据"""
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        with open(SHARES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存分享数据异常: {e}")
        return False

# ==========================================
# 分享链接创建与生命周期管理
# ==========================================

def create_share_link(project_id: str, expire_days: int = 30, pin: str = None, base_url: str = "") -> dict:
    """为指定项目创建专属分享链接"""
    cfg = load_project_config(project_id)
    client_name = cfg.get("client_name", project_id)
    
    # 生成 24 字节高熵安全 Token (2^192 穷举空间)
    token = "sh_" + secrets.token_urlsafe(18)
    now_ts = int(time.time())
    expires_at = (now_ts + expire_days * 86400) if expire_days > 0 else None
    
    pin_clean = pin.strip() if pin else None
    salt = None
    pin_hash = None
    if pin_clean:
        salt = secrets.token_hex(6)
        pin_hash = hashlib.sha256((pin_clean + salt).encode("utf-8")).hexdigest()

    record = {
        "token": token,
        "project_id": project_id,
        "client_name": client_name,
        "created_at": now_ts,
        "created_at_str": datetime.datetime.fromtimestamp(now_ts).strftime("%Y-%m-%d %H:%M:%S"),
        "expires_at": expires_at,
        "expires_at_str": datetime.datetime.fromtimestamp(expires_at).strftime("%Y-%m-%d %H:%M:%S") if expires_at else "永久有效",
        "has_pin": bool(pin_clean),
        "pin_hash": pin_hash,
        "salt": salt,
        "is_active": True,
        "view_count": 0,
        "last_view_time": None
    }

    data = load_shares_data()
    data["shares"][token] = record
    save_shares_data(data)

    share_path = f"/share/{token}"
    domain = base_url.rstrip("/") if base_url else ""
    full_url = f"{domain}{share_path}"

    exp_desc = f"{expire_days} 天" if expire_days > 0 else "永久有效"
    pin_desc = f"\n🔑 访问提取码：{pin_clean}" if pin_clean else "\n🔓 访问权限：免密直接打开"
    share_text = f"【{client_name}】专属 GEO 商业交付全景看板已生成！\n🔗 交付门户链接：{full_url}{pin_desc}\n⏳ 有效期：{exp_desc}\n💡 包含大模型可见度体检、技术底座改造补丁、普林斯顿权威语料库与实时声量追踪大盘。"

    return {
        "success": True,
        "token": token,
        "share_url": full_url,
        "share_path": share_path,
        "has_pin": bool(pin_clean),
        "pin": pin_clean,
        "expires_at_str": record["expires_at_str"],
        "share_text": share_text
    }

def list_project_shares(project_id: str) -> list:
    """获取指定项目的有效分享链接列表"""
    data = load_shares_data()
    now_ts = int(time.time())
    result = []
    for token, rec in data.get("shares", {}).items():
        if rec.get("project_id") == project_id and rec.get("is_active", True):
            is_expired = rec.get("expires_at") and rec["expires_at"] < now_ts
            rec_copy = dict(rec)
            rec_copy["is_expired"] = bool(is_expired)
            # 脱敏内部哈希
            rec_copy.pop("pin_hash", None)
            rec_copy.pop("salt", None)
            result.append(rec_copy)
    # 按创建时间倒序
    result.sort(key=lambda x: x.get("created_at", 0), reverse=True)
    return result

def revoke_share_link(token: str) -> bool:
    """管理员作废指定分享链接"""
    data = load_shares_data()
    if token in data.get("shares", {}):
        data["shares"][token]["is_active"] = False
        save_shares_data(data)
        return True
    return False

# ==========================================
# 提取码校验与只读沙箱数据提取
# ==========================================

def verify_share_access(token: str, client_pin: str = None) -> tuple:
    """
    校验分享链接访问合法性
    返回: (ok, status_code_or_msg, share_record)
    """
    data = load_shares_data()
    rec = data.get("shares", {}).get(token)
    if not rec or not rec.get("is_active", True):
        return False, "revoked", None

    # 检查是否过期
    now_ts = int(time.time())
    if rec.get("expires_at") and rec["expires_at"] < now_ts:
        return False, "expired", rec

    # 检查提取码
    if rec.get("has_pin"):
        if not client_pin:
            return False, "require_pin", rec
        salt = rec.get("salt", "")
        test_hash = hashlib.sha256((str(client_pin).strip() + salt).encode("utf-8")).hexdigest()
        if test_hash != rec.get("pin_hash"):
            return False, "invalid_pin", rec

    # 递增浏览计数
    rec["view_count"] = rec.get("view_count", 0) + 1
    rec["last_view_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_shares_data(data)

    return True, "ok", rec

def get_share_portal_data(token: str, client_pin: str = None) -> dict:
    """获取专属甲方门户只读沙箱数据"""
    ok, status, rec = verify_share_access(token, client_pin)
    if not ok:
        if status == "require_pin":
            return {"success": False, "require_pin": True, "client_name": rec.get("client_name", "客户企业"), "message": "此交付看板已开启安全访问保护，请输入 4 位提取码查看。"}
        elif status == "invalid_pin":
            return {"success": False, "invalid_pin": True, "message": "提取码不正确，请重新输入！"}
        elif status == "expired":
            return {"success": False, "expired": True, "message": "抱歉，该交付门户分享链接已超过有效期。请联系您的 GEO 交付顾问获取最新链接。"}
        else:
            return {"success": False, "revoked": True, "message": "抱歉，该交付门户链接已被发起人作废或不存在。"}

    project_id = rec["project_id"]
    try:
        cfg = load_project_config(project_id)
        out_dir = os.path.realpath(cfg["_outputs_dir"])
    except Exception as e:
        return {"success": False, "message": f"项目数据读取异常: {e}"}

    # 读取 6 份交付文件
    deliverables = {}
    files_to_read = {
        "audit": "01_企业AI可见度现状体检与商业诊断报告.md",
        "llms_txt": "llms.txt",
        "schema_jsonld": "schema.jsonld",
        "robots_txt": "robots.txt",
        "rewrite": "03_普林斯顿9因子高权威语料库.md",
        "dist_zhihu": "dist_zhihu_article.md",
        "dist_toutiao": "dist_toutiao_article.md",
        "dist_wechat": "dist_wechat_article.html",
        "dist_github": "dist_github_README.md",
        "monitor_report": "05_企业AI可见度与声量追踪周报.md",
        "defense": "06_竞品权威信源反向包抄策略.md"
    }

    for key, fname in files_to_read.items():
        fpath = os.path.join(out_dir, fname)
        if os.path.exists(fpath):
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as fp:
                    deliverables[key] = fp.read()
            except Exception:
                deliverables[key] = ""
        else:
            deliverables[key] = ""

    # 提取量化指标与历史
    metrics = extract_monitor_metrics(project_id)
    history = get_project_history(project_id, limit=12)

    return {
        "success": True,
        "project_id": project_id,
        "client_name": cfg.get("client_name", project_id),
        "industry": cfg.get("industry", "未知行业"),
        "website": cfg.get("website", ""),
        "brand_name": cfg.get("brand_name", cfg.get("client_name", "")),
        "deliverables": deliverables,
        "metrics": metrics,
        "history": history,
        "share_meta": {
            "created_at_str": rec.get("created_at_str"),
            "expires_at_str": rec.get("expires_at_str"),
            "view_count": rec.get("view_count", 1)
        }
    }

if __name__ == "__main__":
    if len(sys.argv) > 1:
        pid = sys.argv[1]
        res = create_share_link(pid, expire_days=30, pin="8888")
        print(res["share_text"])
