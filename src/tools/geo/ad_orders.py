"""快速见效代采业务数据管理模块 (AdOrderManager)
负责记录外部平台广告采购与第三方代采的 4 个关键时间戳，
严格遵循纯物理 JSON 持久化（原子写入）与雪花 ID 规范。
"""

import os
import json
import tempfile
from datetime import datetime
from typing import List, Dict, Any, Optional
from tools.geo.idgen import new_id
from tools.geo.utils import PROJECTS_DIR


def parse_iso_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    """解析 ISO 日期时间字符串，解析失败返回 None 或抛出 ValueError"""
    if not dt_str or not isinstance(dt_str, str):
        return None
    dt_clean = dt_str.strip()
    if not dt_clean:
        return None
    # 尝试常用格式解析
    for fmt in (
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(dt_clean, fmt)
        except ValueError:
            continue
    # 尝试 datetime.fromisoformat（Python 3.7+）
    try:
        return datetime.fromisoformat(dt_clean.replace("Z", "+00:00"))
    except Exception:
        raise ValueError(f"非法日期格式: {dt_str}")


class AdOrderManager:
    """代采订单管理类，处理单租户 projects/{id}/ad_orders.json 的读写"""

    def __init__(self, projects_dir: str = "projects"):
        self.projects_dir = projects_dir

    def get_order_file_path(self, project_id: str) -> str:
        """获取目标企业租户的 ad_orders.json 物理路径"""
        return os.path.join(self.projects_dir, project_id, "ad_orders.json")

    def validate_timestamps(
        self,
        client_ordered_at: Optional[str],
        vendor_paid_at: Optional[str],
        vendor_delivered_at: Optional[str],
        client_accepted_at: Optional[str],
    ) -> Dict[str, Any]:
        """校验 4 个时间戳格式与时序逻辑，如果倒挂则抛出 ValueError"""
        t_order = parse_iso_datetime(client_ordered_at)
        t_paid = parse_iso_datetime(vendor_paid_at)
        t_delivered = parse_iso_datetime(vendor_delivered_at)
        t_accepted = parse_iso_datetime(client_accepted_at)

        # 校验时序逻辑倒挂（后面的时间不能早于前面的时间）
        if t_order and t_paid and t_paid < t_order:
            raise ValueError("时序逻辑倒挂: 我方付款时间不能早于客户下单时间")
        if t_paid and t_delivered and t_delivered < t_paid:
            raise ValueError("时序逻辑倒挂: 第三方交付时间不能早于我方付款时间")
        if t_delivered and t_accepted and t_accepted < t_delivered:
            raise ValueError("时序逻辑倒挂: 客户核对通过时间不能早于第三方交付时间")

        # 计算完成状态（4 个时间戳均非空且有效时为 completed，否则为 in_progress）
        is_completed = bool(t_order and t_paid and t_delivered and t_accepted)
        status = "completed" if is_completed else "in_progress"

        return {
            "client_ordered_at": client_ordered_at.strip() if client_ordered_at else None,
            "vendor_paid_at": vendor_paid_at.strip() if vendor_paid_at else None,
            "vendor_delivered_at": vendor_delivered_at.strip() if vendor_delivered_at else None,
            "client_accepted_at": client_accepted_at.strip() if client_accepted_at else None,
            "status": status,
        }

    def list_orders(self, project_id: str) -> List[Dict[str, Any]]:
        """获取租户代采订单列表，文件不存在时返回空列表"""
        file_path = self.get_order_file_path(project_id)
        if not os.path.exists(file_path):
            return []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
        except Exception:
            return []

        if not isinstance(raw_data, list):
            return []

        orders = []
        for item in raw_data:
            if not isinstance(item, dict):
                continue
            # 动态计算 status，避免持久化数据漂移
            t_order = bool(item.get("client_ordered_at"))
            t_paid = bool(item.get("vendor_paid_at"))
            t_deliv = bool(item.get("vendor_delivered_at"))
            t_accept = bool(item.get("client_accepted_at"))
            status = "completed" if (t_order and t_paid and t_deliv and t_accept) else "in_progress"

            order_copy = dict(item)
            order_copy["status"] = status
            if "order_id" not in order_copy and "id" in order_copy:
                order_copy["order_id"] = order_copy["id"]
            if "vendor_name" not in order_copy and "platform_name" in order_copy:
                order_copy["vendor_name"] = order_copy["platform_name"]
            orders.append(order_copy)

        return orders

    def create_order(
        self,
        project_id: str,
        platform_name: str = "",
        external_order_url: str = "",
        client_ordered_at: Optional[str] = None,
        vendor_paid_at: Optional[str] = None,
        vendor_delivered_at: Optional[str] = None,
        client_accepted_at: Optional[str] = None,
        vendor_name: str = "",
        note: str = "",
    ) -> Dict[str, Any]:
        """创建代采订单并原子落盘至 projects/{id}/ad_orders.json"""
        actual_platform = (platform_name or vendor_name or "").strip()
        if not actual_platform:
            raise ValueError("平台名称不能为空")

        actual_url = (external_order_url or note or "").strip()

        validated = self.validate_timestamps(
            client_ordered_at,
            vendor_paid_at,
            vendor_delivered_at,
            client_accepted_at,
        )

        project_dir = os.path.join(self.projects_dir, project_id)
        if not os.path.exists(project_dir):
            os.makedirs(project_dir, exist_ok=True)

        file_path = self.get_order_file_path(project_id)
        current_orders = self.list_orders(project_id)

        oid = new_id()
        new_order_data = {
            "id": oid,
            "order_id": oid,
            "project_id": project_id,
            "platform_name": actual_platform,
            "vendor_name": actual_platform,
            "external_order_url": actual_url,
            "note": actual_url,
            "client_ordered_at": validated["client_ordered_at"],
            "vendor_paid_at": validated["vendor_paid_at"],
            "vendor_delivered_at": validated["vendor_delivered_at"],
            "client_accepted_at": validated["client_accepted_at"],
        }

        # 内存存储（用于落盘，过滤掉动态属性）
        to_save = []
        for o in current_orders:
            to_save.append({
                "id": o.get("id") or o.get("order_id"),
                "order_id": o.get("order_id") or o.get("id"),
                "project_id": o.get("project_id"),
                "platform_name": o.get("platform_name") or o.get("vendor_name", ""),
                "vendor_name": o.get("vendor_name") or o.get("platform_name", ""),
                "external_order_url": o.get("external_order_url") or o.get("note", ""),
                "note": o.get("note") or o.get("external_order_url", ""),
                "client_ordered_at": o.get("client_ordered_at"),
                "vendor_paid_at": o.get("vendor_paid_at"),
                "vendor_delivered_at": o.get("vendor_delivered_at"),
                "client_accepted_at": o.get("client_accepted_at"),
            })
        to_save.append(new_order_data)

        # 临时文件原子替换落盘
        # [2026-11-23 架构拆分停写] 业务状态已全面由小毛驴 Go 后端 geo_ad_orders 承接，真实生产/开发目录停写
        if self.projects_dir == PROJECTS_DIR and os.environ.get("GEO_ENABLE_LEGACY_WRITES") != "1":
            result = dict(new_order_data)
            result["status"] = validated["status"]
            return result

        temp_dir = os.path.dirname(file_path)
        os.makedirs(temp_dir, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", dir=temp_dir, delete=False, encoding="utf-8") as tf:
            json.dump(to_save, tf, ensure_ascii=False, indent=2)
            temp_name = tf.name

        os.replace(temp_name, file_path)

        # 返回带动态 status 的订单对象
        result = dict(new_order_data)
        result["status"] = validated["status"]
        return result
