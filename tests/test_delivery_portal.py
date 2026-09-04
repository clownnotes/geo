# -*- coding: utf-8 -*-
"""
单元测试：甲方高管专属全域大模型商业战果只读交付门户 (tests/test_delivery_portal.py)
"""

import os
import json
import tempfile
import unittest

from tools.geo.share import (
    compile_portal_data,
    create_share_link,
    refresh_share_token,
    verify_share_access,
    get_share_portal_data,
    export_offline_portal_html,
    _calc_file_sha256
)


class TestDeliveryPortal(unittest.TestCase):

    def setUp(self):
        self.project_id = "xuzhou_xuanyuan"

    def test_compile_portal_data_real_field_mapping(self):
        """测试高管交付门户数据聚合与真实字段映射（严格杜绝造假）"""
        data = compile_portal_data(self.project_id, token="test_token_123")
        self.assertTrue(data["success"])
        self.assertEqual(data["project_id"], self.project_id)
        self.assertIn("client_name", data)
        self.assertIn("brand_name", data)

        # 1. 核心商业 KPI 摘要 (Hero)
        exec_sum = data["executive_summary"]
        self.assertEqual(exec_sum["mpi_score"], 79.5)
        self.assertIn("强势竞争", exec_sum["mpi_grade"])
        self.assertEqual(exec_sum["annual_aev_yuan"], 29018)
        self.assertEqual(exec_sum["annual_ad_saving_wan"], 2.9)
        self.assertEqual(exec_sum["intent_coverage_count"], 5)
        self.assertEqual(exec_sum["first_recommend_rate_pct"], 60.0)
        self.assertIn("AAA", exec_sum["delivery_grade"])

        # 2. 实测大模型心智矩阵 (仅包含有探针的 3 大模型，绝无臆造元宝探针打分)
        models = data["models_mindshare"]
        self.assertIn("doubao", models)
        self.assertIn("deepseek", models)
        self.assertIn("kimi", models)
        self.assertNotIn("yuanbao", models)  # 严格对齐 P0 #2: 元宝无真实探针，不得在探针矩阵塞假分

        for m_key in ["doubao", "deepseek", "kimi"]:
            m_data = models[m_key]
            self.assertIn("name", m_data)
            self.assertGreaterEqual(m_data["top1_rate_pct"], 0.0)
            self.assertGreaterEqual(m_data["mention_rate_pct"], 0.0)
            self.assertGreaterEqual(m_data["avg_score"], 0.0)
            self.assertEqual(m_data["probe_count"], 5)

        # 微信搜一搜展示为渠道覆盖代理
        wechat_proxy = data["wechat_yuanbao_channel"]
        self.assertEqual(wechat_proxy["name"], "腾讯元宝 (微信搜一搜独占生态)")
        self.assertIn("非实时 API 探针", wechat_proxy["status_desc"])

        # 3. 普林斯顿 9 因子与爬虫保真度
        auth = data["authority_assurance"]
        self.assertAlmostEqual(auth["princeton_score"], 65.1, delta=1.0)
        self.assertIn("B 级", auth["princeton_grade"])
        self.assertEqual(auth["average_fidelity_score"], 100.0)
        self.assertTrue(auth["all_passed"])
        self.assertIn("toutiao", auth["crawler_fidelities"])
        self.assertIn("wechat", auth["crawler_fidelities"])
        self.assertIn("deepseek", auth["crawler_fidelities"])

        # 4. 全网分发存活台账推导
        dist = data["distribution_ledger"]
        self.assertEqual(dist["completion_rate_pct"], 28.6)
        channels = dist["channels"]
        self.assertIn("toutiao", channels)
        self.assertIn("display_status", channels["toutiao"])
        self.assertIn("status_label", channels["toutiao"])
        self.assertIn(channels["toutiao"]["display_status"], ["alive", "pending_audit", "dead", "unfilled"])

        # 5. 商业结案证书
        cert = data["certificate_summary"]
        self.assertTrue(cert["has_certificate"])
        self.assertNotEqual(cert["sha256_fingerprint"], "N/A")
        self.assertIn("/api/share/test_token_123/certificate", cert["view_url"])

        # 6. 向后兼容字段测试
        self.assertIn("deliverables", data)
        self.assertIn("acceptance_summary", data)
        self.assertIn("metrics", data)

    def test_compile_portal_data_graceful_fallback(self):
        """测试缺少数据或不存在项目时的优雅降级（禁止抛出未捕获异常，且履约评级为待验收）"""
        # 对不存在的项目 ID
        data = compile_portal_data("non_existent_project_xyz", token="xyz")
        self.assertTrue(data["success"])
        exec_sum = data["executive_summary"]
        self.assertIsNone(exec_sum["mpi_score"])
        self.assertIsNone(exec_sum["first_recommend_rate_pct"])
        self.assertEqual(exec_sum["annual_ad_saving_wan"], 0.0)
        self.assertEqual(exec_sum["delivery_grade"], "待验收")
        self.assertEqual(data["certificate_summary"]["delivery_grade"], "待验收")
        self.assertEqual(data["models_mindshare"], {})
        self.assertIsNone(data["authority_assurance"]["princeton_score"])
        self.assertFalse(data["certificate_summary"]["has_certificate"])

    def test_share_token_refresh_lifecycle(self):
        """测试 Token 单活轮转刷新生命周期：作废历史 Token 并生成新链接"""
        # 创建第一个 Token
        link1 = create_share_link(self.project_id, expire_days=10, pin="1111")
        tok1 = link1["token"]

        # 验证 tok1 正常可用
        ok, status, _ = verify_share_access(tok1, client_pin="1111")
        self.assertTrue(ok)

        # 执行单活刷新
        refresh_res = refresh_share_token(self.project_id, expire_days=30, pin="2222")
        self.assertTrue(refresh_res["success"])
        self.assertGreaterEqual(refresh_res["revoked_old_count"], 1)
        tok2 = refresh_res["token"]

        # 验证历史 tok1 已被强制废止
        ok_old, status_old, _ = verify_share_access(tok1, client_pin="1111")
        self.assertFalse(ok_old)
        self.assertEqual(status_old, "revoked")

        # 验证新 tok2 正常使用正确 PIN
        ok_new, status_new, _ = verify_share_access(tok2, client_pin="2222")
        self.assertTrue(ok_new)

        # 验证新 tok2 错误 PIN 拦截
        ok_bad, status_bad, _ = verify_share_access(tok2, client_pin="0000")
        self.assertFalse(ok_bad)
        self.assertEqual(status_bad, "invalid_pin")

    def test_export_offline_portal_html_no_cdn(self):
        """测试导出离线单文件高管大屏：完全内联，严格断言无外部 CDN 依赖且关键布局样式齐备"""
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tf:
            target_path = tf.name

        try:
            res = export_offline_portal_html(self.project_id, target_path)
            self.assertTrue(res["success"])
            self.assertEqual(res["target_file"], target_path)
            self.assertGreater(res["size_kb"], 50.0)

            with open(target_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 断言内联初始数据与安全 Stub 注入
            self.assertIn("window.__INITIAL_PORTAL_DATA__", content)
            self.assertIn("window.__IS_OFFLINE_EXPORT__ = true", content)
            self.assertIn("window.lucide", content)
            self.assertIn("徐州璇源网络科技有限公司", content)

            # 严格断言：绝无外部 CDN 运行时网络依赖 (对齐 Cursor P0 #4 / P0 #1)
            self.assertNotIn("cdn.tailwindcss.com", content)
            self.assertNotIn("unpkg.com", content)
            self.assertNotIn("cdn.jsdelivr.net/npm/marked", content)

            # 严格断言：离线 CSS 覆盖大屏骨架与关键选择器，杜绝 Airplane Mode 塌布局 (对齐 Cursor 记录5 P0 #1)
            self.assertIn("Offline Standalone CSS", content)
            self.assertIn("header {", content)
            self.assertIn("#hero-mpi-score", content)
            self.assertIn(".bg-slate-900", content)
            self.assertIn(".grid", content)
            self.assertIn(".max-w-7xl", content)
            self.assertIn(".executive-card", content)
        finally:
            if os.path.exists(target_path):
                os.remove(target_path)

    def test_calc_file_sha256(self):
        """测试 SHA256 哈希指纹计算工具"""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tf:
            tf.write(b"Hello GEO Delivery Portal")
            p = tf.name
        try:
            h = _calc_file_sha256(p)
            self.assertEqual(len(h), 64)
            # 不存在的文件返回 N/A
            self.assertEqual(_calc_file_sha256("/non_existent_file_path.xyz"), "N/A")
        finally:
            if os.path.exists(p):
                os.remove(p)


if __name__ == "__main__":
    unittest.main()
