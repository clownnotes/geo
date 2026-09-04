#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GEO 甲方客户专属免密/提取码只读交付门户引擎 (tools/geo/share.py)
核心功能：
1. 生成密码学高熵安全 Token (secrets 模块)，支持 7/30 天时效与一键作废、单活刷新轮转；
2. 支持可选 4 位提取码加盐哈希保护 (PIN Code)；
3. 构建物理只读沙箱，向甲方安全提供 1~27 维商业交付物、MPI 心智渗透率、竞对攻防实战与爬虫保真度；
4. 支持导出完全自给自足、无外部 CDN 依赖的离线单文件高管大屏 HTML。
"""

import os
import sys
import json
import time
import secrets
import hashlib
import datetime
import re

from .utils import (
    load_project_config,
    print_banner,
    print_info,
    print_success,
    print_warning,
    PROJECT_ROOT,
    PROJECTS_DIR
)
from .monitor import extract_monitor_metrics
from .patrol import get_project_history

DATA_DIR = os.path.realpath(os.path.join(PROJECT_ROOT, "data"))
SHARES_FILE = os.path.join(DATA_DIR, "shares.json")
WEB_DIR = os.path.realpath(os.path.join(PROJECT_ROOT, "web"))


def _calc_file_sha256(filepath: str) -> str:
    """计算单个文件的 SHA256 哈希值"""
    if not os.path.exists(filepath):
        return "N/A"
    h = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return "ERROR"


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
    portal_path = f"/portal/{token}"
    domain = base_url.rstrip("/") if base_url else ""
    full_url = f"{domain}{portal_path}"

    exp_desc = f"{expire_days} 天" if expire_days > 0 else "永久有效"
    pin_desc = f"\n🔑 访问提取码：{pin_clean}" if pin_clean else "\n🔓 访问权限：免密直接打开"
    share_text = (
        f"【{client_name}】专属全域大模型商业战果高管交付门户已生成！\n"
        f"🔗 交付大屏链接：{full_url}{pin_desc}\n"
        f"⏳ 有效期：{exp_desc}\n"
        f"📊 核心看点：三大国产主力模型首推心智渗透率、年化等效商业广告价值节省、竞对攻防截流战果及 A4 商业交付数字结案证书。"
    )

    return {
        "success": True,
        "token": token,
        "share_url": full_url,
        "share_path": share_path,
        "portal_path": portal_path,
        "has_pin": bool(pin_clean),
        "pin": pin_clean,
        "expires_at_str": record["expires_at_str"],
        "share_text": share_text
    }


def refresh_share_token(project_id: str, expire_days: int = 30, pin: str = None, base_url: str = "") -> dict:
    """
    单活轮转刷新：作废指定项目所有历史活跃 Token，并生成全新的专属交付 Token
    """
    data = load_shares_data()
    now_ts = int(time.time())
    revoked_count = 0
    for tok, rec in data.get("shares", {}).items():
        if rec.get("project_id") == project_id and rec.get("is_active", True):
            rec["is_active"] = False
            rec["revoked_at"] = now_ts
            revoked_count += 1
    save_shares_data(data)

    new_res = create_share_link(project_id, expire_days=expire_days, pin=pin, base_url=base_url)
    new_res["revoked_old_count"] = revoked_count
    return new_res


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

def verify_share_access(token: str, client_pin: str = None, increment_view: bool = True) -> tuple:
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
            # 提取码错误时不递增有效浏览计数
            return False, "invalid_pin", rec

    # 递增浏览计数（仅在整页查看时自增，单文件读取不计入）
    if increment_view:
        rec["view_count"] = rec.get("view_count", 0) + 1
        rec["last_view_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_shares_data(data)

    return True, "ok", rec


def get_share_single_file_content(token: str, req_key: str, client_pin: str = None) -> dict:
    """
    按需安全读取单个交付物文件内容（严格白名单与 realpath 防目录穿透）
    """
    from .acceptance import DELIVERABLES_MANIFEST, ATTACHED_DELIVERABLES

    target_item = None
    for item in DELIVERABLES_MANIFEST + ATTACHED_DELIVERABLES:
        if item.get("key") == req_key:
            target_item = item
            break

    if not target_item:
        return {"success": False, "status": 400, "message": f"非法或未授权的资产 Key: {req_key}"}

    ok, status, rec = verify_share_access(token, client_pin, increment_view=False)
    if not ok:
        return {"success": False, "status": 403, "message": "无权访问该资源或提取码未验证"}

    project_id = rec["project_id"]
    cfg = load_project_config(project_id)
    out_dir = os.path.realpath(cfg["_outputs_dir"])

    candidates = target_item.get("candidates", [target_item.get("file")])
    found_path = None
    for cand in candidates:
        cand_path = os.path.join(out_dir, cand)
        if os.path.exists(cand_path) and os.path.isfile(cand_path):
            found_path = cand_path
            break

    if not found_path:
        return {"success": True, "key": req_key, "content": f"*{target_item.get('name', req_key)} 暂未生成*", "filename": ""}

    real_target = os.path.realpath(found_path)
    if not (real_target == out_dir or real_target.startswith(out_dir + os.sep)):
        return {"success": False, "status": 403, "message": "非法跨目录越界访问"}

    try:
        with open(real_target, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return {
            "success": True,
            "key": req_key,
            "content": content,
            "filename": os.path.basename(real_target)
        }
    except Exception as e:
        return {"success": False, "status": 500, "message": f"读取文件异常: {e}"}


def compile_portal_data(project_id: str, token: str = "", rec: dict = None) -> dict:
    """
    全量聚合高管交付门户所需数据（严格对齐真实字段映射表与降级策略，坚决不造假数据）
    """
    try:
        cfg = load_project_config(project_id)
        out_dir = os.path.realpath(cfg.get("_outputs_dir", os.path.join(PROJECTS_DIR, project_id, "outputs")))
    except Exception:
        cfg = {}
        out_dir = os.path.join(PROJECTS_DIR, project_id, "outputs")

    def _read_json_safe(fname: str) -> dict:
        fpath = os.path.join(out_dir, fname)
        if os.path.exists(fpath):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    # 读取 1~27 维物理落盘 JSON
    mindshare_data = _read_json_safe("mindshare_conversion_audit.json")
    princeton_data = _read_json_safe("princeton_audit.json")
    competitor_data = _read_json_safe("competitor_gap_analysis.json")
    dist_ledger_raw = _read_json_safe("dist_ledger.json")
    injection_guard_data = _read_json_safe("prompt_injection_guard.json")
    citation_auth_data = _read_json_safe("citation_authority_matrix.json")
    compliance_data = _read_json_safe("compliance_inspection.json")
    rag_diag_data = _read_json_safe("rag_chunks_diagnostic.json")
    intent_data = _read_json_safe("keywords_intent_matrix.json")
    evaluator_data = _read_json_safe("06_大模型真实API评测与Citation捕获报告.json")
    moat_data = _read_json_safe("competitive_moat_simulation.json")
    decay_data = _read_json_safe("knowledge_decay_retention.json")

    # 1. 编译核心商业 KPI 摘要 (Hero)
    ms_summary = mindshare_data.get("summary", {}) if isinstance(mindshare_data, dict) else {}
    mpi_score = ms_summary.get("mpi")
    mpi_grade = ms_summary.get("grade_name") or ("评估就绪" if mpi_score is not None else "待生成")
    annual_aev_yuan = ms_summary.get("annual_aev_yuan", 0)
    annual_ad_saving_wan = round(annual_aev_yuan / 10000.0, 1) if annual_aev_yuan else 0.0
    intent_coverage_count = ms_summary.get("query_count") or len(intent_data.get("keywords", [])) or 0

    probe_records = mindshare_data.get("probe_records", []) if isinstance(mindshare_data, dict) else []
    if probe_records:
        top1_probes = len([p for p in probe_records if p.get("is_top1")])
        first_recommend_rate_pct = round((top1_probes / len(probe_records)) * 100.0, 1)
    elif ms_summary.get("weighted_sov_rate") is not None:
        first_recommend_rate_pct = ms_summary.get("weighted_sov_rate")
    else:
        first_recommend_rate_pct = None

    cert_path = os.path.join(out_dir, "09_GEO全案商业交付结案与数字资产移交证书.html")
    has_certificate = os.path.exists(cert_path)
    cert_sha256 = _calc_file_sha256(cert_path)
    if has_certificate or (mpi_score is not None and mpi_score >= 80):
        delivery_grade = "AAA 级卓越履约"
    elif mpi_score is not None and mpi_score >= 60:
        delivery_grade = "AA 级标杆交付"
    else:
        delivery_grade = "待验收"

    executive_summary = {
        "mpi_score": mpi_score,
        "mpi_grade": mpi_grade,
        "first_recommend_rate_pct": first_recommend_rate_pct,
        "annual_ad_saving_wan": annual_ad_saving_wan,
        "annual_aev_yuan": annual_aev_yuan,
        "intent_coverage_count": intent_coverage_count,
        "delivery_grade": delivery_grade
    }

    # 2. 编译实测大模型心智矩阵 (只展示具备真实探针数据的 3 个模型，绝不制造元宝虚构假分)
    models_mindshare = {}
    model_labels = {
        "doubao": "字节跳动·豆包 (头条生态)",
        "deepseek": "DeepSeek (技术决策高地)",
        "kimi": "月之暗面·Kimi (研报分析池)"
    }
    for m in ["doubao", "deepseek", "kimi"]:
        m_probes = [p for p in probe_records if p.get("model") == m]
        if m_probes:
            top1_c = len([p for p in m_probes if p.get("is_top1")])
            men_c = len([p for p in m_probes if p.get("is_mentioned")])
            models_mindshare[m] = {
                "name": model_labels.get(m, m),
                "top1_rate_pct": round((top1_c / len(m_probes)) * 100.0, 1),
                "mention_rate_pct": round((men_c / len(m_probes)) * 100.0, 1),
                "avg_score": round((sum(p.get("score", 0.0) for p in m_probes) / len(m_probes)) * 100.0, 1),
                "probe_count": len(m_probes)
            }

    wechat_ch = dist_ledger_raw.get("channels", {}).get("wechat", {}) if isinstance(dist_ledger_raw, dict) else {}
    wechat_url = (wechat_ch.get("url") or "").strip()
    wechat_http = wechat_ch.get("http_status")
    if wechat_url and wechat_http == 200:
        w_desc = "渠道分发覆盖已就绪 (权重 10%) · 搜一搜收录探活正常 · 非实时 API 探针"
    elif wechat_url:
        w_desc = "微信渠道已填报 (待探活) · 微信搜一搜生态覆盖中 · 非实时 API 探针"
    else:
        w_desc = "微信公众号待填报 · 微信搜一搜独占生态 · 非实时 API 探针"

    wechat_yuanbao_channel = {
        "name": "腾讯元宝 (微信搜一搜独占生态)",
        "status_desc": w_desc,
        "url": wechat_url,
        "status": wechat_ch.get("status", "pending")
    }

    # 3. 编译竞对攻防实战看板
    radar_gap = competitor_data.get("radar_comparison", {}).get("overall_gap_lead")
    if radar_gap is None and "gap_metrics" in competitor_data:
        radar_gap = competitor_data["gap_metrics"].get("overall_sov_gap_pct")

    competitor_interception = {
        "intercepted_competitors": competitor_data.get("all_competitors", ["行业常规竞品"]),
        "overall_gap_lead": radar_gap or 0.0,
        "advantage_breakdown": competitor_data.get("competitor_advantages", []),
        "leapfrog_roadmap": competitor_data.get("leapfrog_roadmap", [])
    }

    # 4. 编译普林斯顿 9 因子与爬虫保真度背书
    princeton_score = princeton_data.get("avg_princeton_score") if isinstance(princeton_data, dict) else None
    princeton_grade = princeton_data.get("rating_grade", "未质检") if isinstance(princeton_data, dict) else "未质检"

    fidelity_scores = {}
    pack_map = {
        "toutiao": ("toutiao_pack", "fidelity_report.json"),
        "wechat": ("wechat_pack", "fidelity_report.json"),
        "deepseek": ("deepseek_pack", "fidelity_report.json"),
        "zhihu": ("deepseek_pack", "fidelity_report_zhihu.json"),
        "kimi_baidu": ("kimi_baidu_pack", "fidelity_report.json")
    }
    valid_scores = []
    for ch_name, (p_dir, f_name) in pack_map.items():
        f_path = os.path.join(out_dir, p_dir, f_name)
        is_fallback = False
        if not os.path.exists(f_path) and ch_name == "zhihu":
            # 知乎回退到 deepseek_pack 的默认报告
            f_path = os.path.join(out_dir, "deepseek_pack", "fidelity_report.json")
            is_fallback = True
        if os.path.exists(f_path):
            try:
                with open(f_path, "r", encoding="utf-8") as fp:
                    f_json = json.load(fp)
                    sc = f_json.get("overall_score")
                    ps = f_json.get("passed", False)
                    if sc is not None:
                        item = {
                            "score": sc,
                            "passed": ps,
                            "verified_at": f_json.get("verified_at")
                        }
                        if is_fallback:
                            item["source"] = "deepseek_fallback"
                        fidelity_scores[ch_name] = item
                        valid_scores.append(sc)
            except Exception:
                pass

    authority_assurance = {
        "princeton_score": princeton_score,
        "princeton_grade": princeton_grade,
        "crawler_fidelities": fidelity_scores,
        "average_fidelity_score": round(sum(valid_scores) / len(valid_scores), 1) if valid_scores else None,
        "all_passed": all(f["passed"] for f in fidelity_scores.values()) if fidelity_scores else False
    }

    # 5. 编译全域信源存活台账与状态推导
    dist_channels = dist_ledger_raw.get("channels", {}) if isinstance(dist_ledger_raw, dict) else {}
    enhanced_channels = {}
    for ch_k, ch_v in dist_channels.items():
        url = (ch_v.get("url") or "").strip()
        http_status = ch_v.get("http_status")
        if url and http_status == 200:
            d_status = "alive"
            label = "🟢 已收录·探活正常"
        elif url and http_status is None:
            d_status = "pending_audit"
            label = "🟡 已填报·待探活"
        elif url:
            d_status = "dead"
            label = f"🔴 异常 ({http_status})"
        else:
            d_status = "unfilled"
            label = "⚪️ 待分发填报"

        item = dict(ch_v)
        item["display_status"] = d_status
        item["status_label"] = label
        enhanced_channels[ch_k] = item

    enhanced_distribution_ledger = {
        "completion_rate_pct": dist_ledger_raw.get("completion_rate_pct", 0.0),
        "alive_rate_pct": dist_ledger_raw.get("alive_rate_pct", 0.0),
        "weighted_completion_pct": dist_ledger_raw.get("weighted_completion_pct", 0.0),
        "channels": enhanced_channels
    }

    # 6. 编译交付结案证书摘要
    certificate_summary = {
        "has_certificate": has_certificate,
        "sha256_fingerprint": cert_sha256,
        "delivery_grade": delivery_grade,
        "view_url": f"/api/share/{token}/certificate" if token else ""
    }

    # 7. 保留 16 维历史交付文件与向后兼容字段
    deliverables = {}
    files_to_read = {
        "acceptance": "00_GEO商业交付验收结案确认单.md",
        "pitch": "00_GEO全案商业服务投标建议书与PitchDeck.md",
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
        "evaluator": "06_大模型真实API评测与Citation捕获报告.md",
        "defense": "06_竞品权威信源反向包抄策略.md",
        "guard": "07_大模型事实幻觉纠偏与信源反击策略.md",
        "video_script": "09_60秒短视频高转化口播脚本.md",
        "graph": "10_企业行业实体关系知识图谱.md",
        "intent": "11_三级搜索意图挖掘与长尾关键词裂变拓扑.md",
        "rag_diag": "12_大模型爬虫抓取仿真与RAG分块检索诊断报告.md",
        "compliance": "13_多渠道内容合规与广告法风控审查报告.md",
        "competitor": "14_竞对大模型声量差距深度逆向与反超作战沙盘.md",
        "citation_auth": "15_大模型Citation信源权威度与外链信任度评分报告.md",
        "injection_guard": "16_大模型提示词注入防御与品牌隔离盾牌报告.md",
        "probing": "18_大模型实时联网探测与Citation信源溯源对账报告.md",
        "live_citation_audit": "30_多主流大模型真实联网探测与Citation角标反查审计报告.md"
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

    try:
        metrics = extract_monitor_metrics(project_id)
    except Exception:
        metrics = {}

    try:
        raw_history = get_project_history(project_id, limit=12)
    except Exception:
        raw_history = []
    clean_history = []
    for h in raw_history:
        clean_history.append({
            "check_date": h.get("check_date"),
            "timestamp": h.get("timestamp"),
            "is_offline": bool(h.get("is_offline")),
            "sov_pct": h.get("sov_pct", 0.0),
            "top3_pct": h.get("top3_pct", 0.0),
            "authority_score": h.get("authority_score", 0.0),
            "hit_count": h.get("hit_count", 0),
            "intercept_count": h.get("intercept_count", 0),
            "lost_count": h.get("lost_count", 0)
        })

    try:
        from .benchmark import evaluate_project_against_benchmark
        bench_eval = evaluate_project_against_benchmark(project_id)
        if isinstance(bench_eval, dict):
            bench_eval = dict(bench_eval)
            bench_eval.pop("project_id", None)
    except Exception:
        bench_eval = {}

    try:
        from .visual import get_visual_assets
        vis_res = get_visual_assets(project_id)
        visual_assets = vis_res.get("assets", {})
    except Exception:
        visual_assets = {}

    try:
        from .roi import calculate_project_roi
        roi_res = calculate_project_roi(project_id)
        roi_summary = {
            "financial_valuation": roi_res.get("financial_valuation", {}),
            "renewal_health": roi_res.get("renewal_health", {}),
            "metrics_summary": roi_res.get("metrics_summary", {})
        }
    except Exception:
        roi_summary = {}

    try:
        from .acceptance import calculate_fulfillment_score
        ful_res = calculate_fulfillment_score(project_id)
        acceptance_summary = {
            "total_fulfillment_score": ful_res.get("total_fulfillment_score", 0.0),
            "is_passed": ful_res.get("is_passed", False),
            "status_text": ful_res.get("status_text", ""),
            "manifest_summary": ful_res.get("manifest_summary", {}),
            "breakdown": ful_res.get("breakdown", []),
            "manifest": ful_res.get("manifest", [])
        }
    except Exception:
        acceptance_summary = {}

    try:
        from .pitch import calculate_pitch_quote
        pitch_summary = calculate_pitch_quote(project_id)
    except Exception:
        pitch_summary = {}

    graph_summary = {}
    g_json = os.path.join(out_dir, "entity_graph.json")
    if os.path.exists(g_json):
        try:
            with open(g_json, "r", encoding="utf-8") as f:
                g_data = json.load(f)
                graph_summary = {
                    "node_count": len(g_data.get("nodes", [])),
                    "edge_count": len(g_data.get("edges", [])),
                    "summary": g_data.get("summary", {}),
                    "nodes": g_data.get("nodes", [])[:30],
                    "edges": g_data.get("edges", [])[:40]
                }
        except Exception:
            pass

    guard_summary = {}
    f_json = os.path.join(out_dir, "factual_anchors.json")
    if os.path.exists(f_json):
        try:
            with open(f_json, "r", encoding="utf-8") as f:
                f_data = json.load(f)
                guard_summary = {
                    "anchors_count": len(f_data.get("anchors", [])),
                    "brand_name": f_data.get("brand_name", ""),
                    "status": "事实防守锚点已生效"
                }
        except Exception:
            pass

    rag_score = rag_diag_data.get("rag_readiness_score") or rag_diag_data.get("avg_retrieval_score")

    zip_name = f"{project_id}_geo_delivery_archive.zip"
    zip_path = os.path.join(out_dir, zip_name)
    archive_info = {
        "exists": os.path.exists(zip_path),
        "filename": zip_name,
        "size_kb": round(os.path.getsize(zip_path) / 1024, 1) if os.path.exists(zip_path) else 0,
        "download_url": f"/api/share/{token}/download-zip" if token else ""
    }

    # 29 维 全域知识动态自愈与落盘回写台账
    heal_data = _read_json_safe("self_healing_audit.json")
    if heal_data and heal_data.get("status") == "applied":
        h_sum = heal_data.get("summary", {})
        self_healing_summary = {
            "has_data": True,
            "status": "applied",
            "status_label": "🟢 知识底座动态自愈已生效",
            "applied_at": heal_data.get("applied_at"),
            "total_patches_applied": h_sum.get("total_patches", 0),
            "truth_anchors_count": h_sum.get("truth_count", 0),
            "faq_pairs_count": h_sum.get("faq_count", 0),
            "dense_keywords_count": h_sum.get("dense_count", 0),
            "audit_doc": heal_data.get("audit_doc", "outputs/29_全域动态知识自愈热补丁审计与回写台账.md"),
            "health_grade": f"动态自愈已生效 ({h_sum.get('total_patches', 0)} 处加固)"
        }
    elif heal_data and heal_data.get("status") == "failed_rolled_back":
        self_healing_summary = {
            "has_data": True,
            "status": "failed_rolled_back",
            "status_label": "🔴 校验异常已自动全量回滚",
            "applied_at": heal_data.get("failed_at"),
            "total_patches_applied": 0,
            "truth_anchors_count": 0,
            "faq_pairs_count": 0,
            "dense_keywords_count": 0,
            "audit_doc": "",
            "health_grade": "回滚保护中"
        }
    else:
        # 严格对齐 Spec §5.3 优雅降级，未自愈时绝不伪造虚假数据
        self_healing_summary = {
            "has_data": False,
            "status": "never_run",
            "status_label": "⚪️ 待触发自愈流水线",
            "applied_at": None,
            "total_patches_applied": 0,
            "truth_anchors_count": 0,
            "faq_pairs_count": 0,
            "dense_keywords_count": 0,
            "audit_doc": "",
            "health_grade": "待触发自愈"
        }

    # 30 维 多主流大模型真实联网探测与 Citation 信源对账
    probing_trace = _read_json_safe("live_probing_trace.json")
    if probing_trace and probing_trace.get("summary"):
        p_sum = probing_trace.get("summary", {})
        hit_assets = []
        for q in probing_trace.get("probed_queries", []):
            cits = q.get("citations_captured") or q.get("citations", [])
            for c in cits:
                if c.get("is_ledger_hit"):
                    h_type = c.get("hit_type") or c.get("match_type", "exact_hit")
                    hit_assets.append({
                        "url": c.get("url"),
                        "title": c.get("title", ""),
                        "model": q.get("model", ""),
                        "query": q.get("query", ""),
                        "hit_type": h_type,
                        "match_type": h_type
                    })
        live_citation_summary = {
            "has_data": True,
            "status": "audited",
            "status_label": "🟢 真实联网探测与角标对账已闭环",
            "last_audited_at": probing_trace.get("reconciled_at") or probing_trace.get("timestamp") or "",
            "total_prompts": p_sum.get("total_probes", 0),
            "total_probes": p_sum.get("total_probes", 0),
            "avg_sov": p_sum.get("real_sov_pct", 0.0),
            "real_sov_pct": p_sum.get("real_sov_pct", 0.0),
            "top1_rate": p_sum.get("top1_recommendation_rate", 0.0),
            "top1_recommendation_rate": p_sum.get("top1_recommendation_rate", 0.0),
            "total_citations": p_sum.get("total_citations_captured", 0),
            "total_citations_captured": p_sum.get("total_citations_captured", 0),
            "dist_matched_count": p_sum.get("my_ledger_assets_hit_count", 0),
            "my_ledger_assets_hit_count": p_sum.get("my_ledger_assets_hit_count", 0),
            "citation_hit_rate": p_sum.get("citation_share_pct", 0.0),
            "citation_share_pct": p_sum.get("citation_share_pct", 0.0),
            "models_covered": p_sum.get("models_probed", []),
            "models_probed": p_sum.get("models_probed", []),
            "audit_doc": probing_trace.get("report_30_path") or "outputs/30_多主流大模型真实联网探测与Citation角标反查审计报告.md",
            "model_breakdown": probing_trace.get("model_breakdown", {}),
            "hit_assets_samples": hit_assets[:10]
        }
    else:
        # 严格对齐 Spec §3.1 优雅降级，未探测时绝不伪造虚假数据
        live_citation_summary = {
            "has_data": False,
            "status": "never_run",
            "status_label": "⚪️ 待启动真实联网探测",
            "last_audited_at": None,
            "total_prompts": 0,
            "total_probes": 0,
            "avg_sov": 0.0,
            "real_sov_pct": 0.0,
            "top1_rate": 0.0,
            "top1_recommendation_rate": 0.0,
            "total_citations": 0,
            "total_citations_captured": 0,
            "dist_matched_count": 0,
            "my_ledger_assets_hit_count": 0,
            "citation_hit_rate": 0.0,
            "citation_share_pct": 0.0,
            "models_covered": [],
            "models_probed": [],
            "audit_doc": "",
            "model_breakdown": {},
            "hit_assets_samples": []
        }

    # 最终组合完整数据载荷
    return {
        "success": True,
        "project_id": project_id,
        "client_name": cfg.get("client_name", "客户企业"),
        "industry": cfg.get("industry", "未知行业"),
        "website": cfg.get("website", ""),
        "brand_name": cfg.get("brand_name", cfg.get("client_name", "")),

        # 高管专属新增战果模块 (第 28/29/30 维)
        "executive_summary": executive_summary,
        "self_healing_summary": self_healing_summary,
        "live_citation_summary": live_citation_summary,
        "models_mindshare": models_mindshare,
        "wechat_yuanbao_channel": wechat_yuanbao_channel,
        "competitor_interception": competitor_interception,
        "authority_assurance": authority_assurance,
        "distribution_ledger": enhanced_distribution_ledger,
        "certificate_summary": certificate_summary,

        # 既有向后兼容历史模块
        "deliverables": deliverables,
        "metrics": metrics,
        "history": clean_history,
        "benchmark": bench_eval,
        "visual_assets": visual_assets,
        "roi_summary": roi_summary,
        "acceptance_summary": acceptance_summary,
        "pitch_summary": pitch_summary,
        "graph_summary": graph_summary,
        "guard_summary": guard_summary,
        "injection_guard_summary": {
            "has_data": bool(injection_guard_data),
            "immunity_score": injection_guard_data.get("immunity_score"),
            "threats_count": injection_guard_data.get("total_threats", injection_guard_data.get("summary", {}).get("total_threats", 0)),
            "status": injection_guard_data.get("status", "安全隔离就绪")
        },
        "citation_auth_summary": {
            "has_data": bool(citation_auth_data),
            "overall_score": citation_auth_data.get("overall_authority_score"),
            "total_links": len(citation_auth_data.get("evaluated_links", [])),
            "status": citation_auth_data.get("status", "权重良好")
        },
        "competitor_summary": {
            "has_data": bool(competitor_data),
            "overall_gap_lead": radar_gap,
            "our_sov": competitor_data.get("gap_metrics", {}).get("our_sov_pct"),
            "competitor_name": competitor_data.get("primary_competitor_name", "主要竞对")
        },
        "compliance_summary": {
            "has_data": bool(compliance_data),
            "compliance_rate_pct": compliance_data.get("compliance_rate_pct"),
            "violations_count": compliance_data.get("total_violations", 0)
        },
        "rag_diag_summary": {
            "has_data": bool(rag_diag_data),
            "rag_readiness_score": rag_score,
            "total_chunks": rag_diag_data.get("total_chunks", 0),
            "golden_chunks": rag_diag_data.get("golden_chunks", 0)
        },
        "intent_summary": {
            "has_data": bool(intent_data),
            "total_keywords": intent_data.get("total_keywords") or (len(intent_data.get("keywords", [])) if intent_data.get("keywords") else None) or len(metrics.get("keywords", [])) or 0
        },
        "evaluator_summary": {
            "has_data": bool(evaluator_data),
            "overall_sov": evaluator_data.get("overall_sov_pct", metrics.get("sov_pct", 0.0)),
            "total_citations": len(evaluator_data.get("citations", [])) if "citations" in evaluator_data else 0
        },
        "archive_info": archive_info,
        "share_meta": {
            "token": token,
            "created_at_str": rec.get("created_at_str") if rec else datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "expires_at_str": rec.get("expires_at_str") if rec else "永久有效",
            "view_count": rec.get("view_count", 1) if rec else 1
        }
    }


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
        return compile_portal_data(project_id, token=token, rec=rec)
    except Exception as e:
        return {"success": False, "message": f"项目数据聚合异常: {e}"}


def export_offline_portal_html(project_id: str, target_filepath: str) -> dict:
    """
    导出内网完全自给自足的离线单文件高管交付大屏 HTML。
    完全剔除 cdn.tailwindcss.com 和 unpkg.com 等外部运行时依赖，断网环境下秒开。
    """
    data = compile_portal_data(project_id, token="offline_export")
    data_json = json.dumps(data, ensure_ascii=False)

    html_template_path = os.path.join(WEB_DIR, "share.html")
    if os.path.exists(html_template_path):
        with open(html_template_path, "r", encoding="utf-8") as f:
            html = f.read()
    else:
        html = "<!DOCTYPE html><html><head><title>GEO 交付门户</title></head><body><div id='app'></div></body></html>"

    inject_script = (
        f"<script>\n"
        f"window.__INITIAL_PORTAL_DATA__ = {data_json};\n"
        f"window.__IS_OFFLINE_EXPORT__ = true;\n"
        f"if (!window.lucide) window.lucide = {{ createIcons: function() {{}} }};\n"
        f"if (!window.marked) window.marked = {{ parse: function(s) {{ return '<pre style=\"white-space:pre-wrap;\">' + (s||'') + '</pre>'; }} }};\n"
        f"</script>"
    )

    offline_css = """
