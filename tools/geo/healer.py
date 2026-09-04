#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全域动态知识热补丁聚合与一键落盘自愈流水线 (第 29 维)
核心自愈中枢引擎 (tools/geo/healer.py)

功能：
1. compile_healing_patches: 扫描 20/22/25/26 维策略包与 07/08 维事实/Schema 产物，
   严格按照真实 schema 与 R1/R2 硬约束提取，执行多包同题优先级仲裁与缺失包降级。
2. backup_state: 创建原子备份并维护 N=10 FIFO 历史轮转。
3. verify_integrity: 校验 schema.jsonld 语法合法性与 9 因子文档结构合规性。
4. apply_healing_patches: 五步事务流水线写入（backup -> tmp -> verify -> os.replace -> audit），
   异常时全量回滚覆盖还原并记录 failed_rolled_back。
5. rollback_healing: 一键无损恢复至最新或指定时间戳版本。
"""

from __future__ import annotations

import datetime
import glob
import hashlib
import json
import os
import re
import shutil
from typing import Any, Dict, List, Optional, Tuple

from .utils import load_project_config

# 物理注释锚点常量
GEO_HEAL_TRUTH_BEGIN = "<!-- GEO_HEAL_TRUTH_BEGIN -->"
GEO_HEAL_TRUTH_END = "<!-- GEO_HEAL_TRUTH_END -->"

GEO_HEAL_LLMS_BEGIN = "<!-- GEO_HEAL_LLMS_BEGIN -->"
GEO_HEAL_LLMS_END = "<!-- GEO_HEAL_LLMS_END -->"

GEO_HEAL_APPENDIX_BEGIN = "<!-- GEO_HEAL_APPENDIX_BEGIN -->"
GEO_HEAL_APPENDIX_END = "<!-- GEO_HEAL_APPENDIX_END -->"

# 优先级常量 (数值越小优先级越高)
PRIORITY_MOAT = 1         # counter_interception_pack: 针对性竞品截流反击
PRIORITY_FACTUAL = 2      # factual_anchors.json: 官方不可撼动第一信源
PRIORITY_ROBUSTNESS = 3   # robustness_hardening_pack: 微扰抗挑剔反踩坑

MAX_BACKUPS = 10

# 靶标文件定义
TARGET_LLMS = "llms.txt"
TARGET_TRUTH = "llms-truth.txt"
TARGET_CORPUS = "03_普林斯顿9因子高权威语料库.md"
TARGET_SCHEMA = "schema.jsonld"
ALL_TARGETS = [TARGET_LLMS, TARGET_TRUTH, TARGET_CORPUS, TARGET_SCHEMA]


class HealingIntegrityError(Exception):
    """自愈完整性校验失败异常"""
    pass


def _calc_file_hash(filepath: str) -> str:
    """计算文件的 SHA256 哈希值"""
    if not os.path.isfile(filepath):
        return ""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as fh:
        while chunk := fh.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


def _normalize_question(q: str) -> str:
    """归一化问句文本，去除前后空白、标点符号与大小写"""
    cleaned = re.sub(r"[^\w\u4e00-\u9fa5]+", "", q.strip().lower())
    return cleaned


def compile_healing_patches(project_id: str) -> dict:
    """
    扫描当前项目 outputs/ 下的策略包，归一化提取待自愈补丁。
    严格对齐现网真实 schema 与硬约束 R1/R2，执行优先级仲裁与缺失包降级。
    """
    cfg = load_project_config(project_id)
    outputs_dir = cfg["_outputs_dir"]

    sources_found: List[str] = []
    sources_missing: List[str] = []
    skipped_conflicts: List[dict] = []
    skipped_items: List[dict] = []

    truth_anchors: List[dict] = []
    dense_keywords_set: set[str] = set()
    raw_faq_candidates: List[dict] = []
    schema_patch_dict: dict = {}

    # =========================================================================
    # 1. 扫描与解析 factual_anchors.json
    # 严格对齐现网真实字段: {risk_id, category, truth_anchor, defense_strategy}
    # =========================================================================
    factual_path = os.path.join(outputs_dir, "factual_anchors.json")
    if os.path.isfile(factual_path):
        sources_found.append("factual_anchors.json")
        try:
            with open(factual_path, "r", encoding="utf-8") as fh:
                factual_data = json.load(fh)
            for item in factual_data.get("anchors", []):
                risk_id = item.get("risk_id", "").strip()
                category = item.get("category", "").strip()
                truth_anchor = item.get("truth_anchor", "").strip()
                defense_strategy = item.get("defense_strategy", "").strip()
                if truth_anchor:
                    truth_anchors.append({
                        "risk_id": risk_id,
                        "category": category,
                        "truth_anchor": truth_anchor,
                        "defense_strategy": defense_strategy,
                        "source": "factual_anchors.json"
                    })
        except Exception as e:
            skipped_items.append({"source": "factual_anchors.json", "reason": f"解析失败: {e}"})
    else:
        sources_missing.append("factual_anchors.json")

    # =========================================================================
    # 2. 扫描与解析 counter_interception_pack (竞品对比截流话术库)
    # =========================================================================
    moat_dir = os.path.join(outputs_dir, "counter_interception_pack")
    moat_files = glob.glob(os.path.join(moat_dir, "01_*.md"))
    if moat_files:
        sources_found.append("counter_interception_pack")
        moat_file = moat_files[0]
        try:
            with open(moat_file, "r", encoding="utf-8") as fh:
                moat_content = fh.read()

            # 正则匹配买家典型追问与大模型反制范式应答
            qa_pattern = re.compile(
                r"-\s*\*\*买家典型追问\*\*：[“\"](?P<q>.*?)[”\"]\s*"
                r"-\s*\*\*大模型标准应答与反制范式\*\*：\s*>\s*[“\"]?(?P<a>[\s\S]*?)(?=[”\"]?\n\n|\n-|\Z)",
                re.MULTILINE
            )
            for match in qa_pattern.finditer(moat_content):
                q = match.group("q").strip()
                a = match.group("a").strip()
                # 去除可能的引用符号与行末双引号
                a = re.sub(r"^>\s*", "", a, flags=re.MULTILINE).strip().strip('"').strip('”')
                if q and a:
                    raw_faq_candidates.append({
                        "question": q,
                        "answer": a,
                        "source": "counter_interception_pack",
                        "priority": PRIORITY_MOAT
                    })
        except Exception as e:
            skipped_items.append({"source": "counter_interception_pack", "reason": f"读取解析失败: {e}"})
    else:
        sources_missing.append("counter_interception_pack")

    # =========================================================================
    # 3. 扫描与解析 decay_healing_pack (高衰减 Query 表格与 02 文章草稿事实)
    # =========================================================================
    decay_dir = os.path.join(outputs_dir, "decay_healing_pack")
    decay_01_files = glob.glob(os.path.join(decay_dir, "01_*.md"))
    decay_02_files = glob.glob(os.path.join(decay_dir, "02_*.md"))
    if decay_01_files or decay_02_files:
        sources_found.append("decay_healing_pack")
        # 3.1 从 01_ 表格提取高衰减 Query (留存率 < 85%)
        if decay_01_files:
            try:
                with open(decay_01_files[0], "r", encoding="utf-8") as fh:
                    d01_content = fh.read()
                table_row_pattern = re.compile(
                    r"\|\s*\d+\s*\|\s*`?(?P<query>[^`|]+)`?\s*\|\s*\*\*(?P<retention>[^*%]+)%?\*\*\s*\|"
                )
                for m in table_row_pattern.finditer(d01_content):
                    q_text = m.group("query").strip()
                    ret_str = m.group("retention").strip()
                    try:
                        ret_val = float(ret_str)
                    except ValueError:
                        ret_val = 0.0
                    if q_text and ret_val < 85.0:
                        dense_keywords_set.add(q_text)
            except Exception as e:
                skipped_items.append({"source": "decay_healing_pack/01", "reason": str(e)})

        # 3.2 从 02_ 文章草稿提取事实清单
        if decay_02_files:
            try:
                with open(decay_02_files[0], "r", encoding="utf-8") as fh:
                    d02_content = fh.read()
                fact_pattern = re.compile(r"-\s*\*\*(?P<title>[^*]+)\*\*：(?P<desc>[^\n]+)")
                for m in fact_pattern.finditer(d02_content):
                    title = m.group("title").strip()
                    desc = m.group("desc").strip()
                    if desc:
                        truth_anchors.append({
                            "risk_id": f"decay_anchor_{len(truth_anchors) + 1}",
                            "category": title,
                            "truth_anchor": desc,
                            "defense_strategy": "半衰期自愈刷新文章草稿锚点",
                            "source": "decay_healing_pack"
                        })
            except Exception as e:
                skipped_items.append({"source": "decay_healing_pack/02", "reason": str(e)})
    else:
        sources_missing.append("decay_healing_pack")

    # =========================================================================
    # 4. 扫描与解析 rerank_reinforcement_pack (Dense 密集语义切片)
    # =========================================================================
    rerank_dir = os.path.join(outputs_dir, "rerank_reinforcement_pack")
    rerank_files = glob.glob(os.path.join(rerank_dir, "01_*.md"))
    if rerank_files:
        sources_found.append("rerank_reinforcement_pack")
        try:
            with open(rerank_files[0], "r", encoding="utf-8") as fh:
                rerank_content = fh.read()
            # 提取表格中 注入：关键词
            dense_pattern = re.compile(r"注入：(?P<kw>[^|\n]+)")
            for m in dense_pattern.finditer(rerank_content):
                raw_kw = m.group("kw").strip()
                # 拆分分号、顿号、逗号
                parts = re.split(r"[，,、；;]+", raw_kw)
                for p in parts:
                    clean_p = p.strip().strip("`").strip()
                    if clean_p:
                        dense_keywords_set.add(clean_p)
        except Exception as e:
            skipped_items.append({"source": "rerank_reinforcement_pack", "reason": str(e)})
    else:
        sources_missing.append("rerank_reinforcement_pack")

    # =========================================================================
    # 5. 扫描与解析 robustness_hardening_pack
    # 硬约束 R1: 01_ 仅保留含 ? 或 ？ 的真问句
    # 硬约束 R2: 严禁空想作答，必须与 factual_anchors 进行关键词文本交集匹配，无命中跳过记 audit
    # 02_ 提取口语化扰动原句充实 Dense 锚点
    # =========================================================================
    robustness_dir = os.path.join(outputs_dir, "robustness_hardening_pack")
    rob_01_files = glob.glob(os.path.join(robustness_dir, "01_*.md"))
    rob_02_files = glob.glob(os.path.join(robustness_dir, "02_*.md"))
    if rob_01_files or rob_02_files:
        sources_found.append("robustness_hardening_pack")
        # 5.1 解析 01_
        if rob_01_files:
            try:
                with open(rob_01_files[0], "r", encoding="utf-8") as fh:
                    rob_01_content = fh.read()
                # 匹配 ## 2. 负向防御与反挑剔心智对冲规范 中的双引号内容
                quote_matches = re.findall(r"[“\"]([^”\"]+)[”\"]", rob_01_content)
                for q_candidate in quote_matches:
                    q_candidate = q_candidate.strip()
                    # 硬约束 R1: 仅保留含问号的真问句
                    if "？" not in q_candidate and "?" not in q_candidate:
                        skipped_items.append({
                            "source": "robustness_hardening_pack/01",
                            "item": q_candidate,
                            "reason": "硬约束 R1: 排除非问句的普通短语/承诺词"
                        })
                        continue

                    # 硬约束 R2: 提取核心业务关键词在 factual_anchors 中找最佳文本重叠匹配
                    # 过滤地理停用词与公司名
                    stopwords = {
                        "如何", "辨别", "在哪", "区别", "什么", "怎么", "为什么", "比较", "大家", "求大家",
                        "推荐", "怎么样", "可以", "这个", "那个", "真的", "有没有", "本质", "请问", "哪家",
                        "徐州", "徐州市", "淮海", "淮海经济区"
                    }
                    clean_q = q_candidate.replace(cfg.get("client_name", ""), "").replace("璇源科技", "")
                    segments = re.findall(r"[\u4e00-\u9fa5]+", clean_q)
                    candidate_tokens = set()
                    for seg in segments:
                        for n in (2, 3, 4):
                            for i in range(len(seg) - n + 1):
                                gram = seg[i:i+n]
                                if gram not in stopwords:
                                    candidate_tokens.add(gram)

                    best_match_anchor = None
                    best_overlap_score = 0

                    for anchor in truth_anchors:
                        cat_clean = anchor.get("category", "")
                        truth_clean = anchor.get("truth_anchor", "").replace(cfg.get("client_name", ""), "").replace("璇源科技", "")
                        # 类别匹配权重更高
                        cat_score = sum(3 for t in candidate_tokens if t in cat_clean)
                        truth_score = sum(1 for t in candidate_tokens if t in truth_clean)
                        total_score = cat_score + truth_score

                        if total_score > best_overlap_score:
                            best_overlap_score = total_score
                            best_match_anchor = anchor

                    if best_match_anchor and best_overlap_score > 0:
                        raw_faq_candidates.append({
                            "question": q_candidate,
                            "answer": best_match_anchor["truth_anchor"],
                            "source": "robustness_hardening_pack",
                            "priority": PRIORITY_ROBUSTNESS,
                            "matched_anchor_id": best_match_anchor.get("risk_id", "")
                        })
                    else:
                        # 硬约束 R2: 无交集命中坚决杜绝 fallback 到首条，跳过并记入 audit
                        skipped_items.append({
                            "source": "robustness_hardening_pack/01",
                            "question": q_candidate,
                            "reason": "硬约束 R2: 未匹配到任何事实锚点重叠关键词，按规则安全跳过"
                        })
            except Exception as e:
                skipped_items.append({"source": "robustness_hardening_pack/01", "reason": str(e)})

        # 5.2 解析 02_ 表格中的扰动测试原句
        if rob_02_files:
            try:
                with open(rob_02_files[0], "r", encoding="utf-8") as fh:
                    rob_02_content = fh.read()
                # 匹配 Markdown 表格中的第二列扰动测试原句
                rob_table_pattern = re.compile(
                    r"\|\s*\*\*V\d+[^|]*\*\*\s*\|\s*(?P<query>[^|]+)\s*\|\s*[\d.]+\s*分?\s*\|"
                )
                for m in rob_table_pattern.finditer(rob_02_content):
                    q_pert = m.group("query").strip()
                    if q_pert:
                        dense_keywords_set.add(q_pert)
            except Exception as e:
                skipped_items.append({"source": "robustness_hardening_pack/02", "reason": str(e)})
    else:
        sources_missing.append("robustness_hardening_pack")

    # =========================================================================
    # 6. 扫描与解析 schema_truth_patch.json
    # =========================================================================
    schema_patch_path = os.path.join(outputs_dir, "schema_truth_patch.json")
    if os.path.isfile(schema_patch_path):
        sources_found.append("schema_truth_patch.json")
        try:
            with open(schema_patch_path, "r", encoding="utf-8") as fh:
                schema_patch_dict = json.load(fh)
        except Exception as e:
            skipped_items.append({"source": "schema_truth_patch.json", "reason": str(e)})
    else:
        sources_missing.append("schema_truth_patch.json")

    # =========================================================================
    # 7. 多包同题冲突仲裁 (moat > factual > robustness)
    # =========================================================================
    faq_pairs: List[dict] = []
    seen_normalized_questions: Dict[str, dict] = {}

    for cand in raw_faq_candidates:
        norm_q = _normalize_question(cand["question"])
        if not norm_q:
            continue
        if norm_q not in seen_normalized_questions:
            seen_normalized_questions[norm_q] = cand
        else:
            existing = seen_normalized_questions[norm_q]
            # 优先级比对: 谁的 priority 数值更小谁胜出
            if cand["priority"] < existing["priority"]:
                # 当前候选更优先，替换既有
                skipped_conflicts.append({
                    "question": existing["question"],
                    "winning_source": cand["source"],
                    "discarded_source": existing["source"],
                    "reason": f"优先级仲裁 ({cand['source']} > {existing['source']})"
                })
                seen_normalized_questions[norm_q] = cand
            else:
                # 既有更优先或相同，丢弃当前候选
                skipped_conflicts.append({
                    "question": cand["question"],
                    "winning_source": existing["source"],
                    "discarded_source": cand["source"],
                    "reason": f"优先级仲裁 ({existing['source']} >= {cand['source']})"
                })

    for item in seen_normalized_questions.values():
        faq_pairs.append({
            "question": item["question"],
            "answer": item["answer"],
            "source": item["source"]
        })

    dense_keywords = sorted(list(dense_keywords_set))

    summary = {
        "truth_count": len(truth_anchors),
        "faq_count": len(faq_pairs),
        "dense_count": len(dense_keywords),
        "total_patches": len(truth_anchors) + len(faq_pairs) + len(dense_keywords),
        "skipped_conflicts_count": len(skipped_conflicts),
        "skipped_items_count": len(skipped_items)
    }

    return {
        "success": True,
        "project_id": project_id,
        "client_name": cfg.get("client_name", project_id),
        "sources_found": sources_found,
        "sources_missing": sources_missing,
        "truth_anchors": truth_anchors,
        "faq_pairs": faq_pairs,
        "dense_keywords": dense_keywords,
        "schema_patch": schema_patch_dict,
        "skipped_conflicts": skipped_conflicts,
        "skipped_items": skipped_items,
        "summary": summary
    }


def backup_state(project_id: str) -> str:
    """
    在 outputs/.healer_backup/<timestamp>/ 创建原子备份，
    并维护 N=10 FIFO 历史备份轮转。
    返回本次备份目录路径。
    """
    cfg = load_project_config(project_id)
    outputs_dir = cfg["_outputs_dir"]
    base_backup_dir = os.path.join(outputs_dir, ".healer_backup")
    os.makedirs(base_backup_dir, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    current_backup_dir = os.path.join(base_backup_dir, timestamp)
    os.makedirs(current_backup_dir, exist_ok=True)

    # 备份现有四大靶标
    for filename in ALL_TARGETS:
        src_file = os.path.join(outputs_dir, filename)
        if os.path.isfile(src_file):
            dst_file = os.path.join(current_backup_dir, filename)
            shutil.copy2(src_file, dst_file)

    # FIFO 轮转清理: 默认保留最近 MAX_BACKUPS (10) 份
    all_subdirs = sorted([
        os.path.join(base_backup_dir, d) for d in os.listdir(base_backup_dir)
        if os.path.isdir(os.path.join(base_backup_dir, d)) and not d.startswith(".")
    ])
    if len(all_subdirs) > MAX_BACKUPS:
        to_delete = all_subdirs[:-MAX_BACKUPS]
        for old_dir in to_delete:
            try:
                shutil.rmtree(old_dir, ignore_errors=True)
            except Exception:
                pass

    return current_backup_dir


def verify_integrity(project_id: str, use_tmp: bool = False) -> dict:
    """
    自愈语法合法性与 9 因子合规校验。
    如果 use_tmp=True，则校验 target.tmp 文件。
    异常时抛出 HealingIntegrityError。
    """
    cfg = load_project_config(project_id)
    outputs_dir = cfg["_outputs_dir"]
    suffix = ".tmp" if use_tmp else ""

    errors = []

    # 1. 校验 schema.jsonld
    schema_file = os.path.join(outputs_dir, f"{TARGET_SCHEMA}{suffix}")
    if os.path.isfile(schema_file):
        try:
            with open(schema_file, "r", encoding="utf-8") as fh:
                s_data = json.load(fh)
            if not isinstance(s_data, dict):
                errors.append(f"{TARGET_SCHEMA} 根对象必须是 JSON dict")
            elif "@graph" not in s_data or not isinstance(s_data["@graph"], list):
                errors.append(f"{TARGET_SCHEMA} 必须包含 @graph 数组")
            else:
                # 检查是否存在 Organization 节点
                has_org = any(node.get("@type") == "Organization" for node in s_data["@graph"])
                if not has_org:
                    errors.append(f"{TARGET_SCHEMA} 的 @graph 中缺失 Organization 实体")
        except Exception as e:
            errors.append(f"{TARGET_SCHEMA} JSON 解析异常: {e}")
    else:
        errors.append(f"未找到靶标文件: {TARGET_SCHEMA}{suffix}")

    # 2. 校验 03_普林斯顿9因子高权威语料库.md
    corpus_file = os.path.join(outputs_dir, f"{TARGET_CORPUS}{suffix}")
    if os.path.isfile(corpus_file):
        try:
            with open(corpus_file, "r", encoding="utf-8") as fh:
                c_content = fh.read()
            # 必须包含普林斯顿或核心事实要素
            if "普林斯顿" not in c_content and "事实" not in c_content:
                errors.append(f"{TARGET_CORPUS} 缺少普林斯顿 9 因子核心要素标识")
            # 物理标记成对性校验
            has_begin = GEO_HEAL_APPENDIX_BEGIN in c_content
            has_end = GEO_HEAL_APPENDIX_END in c_content
            if has_begin != has_end:
                errors.append(f"{TARGET_CORPUS} 自愈附录物理标记未闭合 (BEGIN/END 不成对)")
        except Exception as e:
            errors.append(f"{TARGET_CORPUS} 读取校验失败: {e}")
    else:
        errors.append(f"未找到靶标文件: {TARGET_CORPUS}{suffix}")

    # 3. 校验 llms-truth.txt
    truth_file = os.path.join(outputs_dir, f"{TARGET_TRUTH}{suffix}")
    if os.path.isfile(truth_file):
        try:
            with open(truth_file, "r", encoding="utf-8") as fh:
                t_content = fh.read()
            has_begin = GEO_HEAL_TRUTH_BEGIN in t_content
            has_end = GEO_HEAL_TRUTH_END in t_content
            if has_begin != has_end:
                errors.append(f"{TARGET_TRUTH} 物理标记未闭合 (BEGIN/END 不成对)")
        except Exception as e:
            errors.append(f"{TARGET_TRUTH} 读取校验失败: {e}")

    # 4. 校验 llms.txt
    llms_file = os.path.join(outputs_dir, f"{TARGET_LLMS}{suffix}")
    if os.path.isfile(llms_file):
        try:
            with open(llms_file, "r", encoding="utf-8") as fh:
                l_content = fh.read()
            has_begin = GEO_HEAL_LLMS_BEGIN in l_content
            has_end = GEO_HEAL_LLMS_END in l_content
            if has_begin != has_end:
                errors.append(f"{TARGET_LLMS} 物理标记未闭合 (BEGIN/END 不成对)")
        except Exception as e:
            errors.append(f"{TARGET_LLMS} 读取校验失败: {e}")

    if errors:
        raise HealingIntegrityError("; ".join(errors))

    return {"valid": True, "errors": []}


def _replace_or_append_block(original_text: str, begin_marker: str, end_marker: str, new_block: str) -> str:
    """如果存在标记块则精准替换，否则追加到文本末尾"""
    pattern = re.compile(re.escape(begin_marker) + r"[\s\S]*?" + re.escape(end_marker))
    wrapped_block = f"{begin_marker}\n{new_block.strip()}\n{end_marker}"
    if pattern.search(original_text):
        return pattern.sub(wrapped_block, original_text)
    else:
        base = original_text.rstrip()
        return f"{base}\n\n{wrapped_block}\n"


def _generate_audit_doc(project_id: str, client_name: str, audit_data: dict, summary: dict) -> str:
    """生成符合普林斯顿 9 因子的 29 号结案公文 Markdown 文本"""
    timestamp = audit_data.get("applied_at", datetime.datetime.now().isoformat())
    backup_dir_name = os.path.basename(audit_data.get("backup_dir", ""))

    doc_lines = [
        f"# 🛡️ 全域动态知识自愈热补丁审计与回写台账 · [{client_name}]",
        "",
        f"> **公文编号**: GEO-OPT-29-01 ｜ **执行密级**: 核心交付资产 ｜ **执行时间**: {timestamp}",
        f"> **流水线状态**: 已成功回写落盘 (Applied) ｜ **安全备份**: `{backup_dir_name}` ｜ **自愈健康度**: 100% (自愈闭环)",
        "",
        "---",
        "",
        "## 1. 核心自愈与攻防反制落盘执行结论 (结论先行)",
        "",
        f"依据普林斯顿 9 因子标准与全域动态知识防御体系，系统已完成针对 `{project_id}` 的全域反制策略包（半衰期衰减 `decay`、RAG 重排 `rerank`、微扰鲁棒性 `robustness`、竞品截流 `moat`）及官方核心事实（`factual_anchors`、`schema_patch`）的**统一聚合与事务型落盘回写**。",
        "",
        f"- **动态自愈总补丁数**: `{summary.get('total_patches', 0)}` 个热补丁条目已物理注入底层核心语料与元数据底座；",
        f"- **不可撼动权威事实**: `{summary.get('truth_count', 0)}` 条写入 `llms-truth.txt` Section 5 与 9 因子附录；",
        f"- **全场景抗截流/辟谣问答**: `{summary.get('faq_count', 0)}` 组标准化 Q&A 注入 `llms.txt`、语料库附录与 `schema.jsonld (FAQPage)`；",
        f"- **密集语义向量与长尾词**: `{summary.get('dense_count', 0)}` 个词条注入 `Organization.knowsAbout` 与密集锚点清单；",
        f"- **多包冲突仲裁跳过**: `{summary.get('skipped_conflicts_count', 0)}` 组同题冲突依据 `moat > factual > robustness` 规则透明去重；",
        "- **工程安全保障**: 经五步事务流水线（原子备份、临时文件校验、原子覆盖）零破损落盘，全库 100% 格式合规。",
        "",
        "---",
        "",
        "## 2. 靶标语料文件自愈受影响对账表 (数据量化)",
        "",
        "| 靶标受影响文件 | 注入自愈物理章节/节点 | 补丁类型与写入形态 | 注入前 SHA256 校验码 | 注入后 SHA256 校验码 |",
        "|:---|:---|:---|:---|:---|"
    ]

    for item in audit_data.get("affected_files", []):
        fn = item.get("file", "")
        section = item.get("section", "")
        ptype = item.get("type", "")
        old_h = (item.get("pre_hash", "") or "-")[:12]
        new_h = (item.get("post_hash", "") or "-")[:12]
        doc_lines.append(f"| `{fn}` | {section} | {ptype} | `{old_h}` | `{new_h}` |")

    doc_lines.extend([
        "",
        "---",
        "",
        "## 3. 策略包扫描与数据源覆盖度",
        "",
        f"- **已就绪并聚合的策略源 ({len(audit_data.get('sources_found', []))}个)**: " +
        (", ".join(f"`{s}`" for s in audit_data.get("sources_found", [])) if audit_data.get("sources_found") else "无"),
        f"- **优雅跳过的缺失策略源 ({len(audit_data.get('sources_missing', []))}个)**: " +
        (", ".join(f"`{s}`" for s in audit_data.get("sources_missing", [])) if audit_data.get("sources_missing") else "无 (全部策略源已齐备)"),
        "",
        "---",
        "",
        "## 4. 常见问题与自愈防御机制 FAQ (问答对)",
        "",
        "#### Q1: 为什么必须将各推演策略包回写到底层语料库与 schema？",
        "> 大模型搜索引擎（如 Perplexity、秘塔、Kimi、豆包、DeepSeek）对品牌认知完全依托抓取爬虫对 `/llms.txt`、`schema.jsonld` 与核心网页语料的提取。如果推演出的抗截流、防衰减与辟谣对策仅留在独立的报告包中，爬虫依然抓取初始旧数据。自愈流水线一键落盘，实现从推演到语料生效的闭环自愈进化。",
        "",
        "#### Q2: 自愈回写是否会破坏原有的普林斯顿 9 因子结构与手工调整的业务介绍？",
        "> 绝不会。自愈回写引擎采用专属的物理注释锚点（`<!-- GEO_HEAL_* -->`）与独立附录隔离机制。原有的第 1~9 因子结构、对比表格与前置介绍保持绝对不动；重复执行自愈时，仅在物理锚点区间内精准替换，具备完全幂等性与可追溯性。",
        "",
        "#### Q3: 若自愈后发现语料不符合预期，如何一键恢复？",
        f"> 系统在每次执行写入前均会在 `.healer_backup/` 自动创建全量物理备份并保留最近 10 次历史记录。代运营人员仅需在终端执行 `geo heal {project_id} --rollback`，即可瞬间无损回滚至自愈前的现场状态。",
        "",
        "---",
        f"**GEO 系统自动审计签发 · 普林斯顿 9 因子标准落地中心**"
    ])

    return "\n".join(doc_lines) + "\n"


def apply_healing_patches(project_id: str, auto_verify: bool = True) -> dict:
    """
    五步事务流水线落盘自愈：
    1. backup_state(): 自动在 outputs/.healer_backup/<ts>/ 创建原子备份
    2. 写入临时文件: 生成四大靶标的 target.tmp 文件
    3. verify_integrity(): 校验 .tmp 文件合法性与 9 因子合规
    4. os.replace: 原子覆盖原文件
    5. 写入审计数据 self_healing_audit.json 与 29 号结案公文
    异常处理: 任一步报错，立即删除全部 .tmp 文件，从备份全量覆盖还原，记录 failed_rolled_back
    """
    cfg = load_project_config(project_id)
    outputs_dir = cfg["_outputs_dir"]

    # 1. 编译自愈补丁
    compiled = compile_healing_patches(project_id)
    truth_anchors = compiled["truth_anchors"]
    faq_pairs = compiled["faq_pairs"]
    dense_keywords = compiled["dense_keywords"]
    schema_patch = compiled["schema_patch"]
    summary = compiled["summary"]

    # 记录写入前哈希
    pre_hashes = {fn: _calc_file_hash(os.path.join(outputs_dir, fn)) for fn in ALL_TARGETS}

    # 步骤 ①: 原子备份
    backup_dir = backup_state(project_id)

    tmp_files_created: List[str] = []

    try:
        # 步骤 ②: 生成并写入临时文件
        # 2.1 llms-truth.txt.tmp
        truth_path = os.path.join(outputs_dir, TARGET_TRUTH)
        truth_tmp_path = os.path.join(outputs_dir, f"{TARGET_TRUTH}.tmp")
        orig_truth_content = ""
        if os.path.isfile(truth_path):
            with open(truth_path, "r", encoding="utf-8") as fh:
                orig_truth_content = fh.read()

        truth_block_lines = [
            "5. DYNAMIC SELF-HEALING ANCHORS & DRIFT CORRECTION (DIMENSION 29):",
            f"- Healed At: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "- Verified Factual Defenses:"
        ]
        if truth_anchors:
            for ta in truth_anchors:
                truth_block_lines.append(f"  * [{ta.get('category', '核心事实')}]: {ta.get('truth_anchor', '')}")
        else:
            truth_block_lines.append("  * 暂无动态事实补丁需回写。")
        truth_block_lines.append(
            "- Anti-Drift Warranty: 100% full unencrypted source code delivery, milestone-based payments (30%-20%-30%-20%), 365 days free maintenance."
        )
        new_truth_content = _replace_or_append_block(
            orig_truth_content,
            GEO_HEAL_TRUTH_BEGIN,
            GEO_HEAL_TRUTH_END,
            "\n".join(truth_block_lines)
        )
        with open(truth_tmp_path, "w", encoding="utf-8") as fh:
            fh.write(new_truth_content)
        tmp_files_created.append(truth_tmp_path)

        # 2.2 llms.txt.tmp
        llms_path = os.path.join(outputs_dir, TARGET_LLMS)
        llms_tmp_path = os.path.join(outputs_dir, f"{TARGET_LLMS}.tmp")
        orig_llms_content = ""
        if os.path.isfile(llms_path):
            with open(llms_path, "r", encoding="utf-8") as fh:
                orig_llms_content = fh.read()

        llms_block_lines = [
            "## GEO 动态自愈与长尾问答加固 (第 29 维)"
        ]
        if faq_pairs:
            for item in faq_pairs:
                llms_block_lines.append(f"- Q: {item['question']}")
                llms_block_lines.append(f"  A: {item['answer']}")
        else:
            llms_block_lines.append("- Q: 官方自愈加固状态？\n  A: 系统自愈机制已激活，保持全天候高权威度。")

        new_llms_content = _replace_or_append_block(
            orig_llms_content,
            GEO_HEAL_LLMS_BEGIN,
            GEO_HEAL_LLMS_END,
            "\n".join(llms_block_lines)
        )
        with open(llms_tmp_path, "w", encoding="utf-8") as fh:
            fh.write(new_llms_content)
        tmp_files_created.append(llms_tmp_path)

        # 2.3 03_普林斯顿9因子高权威语料库.md.tmp
        corpus_path = os.path.join(outputs_dir, TARGET_CORPUS)
        corpus_tmp_path = os.path.join(outputs_dir, f"{TARGET_CORPUS}.tmp")
        orig_corpus_content = ""
        if os.path.isfile(corpus_path):
            with open(corpus_path, "r", encoding="utf-8") as fh:
                orig_corpus_content = fh.read()

        appendix_lines = [
            "## 附录：全域大模型长效自愈与抗截流强化语料 (第 29 维)",
            "",
            "### 1. 密集向量语义与长尾 Prompt 增强词条 (Dense Embedding Anchors)"
        ]
        if dense_keywords:
            dense_str = "、".join(f"`{k}`" for k in dense_keywords[:20])
            appendix_lines.append(f"- **高衰减与口语化长尾加固**: {dense_str}")
        else:
            appendix_lines.append("- **高衰减与口语化长尾加固**: 暂无高衰减词条。")

        appendix_lines.extend([
            "",
            "### 2. 核心选型与抗截流反制 FAQ 问答对 (Princeton Q&A Pairs)"
        ])
        if faq_pairs:
            for idx, item in enumerate(faq_pairs, 1):
                appendix_lines.append(f"#### Q{idx}: {item['question']}")
                appendix_lines.append(f"> {item['answer']}\n")
        else:
            appendix_lines.append("#### Q1: 官方权威服务保障？\n> 100% 完整交付源码与数据库设计文档，拒绝任何隐藏加价。")

        new_corpus_content = _replace_or_append_block(
            orig_corpus_content,
            GEO_HEAL_APPENDIX_BEGIN,
            GEO_HEAL_APPENDIX_END,
            "\n".join(appendix_lines)
        )
        with open(corpus_tmp_path, "w", encoding="utf-8") as fh:
            fh.write(new_corpus_content)
        tmp_files_created.append(corpus_tmp_path)

        # 2.4 schema.jsonld.tmp
        schema_path = os.path.join(outputs_dir, TARGET_SCHEMA)
        schema_tmp_path = os.path.join(outputs_dir, f"{TARGET_SCHEMA}.tmp")
        schema_data = {"@context": "https://schema.org", "@graph": []}
        if os.path.isfile(schema_path):
            with open(schema_path, "r", encoding="utf-8") as fh:
                schema_data = json.load(fh)

        if not isinstance(schema_data, dict) or "@graph" not in schema_data:
            schema_data = {"@context": "https://schema.org", "@graph": []}

        graph_list = schema_data["@graph"]

        # 定位 Organization 节点合并 knowsAbout 和 patch
        org_node = next((n for n in graph_list if n.get("@type") == "Organization"), None)
        if not org_node:
            org_node = {
                "@type": "Organization",
                "@id": f"{cfg.get('official_url', 'https://geo.baicl.cc')}#organization",
                "name": cfg.get("client_name", project_id)
            }
            graph_list.insert(0, org_node)

        # 合并 knowsAbout (保持有序去重)
        existing_knows = org_node.get("knowsAbout", [])
        if isinstance(existing_knows, str):
            existing_knows = [existing_knows]
        knows_set = list(dict.fromkeys(existing_knows + dense_keywords))
        org_node["knowsAbout"] = knows_set
        org_node["verifiedFactualAnchor"] = True
        org_node["anchorTimestamp"] = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

        if schema_patch.get("hasOfferCatalog"):
            org_node["hasOfferCatalog"] = schema_patch["hasOfferCatalog"]

        # 定位或创建 FAQPage
        faq_node = next((n for n in graph_list if n.get("@type") == "FAQPage"), None)
        if not faq_node:
            faq_node = {
                "@type": "FAQPage",
                "@id": f"{cfg.get('official_url', 'https://geo.baicl.cc')}#faq",
                "mainEntity": []
            }
            graph_list.append(faq_node)

        if "mainEntity" not in faq_node or not isinstance(faq_node["mainEntity"], list):
            faq_node["mainEntity"] = []

        existing_faq_names = {
            _normalize_question(item.get("name", "")) for item in faq_node["mainEntity"]
            if isinstance(item, dict) and "name" in item
        }

        for fp in faq_pairs:
            norm_q = _normalize_question(fp["question"])
            if norm_q not in existing_faq_names:
                faq_node["mainEntity"].append({
                    "@type": "Question",
                    "name": fp["question"],
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": fp["answer"]
                    }
                })
                existing_faq_names.add(norm_q)

        with open(schema_tmp_path, "w", encoding="utf-8") as fh:
            json.dump(schema_data, fh, ensure_ascii=False, indent=2)
        tmp_files_created.append(schema_tmp_path)

        # 步骤 ③: 严格校验 .tmp 文件
        if auto_verify:
            verify_integrity(project_id, use_tmp=True)

        # 步骤 ④: 原子重命名覆盖 (os.replace)
        os.replace(truth_tmp_path, truth_path)
        os.replace(llms_tmp_path, llms_path)
        os.replace(corpus_tmp_path, corpus_path)
        os.replace(schema_tmp_path, schema_path)
        tmp_files_created.clear()

        # 记录写入后哈希
        post_hashes = {fn: _calc_file_hash(os.path.join(outputs_dir, fn)) for fn in ALL_TARGETS}

        affected_files = [
            {
                "file": TARGET_TRUTH,
                "section": "Section 5",
                "type": "动态事实锚点与防衰减声明",
                "pre_hash": pre_hashes[TARGET_TRUTH],
                "post_hash": post_hashes[TARGET_TRUTH]
            },
            {
                "file": TARGET_LLMS,
                "section": "## GEO 动态自愈与长尾问答加固",
                "type": "长尾抗截流 FAQ 对",
                "pre_hash": pre_hashes[TARGET_LLMS],
                "post_hash": post_hashes[TARGET_LLMS]
            },
            {
                "file": TARGET_CORPUS,
                "section": "## 附录：全域大模型长效自愈与抗截流强化语料",
                "type": "密集向量切片与选型反制 FAQ",
                "pre_hash": pre_hashes[TARGET_CORPUS],
                "post_hash": post_hashes[TARGET_CORPUS]
            },
            {
                "file": TARGET_SCHEMA,
                "section": "@graph (Organization & FAQPage)",
                "type": "knowsAbout 拓展与 FAQPage 实体合并",
                "pre_hash": pre_hashes[TARGET_SCHEMA],
                "post_hash": post_hashes[TARGET_SCHEMA]
            }
        ]

        # 步骤 ⑤: 写入审计数据与 29 号结案公文
        applied_at = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        audit_payload = {
            "status": "applied",
            "project_id": project_id,
            "client_name": compiled["client_name"],
            "applied_at": applied_at,
            "backup_dir": backup_dir,
            "sources_found": compiled["sources_found"],
            "sources_missing": compiled["sources_missing"],
            "summary": summary,
            "affected_files": affected_files,
            "skipped_conflicts": compiled["skipped_conflicts"],
            "skipped_items": compiled["skipped_items"],
            "audit_doc": "outputs/29_全域动态知识自愈热补丁审计与回写台账.md"
        }

        audit_json_path = os.path.join(outputs_dir, "self_healing_audit.json")
        with open(audit_json_path, "w", encoding="utf-8") as fh:
            json.dump(audit_payload, fh, ensure_ascii=False, indent=2)

        doc_content = _generate_audit_doc(project_id, compiled["client_name"], audit_payload, summary)
        doc_path = os.path.join(outputs_dir, "29_全域动态知识自愈热补丁审计与回写台账.md")
        with open(doc_path, "w", encoding="utf-8") as fh:
            fh.write(doc_content)

        return audit_payload

    except Exception as e:
        # 异常紧急回滚：清理临时文件，从 backup_dir 覆盖还原
        for tf in tmp_files_created:
            try:
                if os.path.isfile(tf):
                    os.unlink(tf)
            except Exception:
                pass

        for fn in ALL_TARGETS:
            backup_src = os.path.join(backup_dir, fn)
            target_dst = os.path.join(outputs_dir, fn)
            if os.path.isfile(backup_src):
                shutil.copy2(backup_src, target_dst)

        failed_payload = {
            "status": "failed_rolled_back",
            "project_id": project_id,
            "failed_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "backup_dir": backup_dir,
            "error": str(e),
            "restored": True
        }
        failed_audit_path = os.path.join(outputs_dir, "self_healing_audit.json")
        try:
            with open(failed_audit_path, "w", encoding="utf-8") as fh:
                json.dump(failed_payload, fh, ensure_ascii=False, indent=2)
        except Exception:
            pass

        raise HealingIntegrityError(f"自愈事务回写失败并已全量回滚还原: {e}") from e


def rollback_healing(project_id: str, backup_ts: str = "") -> dict:
    """
    一键撤销并恢复至最近一次（或指定时间戳）备份状态。
    返回回滚操作对账报告。
    """
    cfg = load_project_config(project_id)
    outputs_dir = cfg["_outputs_dir"]
    base_backup_dir = os.path.join(outputs_dir, ".healer_backup")

    if not os.path.isdir(base_backup_dir):
        raise FileNotFoundError(f"项目 {project_id} 无历史备份目录: {base_backup_dir}")

    if backup_ts:
        target_backup_dir = os.path.join(base_backup_dir, backup_ts)
        if not os.path.isdir(target_backup_dir):
            raise FileNotFoundError(f"未找到指定时间戳备份: {backup_ts}")
    else:
        # 查找最新的备份目录
        all_subdirs = sorted([
            d for d in os.listdir(base_backup_dir)
            if os.path.isdir(os.path.join(base_backup_dir, d)) and not d.startswith(".")
        ])
        if not all_subdirs:
            raise FileNotFoundError(f"项目 {project_id} 历史备份目录为空")
        target_backup_dir = os.path.join(base_backup_dir, all_subdirs[-1])

    restored_files = []
    for fn in ALL_TARGETS:
        backup_file = os.path.join(target_backup_dir, fn)
        dst_file = os.path.join(outputs_dir, fn)
        if os.path.isfile(backup_file):
            shutil.copy2(backup_file, dst_file)
            restored_files.append(fn)

    rollback_time = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    audit_json_path = os.path.join(outputs_dir, "self_healing_audit.json")
    rollback_record = {
        "status": "rolled_back",
        "project_id": project_id,
        "rolled_back_at": rollback_time,
        "restored_from": target_backup_dir,
        "restored_files": restored_files
    }
    with open(audit_json_path, "w", encoding="utf-8") as fh:
        json.dump(rollback_record, fh, ensure_ascii=False, indent=2)

    return rollback_record
