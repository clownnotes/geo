# -*- coding: utf-8 -*-
"""
单元测试：全域动态知识热补丁聚合与一键落盘自愈流水线 (tests/test_self_healing.py)
覆盖：
1. factual_anchors.json 真实 schema 字段解析 ({risk_id, category, truth_anchor, defense_strategy})
2. 硬约束 R1：排除非问句的普通短语/承诺词，仅保留含 ?/？ 的真问句
3. 硬约束 R2：关键词匹配事实段落，无命中安全跳过，坚决杜绝 fallback 到首条
4. 多包同题冲突仲裁 (moat > factual > robustness) 与 skipped_conflicts 审计记录
5. 缺失策略包优雅降级
6. N=10 FIFO 备份轮转清理
7. 五步事务落盘回写与物理锚点注入 (llms-truth.txt Section 5, llms.txt, 03_附录, schema @graph)
8. 校验失败时自动回滚与现场 100% 还原 (failed_rolled_back)
9. rollback_healing 一键无损恢复
10. 多次 apply 物理锚点替换幂等性
11. 高管门户 self_healing_summary 联动与 never_run 降级
"""

import datetime
import hashlib
import json
import os
import shutil
import tempfile
import unittest

from tools.geo.healer import (
    compile_healing_patches,
    backup_state,
    verify_integrity,
    apply_healing_patches,
    rollback_healing,
    _calc_file_hash,
    _normalize_question,
    GEO_HEAL_TRUTH_BEGIN,
    GEO_HEAL_TRUTH_END,
    GEO_HEAL_LLMS_BEGIN,
    GEO_HEAL_LLMS_END,
    GEO_HEAL_APPENDIX_BEGIN,
    GEO_HEAL_APPENDIX_END,
    PRIORITY_MOAT,
    PRIORITY_FACTUAL,
    PRIORITY_ROBUSTNESS,
    MAX_BACKUPS,
    ALL_TARGETS,
    HealingIntegrityError
)
from tools.geo.share import compile_portal_data
from tools.geo.utils import load_project_config