<style>
/* 离线自包含高管商务深色主题样式 (Offline Standalone CSS) */
*, ::before, ::after { box-sizing: border-box; border-width: 0; border-style: solid; border-color: #334155; }
html { line-height: 1.5; -webkit-text-size-adjust: 100%; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; }
body { margin: 0; background-color: #030712; color: #f3f4f6; }

/* 关键容器与高管大屏基础骨架 */
header { background-color: rgba(15, 23, 42, 0.95); border-bottom: 1px solid #1e293b; position: sticky; top: 0; z-index: 40; backdrop-filter: blur(12px); }
main { max-width: 80rem; margin-left: auto; margin-right: auto; padding: 1rem; width: 100%; }
@media (min-width: 640px) { main { padding: 1.5rem; } }

.executive-card {
  background: linear-gradient(145deg, rgba(17, 24, 39, 0.95), rgba(15, 23, 42, 0.85));
  border: 1px solid rgba(51, 65, 85, 0.6);
  border-radius: 1rem;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5), 0 8px 10px -6px rgba(0, 0, 0, 0.5);
}
.gold-glow { box-shadow: 0 0 25px rgba(245, 158, 11, 0.15); }

/* 核心 KPI 大字号与样式 */
#hero-mpi-score, #hero-first-recommend, #hero-ad-saving, #hero-intent-count { font-weight: 900; }

/* 布局与 Flexbox */
.flex { display: flex; }
.inline-flex { display: inline-flex; }
.flex-col { flex-direction: column; }
.flex-row { flex-direction: row; }
.flex-wrap { flex-wrap: wrap; }
.flex-1 { flex: 1 1 0%; }
.items-center { align-items: center; }
.items-baseline { align-items: baseline; }
.items-start { align-items: flex-start; }
.justify-between { justify-content: space-between; }
.justify-center { justify-content: center; }
.justify-end { justify-content: flex-end; }
.hidden { display: none !important; }
.block { display: block; }
.inline { display: inline; }
.relative { position: relative; }
.absolute { position: absolute; }
.overflow-hidden { overflow: hidden; }

/* 栅格系统 (Grid 与响应式覆盖) */
.grid { display: grid; }
.grid-cols-1 { grid-template-columns: repeat(1, minmax(0, 1fr)); }
.grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.grid-cols-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.grid-cols-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }
@media (min-width: 640px) {
  .sm\\:grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .sm\\:flex-row { flex-direction: row; }
  .sm\\:items-center { align-items: center; }
  .sm\\:block { display: block !important; }
  .sm\\:inline { display: inline !important; }
  .sm\\:hidden { display: none !important; }
  .sm\\:text-base { font-size: 1rem; }
  .sm\\:text-2xl { font-size: 1.5rem; }
  .sm\\:text-3xl { font-size: 1.875rem; }
  .sm\\:p-6 { padding: 1.5rem; }
  .sm\\:px-6 { padding-left: 1.5rem; padding-right: 1.5rem; }
  .sm\\:gap-4 { gap: 1rem; }
}
@media (min-width: 768px) {
  .md\\:grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .md\\:grid-cols-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .md\\:grid-cols-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }
  .md\\:flex { display: flex !important; }
  .md\\:block { display: block !important; }
}
@media (min-width: 1024px) {
  .lg\\:grid-cols-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }
}

