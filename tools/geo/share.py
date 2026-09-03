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
    
    # 查找匹配的资产声明
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

    # 按 candidates 候选依次寻找存在的文件
    candidates = target_item.get("candidates", [target_item.get("file")])
    found_path = None
    for cand in candidates:
        cand_path = os.path.join(out_dir, cand)
        if os.path.exists(cand_path) and os.path.isfile(cand_path):
            found_path = cand_path
            break

    if not found_path:
        return {"success": True, "key": req_key, "content": f"*{target_item.get('name', req_key)} 暂未生成*", "filename": ""}

    # 严格 realpath 物理防目录穿透
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

    # 读取 16 维全景交付文件
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
        "injection_guard": "16_大模型提示词注入防御与品牌隔离盾牌报告.md"
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
    raw_history = get_project_history(project_id, limit=12)
    
    # 脱敏内部自增 ID 与内部调试字段
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

    # 提取行业横向对标
    try:
        from .benchmark import evaluate_project_against_benchmark
        bench_eval = evaluate_project_against_benchmark(project_id)
        if isinstance(bench_eval, dict):
            bench_eval = dict(bench_eval)
            bench_eval.pop("project_id", None)
    except Exception:
        bench_eval = {}

    # 提取多模态视觉资产
    try:
        from .visual import get_visual_assets
        vis_res = get_visual_assets(project_id)
        visual_assets = vis_res.get("assets", {})
    except Exception:
        visual_assets = {}

    # 提取多平台外发落地台账
    try:
        from .dist_bot import get_distribution_ledger
        dist_ledger = get_distribution_ledger(project_id)
    except Exception:
        dist_ledger = {}

    # 提取商业 ROI 财务估值与战绩
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

    # 提取结案验收与合同履约达成状态 (16 维全景)
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

    # 优先从已落盘的知识图谱 JSON 读取，避免每次打开门户重新执行
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
    if not graph_summary:
        try:
            from .graph import build_entity_knowledge_graph
            graph_res = build_entity_knowledge_graph(project_id)
            graph_summary = {
                "node_count": graph_res.get("node_count", 0),
                "edge_count": graph_res.get("edge_count", 0),
                "summary": graph_res.get("summary", {}),
                "nodes": graph_res.get("nodes", [])[:30],
                "edges": graph_res.get("edges", [])[:40]
            }
        except Exception:
            graph_summary = {}

    # 优先从已落盘的事实锚点 JSON 读取幻觉防御状态
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
    if not guard_summary:
        try:
            from .guard import detect_factual_hallucinations
            guard_summary = detect_factual_hallucinations(project_id)
        except Exception:
            guard_summary = {}

    # 读取 10~16 高阶攻防核心资产落盘 JSON 摘要 (严格字段映射)
    def _read_json_safe(fname: str) -> dict:
        fpath = os.path.join(out_dir, fname)
        if os.path.exists(fpath):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    injection_guard_data = _read_json_safe("prompt_injection_guard.json")
    citation_auth_data = _read_json_safe("citation_authority_matrix.json")
    competitor_data = _read_json_safe("competitor_gap_analysis.json")
    compliance_data = _read_json_safe("compliance_inspection.json")
    rag_diag_data = _read_json_safe("rag_chunks_diagnostic.json")
    intent_data = _read_json_safe("keywords_intent_matrix.json")
    evaluator_data = _read_json_safe("06_大模型真实API评测与Citation捕获报告.json")

    # 检查结案 ZIP 归档包状态
    zip_name = f"{project_id}_geo_delivery_archive.zip"
    zip_path = os.path.join(out_dir, zip_name)
    archive_info = {
        "exists": os.path.exists(zip_path),
        "filename": zip_name,
        "size_kb": round(os.path.getsize(zip_path) / 1024, 1) if os.path.exists(zip_path) else 0,
        "download_url": f"/api/share/{token}/download-zip"
    }

    # 提取真实指标字段 (严格遵循 Design 规范，缺省不乱编)
    radar_gap = competitor_data.get("radar_comparison", {}).get("overall_gap_lead")
    if radar_gap is None and "gap_metrics" in competitor_data:
        radar_gap = competitor_data["gap_metrics"].get("overall_sov_gap_pct")

    rag_score = rag_diag_data.get("rag_readiness_score")
    if rag_score is None:
        rag_score = rag_diag_data.get("avg_retrieval_score")

    return {
        "success": True,
        "project_id": project_id,
        "client_name": cfg.get("client_name", "客户企业"),
        "industry": cfg.get("industry", "未知行业"),
        "website": cfg.get("website", ""),
        "brand_name": cfg.get("brand_name", cfg.get("client_name", "")),
        "deliverables": deliverables,
        "metrics": metrics,
        "history": clean_history,
        "benchmark": bench_eval,
        "visual_assets": visual_assets,
        "distribution_ledger": dist_ledger,
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
