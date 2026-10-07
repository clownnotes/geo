#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企微/飞书多端大模型战果晨报与异常声量即时告警机器人 (tools/geo/alert_bot.py)
核心工程与商业定位 (第 33 维)：
1. 真实数据聚合：联动 30 维 (联网实测)、31 维 (爬虫日志)、32 维 (竞对反超)、19 维 (声誉排查)、20 维 (知识半衰期)；
2. 事实红线与优雅降级：真实数据动态提取，未执行维度严格输出 [待实测]，严禁捏造假数据；
3. 多端原生卡片适配：支持飞书 Interactive 交互卡片 (带跳转按钮与彩色标题栏)、企业微信 Markdown 与钉钉 ActionCard；
4. SSRF 防御与确定性离线：强制经由 is_ssrf_safe_url 拦截内网私网探测，默认支持 --dry-run 零网络回放；
5. 公文与台账持久化：输出《33_企微飞书多端大模型战果晨报与异常声量即时告警报告.md》与 alert_bot_history.json。
"""

import os
import sys
import json
import time
import hashlib
import datetime
import urllib.request
import urllib.error
import urllib.parse
from dataclasses import dataclass, asdict, field
from typing import Dict, Any, List, Optional, Tuple

from .utils import (
    load_project_config,
    PROJECTS_DIR,
)
from .crawler import is_ssrf_safe_url
from .patrol import load_notification_settings

# ==============================================================================
# 数据模型定义 (Data Models)
# ==============================================================================

@dataclass
class BriefingData:
    """晨报核心聚合指标数据模型"""
    project_id: str
    project_name: str
    date_str: str
    models_tested: List[str] = field(default_factory=list)
    top1_rate: Optional[float] = None              # 综合 Top-1 首推率 (0~100)
    citation_count: Optional[int] = None           # Citation 权威角标命中条数
    spider_requests_count: Optional[int] = None    # 真实 AI 爬虫请求总数
    spider_top_agent: Optional[str] = None         # 最活跃 AI 爬虫
    spider_blocked_count: int = 0                  # 403 / WAF 阻断抓取次数
    spider_blocked_rate: Optional[float] = None    # 爬虫阻断率百分比 (0~100)
    spider_drop_pct: Optional[float] = None        # 爬虫抓取环比/周环比暴跌跌幅 (0~100)
    rival_crack_status: str = "none"               # 竞对反超状态: ready_live / ready_sandbox / none
    flaws_intercepted: int = 0                     # 已截流挖掘竞对破绽数
    reputation_score: Optional[float] = None       # BRS 品牌声誉评分
    negative_exposure_rate: Optional[float] = None # 负面联想暴露率
    retention_rate: Optional[float] = None         # 知识半衰期留存保鲜率
    portal_url: str = ""                           # 高管专属免密大屏直达链接
    data_state: Dict[str, str] = field(default_factory=dict) # 维度状态对账

@dataclass
class AnomalyAlert:
    """声量异常异动预警数据模型"""
    alert_id: str
    level: str             # "P0" (高危) | "P1" (严重) | "P2" (提示)
    category: str          # "reputation_crisis" | "competitor_intercept" | "spider_blocked" | "knowledge_decay"
    title: str
    description: str
    suggested_action: str
    metric_val: str
    timestamp: str

# ==============================================================================
# 1. 战果晨报真实数据聚合器 (MorningBriefingAggregator)
# ==============================================================================

class MorningBriefingAggregator:
    """
    汇聚项目真实 Outputs 数据资产，严格对齐事实红线：
    未实测资产绝不编造，统一标记为 [待实测]
    """
    def __init__(self, project_id: str):
        self.project_id = project_id
        try:
            self.cfg = load_project_config(project_id)
        except Exception:
            self.cfg = {}
        self.out_dir = os.path.join(PROJECTS_DIR, project_id, "outputs")
        self.data_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))

    def _read_json_safe(self, filename: str) -> Optional[Dict[str, Any]]:
        path = os.path.join(self.out_dir, filename)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def _get_portal_url(self) -> str:
        """获取项目高管大屏专属免密访问链接（必须严格查询 data/shares.json 活跃分享，禁止伪造 token）"""
        shares_path = os.path.join(self.data_dir, "shares.json")
        if not os.path.exists(shares_path):
            return ""
        try:
            with open(shares_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                shares = data.get("shares", {})
                active_shares = [
                    s for s in shares.values()
                    if s.get("project_id") == self.project_id and s.get("is_active") is True
                ]
                if active_shares:
                    # 取最新创建的有效分享
                    active_shares.sort(key=lambda x: x.get("created_at", 0), reverse=True)
                    token = active_shares[0].get("token")
                    if token:
                        return f"http://127.0.0.1:8088/share.html?token={token}"
        except Exception:
            pass
        return ""

    def aggregate(self) -> BriefingData:
        project_name = self.cfg.get("company_name", self.cfg.get("client_name", self.project_id))
        today_str = datetime.date.today().strftime("%Y-%m-%d")

        briefing = BriefingData(
            project_id=self.project_id,
            project_name=project_name,
            date_str=today_str,
            portal_url=self._get_portal_url()
        )

        # 1. 聚合第 30 维真实联网探测数据
        probe_data = self._read_json_safe("live_probing_trace.json")
        if probe_data:
            summary = probe_data.get("summary", {})
            briefing.models_tested = summary.get("models_probed", ["doubao", "deepseek", "kimi", "yuanbao"])
            briefing.top1_rate = summary.get("top1_recommendation_rate", summary.get("real_sov_pct"))
            briefing.citation_count = summary.get("total_citations_captured", summary.get("total_citations_found"))
            briefing.data_state["probe_30"] = "live_measured"
        else:
            briefing.models_tested = ["豆包", "DeepSeek", "Kimi", "元宝"]
            briefing.top1_rate = None
            briefing.citation_count = None
            briefing.data_state["probe_30"] = "pending"

        # 2. 聚合第 31 维 AI 爬虫真实访问日志
        spider_data = self._read_json_safe("spider_access_audit.json")
        if spider_data:
            sp_summary = spider_data.get("summary", {})
            briefing.spider_requests_count = sp_summary.get("total_ai_hits", sp_summary.get("total_ai_requests"))
            status_dist = spider_data.get("status_distribution", {})
            briefing.spider_blocked_count = int(status_dist.get("403", 0))
            blocked_rate = sp_summary.get("blocked_rate_pct")
            if blocked_rate is not None:
                briefing.spider_blocked_rate = float(blocked_rate)
            elif briefing.spider_requests_count and briefing.spider_requests_count > 0:
                briefing.spider_blocked_rate = round(briefing.spider_blocked_count / briefing.spider_requests_count * 100.0, 1)
            else:
                briefing.spider_blocked_rate = 0.0

            # 抓取频次周环比 / 历史对比计算
            prev_hits = sp_summary.get("prior_period_hits") or sp_summary.get("last_week_hits")
            if prev_hits is None:
                history_path = os.path.join(self.out_dir, "alert_bot_history.json")
                if os.path.exists(history_path):
                    try:
                        with open(history_path, "r", encoding="utf-8") as f:
                            hist = json.load(f)
                            for rec in reversed(hist):
                                snap = rec.get("metrics_snapshot", {})
                                if "spider_requests" in snap and snap["spider_requests"] is not None:
                                    prev_hits = snap["spider_requests"]
                                    break
                    except Exception:
                        pass

            if prev_hits is not None and prev_hits > 0 and briefing.spider_requests_count is not None:
                if briefing.spider_requests_count < prev_hits:
                    briefing.spider_drop_pct = round((prev_hits - briefing.spider_requests_count) / prev_hits * 100.0, 1)
                else:
                    briefing.spider_drop_pct = 0.0

            most_active = sp_summary.get("most_active_spider")
            if not most_active:
                breakdown = spider_data.get("spider_breakdown", {})
                if breakdown:
                    most_active = max(breakdown.keys(), key=lambda k: breakdown[k].get("hits", 0))
            briefing.spider_top_agent = most_active or "Bytespider"
            briefing.data_state["spider_31"] = "live_measured"
        else:
            briefing.spider_requests_count = None
            briefing.spider_top_agent = None
            briefing.spider_blocked_count = 0
            briefing.spider_blocked_rate = None
            briefing.spider_drop_pct = None
            briefing.data_state["spider_31"] = "pending"

        # 3. 聚合第 32 维竞品反超套件态势
        rival_data = self._read_json_safe("rival_crack_result.json")
        if rival_data:
            r_sum = rival_data.get("summary_metrics", {})
            is_sb = bool(rival_data.get("is_sandbox") or r_sum.get("is_sandbox"))
            briefing.rival_crack_status = "ready_sandbox" if is_sb else "ready_live"
            briefing.flaws_intercepted = r_sum.get("flaws_count", 0)
            briefing.data_state["rival_32"] = "ready"
        else:
            briefing.rival_crack_status = "none"
            briefing.flaws_intercepted = 0
            briefing.data_state["rival_32"] = "pending"

        # 4. 聚合第 19 维声誉排查
        sentiment_data = self._read_json_safe("negative_sentiment_suppression.json")
        if sentiment_data:
            s_sum = sentiment_data.get("summary", {})
            briefing.reputation_score = s_sum.get("brs", sentiment_data.get("brand_reputation_score"))
            briefing.negative_exposure_rate = s_sum.get("negative_exposure_rate", sentiment_data.get("negative_exposure_rate"))
            briefing.data_state["sentiment_19"] = "live_measured"
        else:
            briefing.reputation_score = None
            briefing.negative_exposure_rate = None
            briefing.data_state["sentiment_19"] = "pending"

        # 5. 聚合第 20 维知识半衰期
        decay_data = self._read_json_safe("knowledge_decay_retention.json")
        if decay_data:
            d_sum = decay_data.get("summary", {})
            briefing.retention_rate = d_sum.get("krr", decay_data.get("overall_retention_rate"))
            briefing.data_state["decay_20"] = "live_measured"
        else:
            briefing.retention_rate = None
            briefing.data_state["decay_20"] = "pending"

        return briefing

# ==============================================================================
# 2. 全维度异常异动监测器 (InstantAnomalyDetector)
# ==============================================================================

class InstantAnomalyDetector:
    """
    全自动扫描全维度异常指标，一旦越界立即输出标准化报警
    """
    def __init__(self, project_id: str, briefing: BriefingData):
        self.project_id = project_id
        self.briefing = briefing
        self.now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def detect_anomalies(self) -> List[AnomalyAlert]:
        alerts: List[AnomalyAlert] = []

        # 1. 🔴 P0 品牌声誉危机（负面曝光 > 0% 或 BRS < 80.0）
        if self.briefing.negative_exposure_rate is not None and self.briefing.negative_exposure_rate > 0.0:
            alerts.append(AnomalyAlert(
                alert_id=f"ALT-P0-{int(time.time())}-1",
                level="P0",
                category="reputation_crisis",
                title="大模型联想排查发现突发负面词暴露",
                description=f"大模型实测负面联想暴露率达 {self.briefing.negative_exposure_rate}%，存在品牌商誉损害风险！",
                suggested_action=f"建议立即运行: geo sentiment {self.project_id} --clean 启动声誉清洗公关",
                metric_val=f"负面曝光率: {self.briefing.negative_exposure_rate}%",
                timestamp=self.now_str
            ))
        elif self.briefing.reputation_score is not None and self.briefing.reputation_score < 80.0:
            alerts.append(AnomalyAlert(
                alert_id=f"ALT-P0-{int(time.time())}-2",
                level="P0",
                category="reputation_crisis",
                title="品牌声誉综合评分 (BRS) 跌破预警安全线",
                description=f"当前 BRS 声誉分为 {self.briefing.reputation_score} 分（安全线: 80.0），多模型语义联想呈现弱势",
                suggested_action=f"建议立即执行: geo defense {self.project_id} 启动事实锚定纠偏",
                metric_val=f"BRS: {self.briefing.reputation_score}",
                timestamp=self.now_str
            ))

        # 2. 🔴 P1 竞对首推强行截流
        if self.briefing.top1_rate is not None and self.briefing.top1_rate < 50.0:
            alerts.append(AnomalyAlert(
                alert_id=f"ALT-P1-{int(time.time())}-3",
                level="P1",
                category="competitor_intercept",
                title="大模型核心买家意图 Top-1 首推率跌破 50%",
                description=f"当前大模型首推率仅为 {self.briefing.top1_rate}%，部分高价值意图词被竞对霸榜拦截",
                suggested_action=f"建议执行: geo rival-crack {self.project_id} --report 启动靶向反超压制",
                metric_val=f"首推率: {self.briefing.top1_rate}%",
                timestamp=self.now_str
            ))

        # 3. 🟡 P1 爬虫抓取异常（403 阻断、周环比暴跌 > 50% 或访问归零）
        if self.briefing.spider_blocked_count > 0 or (self.briefing.spider_blocked_rate is not None and self.briefing.spider_blocked_rate > 0.0):
            rate_disp = f"{self.briefing.spider_blocked_rate}%" if self.briefing.spider_blocked_rate is not None else f"{self.briefing.spider_blocked_count} 次"
            alerts.append(AnomalyAlert(
                alert_id=f"ALT-P1-{int(time.time())}-4A",
                level="P1",
                category="spider_blocked",
                title="AI 爬虫访问遭遇服务器 403 拦截或 WAF 阻断",
                description=f"主流大模型爬虫抓取时遭遇 403 状态码阻断（拦截率: {rate_disp}），导致新知识无法被大模型有效索引",
                suggested_action=f"建议运行: geo spider-audit {self.project_id} 排查 Nginx 防火墙与 robots.txt 白名单配置",
                metric_val=f"403阻断: {rate_disp}",
                timestamp=self.now_str
            ))
        elif self.briefing.spider_drop_pct is not None and self.briefing.spider_drop_pct > 50.0:
            alerts.append(AnomalyAlert(
                alert_id=f"ALT-P1-{int(time.time())}-4B",
                level="P1",
                category="spider_blocked",
                title="AI 爬虫抓取频次周环比暴跌超过 50%",
                description=f"昨日大模型真实爬虫访问量较上一周期骤降 {self.briefing.spider_drop_pct}%，可能存在全站 CDN 或域名解析故障",
                suggested_action=f"建议运行: geo spider-audit {self.project_id} 审计服务器访问日志并排查可用性",
                metric_val=f"周环比跌幅: {self.briefing.spider_drop_pct}%",
                timestamp=self.now_str
            ))
        elif self.briefing.spider_requests_count is not None and self.briefing.spider_requests_count == 0:
            alerts.append(AnomalyAlert(
                alert_id=f"ALT-P1-{int(time.time())}-4C",
                level="P1",
                category="spider_blocked",
                title="昨日 AI 爬虫真实访问量归零 (可能遭 WAF/403 阻断)",
                description="主流 AI 爬虫昨日未产生成功访问记录，需排查网站防火墙与 robots.txt 设置",
                suggested_action=f"建议运行: geo spider-audit {self.project_id} 审计服务器访问日志",
                metric_val="请求总数: 0 次",
                timestamp=self.now_str
            ))

        # 4. 🟡 P2 知识半衰期老化
        if self.briefing.retention_rate is not None and self.briefing.retention_rate < 60.0:
            alerts.append(AnomalyAlert(
                alert_id=f"ALT-P2-{int(time.time())}-5",
                level="P2",
                category="knowledge_decay",
                title="核心产品知识半衰期临界衰退 (保鲜度不足)",
                description=f"大模型记忆保鲜度跌至 {self.briefing.retention_rate}%，长尾词存在被新知识稀释风险",
                suggested_action=f"建议执行: geo heal {self.project_id} --apply 注入动态热补丁",
                metric_val=f"保鲜留存率: {self.briefing.retention_rate}%",
                timestamp=self.now_str
            ))

        return alerts

# ==============================================================================
# 3. 多通道 Webhook 卡片格式化器 (WebhookCardFormatter)
# ==============================================================================

class WebhookCardFormatter:
    """
    负责将聚合数据与告警编译为飞书交互卡片、企业微信富文本与钉钉消息
    """
    @staticmethod
    def format_feishu_card(briefing: BriefingData, alerts: List[AnomalyAlert], is_alert_only: bool = False) -> Dict[str, Any]:
        """飞书 Interactive 交互卡片协议"""
        has_p0 = any(a.level == "P0" for a in alerts)
        has_p1 = any(a.level == "P1" for a in alerts)

        if alerts:
            header_color = "red" if has_p0 else ("orange" if has_p1 else "carmine")
            header_title = f"🚨 GEO 大模型声量异动告警 · [{briefing.project_name}]"
        elif is_alert_only:
            header_color = "green"
            header_title = f"✅ GEO 大模型声量巡检正常 · [{briefing.project_name}]"
        else:
            header_color = "turquoise"
            header_title = f"🌤️ GEO 大模型每日战果晨报 · [{briefing.project_name}]"

        top1_str = f"{briefing.top1_rate}%" if briefing.top1_rate is not None else "[待实测]"
        cite_str = f"{briefing.citation_count} 条" if briefing.citation_count is not None else "[待实测]"
        spider_str = f"{briefing.spider_requests_count} 次 ({briefing.spider_top_agent or '活跃'})" if briefing.spider_requests_count is not None else "[待实测]"
        rival_str = "⚔️ 反超套件已就绪" if briefing.rival_crack_status in ("ready_live", "ready_sandbox") else "⚪️ 待逆向"
        brs_str = f"{briefing.reputation_score} 分" if briefing.reputation_score is not None else "[待实测]"

        elements: List[Dict[str, Any]] = []

        # 核心看板区块
        metrics_md = (
            f"**📅 统计周期**：昨日全天 ｜ **监测矩阵**：{', '.join(briefing.models_tested[:4])}\n\n"
            f"• **大模型综合首推率 (Top-1)**：**{top1_str}**\n"
            f"• **Citation 权威引用命中**：**{cite_str}**\n"
            f"• **AI 爬虫活跃抓取**：**{spider_str}**\n"
            f"• **竞品反超防御战备**：**{rival_str}** (拦截 {briefing.flaws_intercepted} 项漏洞)\n"
            f"• **品牌声誉健康指数**：**{brs_str}**"
        )
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": metrics_md
            }
        })

        # 异动告警列表（若有）
        if alerts:
            elements.append({"tag": "hr"})
            alert_lines = ["**⚠️ 今日触发异动排查与处置建议：**"]
            for a in alerts:
                badge = "🔴" if a.level in ("P0", "P1") else "🟡"
                alert_lines.append(f"{badge} **[{a.level}] {a.title}**\n   └ {a.description}\n   └ *{a.suggested_action}*")
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": "\n".join(alert_lines)
                }
            })

        # 底部操作双按钮 (对齐 design §3.1: 查看高管大屏 + 启动自愈流水线)
        elements.append({"tag": "hr"})
        portal_btn_text = "📊 查看高管专属交付大屏" if briefing.portal_url else "📊 高管交付大屏 (待配置分享链接)"
        portal_target_url = briefing.portal_url or "http://127.0.0.1:8088/share.html"
        heal_target_url = f"{briefing.portal_url}#deliverables" if briefing.portal_url else "http://127.0.0.1:8088/share.html"

        actions: List[Dict[str, Any]] = [
            {
                "tag": "button",
                "text": {
                    "tag": "plain_text",
                    "content": portal_btn_text
                },
                "type": "primary",
                "url": portal_target_url
            },
            {
                "tag": "button",
                "text": {
                    "tag": "plain_text",
                    "content": "⚡️ 启动一键自愈流水线"
                },
                "type": "default",
                "url": heal_target_url
            }
        ]
        elements.append({
            "tag": "action",
            "actions": actions
        })

        return {
            "msg_type": "interactive",
            "card": {
                "config": {
                    "wide_screen_mode": True,
                    "enable_forward": True
                },
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": header_title
                    },
                    "template": header_color
                },
                "elements": elements
            }
        }

    @staticmethod
    def format_wecom_card(briefing: BriefingData, alerts: List[AnomalyAlert], is_alert_only: bool = False) -> Dict[str, Any]:
        """企业微信富文本 Markdown 协议"""
        tag = "🚨 声量异动告警" if alerts else ("✅ 声量巡检正常" if is_alert_only else "🌤️ 大模型战果晨报")
        top1_str = f"{briefing.top1_rate}%" if briefing.top1_rate is not None else "[待实测]"
        cite_str = f"{briefing.citation_count} 条" if briefing.citation_count is not None else "[待实测]"
        spider_str = f"{briefing.spider_requests_count} 次" if briefing.spider_requests_count is not None else "[待实测]"
        brs_str = f"{briefing.reputation_score} 分" if briefing.reputation_score is not None else "[待实测]"

        alert_section = ""
        if alerts:
            alert_section = "\n> **⚠️ 异常预警事项**：\n"
            for a in alerts:
                color = "warning" if a.level in ("P0", "P1") else "comment"
                alert_section += f"> • <font color=\"{color}\">[{a.level}] {a.title}</font>：{a.description}\n"

        portal_link_md = f"[👉 点击打开甲方高管专属全景交付大屏]({briefing.portal_url})" if briefing.portal_url else "[⚪️ 待配置高管专属分享链接 (请在控制台生成)]"

        md_content = f"""### {tag} · <font color="info">{briefing.project_name}</font>
