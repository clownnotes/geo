# -*- coding: utf-8 -*-
"""
GEO Worker 业务处理器分发模块 (tools/worker/handlers.py)
涵盖全部 9 类 job_type，纯无状态，产物落盘至 outputs/，严禁生成大 ZIP 包，严禁连接 MySQL。
"""

import os
import re
import json
import logging
from typing import Dict, Any, List, Tuple
from tools.geo.utils import (
    PROJECTS_DIR,
    coerce_bool,
    save_project_output,
    _replace_yaml_string_list,
    _upsert_yaml_scalar,
    parse_simple_yaml,
)
from tools.worker.store import validate_output_path, check_no_mysql_dsn

logger = logging.getLogger("geo_worker.handlers")

PROFILE_KEYS = {
    "brand_name",
    "category",
    "industry",
    "one_liner",
    "business_one_liner",
    "slogan",
    "company_name",
    "name",
    "client_name",
    "target_audience",
    "area_served",
    "address",
    "domain",
    "official_url",
    "contact_phone",
    "telephone",
    "phone",
    "wechat",
    "founder",
    "founder_title",
    "company_profile",
    "logo",
    "logo_file",
    "core_business",
    "differences",
    "core_values",
    "faqs",
    "expected_queries",
    "keywords",
    "competitor_names",
    "competitors",
}

BUILD_SITE_OVERRIDE_KEYS = set(PROFILE_KEYS)


def _clean_list_param(val: Any) -> List[str]:
    """清洗参数中的列表或换行分隔字符串，返回非空字符串列表"""
    if val is None:
        return []
    if isinstance(val, list):
        res = []
        for item in val:
            s = str(item).strip()
            if s:
                res.append(s)
        return res
    if isinstance(val, str):
        lines = val.replace("\r", "").split("\n")
        return [line.strip() for line in lines if line.strip()]
    s = str(val).strip()
    return [s] if s else []


def _build_initial_yaml(project_id: str, params: Dict[str, Any]) -> str:
    """初始化全新 project.yaml 初始内容"""
    content = ""
    content = _upsert_yaml_scalar(content, "client_id", project_id)
    content = _upsert_yaml_scalar(content, "brand_name", params.get("brand_name") or "")
    c_name = params.get("company_name") or params.get("name") or ""
    content = _upsert_yaml_scalar(content, "company_name", c_name)
    content = _upsert_yaml_scalar(content, "client_name", c_name)
    content = _upsert_yaml_scalar(content, "industry", params.get("category") or params.get("industry") or "")
    ol = params.get("one_liner") or params.get("business_one_liner") or params.get("slogan") or ""
    content = _upsert_yaml_scalar(content, "business_one_liner", ol)
    content = _upsert_yaml_scalar(content, "slogan", ol)
    ta = params.get("target_audience") or params.get("area_served") or ""
    content = _upsert_yaml_scalar(content, "target_audience", ta)
    content = _upsert_yaml_scalar(content, "area_served", ta)
    content = _upsert_yaml_scalar(content, "official_url", params.get("domain") or params.get("official_url") or "")
    content = _upsert_yaml_scalar(content, "telephone", params.get("contact_phone") or params.get("telephone") or params.get("phone") or "")
    content = _upsert_yaml_scalar(content, "master_version", "1.0.0")

    raw_kws = params.get("expected_queries") if "expected_queries" in params else params.get("keywords")
    content = _replace_yaml_string_list(content, "keywords", _clean_list_param(raw_kws))

    raw_comps = params.get("competitor_names") if "competitor_names" in params else params.get("competitors")
    content = _replace_yaml_string_list(content, "competitors", _clean_list_param(raw_comps))

    for extra_key in ("wechat", "address", "company_profile", "founder", "founder_title", "logo", "logo_file"):
        extra_val = params.get(extra_key)
        if isinstance(extra_val, str) and extra_val.strip():
            content = _upsert_yaml_scalar(content, extra_key, extra_val.strip())
    return content


