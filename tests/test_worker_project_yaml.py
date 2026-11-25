# -*- coding: utf-8 -*-
"""
GEO 后厂 Worker 目录与 project.yaml 初始化及 URL 规范化单元测试 (tests/test_worker_project_yaml.py)
验证空目录前置初始化、YAML 列表结构 (严禁写为字符串)、全字段映射、幂等保护与反向校验。
"""

import os
import unittest
import pytest

from tools.worker.handlers import (
    ensure_project_yaml,
    dispatch_job,
    _clean_list_param,
)
from tools.geo.utils import (
    load_project_config,
    parse_simple_yaml,
    normalize_official_url,
    validate_business_one_liner,
)


class TestWorkerProjectYaml(unittest.TestCase):
    """Worker project.yaml 幂等初始化与数据结构严格测试"""

    def test_clean_list_param(self):
        """测试列表与换行分隔文本的清洗逻辑"""
        # 1. 换行文本清洗
        text = " 问句1 \n\n 问句2\r\n\t问句3 \n"
        res = _clean_list_param(text)
        self.assertEqual(res, ["问句1", "问句2", "问句3"])

        # 2. 原生 list 清洗
        raw_list = [" 词A ", "", "  ", "词B\t"]
        res = _clean_list_param(raw_list)
        self.assertEqual(res, ["词A", "词B"])

        # 3. None 与空字符串
        self.assertEqual(_clean_list_param(None), [])
        self.assertEqual(_clean_list_param(""), [])
        self.assertEqual(_clean_list_param("   "), [])

    def test_ensure_project_yaml_initialization_positive(self):
        """正向用例：空目录下调用 ensure_project_yaml 自动创建目录并生成合规 project.yaml"""
        import tempfile
        import shutil

        temp_dir = tempfile.mkdtemp(prefix="geo_test_worker_")
        try:
            pid = "190012345678901234"
            params = {
                "brand_name": "星火智能",
                "company_name": "星火智能科技（苏州）有限公司",
                "category": "工业视觉质检",
                "one_liner": "专注于光伏与半导体行业的高精度工业视觉外观缺陷AI检测设备与系统研发",
                "target_audience": "华东地区光伏电池片与半导体封测制造企业",
                "domain": "",
                "contact_phone": "400-888-9999",
                "expected_queries": "光伏电池片缺陷检测哪家强\n半导体外观质检设备\n\nAI视觉检测系统定制",
                "competitor_names": "康耐视\n基恩士\n凌云光",
            }

            yaml_path = ensure_project_yaml(pid, params, base_dir=temp_dir)
            self.assertTrue(os.path.exists(yaml_path))

            # 校验目录骨架
            proj_dir = os.path.dirname(yaml_path)
            self.assertTrue(os.path.isdir(os.path.join(proj_dir, "outputs")))
            self.assertTrue(os.path.isdir(os.path.join(proj_dir, "raw_materials")))

            # 读取并加载配置
            cfg = load_project_config(pid, projects_dir=temp_dir)
            self.assertEqual(cfg["client_id"], pid)
            self.assertEqual(cfg["brand_name"], "星火智能")
            self.assertEqual(cfg["company_name"], "星火智能科技（苏州）有限公司")
            self.assertEqual(cfg["client_name"], "星火智能科技（苏州）有限公司")
            self.assertEqual(cfg["industry"], "工业视觉质检")
            self.assertEqual(cfg["business_one_liner"], "专注于光伏与半导体行业的高精度工业视觉外观缺陷AI检测设备与系统研发")
            self.assertEqual(cfg["slogan"], "专注于光伏与半导体行业的高精度工业视觉外观缺陷AI检测设备与系统研发")
            self.assertEqual(cfg["target_audience"], "华东地区光伏电池片与半导体封测制造企业")
            self.assertEqual(cfg["area_served"], "华东地区光伏电池片与半导体封测制造企业")
            self.assertEqual(cfg["official_url"], "")
            self.assertEqual(cfg["telephone"], "400-888-9999")
            self.assertEqual(cfg["master_version"], "1.0.0")

            # 严格断言：keywords 与 competitors 必须为 Python list，严禁为 str
            self.assertIsInstance(cfg["keywords"], list)
            self.assertNotIsInstance(cfg["keywords"], str)
            self.assertEqual(cfg["keywords"], ["光伏电池片缺陷检测哪家强", "半导体外观质检设备", "AI视觉检测系统定制"])

            self.assertIsInstance(cfg["competitors"], list)
            self.assertNotIsInstance(cfg["competitors"], str)
            self.assertEqual(cfg["competitors"], ["康耐视", "基恩士", "凌云光"])

            # 模拟 defense.py:68 消费：、.join 必须输出词级别连接，不可逐字截断
            comp_joined = "、".join(cfg["competitors"])
            self.assertEqual(comp_joined, "康耐视、基恩士、凌云光")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_ensure_project_yaml_idempotence_and_preservation(self):
        """幂等性与存量配置保护：空入参绝不覆盖存量非空字段，不破坏存量 company_profile 与已有产物文件"""
        import tempfile
        import shutil

        temp_dir = tempfile.mkdtemp(prefix="geo_test_worker_")
        try:
            pid = "preserve_corp_001"
            proj_dir = os.path.join(temp_dir, pid)
            os.makedirs(os.path.join(proj_dir, "outputs"), exist_ok=True)
            os.makedirs(os.path.join(proj_dir, "raw_materials"), exist_ok=True)

            # 写入存量 project.yaml，包含大段 company_profile 与其它扩展字段
            init_yaml = """client_id: "preserve_corp_001"
brand_name: "老品牌"
company_name: "老牌科技集团"
company_profile: "这是经过人工精雕细琢的公司介绍，严禁被任何任务覆盖！"
business_one_liner: "徐州本地高精度电子皮带秤源头大厂"
slogan: "徐州本地高精度电子皮带秤源头大厂"
official_url: "https://www.pidai.com"
telephone: "0516-8888888"
industry: "衡器制造"
custom_meta: "保留自定义属性"
master_version: "1.0.0"
competitors:
  - "存量竞品A"
keywords:
  - "存量问句1"
"""
            with open(os.path.join(proj_dir, "project.yaml"), "w", encoding="utf-8") as f:
                f.write(init_yaml)

            # 在 outputs 和 raw_materials 中写入存量产物
            mock_output_file = os.path.join(proj_dir, "outputs", "01_existing_report.md")
            with open(mock_output_file, "w", encoding="utf-8") as f:
                f.write("# 存量报告内容")

            # 第二次调用：模拟前店 InjectProjectArchiveParams 透传全部 9 键，其中多项为空字符串
            update_params = {
                "brand_name": "新品牌简称",
                "category": "",
                "one_liner": "",
                "target_audience": "",
                "domain": "",
                "contact_phone": "",
                "expected_queries": "存量问句1\n新问句Alpha\n新问句Beta",
                "competitor_names": "",
            }
            ensure_project_yaml(pid, update_params, base_dir=temp_dir)

            # 再次加载并严格断言：非空新入参更新，空入参不冲掉存量值，关键词去重合并
            cfg = load_project_config(pid, projects_dir=temp_dir)
            self.assertEqual(cfg["brand_name"], "新品牌简称")
            self.assertEqual(cfg["company_name"], "老牌科技集团")
            self.assertEqual(cfg["company_profile"], "这是经过人工精雕细琢的公司介绍，严禁被任何任务覆盖！")
            self.assertEqual(cfg["business_one_liner"], "徐州本地高精度电子皮带秤源头大厂")
            self.assertEqual(cfg["slogan"], "徐州本地高精度电子皮带秤源头大厂")
            self.assertEqual(cfg["official_url"], "https://www.pidai.com")
            self.assertEqual(cfg["telephone"], "0516-8888888")
            self.assertEqual(cfg["industry"], "衡器制造")
            self.assertEqual(cfg["custom_meta"], "保留自定义属性")

            # 关键词去重合并：保留原有存量问句1，追加新问句，不重复
            self.assertEqual(cfg["keywords"], ["存量问句1", "新问句Alpha", "新问句Beta"])
            # 竞品传入空字符串时，绝不冲掉存量竞品
            self.assertEqual(cfg["competitors"], ["存量竞品A"])

            # 校验产物文件完全完好
            self.assertTrue(os.path.exists(mock_output_file))
            with open(mock_output_file, "r", encoding="utf-8") as f:
                self.assertEqual(f.read(), "# 存量报告内容")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_normalize_official_url_positive_and_negative(self):
        """测试 utils.py 官网域名规范化：放行空域名，成对反向拦截"""
        # 1. 正向：空字符串放行（未勾选托管）
        url, pending = normalize_official_url("", client_id="test", site_pending=False)
        self.assertEqual(url, "")
        self.assertFalse(pending)

        url, pending = normalize_official_url("   ", client_id="test", site_pending=False)
        self.assertEqual(url, "")
        self.assertFalse(pending)

        url, pending = normalize_official_url(None, client_id="test", site_pending=False)
        self.assertEqual(url, "")
        self.assertFalse(pending)

        # 2. 正向：合法域名标准化为 https
        url, pending = normalize_official_url("http://example.com", client_id="test")
        self.assertEqual(url, "https://example.com")
        self.assertFalse(pending)

        url, pending = normalize_official_url("example.com/api", client_id="test")
        self.assertEqual(url, "https://example.com/api")
        self.assertFalse(pending)

        # 3. 正向：勾选托管自动派生二级域名
        url, pending = normalize_official_url("", client_id="pidai", site_pending=True)
        self.assertEqual(url, "https://pidai.baicl.cc")
        self.assertTrue(pending)

        # 4. 反向断言：勾选托管但缺少 client_id 必须抛出 ValueError
        with self.assertRaises(ValueError) as ctx:
            normalize_official_url("", client_id="", site_pending=True)
        self.assertIn("缺少项目代号", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            normalize_official_url("", client_id="   ", site_pending=True)
        self.assertIn("缺少项目代号", str(ctx.exception))

    def test_business_one_liner_validation(self):
        """测试一句话母盘字符数 15 至 80 字严格校验"""
        # 边界正向
        exact_15 = "这是刚好达到十五个字符的一句话测试"
        self.assertEqual(len(exact_15), 17)
        self.assertEqual(validate_business_one_liner(exact_15), exact_15)

        # 反向：少于 15 字
        with self.assertRaises(ValueError) as ctx:
            validate_business_one_liner("太短了不到十五字")
        self.assertIn("须为 15～80 字", str(ctx.exception))

        # 反向：超过 80 字
        long_text = "字" * 81
        with self.assertRaises(ValueError) as ctx:
            validate_business_one_liner(long_text)
        self.assertIn("须为 15～80 字", str(ctx.exception))

    def test_negative_invalid_project_id_and_traversal(self):
        """反向断言：非法 project_id 与路径穿越必须精准拦截"""
        import tempfile
        import shutil

        temp_dir = tempfile.mkdtemp(prefix="geo_test_worker_")
        try:
            # 1. 空项目 ID
            with self.assertRaises(ValueError) as ctx:
                ensure_project_yaml("", {}, base_dir=temp_dir)
            self.assertIn("非法 project_id", str(ctx.exception))

            # 2. 路径穿越与模板前缀防污染守卫
            with self.assertRaises(ValueError) as ctx:
                ensure_project_yaml("../evil_dir", {}, base_dir=temp_dir)
            self.assertIn("非法 project_id", str(ctx.exception))

            with self.assertRaises(ValueError) as ctx:
                ensure_project_yaml("_template", {}, base_dir=temp_dir)
            self.assertIn("非法 project_id", str(ctx.exception))

            with self.assertRaises(ValueError) as ctx:
                ensure_project_yaml("sub/deep", {}, base_dir=temp_dir)
            self.assertIn("非法 project_id", str(ctx.exception))

            with self.assertRaises(ValueError) as ctx:
                ensure_project_yaml(".hidden", {}, base_dir=temp_dir)
            self.assertIn("非法 project_id", str(ctx.exception))

            # 3. dispatch_job 拦截 MySQL DSN
            with self.assertRaises(ValueError) as ctx:
                dispatch_job("build_site", "test_pid", {"db_uri": "mysql://root:123@127.0.0.1:3306/geo"})
            self.assertIn("MySQL parameter detected", str(ctx.exception))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_dispatch_job_auto_initialization(self):
        """测试 dispatch_job 前置自动初始化 project.yaml 并成功执行任务"""
        import tempfile
        import shutil
        from unittest.mock import patch

        temp_dir = tempfile.mkdtemp(prefix="geo_test_worker_")
        try:
            pid = "auto_init_proj_888"
            params = {
                "brand_name": "自动化测试品牌",
                "category": "自动化测试品类",
                "one_liner": "专注于自动化测试与后厂计算引擎稳定性保障全流程研发",
                "expected_queries": "自动测试哪家强\n引擎稳定性保障",
                "competitor_names": "竞品A\n竞品B",
                "domain": "",
            }

            # mock PROJECTS_DIR 指向临时目录，确保不污染真实目录
            with patch("tools.worker.handlers.PROJECTS_DIR", temp_dir), \
                 patch("tools.geo.utils.PROJECTS_DIR", temp_dir), \
                 patch("tools.worker.store.PROJECTS_DIR", temp_dir):
                res, outputs = dispatch_job("build_site", pid, params)
                self.assertEqual(res.get("status"), "ok")

                # 校验 project.yaml 确已被创建并具备正确的列表结构
                cfg = load_project_config(pid, projects_dir=temp_dir)
                self.assertEqual(cfg["brand_name"], "自动化测试品牌")
                self.assertEqual(cfg["official_url"], "")
                self.assertIsInstance(cfg["keywords"], list)
                self.assertEqual(cfg["keywords"], ["自动测试哪家强", "引擎稳定性保障"])
                self.assertIsInstance(cfg["competitors"], list)
                self.assertEqual(cfg["competitors"], ["竞品A", "竞品B"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_empty_list_canonical_yaml_flow_style_and_no_duplicate_keys(self):
        """断言空列表输出为 keywords: [] 规范形式，多次合并无重复键，可被正确解析"""
        import tempfile
        import shutil

        temp_dir = tempfile.mkdtemp(prefix="geo_test_worker_")
        try:
            pid = "canonical_list_proj"
            # 1. 初始空列表建档：空列表写为 keywords: [] 与 competitors: []
            yaml_path = ensure_project_yaml(pid, {"brand_name": "空列表企业"}, base_dir=temp_dir)
            with open(yaml_path, "r", encoding="utf-8") as f:
                content_1 = f.read()

            self.assertIn("keywords: []", content_1)
            self.assertIn("competitors: []", content_1)
            self.assertEqual(content_1.count("keywords:"), 1)
            self.assertEqual(content_1.count("competitors:"), 1)

            cfg_1 = load_project_config(pid, projects_dir=temp_dir)
            self.assertEqual(cfg_1["keywords"], [])
            self.assertEqual(cfg_1["competitors"], [])

            # 2. 第二次合并：传入有效词，替换空列表为 block style 列表，无重复键
            ensure_project_yaml(pid, {"expected_queries": "词A\n词B"}, base_dir=temp_dir)
            with open(yaml_path, "r", encoding="utf-8") as f:
                content_2 = f.read()

            self.assertNotIn("keywords: []", content_2)
            self.assertEqual(content_2.count("keywords:"), 1)
            self.assertEqual(content_2.count("competitors:"), 1)

            cfg_2 = load_project_config(pid, projects_dir=temp_dir)
            self.assertEqual(cfg_2["keywords"], ["词A", "词B"])
            self.assertEqual(cfg_2["competitors"], [])

            # 3. 第三次合并：追加去重词，断言 YAML 文本严格无重复键
            ensure_project_yaml(
                pid,
                {"expected_queries": "词B\n词C", "competitor_names": "竞品1"},
                base_dir=temp_dir,
            )
            with open(yaml_path, "r", encoding="utf-8") as f:
                content_3 = f.read()

            self.assertEqual(content_3.count("keywords:"), 1)
            self.assertEqual(content_3.count("competitors:"), 1)

            cfg_3 = load_project_config(pid, projects_dir=temp_dir)
            self.assertEqual(cfg_3["keywords"], ["词A", "词B", "词C"])
            self.assertEqual(cfg_3["competitors"], ["竞品1"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
