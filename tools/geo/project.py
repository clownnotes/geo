"""客户项目工作区加载与校验（projects/<client_id>/）。"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

from . import miniyaml

PROJECTS_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "projects")

_REQUIRED = ("client_id", "client_name", "official_url", "keywords")


def _as_list(value) -> list:
    """宽容处理：列表照收，标量包一层，空值/dict 视为未配置。"""
    if isinstance(value, list):
        return value
    if isinstance(value, (str, int, float)) and str(value).strip():
        return [str(value).strip()]
    return []


@dataclass
class GeoProject:
    client_id: str
    root: str
    raw: dict = field(default_factory=dict)

    # ---- 便捷字段（缺失时给出安全默认值） ----
    @property
    def name(self) -> str:
        return str(self.raw.get("client_name", self.client_id))

    @property
    def url(self) -> str:
        return str(self.raw.get("official_url", "")).rstrip("/")

    @property
    def industry(self) -> str:
        return str(self.raw.get("industry", ""))

    @property
    def entity(self) -> dict:
        ent = self.raw.get("entity") or {}
        return ent if isinstance(ent, dict) else {}

    @property
    def core_values(self) -> list:
        return _as_list(self.raw.get("core_values"))

    @property
    def keywords(self) -> list:
        return _as_list(self.raw.get("keywords"))

    @property
    def competitors(self) -> list:
        return _as_list(self.raw.get("competitors"))

    @property
    def models(self) -> list:
        return _as_list(self.raw.get("models")) or ["deepseek"]

    @property
    def guarantee(self) -> list:
        return _as_list(self.raw.get("guarantee")) or ["100% 源码交付"]

    def path(self, *parts: str) -> str:
        """返回项目工作区内的绝对路径（自动补齐父目录）。"""
        target = os.path.join(self.root, *parts)
        parent = os.path.dirname(target)
        if parent:
            os.makedirs(parent, exist_ok=True)
        return target

    def output_dir(self, stage: str) -> str:
        target = os.path.join(self.root, "outputs", stage)
        os.makedirs(target, exist_ok=True)
        return target

    def write_output(self, stage: str, filename: str, content: str) -> str:
        target = os.path.join(self.output_dir(stage), filename)
        with open(target, "w", encoding="utf-8") as fh:
            fh.write(content)
        return target


def load_project(client_id: str) -> GeoProject:
    root = os.path.join(PROJECTS_ROOT, client_id)
    config_path = os.path.join(root, "project.yaml")
    if not os.path.isfile(config_path):
        raise FileNotFoundError(
            f"未找到客户项目 {client_id!r}：{config_path}\n"
            f"请先执行: python3 -m tools.geo init {client_id}"
        )
    raw: dict = miniyaml.load(config_path)
    missing = [key for key in _REQUIRED if not raw.get(key)]
    if missing:
        raise ValueError(
            f"project.yaml 缺少必填字段: {', '.join(missing)}（参照 projects/_template/project.yaml 补全后重试）"
        )
    if str(raw["client_id"]) != client_id:
        raise ValueError(f"client_id({raw['client_id']}) 与目录名({client_id}) 不一致")
    return GeoProject(client_id=client_id, root=root, raw=raw)


def create_project(client_id: str, fields: dict) -> str:
    """按模板字段创建新客户工作区，返回项目根目录。"""
    root = os.path.join(PROJECTS_ROOT, client_id)
    if os.path.exists(os.path.join(root, "project.yaml")):
        raise FileExistsError(f"项目 {client_id} 已存在: {root}")
    for sub in ("raw_materials", "outputs"):
        os.makedirs(os.path.join(root, sub), exist_ok=True)
    lines: list = [f"client_id: {client_id!r}"]
    key_order = ["client_name", "official_url", "industry", "contact_phone"]
    for key in key_order:
        if key in fields:
            lines.append(f"{key}: {fields[key]!r}")
    for key in ("core_values", "keywords", "competitors", "models", "guarantee"):
        values: list = fields.get(key) or []
        if values:
            lines.append(f"{key}:")
            lines.extend(f"  - {v!r}" for v in values)
        elif key == "keywords":
            lines.append("keywords: 未填写——必填，每行一个：'  - \"意图词\"'")
        else:
            lines.append(f"{key}:")
    body = "\n".join(lines) + "\n"
    with open(os.path.join(root, "project.yaml"), "w", encoding="utf-8") as fh:
        fh.write(body)
    return root
