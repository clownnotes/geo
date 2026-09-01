"""
GEO Commercial Delivery Toolkit
商用 GEO 交付工作台与自动化工具套件
"""

__version__ = "1.3.0"

from .intent import mine_project_intent, generate_intent_for_company
from .ingest import ingest_project_materials, fetch_and_clean_url, distill_knowledge_facts
from .defense import run_defense, generate_defense_strategy_fallback
from .audit import run_audit
from .scaffold import run_scaffold
from .rewrite import run_rewrite
from .distribute import run_distribute
from .monitor import run_monitor, extract_monitor_metrics
from .server import start_server