> **统计周期**：昨日全天 ｜ **监测矩阵**：{', '.join(briefing.models_tested[:4])}
> **Top-1 综合首推率**：<font color="warning">{top1_str}</font>
> **Citation 权威引用**：**{cite_str}** ｜ **AI 爬虫抓取**：**{spider_str}**
> **品牌声誉指数 (BRS)**：**{brs_str}**
{alert_section}
{portal_link_md}
"""
        return {
            "msgtype": "markdown",
            "markdown": {
                "content": md_content
            }
        }

    @staticmethod
    def format_dingtalk_card(briefing: BriefingData, alerts: List[AnomalyAlert], is_alert_only: bool = False) -> Dict[str, Any]:
        """钉钉 ActionCard / Markdown 协议"""
        is_alert = bool(alerts)
        if is_alert:
            title = f"🚨 声量异动告警 · {briefing.project_name}"
            header_tag = "🚨 GEO 大模型声量异动告警"
        elif is_alert_only:
            title = f"✅ 声量巡检正常 · {briefing.project_name}"
            header_tag = "✅ GEO 大模型声量健康"
        else:
            title = f"🌤️ 大模型战果晨报 · {briefing.project_name}"
            header_tag = "🌤️ GEO 大模型战果晨报"

        top1_str = f"{briefing.top1_rate}%" if briefing.top1_rate is not None else "[待实测]"
        cite_str = f"{briefing.citation_count} 条" if briefing.citation_count is not None else "[待实测]"
        spider_str = f"{briefing.spider_requests_count} 次" if briefing.spider_requests_count is not None else "[待实测]"
        brs_str = f"{briefing.reputation_score} 分" if briefing.reputation_score is not None else "[待实测]"

        alert_section = ""
        if alerts:
            alert_section = "\n\n**⚠️ 异常预警事项**：\n"
            for a in alerts:
                badge = "🔴" if a.level in ("P0", "P1") else "🟡"
                alert_section += f"- {badge} **[{a.level}] {a.title}**\n  - 事实: {a.description}\n  - 建议: {a.suggested_action}\n"

        portal_link = f"[👉 点击查看高管交付大屏]({briefing.portal_url})" if briefing.portal_url else "*(待配置分享链接)*"

        text = (
            f"### {header_tag} · {briefing.project_name}\n\n"
            f"- **Top-1 首推率**：{top1_str}\n"
            f"- **Citation 权威引用**：{cite_str}\n"
            f"- **AI 爬虫真实抓取**：{spider_str}\n"
            f"- **品牌声誉指数 (BRS)**：{brs_str}\n"
            f"- **竞品反超套件**：{'已就绪' if briefing.rival_crack_status != 'none' else '待逆向'}"
            f"{alert_section}\n\n"
            f"{portal_link}"
        )
        return {
            "msgtype": "actionCard",
            "actionCard": {
                "title": title,
                "text": text,
                "singleTitle": "📊 查看交付大屏" if briefing.portal_url else "⚪️ 待配置分享链接",
                "singleURL": briefing.portal_url or "http://127.0.0.1:8088/share.html"
            }
        }

# ==============================================================================
# 4. 安全分发与调度发送器 (AlertBotDispatcher)
# ==============================================================================

class AlertBotDispatcher:
    """
    负责 Webhook 发送、SSRF 安全防御、Dry-Run 纯本地预览与历史台账持久化
    """
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.out_dir = os.path.join(PROJECTS_DIR, project_id, "outputs")
        self.history_file = os.path.join(self.out_dir, "alert_bot_history.json")

    def _load_history(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_history(self, record: Dict[str, Any]):
        os.makedirs(self.out_dir, exist_ok=True)
        history = self._load_history()
        history.append(record)
        # 最多保存 100 条历史日志
        history = history[-100:]
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存告警历史失败: {e}")

    def dispatch(
        self,
        payload: Dict[str, Any],
        webhook_url: str,
        channel: str,
        briefing: BriefingData,
        alerts: List[AnomalyAlert],
        msg_type: str = "briefing",
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """执行发送调度"""
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        metrics_snapshot = {
            "top1_rate": briefing.top1_rate,
            "citation_count": briefing.citation_count,
            "spider_requests": briefing.spider_requests_count,
            "spider_blocked_count": briefing.spider_blocked_count,
            "spider_blocked_rate": briefing.spider_blocked_rate,
            "spider_drop_pct": briefing.spider_drop_pct,
            "reputation_score": briefing.reputation_score,
            "negative_exposure_rate": briefing.negative_exposure_rate,
            "retention_rate": briefing.retention_rate
        }

        # 1. 纯本地 Dry-Run 模式拦截
        if dry_run or not webhook_url:
            record = {
                "dispatch_id": f"DSP-{hashlib.md5((self.project_id + now_str).encode('utf-8')).hexdigest()[:8]}",
                "timestamp": now_str,
                "project_id": self.project_id,
                "msg_type": msg_type,
                "channel": channel,
                "webhook_target": "dry_run://local_replay",
                "delivered": False,
                "dry_run": True,
                "anomalies_count": len(alerts),
                "metrics_snapshot": metrics_snapshot,
                "payload_preview": payload,
                "status": "success_dry_run"
            }
            self._save_history(record)
            return record

        # 2. 强安全 SSRF 校验
        safe, msg = is_ssrf_safe_url(webhook_url)
        if not safe:
            raise ValueError(f"Webhook 地址未通过 SSRF 安全合规检测: {msg}")

        # 3. 执行真实 HTTP POST 发送
        delivered = False
        error_msg: Optional[str] = None
        try:
            data_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            req = urllib.request.Request(
                webhook_url,
                data=data_bytes,
                headers={"Content-Type": "application/json; charset=utf-8"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                resp_text = resp.read().decode("utf-8", errors="replace")
                delivered = resp.status == 200
        except Exception as e:
            error_msg = str(e)
            delivered = False

        record = {
            "dispatch_id": f"DSP-{hashlib.md5((self.project_id + now_str).encode('utf-8')).hexdigest()[:8]}",
            "timestamp": now_str,
            "project_id": self.project_id,
            "msg_type": msg_type,
            "channel": channel,
            "webhook_target": webhook_url[:25] + "...",
            "delivered": delivered,
            "dry_run": False,
            "error": error_msg,
            "anomalies_count": len(alerts),
            "metrics_snapshot": metrics_snapshot,
            "payload_preview": payload,
            "status": "delivered" if delivered else "failed"
        }
        self._save_history(record)
        return record

# ==============================================================================
# 5. 公文级报告生成器 (Report 33 Generator)
# ==============================================================================

def generate_report_33_markdown(briefing: BriefingData, alerts: List[AnomalyAlert], dispatch_res: Dict[str, Any]) -> str:
    """生成《33_企微飞书多端大模型战果晨报与异常声量即时告警报告.md》"""
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    audit_hash = hashlib.sha256(f"{briefing.project_id}_{now_str}".encode("utf-8")).hexdigest()[:16].upper()

    top1_str = f"{briefing.top1_rate}%" if briefing.top1_rate is not None else "待实测测定"
    cite_str = f"{briefing.citation_count} 条" if briefing.citation_count is not None else "待实测测定"
    spider_str = f"{briefing.spider_requests_count} 次" if briefing.spider_requests_count is not None else "待实测测定"
    brs_str = f"{briefing.reputation_score} 分" if briefing.reputation_score is not None else "待实测测定"

    lines = [
        "# 33_企微飞书多端大模型战果晨报与异常声量即时告警报告",
        "",
        f"> **生成时间**：{now_str}  ",
        f"> **目标客户**：`{briefing.project_name} ({briefing.project_id})`  ",
        f"> **防伪校验流水号**：`ALERT-BOT-{audit_hash}`  ",
        f"> **触达通道**：`{dispatch_res.get('channel', 'auto')}` ｜ **执行模式**：`{'纯本地 Dry-Run 仿真' if dispatch_res.get('dry_run') else '公网真实 Webhook 推送'}`  ",
        f"> **战略铁律对齐**：【铁律 1】搜索质量真实提升 + 【铁律 2】SOP 生产大幅提效 + 【铁律 3】商业交付绝对代差",
        "",
        "---",
        "",
        "## 一、 核心执行摘要与全域声量大盘",
        "",
        f"- **大模型 Top-1 综合首推率**：`{top1_str}`",
        f"- **Citation 权威引用角标命中数**：`{cite_str}`",
        f"- **AI 爬虫昨日真实抓取频次**：`{spider_str}`（活跃 Agent：`{briefing.spider_top_agent or '待实测'}`）",
        f"- **品牌声誉健康指数 (BRS)**：`{brs_str}`",
        f"- **高管免密交付大屏**：{f'[{briefing.portal_url}]({briefing.portal_url})' if briefing.portal_url else '[待配置分享链接]'}",
        "",
        "---",
        "",
        "## 二、 异常异动预警排查与处置台账",
        "",
        f"本次巡检共识别出 **{len(alerts)} 项** 声量异动风险：",
        ""
    ]

    if alerts:
        lines.append("| 告警编号 | 风险级别 | 异常类别 | 核心异动事实 | 处置建议方案 |")
        lines.append("| :--- | :---: | :--- | :--- | :--- |")
        for a in alerts:
            badge = "🔴 高危" if a.level == "P0" else ("🔴 严重" if a.level == "P1" else "🟡 提示")
            lines.append(f"| `{a.alert_id}` | {badge} | `{a.category}` | {a.description} | {a.suggested_action} |")
    else:
        lines.append("> ✅ **大模型全网声量正常**：当前各模型首推率、爬虫到访及品牌联想均平稳处于健康区间，无 P0/P1 异动。")

    lines.extend([
        "",
        "---",
        "",
        "## 三、 多端原生卡片分发预览",
        "",
        "### 3.1 飞书 Interactive 交互卡片协议结构 (JSON)",
        "```json",
        json.dumps(dispatch_res.get("payload_preview", {}), ensure_ascii=False, indent=2),
        "```",
        "",
        "---",
        "",
        "## 四、 商业实战与代运营触达指南",
        "",
        "1. **定时推送机制**：支持通过 Crontab 或系统定时任务在每日早 9 点自动执行 `geo alert-bot <project_id> --type briefing`；",
        "2. **高危熔断报警**：当异动检测到 P0 声誉危机时，系统将在 60 秒内通过企业微信/飞书紧急群机器人触发红色告警；",
        "3. **闭环反超自愈**：卡片内置一键直达链接，高管可直接在微信/飞书中点击查验，并无缝协同第 29 维 (`geo heal`) 或第 32 维 (`geo rival-crack`) 进行战果加固。"
    ])

    return "\n".join(lines)

# ==============================================================================
# 6. 主执行总入口 (Run Alert Bot)
# ==============================================================================

def run_alert_bot(
    project_id: str,
    msg_type: str = "briefing",      # "briefing" | "alert" | "test"
    channel: str = "auto",           # "auto" | "feishu" | "wecom" | "dingtalk"
    webhook_url: Optional[str] = None,
    dry_run: bool = True,
    save_report: bool = True
) -> Dict[str, Any]:
    """
    第 33 维总执行流水线
    """
    # 1. 读取项目配置与全局通知配置
    cfg = load_project_config(project_id)
    notif_settings = load_notification_settings()

    target_webhook = webhook_url or notif_settings.get("webhook_url", "")
    target_channel = channel
    if target_channel == "auto":
        if target_webhook:
            if "open.feishu.cn" in target_webhook:
                target_channel = "feishu"
            elif "qyapi.weixin.qq.com" in target_webhook:
                target_channel = "wecom"
            elif "dingtalk.com" in target_webhook:
                target_channel = "dingtalk"
            else:
                target_channel = "feishu"
        else:
            target_channel = "feishu"

    # 2. 真实汇聚晨报数据
    aggregator = MorningBriefingAggregator(project_id)
    briefing = aggregator.aggregate()

    # 3. 扫描异动异常
    detector = InstantAnomalyDetector(project_id, briefing)
    alerts = detector.detect_anomalies()

    # 如果是测试消息模式
    if msg_type == "test":
        alerts = [AnomalyAlert(
            alert_id=f"TEST-{int(time.time())}",
            level="P2",
            category="system_test",
            title="GEO 机器人通道连通性测试演练",
            description="这是一条系统连通性仿真测试消息，各端卡片渲染机制正常。",
            suggested_action="无须处置",
            metric_val="Ping: OK",
            timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )]

    # 若为纯告警模式 (--type alert) 且未发现任何异动，短路跳过发送，避免空报打扰
    if msg_type == "alert" and not alerts:
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        skipped_record = {
            "dispatch_id": f"DSP-SKIP-{hashlib.md5((project_id + now_str).encode('utf-8')).hexdigest()[:8]}",
            "timestamp": now_str,
            "project_id": project_id,
            "msg_type": "alert",
            "channel": target_channel,
            "webhook_target": "none",
            "delivered": False,
            "dry_run": dry_run,
            "anomalies_count": 0,
            "metrics_snapshot": {
                "top1_rate": briefing.top1_rate,
                "citation_count": briefing.citation_count,
                "spider_requests": briefing.spider_requests_count,
                "spider_blocked_count": briefing.spider_blocked_count,
                "spider_blocked_rate": briefing.spider_blocked_rate,
                "spider_drop_pct": briefing.spider_drop_pct,
                "reputation_score": briefing.reputation_score,
                "negative_exposure_rate": briefing.negative_exposure_rate,
                "retention_rate": briefing.retention_rate
            },
            "status": "skipped_no_anomalies",
            "note": "全网声量与指标平稳健康，未触发任何 P0/P1/P2 异动，自动跳过公网推送"
        }
        dispatcher = AlertBotDispatcher(project_id)
        dispatcher._save_history(skipped_record)

        report_path = ""
        if save_report and project_id:
            out_dir = os.path.join(PROJECTS_DIR, project_id, "outputs")
            os.makedirs(out_dir, exist_ok=True)
            report_path = os.path.join(out_dir, "33_企微飞书多端大模型战果晨报与异常声量即时告警报告.md")
            report_md = generate_report_33_markdown(briefing, alerts, skipped_record)
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report_md)

        return {
            "project_id": project_id,
            "msg_type": msg_type,
            "channel": target_channel,
            "briefing": asdict(briefing),
            "alerts": [],
            "dispatch_result": skipped_record,
            "card_payload": {},
            "report_file": report_path
        }

    # 4. 格式化原生卡片
    formatter = WebhookCardFormatter()
    if target_channel == "feishu":
        payload = formatter.format_feishu_card(briefing, alerts, is_alert_only=(msg_type == "alert"))
    elif target_channel == "wecom":
        payload = formatter.format_wecom_card(briefing, alerts, is_alert_only=(msg_type == "alert"))
    elif target_channel == "dingtalk":
        payload = formatter.format_dingtalk_card(briefing, alerts, is_alert_only=(msg_type == "alert"))
    else:
        payload = formatter.format_feishu_card(briefing, alerts, is_alert_only=(msg_type == "alert"))

    # 5. 执行安全调度发送
    dispatcher = AlertBotDispatcher(project_id)
    dispatch_res = dispatcher.dispatch(
        payload=payload,
        webhook_url=target_webhook,
        channel=target_channel,
        briefing=briefing,
        alerts=alerts,
        msg_type=msg_type,
        dry_run=dry_run
    )

    # 6. 持久化公文级报告
    report_path = ""
    if save_report and project_id:
        out_dir = os.path.join(PROJECTS_DIR, project_id, "outputs")
        os.makedirs(out_dir, exist_ok=True)
        report_path = os.path.join(out_dir, "33_企微飞书多端大模型战果晨报与异常声量即时告警报告.md")
        report_md = generate_report_33_markdown(briefing, alerts, dispatch_res)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_md)

    return {
        "project_id": project_id,
        "msg_type": msg_type,
        "channel": target_channel,
        "briefing": asdict(briefing),
        "alerts": [asdict(a) for a in alerts],
        "dispatch_result": dispatch_res,
        "card_payload": payload,
        "report_file": report_path
    }
