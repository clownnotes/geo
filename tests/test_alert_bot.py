#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单元测试：第 33 维 企微/飞书多端大模型战果晨报与异常声量即时告警机器人 (tests/test_alert_bot.py)
测试范围：
1. SSRF 强安全防护与内网阻断校验；
2. 晨报数据聚合真实性与事实红线（未实测严禁捏造，返回 None）；
3. 全维度声量异动检测器（P0 声誉、P1 截流、P1 爬虫阻断、P2 衰减）；
4. 飞书/企微/钉钉多端原生卡片协议生成（交互式卡片、按钮与 Markdown）；
5. 调度器纯本地 Dry-Run 仿真与历史台账持久化；
6. 33 号公文结案报告落盘与流水号防伪；
7. 高管交付大屏反哺与 never_run 优雅降级契约；
8. Web 服务端 REST API 鉴权拦截与路由响应。
"""

import os
import json
import unittest
from io import BytesIO
from unittest.mock import MagicMock

from tools.geo.alert_bot import (
    BriefingData,
    AnomalyAlert,
    MorningBriefingAggregator,
    InstantAnomalyDetector,
    WebhookCardFormatter,
    AlertBotDispatcher,
    run_alert_bot,
    generate_report_33_markdown,
)
from tools.geo.share import compile_portal_data
from tools.geo.server import GeoWebHandler, create_session
from tools.geo.crawler import is_ssrf_safe_url


class TestAlertBotPipeline(unittest.TestCase):
    """第 33 维告警与战果晨报机器人全生命周期测试套件"""

    def setUp(self):
        self.project_id = "xuzhou_xuanyuan"

    def test_01_ssrf_protection(self):
        """测试 1: SSRF 恶意内网探测拦截与合法公网地址校验"""
        # 1. 恶意探测内部私有回环
        safe_local, msg_local = is_ssrf_safe_url("http://192.168.1.100/webhook")
        self.assertFalse(safe_local)
        self.assertIn("安全策略拦截", msg_local)

        safe_10, msg_10 = is_ssrf_safe_url("http://10.254.1.1/hook")
        self.assertFalse(safe_10)

        # 2. 合法公网 Webhook
        safe_feishu, msg_feishu = is_ssrf_safe_url("https://open.feishu.cn/open-apis/bot/v2/hook/abc-123")
        self.assertTrue(safe_feishu)

        # 3. 调度器真实模式下传入非法内网地址必须直接抛出 ValueError
        dispatcher = AlertBotDispatcher(self.project_id)
        dummy_briefing = BriefingData(project_id="test", project_name="测试", date_str="2026-09-04")
        with self.assertRaises(ValueError) as ctx:
            dispatcher.dispatch(
                payload={"msg": "test"},
                webhook_url="http://192.168.0.5/hack",
                channel="wecom",
                briefing=dummy_briefing,
                alerts=[],
                dry_run=False  # 非 dry-run 触发网络拦截
            )
        self.assertIn("SSRF", str(ctx.exception))

    def test_02_data_aggregation_fact_redline(self):
        """测试 2: 真实资产数据聚合与未实测项目事实红线约束"""
        # 针对真实项目进行聚合
        aggregator = MorningBriefingAggregator(self.project_id)
        briefing = aggregator.aggregate()

        self.assertEqual(briefing.project_id, self.project_id)
        self.assertIsNotNone(briefing.top1_rate)
        self.assertIsNotNone(briefing.citation_count)
        self.assertIsNotNone(briefing.spider_requests_count)
        self.assertIsNotNone(briefing.reputation_score)
        self.assertTrue(briefing.portal_url.startswith("http://"))

        # 针对无资产空项目：严禁捏造任何假数据，指标必须恒为 None
        empty_aggregator = MorningBriefingAggregator("non_existent_dummy_project_999")
        empty_briefing = empty_aggregator.aggregate()

        self.assertIsNone(empty_briefing.top1_rate, "空项目首推率严禁捏造，必须为 None")
        self.assertIsNone(empty_briefing.citation_count, "空项目 Citation 严禁捏造，必须为 None")
        self.assertIsNone(empty_briefing.spider_requests_count, "空项目爬虫访问严禁捏造，必须为 None")
        self.assertIsNone(empty_briefing.reputation_score, "空项目声誉评分严禁捏造，必须为 None")
        self.assertEqual(empty_briefing.data_state.get("probe_30"), "pending")

    def test_03_anomaly_detector_levels(self):
        """测试 3: 全维度异动告警检测（P0、P1、P2 灵敏度与反制建议）"""
        # 1. 模拟声誉受损 (P0) 与首推跌破 50% (P1)
        mock_briefing = BriefingData(
            project_id="test_client",
            project_name="测试企业",
            date_str="2026-09-04",
            top1_rate=42.0,                  # 跌破 50% ➔ 触发 P1
            negative_exposure_rate=15.0,      # 负面曝光 > 0% ➔ 触发 P0
            reputation_score=72.0,            # BRS < 80 ➔ 触发 P0
            spider_requests_count=0,          # 爬虫归零 ➔ 触发 P1
            retention_rate=55.0               # 保鲜度 < 60% ➔ 触发 P2
        )
        detector = InstantAnomalyDetector("test_client", mock_briefing)
        alerts = detector.detect_anomalies()

        self.assertGreaterEqual(len(alerts), 4)
        levels = [a.level for a in alerts]
        self.assertIn("P0", levels)
        self.assertIn("P1", levels)
        self.assertIn("P2", levels)

        # 检查反制建议指令
        p0_alert = next(a for a in alerts if a.level == "P0")
        self.assertIn("geo sentiment", p0_alert.suggested_action)

        # 2. 健康项目不应触发任何异动
        healthy_briefing = BriefingData(
            project_id="healthy_client",
            project_name="健康企业",
            date_str="2026-09-04",
            top1_rate=95.0,
            negative_exposure_rate=0.0,
            reputation_score=98.0,
            spider_requests_count=350,
            retention_rate=88.0
        )
        healthy_detector = InstantAnomalyDetector("healthy_client", healthy_briefing)
        self.assertEqual(len(healthy_detector.detect_anomalies()), 0)

    def test_04_card_formatters(self):
        """测试 4: 飞书 Interactive、企微 Markdown、钉钉 ActionCard 格式协议"""
        briefing = BriefingData(
            project_id=self.project_id,
            project_name="徐州璇源网络科技有限公司",
            date_str="2026-09-04",
            top1_rate=88.5,
            citation_count=12,
            spider_requests_count=260,
            spider_top_agent="bytespider",
            rival_crack_status="ready_live",
            reputation_score=96.0,
            portal_url="http://127.0.0.1:8088/portal?auth=test_token"
        )
        alerts = [
            AnomalyAlert(
                alert_id="ALT-P1-001",
                level="P1",
                category="competitor_intercept",
                title="竞对拦截警报",
                description="发现竞对拦截词",
                suggested_action="运行 geo rival-crack",
                metric_val="42%",
                timestamp="2026-09-04 09:00:00"
            )
        ]

        fmt = WebhookCardFormatter()

        # 1. 飞书卡片校验
        feishu_card = fmt.format_feishu_card(briefing, alerts)
        self.assertEqual(feishu_card["msg_type"], "interactive")
        card_content = feishu_card["card"]
        self.assertTrue(card_content["config"]["wide_screen_mode"])
        self.assertIn("徐州璇源网络科技有限公司", card_content["header"]["title"]["content"])
        self.assertEqual(card_content["header"]["template"], "orange")  # 有 P1 告警使用 orange/carmine
        # 校验直达大屏按钮
        action_elements = [el for el in card_content["elements"] if el.get("tag") == "action"]
        self.assertTrue(len(action_elements) > 0)
        self.assertEqual(action_elements[0]["actions"][0]["url"], briefing.portal_url)

        # 2. 企微 Markdown 卡片校验
        wecom_card = fmt.format_wecom_card(briefing, alerts)
        self.assertEqual(wecom_card["msgtype"], "markdown")
        wecom_md = wecom_card["markdown"]["content"]
        self.assertIn("徐州璇源网络科技有限公司", wecom_md)
        self.assertIn(briefing.portal_url, wecom_md)
        self.assertIn("Top-1 综合首推率", wecom_md)

        # 3. 钉钉 ActionCard 校验
        ding_card = fmt.format_dingtalk_card(briefing, alerts)
        self.assertEqual(ding_card["msgtype"], "actionCard")
        self.assertEqual(ding_card["actionCard"]["singleURL"], briefing.portal_url)

    def test_05_dispatcher_dry_run_and_history(self):
        """测试 5: 调度器纯本地 Dry-Run 仿真与历史台账持久化"""
        dispatcher = AlertBotDispatcher(self.project_id)
        briefing = MorningBriefingAggregator(self.project_id).aggregate()
        payload = WebhookCardFormatter.format_feishu_card(briefing, [])

        res = dispatcher.dispatch(
            payload=payload,
            webhook_url="https://open.feishu.cn/open-apis/bot/v2/hook/dummy",
            channel="feishu",
            briefing=briefing,
            alerts=[],
            msg_type="briefing",
            dry_run=True
        )

        self.assertTrue(res["dry_run"])
        self.assertFalse(res["delivered"])
        self.assertEqual(res["status"], "success_dry_run")
        self.assertTrue(res["dispatch_id"].startswith("DSP-"))

        # 验证历史文件是否存在
        history = dispatcher._load_history()
        self.assertGreaterEqual(len(history), 1)
        self.assertEqual(history[-1]["dispatch_id"], res["dispatch_id"])

    def test_06_run_alert_bot_pipeline_and_report(self):
        """测试 6: 端到端运行主流水线并校验 33 号公文报告"""
        res = run_alert_bot(
            self.project_id,
            msg_type="briefing",
            channel="feishu",
            dry_run=True,
            save_report=True
        )

        self.assertEqual(res["project_id"], self.project_id)
        self.assertEqual(res["msg_type"], "briefing")
        self.assertIn("briefing", res)
        self.assertIn("dispatch_result", res)

        # 检查持久化公文
        report_file = res["report_file"]
        self.assertTrue(os.path.exists(report_file))
        with open(report_file, "r", encoding="utf-8") as f:
            md_text = f.read()

        self.assertIn("33_企微飞书多端大模型战果晨报与异常声量即时告警报告", md_text)
        self.assertIn("ALERT-BOT-", md_text, "报告应包含防伪校验流水号")
        self.assertIn("大模型 Top-1 综合首推率", md_text)
        self.assertIn("高管免密交付大屏", md_text)

    def test_07_portal_integration_and_never_run(self):
        """测试 7: 高管交付门户战果反哺与 never_run 优雅降级契约"""
        # 已有运行记录的项目
        portal_active = compile_portal_data(self.project_id)
        self.assertIn("alert_bot_summary", portal_active)
        summary_active = portal_active["alert_bot_summary"]
        self.assertTrue(summary_active["has_data"])
        self.assertEqual(summary_active["status"], "active")
        self.assertIn("🤖", summary_active["status_label"])
        self.assertGreaterEqual(summary_active["total_dispatched"], 1)

        # 检查 33 号报告映射
        self.assertIn("alert_bot_audit", portal_active["deliverables"])
        self.assertIn("33_企微飞书多端大模型战果晨报", portal_active["deliverables"]["alert_bot_audit"])

        # 未配置的项目 (_template)
        portal_empty = compile_portal_data("_template")
        self.assertIn("alert_bot_summary", portal_empty)
        summary_empty = portal_empty["alert_bot_summary"]
        self.assertFalse(summary_empty["has_data"])
        self.assertEqual(summary_empty["status"], "never_run")
        self.assertIn("⚪️", summary_empty["status_label"])

    def test_08_api_endpoints_and_auth(self):
        """测试 8: Web API 鉴权拦截与路由响应"""
        handler = GeoWebHandler.__new__(GeoWebHandler)
        handler.headers = {}
        handler.client_address = ("127.0.0.1", 54321)

        sent_chunks = []
        def mock_send(data, status=200):
            sent_chunks.append((status, data))

        handler.send_json = mock_send

        # 1. 未携带 Token 访问受保护接口必须被 401 拦截
        handler.path = f"/api/projects/{self.project_id}/alert-bot/history"
        handler.command = "GET"
        handler.do_GET()
        self.assertEqual(len(sent_chunks), 1)
        self.assertEqual(sent_chunks[0][0], 401)
        self.assertFalse(sent_chunks[0][1].get("success"))

        # 2. 携带有效 Bearer Token 访问 GET /alert-bot/history
        token = create_session("admin")
        handler.headers = {"Authorization": f"Bearer {token}"}
        sent_chunks.clear()
        handler.do_GET()
        self.assertEqual(len(sent_chunks), 1)
        self.assertEqual(sent_chunks[0][0], 200)
        self.assertTrue(sent_chunks[0][1].get("success"))
        self.assertIn("history", sent_chunks[0][1])

        # 3. 访问 GET /alert-bot/preview
        handler.path = f"/api/projects/{self.project_id}/alert-bot/preview?type=briefing&channel=feishu"
        sent_chunks.clear()
        handler.do_GET()
        self.assertEqual(len(sent_chunks), 1)
        self.assertEqual(sent_chunks[0][0], 200)
        self.assertTrue(sent_chunks[0][1].get("success"))
        self.assertIn("card_payload", sent_chunks[0][1])

        # 4. 访问 GET /alert-bot/report
        handler.path = f"/api/projects/{self.project_id}/alert-bot/report"
        sent_chunks.clear()
        handler.do_GET()
        self.assertEqual(len(sent_chunks), 1)
        self.assertEqual(sent_chunks[0][0], 200)
        self.assertIn("33_企微飞书多端大模型战果晨报", sent_chunks[0][1].get("content", ""))

        # 5. 访问 POST /alert-bot/send (带 dry_run=True)
        handler.path = f"/api/projects/{self.project_id}/alert-bot/send"
        handler.headers["Content-Length"] = "10"
        handler.read_json_body = lambda: {"type": "briefing", "channel": "wecom", "dry_run": True}
        sent_chunks.clear()
        handler.do_POST()
        self.assertEqual(len(sent_chunks), 1)
        self.assertEqual(sent_chunks[0][0], 200)
        self.assertTrue(sent_chunks[0][1].get("success"))
        self.assertTrue(sent_chunks[0][1]["data"]["dispatch_result"]["dry_run"])


if __name__ == "__main__":
    unittest.main()
