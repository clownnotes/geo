"""
GEO Commercial Delivery Toolkit
商用 GEO 交付工作台与自动化工具套件
"""

__version__ = "1.2.0"

from .intent import mine_project_intent, generate_intent_for_company
from .ingest import ingest_project_materials, fetch_and_clean_url, distill_knowledge_facts
from .audit import run_audit
from .scaffold import run_scaffold
from .rewrite import run_rewrite
from .distribute import run_distribute
from .monitor import run_monitor
from .server import start_server