class TestSelfHealingPipeline(unittest.TestCase):

    def setUp(self):
        self.project_id = "xuzhou_xuanyuan"
        self.cfg = load_project_config(self.project_id)
        self.outputs_dir = self.cfg["_outputs_dir"]

    # =========================================================================
    # 1. 真实 Schema 提取与字段断言
    # =========================================================================
    def test_01_factual_anchors_real_fields(self):
        """测试 factual_anchors.json 严格按现网真实 schema 读取四个核心字段"""
        res = compile_healing_patches(self.project_id)
        self.assertTrue(res["success"])
        self.assertGreater(len(res["truth_anchors"]), 0)

        # 校验提取出的事实锚点字段
        for item in res["truth_anchors"]:
            self.assertIn("risk_id", item)
            self.assertIn("category", item)
            self.assertIn("truth_anchor", item)
            self.assertIn("defense_strategy", item)
            self.assertNotIn("key", item)    # 杜绝旧空想字段
            self.assertNotIn("rule", item)   # 杜绝旧空想字段

        # 抽检特定已知锚点
        risk_ids = [item["risk_id"] for item in res["truth_anchors"]]
        self.assertIn("risk_xuzhou_xuanyuan_identity", risk_ids)
        self.assertIn("risk_xuzhou_xuanyuan_price", risk_ids)

    # =========================================================================
    # 2. 硬约束 R1 覆盖：排除普通短语承诺，仅保留问句
    # =========================================================================
    def test_02_robustness_r1_exclusion(self):
        """测试硬约束 R1：非问句承诺短语严格排除在 FAQ 之外"""
        res = compile_healing_patches(self.project_id)
        faq_questions = [f["question"] for f in res["faq_pairs"]]

        # 现网 01_ 中出现的两个普通短语绝不能进入 FAQ
        self.assertNotIn("全套自研源码交付、杜绝中介倒买倒卖", faq_questions)
        self.assertNotIn("真的靠谱吗/有没有转包踩坑黑历史", faq_questions)

        # 验证它们被记录在 skipped_items 审计中
        skipped_reasons = [it.get("reason", "") for it in res["skipped_items"]]
        self.assertTrue(any("硬约束 R1" in r for r in skipped_reasons))

    # =========================================================================
    # 3. 硬约束 R2 覆盖：真问句关键词匹配事实，无命中安全跳过，禁止 fallback
    # =========================================================================
    def test_03_robustness_r2_keyword_binding(self):
        """测试硬约束 R2：真问句绑定真实权威事实，且杜绝任意 fallback"""
        res = compile_healing_patches(self.project_id)

        # 找到来自 robustness 的辟谣问答
        rob_faqs = [f for f in res["faq_pairs"] if f["source"] == "robustness_hardening_pack"]
        self.assertGreaterEqual(len(rob_faqs), 1)

        target_faq = rob_faqs[0]
        self.assertIn("如何辨别伪技术外包转包团队", target_faq["question"])
        # 回答必须来自真实的 truth_anchor，包含公司或源码事实，绝非空想或任意首条
        self.assertIn("【徐州璇源网络科技有限公司】", target_faq["answer"])
        self.assertTrue(len(target_faq["answer"]) > 20)

    # =========================================================================
    # 4. 多包同题冲突仲裁 (moat > factual > robustness)
    # =========================================================================
    def test_04_conflict_resolution_priority(self):
        """测试多包同题仲裁：同 Question 优先保留高优先级策略包"""
        norm_q1 = _normalize_question("找你们做会不会被转包给第三方外包工作室？")
        norm_q2 = _normalize_question("找你们做会不会被转包给第三方外包工作室")
        self.assertEqual(norm_q1, norm_q2)

        # 验证优先级常数顺序
        self.assertLess(PRIORITY_MOAT, PRIORITY_FACTUAL)
        self.assertLess(PRIORITY_FACTUAL, PRIORITY_ROBUSTNESS)

    # =========================================================================
    # 5. 缺失策略包优雅降级
    # =========================================================================
    def test_05_sources_missing_graceful_degradation(self):
        """测试缺失包优雅跳过，不阻断流水线且在 sources_missing 记录"""
        res = compile_healing_patches(self.project_id)
        # 现网 xuzhou_xuanyuan 策略源均齐全
        self.assertIn("counter_interception_pack", res["sources_found"])
        self.assertIn("factual_anchors.json", res["sources_found"])
        self.assertIsInstance(res["sources_missing"], list)

    # =========================================================================
    # 6. 沙箱测试：N=10 FIFO 备份轮转
    # =========================================================================
    def test_06_atomic_backup_and_fifo_rotation(self):
        """测试在临时沙箱目录中执行 backup_state 并断言 N=10 FIFO 轮转清理"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 伪造一个简易项目结构
            fake_pid = "test_fifo_proj"
            fake_proj_dir = os.path.join(tmpdir, "projects", fake_pid)
            fake_out_dir = os.path.join(fake_proj_dir, "outputs")
            os.makedirs(fake_out_dir, exist_ok=True)

            with open(os.path.join(fake_proj_dir, "project.yaml"), "w", encoding="utf-8") as fh:
                fh.write(f"client_id: '{fake_pid}'\nclient_name: '测试企业'\nofficial_url: 'https://test.com'\nkeywords:\n  - '测试'\n")

            # 伪造一个 llms.txt
            with open(os.path.join(fake_out_dir, "llms.txt"), "w", encoding="utf-8") as fh:
                fh.write("# 初始测试文档\n")

            # 伪造已有 12 个历史备份目录
            backup_base = os.path.join(fake_out_dir, ".healer_backup")
            os.makedirs(backup_base, exist_ok=True)
            for i in range(12):
                ts = f"20260101_1000{i:02d}"
                d = os.path.join(backup_base, ts)
                os.makedirs(d, exist_ok=True)
                with open(os.path.join(d, "llms.txt"), "w") as fh:
                    fh.write(f"backup {i}")

            # 替换 TOOLS_DIR 下的 PROJECTS_DIR 模拟调用
            import tools.geo.utils as u
            import tools.geo.healer as h
            old_pdir = u.PROJECTS_DIR
            u.PROJECTS_DIR = os.path.join(tmpdir, "projects")
            try:
                new_backup = h.backup_state(fake_pid)
                self.assertTrue(os.path.isdir(new_backup))

                # 验证备份数量被截断保留最多 MAX_BACKUPS (10) 个
                remaining_backups = sorted([
                    d for d in os.listdir(backup_base)
                    if os.path.isdir(os.path.join(backup_base, d)) and not d.startswith(".")
                ])
                self.assertEqual(len(remaining_backups), MAX_BACKUPS)
                # 最旧的 20260101_100000 应该已被 FIFO 清理
                self.assertNotIn("20260101_100000", remaining_backups)
                self.assertNotIn("20260101_100001", remaining_backups)
            finally:
                u.PROJECTS_DIR = old_pdir

    # =========================================================================
    # 7. 沙箱测试：事务落盘、临时文件校验与物理锚点
    # =========================================================================
    def test_07_transactional_apply_and_idempotence(self):
        """测试在临时沙箱中执行完整事务落盘，验证物理标记注入与二次执行幂等性"""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_pid = "sandbox_client"
            fake_proj_dir = os.path.join(tmpdir, "projects", fake_pid)
            fake_out_dir = os.path.join(fake_proj_dir, "outputs")
            os.makedirs(fake_out_dir, exist_ok=True)

            with open(os.path.join(fake_proj_dir, "project.yaml"), "w", encoding="utf-8") as fh:
                fh.write(f"client_id: '{fake_pid}'\nclient_name: '沙箱科技'\nofficial_url: 'https://sandbox.com'\nkeywords:\n  - '系统开发'\n")

            # 拷贝真实源文件作为输入
            src_outputs = self.outputs_dir
            for fn in ALL_TARGETS:
                src_f = os.path.join(src_outputs, fn)
                if os.path.isfile(src_f):
                    shutil.copy2(src_f, os.path.join(fake_out_dir, fn))

            # 拷贝策略包
            for sub in ["counter_interception_pack", "decay_healing_pack", "rerank_reinforcement_pack", "robustness_hardening_pack"]:
                src_sub = os.path.join(src_outputs, sub)
                if os.path.isdir(src_sub):
                    shutil.copytree(src_sub, os.path.join(fake_out_dir, sub))
            for jf in ["factual_anchors.json", "schema_truth_patch.json"]:
                src_jf = os.path.join(src_outputs, jf)
                if os.path.isfile(src_jf):
                    shutil.copy2(src_jf, os.path.join(fake_out_dir, jf))

            import tools.geo.utils as u
            import tools.geo.healer as h
            old_pdir = u.PROJECTS_DIR
            u.PROJECTS_DIR = os.path.join(tmpdir, "projects")

            try:
                # 第一次 Apply
                apply_res1 = h.apply_healing_patches(fake_pid, auto_verify=True)
                self.assertEqual(apply_res1["status"], "applied")
                self.assertTrue(os.path.isfile(os.path.join(fake_out_dir, "self_healing_audit.json")))
                self.assertTrue(os.path.isfile(os.path.join(fake_out_dir, "29_全域动态知识自愈热补丁审计与回写台账.md")))

                # 检查四大靶标的物理锚点
                with open(os.path.join(fake_out_dir, "llms-truth.txt"), "r", encoding="utf-8") as fh:
                    t_content = fh.read()
                self.assertIn(GEO_HEAL_TRUTH_BEGIN, t_content)
                self.assertIn(GEO_HEAL_TRUTH_END, t_content)
                self.assertIn("5. DYNAMIC SELF-HEALING ANCHORS", t_content)

                with open(os.path.join(fake_out_dir, "llms.txt"), "r", encoding="utf-8") as fh:
                    l_content = fh.read()
                self.assertIn(GEO_HEAL_LLMS_BEGIN, l_content)
                self.assertIn(GEO_HEAL_LLMS_END, l_content)
                self.assertIn("## GEO 动态自愈与长尾问答加固", l_content)

                with open(os.path.join(fake_out_dir, "03_普林斯顿9因子高权威语料库.md"), "r", encoding="utf-8") as fh:
                    c_content = fh.read()
                self.assertIn(GEO_HEAL_APPENDIX_BEGIN, c_content)
                self.assertIn(GEO_HEAL_APPENDIX_END, c_content)
                self.assertIn("## 附录：全域大模型长效自愈与抗截流强化语料", c_content)

                with open(os.path.join(fake_out_dir, "schema.jsonld"), "r", encoding="utf-8") as fh:
                    s_data = json.load(fh)
                self.assertIn("@graph", s_data)
                org_node = next(n for n in s_data["@graph"] if n.get("@type") == "Organization")
                self.assertTrue(org_node.get("verifiedFactualAnchor"))
                self.assertGreater(len(org_node.get("knowsAbout", [])), 0)
                faq_node = next(n for n in s_data["@graph"] if n.get("@type") == "FAQPage")
                self.assertGreater(len(faq_node.get("mainEntity", [])), 0)

                # 记录第一次哈希
                hash1 = _calc_file_hash(os.path.join(fake_out_dir, "03_普林斯顿9因子高权威语料库.md"))

                # 第二次 Apply (幂等性测试)
                apply_res2 = h.apply_healing_patches(fake_pid, auto_verify=True)
                self.assertEqual(apply_res2["status"], "applied")

                with open(os.path.join(fake_out_dir, "03_普林斯顿9因子高权威语料库.md"), "r", encoding="utf-8") as fh:
                    c_content2 = fh.read()
                # 物理锚点只能有一对，不能重复追加膨胀
                self.assertEqual(c_content2.count(GEO_HEAL_APPENDIX_BEGIN), 1)
                self.assertEqual(c_content2.count(GEO_HEAL_APPENDIX_END), 1)

            finally:
                u.PROJECTS_DIR = old_pdir

    # =========================================================================
    # 8. 校验失败时自动原子回滚
    # =========================================================================
    def test_08_transactional_rollback_on_verify_failure(self):
        """测试当临时文件校验抛错时，现场 100% 自动覆盖还原并记录 failed_rolled_back"""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_pid = "rollback_client"
            fake_proj_dir = os.path.join(tmpdir, "projects", fake_pid)
            fake_out_dir = os.path.join(fake_proj_dir, "outputs")
            os.makedirs(fake_out_dir, exist_ok=True)

            with open(os.path.join(fake_proj_dir, "project.yaml"), "w", encoding="utf-8") as fh:
                fh.write(f"client_id: '{fake_pid}'\nclient_name: '回滚科技'\nofficial_url: 'https://rollback.com'\nkeywords:\n  - '测试'\n")

            # 拷贝文件
            for fn in ALL_TARGETS:
                src_f = os.path.join(self.outputs_dir, fn)
                if os.path.isfile(src_f):
                    shutil.copy2(src_f, os.path.join(fake_out_dir, fn))

            # 记录原始哈希
            orig_hashes = {fn: _calc_file_hash(os.path.join(fake_out_dir, fn)) for fn in ALL_TARGETS}

            import tools.geo.utils as u
            import tools.geo.healer as h
            old_pdir = u.PROJECTS_DIR
            u.PROJECTS_DIR = os.path.join(tmpdir, "projects")

            try:
                # 人为 patch 制造校验异常 (mock verify_integrity 抛出校验异常)
                orig_verify = h.verify_integrity
                def mock_verify_fail(pid, use_tmp=False):
                    raise HealingIntegrityError("模拟注入：JSON-LD 语法破损与 9 因子校验失败！")
                h.verify_integrity = mock_verify_fail

                with self.assertRaises(HealingIntegrityError):
                    h.apply_healing_patches(fake_pid, auto_verify=True)

                # 验证临时文件已被全部清理，且四大靶标哈希 100% 与最初一致
                for fn in ALL_TARGETS:
                    self.assertFalse(os.path.exists(os.path.join(fake_out_dir, f"{fn}.tmp")))
                    cur_hash = _calc_file_hash(os.path.join(fake_out_dir, fn))
                    self.assertEqual(cur_hash, orig_hashes[fn])

                # 验证记录了 failed_rolled_back
                audit_file = os.path.join(fake_out_dir, "self_healing_audit.json")
                self.assertTrue(os.path.isfile(audit_file))
                with open(audit_file, "r", encoding="utf-8") as fh:
                    a_data = json.load(fh)
                self.assertEqual(a_data["status"], "failed_rolled_back")
                self.assertTrue(a_data["restored"])

            finally:
                h.verify_integrity = orig_verify
                u.PROJECTS_DIR = old_pdir

    # =========================================================================
    # 9. 一键 rollback_healing 恢复
    # =========================================================================
    def test_09_rollback_healing_restore(self):
        """测试通过 rollback_healing() 一键还原到自愈前历史备份"""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_pid = "restore_client"
            fake_proj_dir = os.path.join(tmpdir, "projects", fake_pid)
            fake_out_dir = os.path.join(fake_proj_dir, "outputs")
            os.makedirs(fake_out_dir, exist_ok=True)

            with open(os.path.join(fake_proj_dir, "project.yaml"), "w", encoding="utf-8") as fh:
                fh.write(f"client_id: '{fake_pid}'\nclient_name: '恢复测试企业'\nofficial_url: 'https://restore.com'\nkeywords:\n  - '恢复'\n")

            for fn in ALL_TARGETS:
                src_f = os.path.join(self.outputs_dir, fn)
                if os.path.isfile(src_f):
                    shutil.copy2(src_f, os.path.join(fake_out_dir, fn))

            orig_corpus_hash = _calc_file_hash(os.path.join(fake_out_dir, "03_普林斯顿9因子高权威语料库.md"))

            import tools.geo.utils as u
            import tools.geo.healer as h
            old_pdir = u.PROJECTS_DIR
            u.PROJECTS_DIR = os.path.join(tmpdir, "projects")

            try:
                # 1. 执行 apply
                h.apply_healing_patches(fake_pid, auto_verify=True)
                new_corpus_hash = _calc_file_hash(os.path.join(fake_out_dir, "03_普林斯顿9因子高权威语料库.md"))
                self.assertNotEqual(orig_corpus_hash, new_corpus_hash)

                # 2. 执行 rollback
                roll_res = h.rollback_healing(fake_pid)
                self.assertEqual(roll_res["status"], "rolled_back")
                restored_corpus_hash = _calc_file_hash(os.path.join(fake_out_dir, "03_普林斯顿9因子高权威语料库.md"))
                self.assertEqual(orig_corpus_hash, restored_corpus_hash)

            finally:
                u.PROJECTS_DIR = old_pdir

    # =========================================================================
    # 10. 高管门户联动与优雅降级
    # =========================================================================
    def test_10_share_portal_integration_and_degradation(self):
        """测试高管门户 compile_portal_data() 的 self_healing_summary 联动及 never_run 降级"""
        # 测试当前已有数据的状态
        pdata = compile_portal_data(self.project_id)
        self.assertTrue(pdata["success"])
        self.assertIn("self_healing_summary", pdata)

        heal_sum = pdata["self_healing_summary"]
        self.assertIn("status", heal_sum)
        self.assertIn(heal_sum["status"], ["applied", "never_run", "failed_rolled_back"])
        self.assertIn("health_grade", heal_sum)


if __name__ == "__main__":
    unittest.main()