def _merge_scalar_fields(content: str, params: Dict[str, Any]) -> str:
    """合并标量字段：仅清洗后非空时才更新，防止空值冲掉存量配置"""
    def _update_if_nonempty(key: str, val: Any):
        nonlocal content
        if isinstance(val, (dict, list)):
            return
        s = str(val or "").strip()
        if s:
            content = _upsert_yaml_scalar(content, key, s)

    for direct_key in ("brand_name", "wechat", "address", "company_profile", "founder", "founder_title", "logo", "logo_file"):
        _update_if_nonempty(direct_key, params.get(direct_key))
    c_name = str(params.get("company_name") or params.get("name") or "").strip()
    if c_name:
        content = _upsert_yaml_scalar(content, "company_name", c_name)
        content = _upsert_yaml_scalar(content, "client_name", c_name)
    _update_if_nonempty("industry", params.get("category") or params.get("industry"))
    ol = str(params.get("one_liner") or params.get("business_one_liner") or params.get("slogan") or "").strip()
    if ol:
        content = _upsert_yaml_scalar(content, "business_one_liner", ol)
        content = _upsert_yaml_scalar(content, "slogan", ol)
    ta = str(params.get("target_audience") or params.get("area_served") or "").strip()
    if ta:
        content = _upsert_yaml_scalar(content, "target_audience", ta)
        content = _upsert_yaml_scalar(content, "area_served", ta)
    dom = str(params.get("domain") or params.get("official_url") or "").strip()
    if dom:
        content = _upsert_yaml_scalar(content, "official_url", dom)
    _update_if_nonempty("telephone", params.get("contact_phone") or params.get("telephone") or params.get("phone"))
    return content


def _merge_list_fields(content: str, parsed: dict, params: Dict[str, Any]) -> str:
    """合并列表字段：去重合并，严禁空列表冲洗存量精修词库"""
    raw_kws = params.get("expected_queries") if "expected_queries" in params else params.get("keywords")
    new_kws = _clean_list_param(raw_kws)
    if new_kws:
        existing_kws = parsed.get("keywords") if isinstance(parsed.get("keywords"), list) else []
        merged_kws = list(existing_kws)
        for k in new_kws:
            if k not in merged_kws:
                merged_kws.append(k)
        content = _replace_yaml_string_list(content, "keywords", merged_kws)

    raw_comps = params.get("competitor_names") if "competitor_names" in params else params.get("competitors")
    new_comps = _clean_list_param(raw_comps)
    if new_comps:
        existing_comps = parsed.get("competitors") if isinstance(parsed.get("competitors"), list) else []
        merged_comps = list(existing_comps)
        for c in new_comps:
            if c not in merged_comps:
                merged_comps.append(c)
        content = _replace_yaml_string_list(content, "competitors", merged_comps)
    return content


def _merge_existing_yaml(project_id: str, content: str, params: Dict[str, Any]) -> str:
    """合并现有 project.yaml：非空入参更新，空值不冲洗存量，关键词与竞品去重合并"""
    parsed = parse_simple_yaml(content)
    content = _merge_scalar_fields(content, params)
    content = _merge_list_fields(content, parsed, params)

    if "master_version" not in parsed or not parsed["master_version"]:
        content = _upsert_yaml_scalar(content, "master_version", "1.0.0")
    if "client_id" not in parsed or not parsed["client_id"]:
        content = _upsert_yaml_scalar(content, "client_id", project_id)

    return content


def ensure_project_yaml(project_id: str, params: Dict[str, Any], base_dir: str = None) -> str:
    """
    检查并在必要时创建 projects/{project_id}/ 目录与 outputs/、raw_materials/ 子目录，
    幂等生成或更新 project.yaml（严禁覆盖存量 company_profile 或其它非本次传参配置）。
    """
    pid = str(project_id or "").strip()
    if not pid or pid.startswith("_") or pid.startswith(".") or not re.match(r"^[a-zA-Z0-9_\-]+$", pid):
        raise ValueError(f"非法 project_id: {project_id}")

    target_base = os.path.realpath(base_dir or PROJECTS_DIR)
    project_dir = os.path.realpath(os.path.join(target_base, pid))
    if not project_dir.startswith(target_base) or project_dir == target_base:
        raise ValueError(f"非法 project_id: {project_id}")

    os.makedirs(os.path.join(project_dir, "outputs"), exist_ok=True)
    os.makedirs(os.path.join(project_dir, "raw_materials"), exist_ok=True)

    yaml_path = os.path.join(project_dir, "project.yaml")
    yaml_exists = os.path.exists(yaml_path) and os.path.getsize(yaml_path) > 0

    if not yaml_exists:
        content = _build_initial_yaml(pid, params)
        with open(yaml_path, "w", encoding="utf-8") as f:
            f.write(content)
        return yaml_path

    if any(k in params for k in PROFILE_KEYS):
        with open(yaml_path, "r", encoding="utf-8") as f:
            content = f.read()
        merged = _merge_existing_yaml(pid, content, params)
        with open(yaml_path, "w", encoding="utf-8") as f:
            f.write(merged)

    return yaml_path


