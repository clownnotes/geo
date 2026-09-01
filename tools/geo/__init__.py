"""
GEO Commercial Delivery Toolkit
商用 GEO 交付工作台与自动化工具套件
"""

__version__ = "1.5.0"

from .intent import mine_project_intent, generate_intent_for_company
from .ingest import ingest_project_materials, fetch_and_clean_url, distill_knowledge_facts
from .defense import run_defense, generate_defense_strategy_fallback
from .audit import run_audit
from .scaffold import run_scaffold
from .rewrite import run_rewrite
from .distribute import run_distribute
from .monitor import run_monitor, extract_monitor_metrics
from .patrol import (
    run_patrol_all,
    run_patrol_project,
    get_project_history,
    record_project_history,
    load_notification_settings,
    save_notification_settings,
    send_webhook_alert
)
from .share import (
    create_share_link,
    list_project_shares,
    revoke_share_link,
    get_share_portal_data
)
from .server import start_server
