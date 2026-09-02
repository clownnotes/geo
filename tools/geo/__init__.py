"""
GEO Commercial Delivery Toolkit
商用 GEO 交付工作台与自动化工具套件
"""

__version__ = "2.2.0"

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
from .benchmark import (
    calculate_industry_benchmarks,
    evaluate_project_against_benchmark,
    run_batch_pipeline
)
from .evolution import (
    analyze_prompt_portfolio,
    generate_fission_prompts,
    apply_evolved_prompts
)
from .group import (
    load_groups_config,
    save_group_config,
    calculate_group_matrix,
    analyze_group_defense
)
from .visual import (
    generate_comparison_svg,
    generate_architecture_svg,
    generate_video_script,
    generate_all_visual_assets,
    get_visual_assets
)
from .playground import (
    simulate_llm_query,
    evaluate_response_quality,
    run_playground_simulation,
    run_batch_simulation
)
from .dist_bot import (
    get_distribution_ledger,
    record_distributed_url,
    verify_distribution_url,
    verify_all_channels,
    format_rich_text_copy
)
from .roi import (
    calculate_project_roi,
    predict_renewal_health,
    save_roi_settings,
    load_roi_settings
)
from .server import start_server