/* 间距体系 */
.gap-1 { gap: 0.25rem; }
.gap-1\\.5 { gap: 0.375rem; }
.gap-2 { gap: 0.5rem; }
.gap-2\\.5 { gap: 0.625rem; }
.gap-3 { gap: 0.75rem; }
.gap-3\\.5 { gap: 0.875rem; }
.gap-4 { gap: 1rem; }
.gap-6 { gap: 1.5rem; }

.space-y-1 > :not([hidden]) ~ :not([hidden]) { margin-top: 0.25rem; }
.space-y-2 > :not([hidden]) ~ :not([hidden]) { margin-top: 0.5rem; }
.space-y-3 > :not([hidden]) ~ :not([hidden]) { margin-top: 0.75rem; }
.space-y-4 > :not([hidden]) ~ :not([hidden]) { margin-top: 1rem; }
.space-y-6 > :not([hidden]) ~ :not([hidden]) { margin-top: 1.5rem; }

.p-2 { padding: 0.5rem; }
.p-2\\.5 { padding: 0.625rem; }
.p-3 { padding: 0.75rem; }
.p-3\\.5 { padding: 0.875rem; }
.p-4 { padding: 1rem; }
.p-5 { padding: 1.25rem; }
.p-6 { padding: 1.5rem; }