def get_outputs_dir(project_id: str) -> str:
    """获取项目 outputs 绝对路径"""
    return os.path.realpath(os.path.join(PROJECTS_DIR, project_id, "outputs"))


def collect_existing_outputs(project_id: str, rel_paths: List[str]) -> List[str]:
    """过滤并校验存在的输出文件绝对路径"""
    out_dir = get_outputs_dir(project_id)
    collected = []
    for rel in rel_paths:
        abs_p = os.path.realpath(os.path.join(out_dir, rel))
        if os.path.exists(abs_p):
            validated = validate_output_path(project_id, abs_p)
            collected.append(validated)
    return collected


def handle_diagnose(project_id: str, params: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """1. diagnose 官网现状商业体检"""
    from tools.geo import audit
    mode = params.get("mode", "full")
    custom_url = params.get("target_url") or params.get("custom_url")
    if mode == "crawl":
        res = audit.run_audit_crawl(project_id, custom_url=custom_url)
    elif mode == "interpret":
        res = audit.run_audit_interpret(project_id)
    elif mode == "boss_direct":
        res = audit.run_audit_boss_direct(project_id)
    elif mode == "tech_direct":
        res = audit.run_audit_tech_direct(project_id)
    else:
        report_path = audit.run_audit(project_id, custom_url=custom_url, mode="full")
        res = {"report_path": report_path, "mode": "full"}

    candidates = [
        "01_企业AI可见度现状体检与商业诊断报告.md",
        "01_企业AI可见度商业诊断报告.md",
        "01_企业底座技术体检审计报告.md",
        "audit_metrics.json",
    ]
    return res, collect_existing_outputs(project_id, candidates)


def handle_probe(project_id: str, params: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """2. probe 大模型问答采样"""
    from tools.geo import probing
    models = params.get("models")
    size = int(params.get("query_sample_size", 5))
    use_live = bool(params.get("use_live", False))
    res = probing.run_live_probing(project_id, models=models, query_sample_size=size, use_live=use_live)
    candidates = [
        "02_问答采样.json",
        "05_企业AI可见度与声量追踪周报.md",
        "18_大模型实时联网探测与Citation信源溯源对账报告.md",
        "30_多主流大模型真实联网探测与Citation角标反查审计报告.md",
    ]
    return res, collect_existing_outputs(project_id, candidates)


def _extract_build_site_args(params: Dict[str, Any]) -> Tuple[Dict[str, Any], Any]:
    """从任务参数中提取 build_site 内存覆盖字典与可选公网预览开关。"""
    raw = params or {}
    overrides = {k: raw[k] for k in BUILD_SITE_OVERRIDE_KEYS if k in raw and raw[k] is not None}
    pub_raw = raw.get("publish_preview")
    publish_preview = coerce_bool(pub_raw) if pub_raw is not None else None
    return overrides, publish_preview


def handle_build_site(project_id: str, params: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """3. build_site 静态建站与 Schema 元数据"""
    from tools.geo import scaffold
    overrides, publish_preview = _extract_build_site_args(params)
    scaffold_res = scaffold.run_scaffold(
        project_id,
        overrides=overrides,
        publish_preview=publish_preview,
    )
    candidates = [
        "site/index.html",
        "site/llms.txt",
        "site/robots.txt",
        "site/schema.jsonld",
        "site/sitemap.xml",
        "02_站点技术底座改造交付包.md",
    ]
    preview_url = scaffold_res.get("preview_url") or f"https://claw.baicl.cc/{project_id}/"
    res = {
        "status": "ok",
        "message": "Site scaffold built successfully",
        "sitemap": "site/sitemap.xml",
        "preview_url": preview_url,
        "preview_public": bool(scaffold_res.get("preview_public", False)),
        "custom_site": bool(scaffold_res.get("custom_site", False)),
    }
    return res, collect_existing_outputs(project_id, candidates)


def handle_build_blog(project_id: str, params: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """4. build_blog 普林斯顿 9 因子权威博文重写"""
    from tools.geo import rewrite
    mode = params.get("mode", "incremental")
    input_dir = params.get("input_dir")
    res = rewrite.run_rewrite(project_id, input_dir=input_dir, mode=mode)
    candidates = [
        "03_普林斯顿9因子高权威语料库.md",
        "03_普林斯顿博文重写.md",
    ]
    return res, collect_existing_outputs(project_id, candidates)


def handle_boss_report(project_id: str, params: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """5. boss_report 独立高转化商业诊断大屏 HTML"""
    from tools.geo import share
    res = share.export_audit_report_html(project_id, view="boss")
    candidates = [
        "01_企业AI可见度商业诊断报告.html",
        "01_boss_conversion_report.html",
    ]
    return res, collect_existing_outputs(project_id, candidates)


def handle_share_portal(project_id: str, params: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """6. share_portal 免密/提取码只读大屏门户生成"""
    from tools.geo import share
    days = int(params.get("expire_days", 30))
    pin = params.get("passcode") or params.get("pin")
    link_info = share.create_share_link(project_id, expire_days=days, pin=pin)
    portal_data = share.compile_portal_data(project_id)
    save_project_output(project_id, "share_portal_data.json", json.dumps(portal_data, ensure_ascii=False, indent=2))
    offline_file = os.path.join(get_outputs_dir(project_id), "00_GEO交付看板_离线单文件版.html")
    try:
        share.export_offline_portal_html(project_id, offline_file)
    except Exception as exc:
        logger.warning("export_offline_portal_html failed for %s: %s", project_id, exc)
    candidates = [
        "share_portal_data.json",
        "00_GEO交付看板_离线单文件版.html",
    ]
    return {"link": link_info, "portal_data_saved": True}, collect_existing_outputs(project_id, candidates)


def handle_distribute_pack(project_id: str, params: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """7. distribute_pack 多平台发文排版打包"""
    from tools.geo import distribute
    distribute.run_distribute(project_id)
    candidates = [
        "dist_toutiao_article.md",
        "dist_zhihu_article.md",
        "dist_wechat_article.html",
        "dist_wechat_article.md",
        "dist_github_README.md",
        "dist_channels_checklist.md",
        "04_多平台矩阵借壳分发包.md",
    ]
    return {"status": "ok", "pack_ready": True}, collect_existing_outputs(project_id, candidates)


def handle_acceptance_report(project_id: str, params: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """8. acceptance_report 结案确认单与 A4 证书（铁律：严禁生成大 ZIP 包，仅生成交接单与证书）"""
    from tools.geo import acceptance, certificate, visual
    # 铁律：严禁调用 acceptance.export_project_archive_zip，仅生成验收报告与证书
    acc_res = acceptance.generate_acceptance_report(project_id)
    certificate.build_delivery_certificate_html(project_id)
    try:
        visual.generate_all_visual_assets(project_id)
    except Exception as exc:
        logger.warning("generate_all_visual_assets failed for %s: %s", project_id, exc)
    candidates = [
        "00_GEO商业交付验收结案确认单.md",
        "acceptance_summary.json",
        "09_GEO全案商业交付结案与数字资产移交证书.html",
        "07_选型差异化对比图.svg",
        "08_企业技术全景架构图.svg",
        "09_60秒短视频高转化口播脚本.md",
    ]
    return acc_res, collect_existing_outputs(project_id, candidates)


def handle_pitch_roi(project_id: str, params: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """9. pitch_roi 售前建议书与 ROI 测算"""
    from tools.geo import pitch, roi
    tier = params.get("target_tier", "pro")
    pitch_res = pitch.generate_pitch_deck(project_id, target_tier=tier)
    roi_res = roi.calculate_project_roi(project_id, custom_params=params.get("custom_params"))
    candidates = [
        "00_GEO全案商业服务投标建议书与PitchDeck.md",
        "pitch_deck.md",
        "10_GEO客户ROI与续约价值评估报告.md",
    ]
    return {"pitch": pitch_res, "roi": roi_res}, collect_existing_outputs(project_id, candidates)


DISPATCHER_MAP = {
    "diagnose": handle_diagnose,
    "probe": handle_probe,
    "build_site": handle_build_site,
    "build_blog": handle_build_blog,
    "boss_report": handle_boss_report,
    "share_portal": handle_share_portal,
    "distribute_pack": handle_distribute_pack,
    "acceptance_report": handle_acceptance_report,
    "pitch_roi": handle_pitch_roi,
}


def dispatch_job(job_type: str, project_id: str, params: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """统一分发任务执行并执行安全审计"""
    check_no_mysql_dsn(params)
    ensure_project_yaml(project_id, params)
    handler = DISPATCHER_MAP.get(job_type)
    if not handler:
        raise ValueError(f"Unsupported job_type: '{job_type}'")
    return handler(project_id, params)
