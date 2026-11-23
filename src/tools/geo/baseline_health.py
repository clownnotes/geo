"""基本盘业务健康度巡检模块 (BaselineHealthChecker)
基于博文物理文件（排除 index.html 列表页）动态计算企业博文发文距离天数，
并执行 30 天月度保活健康度巡检，严格防范新项目与初创期的虚假超时报警。
"""

import os
import re
import glob
from datetime import datetime, date
from typing import Dict, Any, Optional, List


def extract_article_date(html_content: str) -> Optional[str]:
    """从 HTML 内容中提取 datePublished 或 time datetime 日期字符串 (YYYY-MM-DD)"""
    date_m = re.search(r'datePublished["\']:\s*["\'](\d{4}-\d{2}-\d{2})', html_content)
    if date_m:
        return date_m.group(1)

    date_m2 = re.search(r'<time[^>]*datetime=["\'](\d{4}-\d{2}-\d{2})["\']', html_content)
    if date_m2:
        return date_m2.group(1)

    date_m3 = re.search(r'(\d{4}-\d{2}-\d{2})', html_content)
    if date_m3:
        return date_m3.group(1)

    return None


class BaselineHealthChecker:
    """基本盘健康度巡检服务"""

    def __init__(self, projects_dir: str = "projects"):
        self.projects_dir = projects_dir

    def get_blog_dir(self, project_id: str) -> str:
        """获取目标企业的博客文章目录路径"""
        return os.path.join(self.projects_dir, project_id, "outputs", "blog")

    def scan_project_articles(self, project_id: str) -> List[Dict[str, str]]:
        """扫描指定租户的所有实际博文（排除 index.html 列表页），返回博文清单"""
        blog_dir = self.get_blog_dir(project_id)
        if not os.path.exists(blog_dir):
            return []

        article_files = glob.glob(os.path.join(blog_dir, "*.html"))
        results = []

        for fpath in article_files:
            fname = os.path.basename(fpath)
            # 严格排除 index.html 博客列表页
            if fname.lower() == "index.html":
                continue

            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
                pub_date = extract_article_date(content)
                if pub_date:
                    results.append({"filename": fname, "date": pub_date})
            except Exception:
                continue

        return results

    def calculate_health(
        self,
        project_id: str,
        current_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """计算指定企业的长期基本盘健康度指标"""
        project_dir = os.path.join(self.projects_dir, project_id)
        if not os.path.exists(project_dir):
            raise FileNotFoundError(f"企业租户不存在: {project_id}")

        if current_date is None:
            current_date = datetime.now().date()

        articles = self.scan_project_articles(project_id)

        # 守卫 1：如果没有任何博文（新开通项目或初创期密集提纯中），归为 initial_batch
        if not articles:
            return {
                "project_id": project_id,
                "phase": "initial_batch",
                "phase_label": "初期建档交付期",
                "status": "initial_batch",
                "health_status": "healthy",
                "is_warning": False,
                "needs_monthly_post": False,
                "total_articles": 0,
                "article_count": 0,
                "latest_published_at": None,
                "last_article_published_at": None,
                "days_since_latest": 0,
                "days_since_last_article": 0,
                "message": "企业处于初创密集建档期，无需进行 30 天月度保活巡检",
            }

        # 守卫 2：已发布过博文，进入 monthly_retention 月度保活期
        # 找出最新的一篇博文日期
        sorted_articles = sorted(articles, key=lambda x: x["date"], reverse=True)
        latest_date_str = sorted_articles[0]["date"]

        try:
            latest_date = datetime.strptime(latest_date_str, "%Y-%m-%d").date()
            days_diff = (current_date - latest_date).days
            if days_diff < 0:
                days_diff = 0
        except Exception:
            days_diff = 0

        # 判断是否超过 30 天未发文
        needs_monthly_post = days_diff > 30
        status_code = "warning" if needs_monthly_post else "healthy"

        if needs_monthly_post:
            msg = f"已超过 30 天未发布新博文（距上次发文已有 {days_diff} 天），需发布月度保活博文"
        else:
            msg = f"月度保活状态正常（距上次发文 {days_diff} 天）"

        return {
            "project_id": project_id,
            "phase": "monthly_retention",
            "phase_label": "月度保活维护期",
            "status": status_code,
            "health_status": status_code,
            "is_warning": needs_monthly_post,
            "needs_monthly_post": needs_monthly_post,
            "total_articles": len(articles),
            "article_count": len(articles),
            "latest_published_at": latest_date_str,
            "last_article_published_at": latest_date_str,
            "days_since_latest": days_diff,
            "days_since_last_article": days_diff,
            "message": msg,
        }

    def check_health(self, project_id: str, current_date: Optional[date] = None) -> Dict[str, Any]:
        """别名方法，与 calculate_health 等价"""
        return self.calculate_health(project_id, current_date)