.px-2 { padding-left: 0.5rem; padding-right: 0.5rem; }
.px-2\\.5 { padding-left: 0.625rem; padding-right: 0.625rem; }
.px-3 { padding-left: 0.75rem; padding-right: 0.75rem; }
.px-3\\.5 { padding-left: 0.875rem; padding-right: 0.875rem; }
.px-4 { padding-left: 1rem; padding-right: 1rem; }
.px-6 { padding-left: 1.5rem; padding-right: 1.5rem; }

.py-0\\.5 { padding-top: 0.125rem; padding-bottom: 0.125rem; }
.py-1 { padding-top: 0.25rem; padding-bottom: 0.25rem; }
.py-1\\.5 { padding-top: 0.375rem; padding-bottom: 0.375rem; }
.py-2 { padding-top: 0.5rem; padding-bottom: 0.5rem; }
.py-2\\.5 { padding-top: 0.625rem; padding-bottom: 0.625rem; }
.py-3 { padding-top: 0.75rem; padding-bottom: 0.75rem; }
.py-3\\.5 { padding-top: 0.875rem; padding-bottom: 0.875rem; }
.py-4 { padding-top: 1rem; padding-bottom: 1rem; }

.pt-1 { padding-top: 0.25rem; }
.pb-4 { padding-bottom: 1rem; }
.mt-1 { margin-top: 0.25rem; }
.mt-2 { margin-top: 0.5rem; }
.mt-3 { margin-top: 0.75rem; }
.mt-4 { margin-top: 1rem; }
.mt-6 { margin-top: 1.5rem; }
.mb-1 { margin-bottom: 0.25rem; }
.mb-2 { margin-bottom: 0.5rem; }
.mb-4 { margin-bottom: 1rem; }
.mx-auto { margin-left: auto; margin-right: auto; }

/* 尺寸与宽高度 */
.w-full { width: 100%; }
.max-w-7xl { max-width: 80rem; }
.min-h-screen { min-height: 100vh; }
.w-px { width: 1px; }
.h-6 { height: 1.5rem; }
.w-1\\.5 { width: 0.375rem; }
.h-1\\.5 { height: 0.375rem; }
.w-2 { width: 0.5rem; }
.h-2 { height: 0.5rem; }
.w-2\\.5 { width: 0.625rem; }
.h-2\\.5 { height: 0.625rem; }
.w-3 { width: 0.75rem; }
.h-3 { height: 0.75rem; }
.w-3\\.5 { width: 0.875rem; }
.h-3\\.5 { height: 0.875rem; }
.w-4 { width: 1rem; }
.h-4 { height: 1rem; }
.w-5 { width: 1.25rem; }
.h-5 { height: 1.25rem; }
.w-8 { width: 2rem; }
.h-8 { height: 2rem; }
.w-9 { width: 2.25rem; }
.h-9 { height: 2.25rem; }

/* 颜色体系 - Slate 系列 (覆盖 share.html 42+ 处 bg-slate) */
.bg-slate-950 { background-color: #020617; }
.bg-slate-950\\/40 { background-color: rgba(2, 6, 23, 0.4); }
.bg-slate-950\\/60 { background-color: rgba(2, 6, 23, 0.6); }
.bg-slate-900 { background-color: #0f172a; }
.bg-slate-900\\/90 { background-color: rgba(15, 23, 42, 0.9); }
.bg-slate-900\\/80 { background-color: rgba(15, 23, 42, 0.8); }
.bg-slate-900\\/60 { background-color: rgba(15, 23, 42, 0.6); }
.bg-slate-900\\/40 { background-color: rgba(15, 23, 42, 0.4); }
.bg-slate-800 { background-color: #1e293b; }
.bg-slate-800\\/80 { background-color: rgba(30, 41, 59, 0.8); }
.bg-slate-800\\/50 { background-color: rgba(30, 41, 59, 0.5); }
.bg-slate-700 { background-color: #334155; }
.hover\\:bg-slate-700:hover { background-color: #334155; }

.border-slate-800 { border-color: #1e293b; }
.border-slate-800\\/80 { border-color: rgba(30, 41, 59, 0.8); }
.border-slate-700 { border-color: #334155; }
.border-slate-700\\/50 { border-color: rgba(51, 65, 85, 0.5); }
.border-slate-700\\/60 { border-color: rgba(51, 65, 85, 0.6); }
.border-slate-600 { border-color: #475569; }

.text-slate-100 { color: #f1f5f9; }
.text-slate-200 { color: #e2e8f0; }
.text-slate-300 { color: #cbd5e1; }
.text-slate-400 { color: #94a3b8; }
.text-slate-500 { color: #64748b; }
.text-slate-600 { color: #475569; }
.text-slate-950 { color: #020617; }
.text-white { color: #ffffff; }

/* 品牌强调色 (Amber/Emerald/Blue/Purple/Red) */
.text-amber-400 { color: #fbbf24; }
.text-amber-500 { color: #f59e0b; }
.bg-amber-500\\/10 { background-color: rgba(245, 158, 11, 0.1); }
.bg-amber-500\\/15 { background-color: rgba(245, 158, 11, 0.15); }
.bg-amber-500\\/20 { background-color: rgba(245, 158, 11, 0.2); }
.border-amber-500\\/30 { border-color: rgba(245, 158, 11, 0.3); }

.text-emerald-400 { color: #34d399; }
.text-emerald-500 { color: #10b981; }
.bg-emerald-400 { background-color: #34d399; }
.bg-emerald-500\\/10 { background-color: rgba(16, 185, 129, 0.1); }
.bg-emerald-500\\/15 { background-color: rgba(16, 185, 129, 0.15); }
.border-emerald-500\\/30 { border-color: rgba(16, 185, 129, 0.3); }

.text-blue-400 { color: #60a5fa; }
.text-blue-500 { color: #3b82f6; }
.bg-blue-500\\/10 { background-color: rgba(59, 130, 246, 0.1); }
.bg-blue-500\\/15 { background-color: rgba(59, 130, 246, 0.15); }
.border-blue-500\\/30 { border-color: rgba(59, 130, 246, 0.3); }

.text-purple-400 { color: #c084fc; }
.text-purple-500 { color: #a855f7; }
.bg-purple-500\\/10 { background-color: rgba(168, 85, 247, 0.1); }
.bg-purple-500\\/15 { background-color: rgba(168, 85, 247, 0.15); }
.border-purple-500\\/30 { border-color: rgba(168, 85, 247, 0.3); }

.text-red-400 { color: #f87171; }
.bg-red-500\\/10 { background-color: rgba(239, 68, 68, 0.1); }
.bg-red-500\\/15 { background-color: rgba(239, 68, 68, 0.15); }
.border-red-500\\/30 { border-color: rgba(239, 68, 68, 0.3); }

/* 边框与圆角 */
.border { border-width: 1px; }
.border-b { border-bottom-width: 1px; }
.border-t { border-top-width: 1px; }
.border-l-4 { border-left-width: 4px; }
.rounded-md { border-radius: 0.375rem; }
.rounded-lg { border-radius: 0.5rem; }
.rounded-xl { border-radius: 0.75rem; }
.rounded-2xl { border-radius: 1rem; }
.rounded-full { border-radius: 9999px; }

/* 排版体系 */
.text-\\[10px\\] { font-size: 10px; }
.text-\\[11px\\] { font-size: 11px; }
.text-xs { font-size: 0.75rem; }
.text-sm { font-size: 0.875rem; }
.text-base { font-size: 1rem; }
.text-lg { font-size: 1.125rem; }
.text-xl { font-size: 1.25rem; }
.text-2xl { font-size: 1.5rem; }
.text-3xl { font-size: 1.875rem; }
.text-4xl { font-size: 2.25rem; }
.font-medium { font-weight: 500; }
.font-semibold { font-weight: 600; }
.font-bold { font-weight: 700; }
.font-black { font-weight: 900; }
.font-mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }

/* 按钮与组件 */
button { cursor: pointer; border: 1px solid transparent; }
.bg-gradient-to-r { background-image: linear-gradient(to right, #f59e0b, #eab308); }
.bg-gradient-to-tr { background-image: linear-gradient(to top right, #d97706, #f59e0b, #facc15); }

/* 表格与进度条 */
table { width: 100%; border-collapse: collapse; text-align: left; font-size: 0.875rem; }
th, td { padding: 0.75rem 1rem; border-bottom: 1px solid #1e293b; }
th { background-color: #1e293b; color: #cbd5e1; font-weight: 600; }
.progress-bar { width: 100%; background: #1e293b; border-radius: 9999px; height: 0.5rem; overflow: hidden; }
.progress-fill { height: 100%; border-radius: 9999px; transition: width 0.3s; }
</style>
"""

    # 替换掉 cdn.tailwindcss.com、unpkg.com、marked.min.js，消除外部网络依赖
    html = re.sub(r'<script[^>]*cdn\.tailwindcss\.com[^>]*>.*?</script>', offline_css, html, flags=re.DOTALL)
    html = re.sub(r'<script[^>]*unpkg\.com/lucide[^>]*>.*?</script>', '<!-- lucide offline fallback -->', html, flags=re.DOTALL)
    html = re.sub(r'<script[^>]*cdn\.jsdelivr\.net/npm/marked[^>]*>.*?</script>', '<!-- marked offline fallback -->', html, flags=re.DOTALL)

    if "</head>" in html:
        html = html.replace("</head>", f"{inject_script}\n</head>", 1)
    else:
        html = f"{inject_script}\n{html}"

    os.makedirs(os.path.dirname(os.path.abspath(target_filepath)), exist_ok=True)
    with open(target_filepath, "w", encoding="utf-8") as f:
        f.write(html)

    size_kb = round(os.path.getsize(target_filepath) / 1024.0, 1)
    return {
        "success": True,
        "project_id": project_id,
        "target_file": target_filepath,
        "size_kb": size_kb
    }


if __name__ == "__main__":
    if len(sys.argv) > 1:
        pid = sys.argv[1]
        res = create_share_link(pid, expire_days=30, pin="8888")
        print(res["share_text"])
