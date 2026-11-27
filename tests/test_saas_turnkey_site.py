# -*- coding: utf-8 -*-
"""
SaaS 交钥匙静态官网编译、留白规则、LOGO 安全门禁、防覆盖保护与预览开关单元测试
覆盖 tasks.md 2.1 / 2.2 / 3.1 / 3.2 正向契约与成对反向红线断言。
全程使用隔离临时目录，不污染真实 projects/ 目录。
"""

import hashlib
import html.parser
import json
import os
import re
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

_SRC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from tools.geo import scaffold, utils as geo_utils
from tools.geo.utils import load_project_config, parse_simple_yaml
from tools.worker import handlers as worker_handlers, store as worker_store
from tools.worker.handlers import dispatch_job, handle_build_site

EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FAFF"
    "\U00002702-\U000027B0"
    "]+",
    flags=re.UNICODE,
)

VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}


class _BalancedHTMLChecker(html.parser.HTMLParser):
    """校验 HTML 结构标签成对闭合且无悬空闭合标签。"""

    def __init__(self):
        super().__init__()
        self.stack = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        t = tag.lower()
        if t not in VOID_TAGS:
            self.stack.append(t)

    def handle_endtag(self, tag):
        t = tag.lower()
        if t in VOID_TAGS:
            return
        if not self.stack or self.stack[-1] != t:
            self.errors.append(f"Mismatch end tag </{t}>, stack={self.stack[-3:]}")
            return
        self.stack.pop()


def _assert_valid_clean_html(test_case: unittest.TestCase, html_text: str) -> None:
    test_case.assertEqual(EMOJI_RE.findall(html_text), [], "HTML 中严禁出现任何 Emoji")
    test_case.assertNotRegex(html_text, r"\{\{[A-Z0-9_]+\}\}", "存在未替换的模板占位符")
    checker = _BalancedHTMLChecker()
    checker.feed(html_text)
    test_case.assertEqual(checker.errors, [], f"HTML 闭合错误: {checker.errors}")
    test_case.assertEqual(checker.stack, [], f"HTML 存在未闭合标签: {checker.stack}")
    root_refs = re.findall(r'(?:href|src)="/[^"]*"', html_text)
    test_case.assertEqual(root_refs, [], f"站内引用必须为相对路径，禁止根路径引用: {root_refs}")


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


class TestSaasTurnkeySite(unittest.TestCase):
    """SaaS 交钥匙静态官网与可控预览全链路测试集"""

    def setUp(self):
        self.tmp_root = tempfile.mkdtemp(prefix="geo_saas_site_ut_")
        self.projects_dir = os.path.join(self.tmp_root, "projects")
        os.makedirs(self.projects_dir, exist_ok=True)
        self._patches = [
            patch.object(geo_utils, "PROJECTS_DIR", self.projects_dir),
            patch.object(worker_handlers, "PROJECTS_DIR", self.projects_dir),
            patch.object(worker_store, "PROJECTS_DIR", self.projects_dir),
        ]
        for p in self._patches:
            p.start()

    def tearDown(self):
        for p in reversed(self._patches):
            p.stop()
        shutil.rmtree(self.tmp_root, ignore_errors=True)

    def _create_project(self, pid: str, yaml_text: str) -> str:
        p_dir = os.path.join(self.projects_dir, pid)
        os.makedirs(os.path.join(p_dir, "outputs"), exist_ok=True)
        os.makedirs(os.path.join(p_dir, "raw_materials"), exist_ok=True)
        with open(os.path.join(p_dir, "project.yaml"), "w", encoding="utf-8") as f:
            f.write(yaml_text)
        return p_dir

    def test_01_parse_simple_yaml_dict_lists_and_real_project_compat(self):
        """验证零依赖 parse_simple_yaml 兼容解析字典列表、字符串列表、引号冒号与布尔标量"""
        yaml_sample = '''
client_id: "acme_01"
company_name: "江苏智造装备有限公司"
custom_site: true
empty_block:
inline_empty: []
core_business:
  - name: "激光切割成套装备"
    description: "万瓦级光纤激光切割：支持厚板高精度加工"
    cycle: "15 个工作日"
    price: "¥180,000 起"
  - name: "自动化上下料桁架"
    description: "7x24 小时无人化产线联动"
differences:
  - "核心光源质保 3 年：原厂直供无中间商"
  - "https://www.acme-laser.cn"
faqs:
  - question: "设备交期需要多久？"
    answer: "标准机型 15 个工作日内完成出厂联调。"
'''
        parsed = parse_simple_yaml(yaml_sample)
        self.assertEqual(parsed["client_id"], "acme_01")
        self.assertTrue(parsed["custom_site"])
        self.assertEqual(parsed["empty_block"], [])
        self.assertEqual(parsed["inline_empty"], [])
        self.assertEqual(len(parsed["core_business"]), 2)
        self.assertEqual(parsed["core_business"][0]["name"], "激光切割成套装备")
        self.assertEqual(parsed["core_business"][0]["price"], "¥180,000 起")
        self.assertEqual(parsed["core_business"][1]["name"], "自动化上下料桁架")
        self.assertEqual(
            parsed["differences"],
            ["核心光源质保 3 年：原厂直供无中间商", "https://www.acme-laser.cn"],
        )
        self.assertEqual(
            parsed["faqs"],
            [{"question": "设备交期需要多久？", "answer": "标准机型 15 个工作日内完成出厂联调。"}],
        )

        real_xuanyuan = os.path.join(geo_utils.PROJECT_ROOT, "projects", "xuzhou_xuanyuan", "project.yaml")
        if os.path.isfile(real_xuanyuan):
            with open(real_xuanyuan, "r", encoding="utf-8") as f:
                real_parsed = parse_simple_yaml(f.read())
            self.assertIsInstance(real_parsed.get("core_business"), list)
            self.assertGreaterEqual(len(real_parsed["core_business"]), 3)
            self.assertIsInstance(real_parsed["core_business"][0], dict)
            self.assertIn("name", real_parsed["core_business"][0])

    def test_02_full_profile_compiles_five_files_and_valid_html(self):
        """正向场景：完整客户资料 + 合法 LOGO 编译出合规五件套、三重爬虫冗余且 0 Emoji"""
        pid = "full_laser_corp"
        p_dir = self._create_project(
            pid,
            '''client_id: "full_laser_corp"
company_name: "苏州星辰激光装备股份有限公司"
brand_name: "星辰激光"
slogan: "高功率工业光纤激光切割装备源头制造商"
company_profile: "星辰激光深耕金属板材成形装备研发与制造，面向重工与汽车零部件工厂提供整线交付。"
industry: "工业激光装备制造"
area_served: "长三角及全国制造业基地"
founder: "张工"
founder_title: "总工程师"
telephone: "0512-88997766"
wechat: "xingchen_laser"
address: "江苏省苏州市工业园区星湖街 99 号"
official_url: "https://ai.xingchen-laser.com"
logo_file: "raw_materials/brand_logo.png"
core_business:
  - name: "三万瓦超大幅面激光切割机"
    description: "支持 60mm 碳钢稳定批量切割"
    cycle: "20 个工作日"
    price: "按幅面配置报价"
differences:
  - "整机床身高温退火去应力，10 年不变形"
  - "全国 24 小时驻地售后工程师上门响应"
faqs:
  - question: "是否支持来料打样测试？"
    answer: "支持免费寄样或携图纸到苏州工厂现场切板实测。"
''',
        )
        logo_src = os.path.join(p_dir, "raw_materials", "brand_logo.png")
        with open(logo_src, "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\nfake_png_payload")

        res = scaffold.run_scaffold(pid)
        site_dir = os.path.join(p_dir, "outputs", "site")
        for fname in ("index.html", "llms.txt", "schema.jsonld", "robots.txt", "sitemap.xml"):
            self.assertTrue(os.path.isfile(os.path.join(site_dir, fname)), f"缺少 {fname}")
            self.assertTrue(os.path.isfile(os.path.join(p_dir, "outputs", fname)), f"根 outputs 缺少双写 {fname}")

        self.assertFalse(res["preview_public"], "新编译站点默认必须关闭公网预览")
        self.assertTrue(os.path.isfile(os.path.join(site_dir, "assets", "brand_logo.png")))

        with open(os.path.join(site_dir, "index.html"), "r", encoding="utf-8") as f:
            html_text = f.read()
        _assert_valid_clean_html(self, html_text)
        self.assertIn('src="assets/brand_logo.png"', html_text)
        self.assertIn('rel="alternate" type="text/markdown"', html_text)
        self.assertIn('href="llms.txt"', html_text)
        self.assertIn('rel="sitemap" type="application/xml"', html_text)
        self.assertIn('href="sitemap.xml"', html_text)
        self.assertIn('href="https://ai.xingchen-laser.com/"', html_text)
        self.assertIn("三万瓦超大幅面激光切割机", html_text)
        self.assertIn("整机床身高温退火去应力", html_text)
        self.assertIn("是否支持来料打样测试？", html_text)
        for anchor in ("HEADER", "HERO", "SERVICES", "ADVANTAGES", "FAQ", "FOOTER"):
            self.assertIn(f"<!-- SAAS_SECTION:{anchor} -->", html_text)
            self.assertIn(f"<!-- /SAAS_SECTION:{anchor} -->", html_text)

        with open(os.path.join(site_dir, "schema.jsonld"), "r", encoding="utf-8") as f:
            schema_obj = json.loads(f.read())
        types = [node.get("@type") for node in schema_obj["@graph"]]
        self.assertIn("Organization", types)
        self.assertIn("Service", types)
        self.assertIn("FAQPage", types)

    def test_03_minimal_profile_leaves_blank_with_zero_fake_data(self):
        """缺省留白场景：仅提供公司名与电话时，无 img、无空板块、绝不注入软件外包假数据"""
        pid = "minimal_valve_co"
        p_dir = self._create_project(
            pid,
            '''client_id: "minimal_valve_co"
company_name: "温州远大阀门制造有限公司"
telephone: "0577-86869999"
''',
        )
        scaffold.run_scaffold(pid)
        site_dir = os.path.join(p_dir, "outputs", "site")
        with open(os.path.join(site_dir, "index.html"), "r", encoding="utf-8") as f:
            html_text = f.read()
        with open(os.path.join(site_dir, "llms.txt"), "r", encoding="utf-8") as f:
            llms_text = f.read()
        with open(os.path.join(site_dir, "schema.jsonld"), "r", encoding="utf-8") as f:
            schema_text = f.read()
        with open(os.path.join(site_dir, "sitemap.xml"), "r", encoding="utf-8") as f:
            sitemap_text = f.read()

        _assert_valid_clean_html(self, html_text)
        body_text = html_text.split("<body", 1)[1]
        self.assertIn("温州远大阀门制造有限公司", body_text)
        self.assertIn("0577-86869999", body_text)
        self.assertNotIn("<img", body_text)
        self.assertNotIn('id="services"', body_text)
        self.assertNotIn('id="advantages"', body_text)
        self.assertNotIn('id="faq"', body_text)
        self.assertNotIn("saas-hero-slogan", body_text)
        self.assertNotIn("saas-hero-card", body_text)
        self.assertNotIn("saas-badge", body_text)

        forbidden_fakes = (
            "13150568888",
            "nextdoor",
            "老白",
            "小程序",
            "ERP",
            "¥12,000",
            "¥3,000",
            "365 天",
            "江苏省徐州市",
            "示例企业",
            "示例科技",
        )
        combined = html_text + "\n" + llms_text + "\n" + schema_text
        for fake in forbidden_fakes:
            self.assertNotIn(fake, combined, f"发现残留假数据: {fake}")

        schema_obj = json.loads(schema_text)
        types = [node.get("@type") for node in schema_obj["@graph"]]
        self.assertNotIn("FAQPage", types)
        self.assertNotIn("Service", types)
        self.assertIn(f"https://claw.baicl.cc/{pid}/", sitemap_text)

    def test_04_partial_logo_and_services_hides_missing_faq(self):
        """按需渲染场景：上传合法 SVG LOGO + 2 项业务但无 FAQ 时，仅展示已有板块并隐藏 FAQ"""
        pid = "partial_pump_co"
        p_dir = self._create_project(
            pid,
            '''client_id: "partial_pump_co"
company_name: "博山特种水泵厂"
logo_file: "logo.svg"
core_business:
  - "矿用耐磨多级离心泵"
  - "化工耐腐蚀磁力泵"
''',
        )
        with open(os.path.join(p_dir, "raw_materials", "logo.svg"), "w", encoding="utf-8") as f:
            f.write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"></svg>')

        scaffold.run_scaffold(pid)
        site_dir = os.path.join(p_dir, "outputs", "site")
        with open(os.path.join(site_dir, "index.html"), "r", encoding="utf-8") as f:
            html_text = f.read()
        _assert_valid_clean_html(self, html_text)
        self.assertIn('src="assets/logo.svg"', html_text)
        self.assertIn('id="services"', html_text)
        self.assertIn("矿用耐磨多级离心泵", html_text)
        self.assertIn("化工耐腐蚀磁力泵", html_text)
        self.assertNotIn('id="faq"', html_text)
        self.assertNotIn('id="advantages"', html_text)

    def test_05_negative_logo_traversal_outside_path_and_invalid_ext(self):
        """反向安全断言：越界路径、.. 穿越、软链越界与非图片白名单后缀一律拒绝复制并安全留白"""
        outside_secret = os.path.join(self.tmp_root, "outside_secret.png")
        with open(outside_secret, "wb") as f:
            f.write(b"TOP_SECRET_DO_NOT_LEAK")

        pid = "sec_logo_test"
        p_dir = self._create_project(pid, 'client_id: "sec_logo_test"\ncompany_name: "安全测试企业"\n')
        bad_script = os.path.join(p_dir, "raw_materials", "evil.html")
        with open(bad_script, "w", encoding="utf-8") as f:
            f.write("<script>alert(1)</script>")

        symlink_logo = os.path.join(p_dir, "raw_materials", "link_out.png")
        os.symlink(outside_secret, symlink_logo)

        malicious_cases = [
            outside_secret,
            "/etc/passwd",
            "../../outside_secret.png",
            "raw_materials/../../outside_secret.png",
            "raw_materials/link_out.png",
            "raw_materials/evil.html",
            "project.yaml",
            "https://evil.example.com/logo.png",
            "raw_materials/non_existent.webp",
        ]
        site_dir = os.path.join(p_dir, "outputs", "site")
        assets_dir = os.path.join(site_dir, "assets")

        for bad_logo in malicious_cases:
            with self.subTest(bad_logo=bad_logo):
                scaffold.run_scaffold(pid, overrides={"logo_file": bad_logo})
                with open(os.path.join(site_dir, "index.html"), "r", encoding="utf-8") as f:
                    html_text = f.read()
                self.assertNotIn("<img", html_text)
                self.assertNotIn("TOP_SECRET", html_text)
                if os.path.isdir(assets_dir):
                    self.assertEqual(os.listdir(assets_dir), [], f"越界文件被非法复制: {bad_logo}")

    def test_06_custom_site_true_protects_html_llms_schema_sitemap_and_real_nextgeo(self):
        """防覆盖保护断言：custom_site=true 时跳过覆盖已有 index/llms/schema/sitemap 及子目录，且真实 nextgeo 零改动"""
        pid = "locked_vip_client"
        p_dir = self._create_project(
            pid,
            '''client_id: "locked_vip_client"
company_name: "精修锁定客户"
custom_site: true
official_url: "https://vip.example.com"
''',
        )
        site_dir = os.path.join(p_dir, "outputs", "site")
        os.makedirs(os.path.join(site_dir, "blog"), exist_ok=True)
        protected_contents = {
            "index.html": "<!DOCTYPE html><html><body>CUSTOM_HANDCRAFTED_INDEX</body></html>",
            "llms.txt": "# CUSTOM_LLMS_TXT\n",
            "schema.jsonld": '{"@context":"https://schema.org","custom":true}',
            "sitemap.xml": '<?xml version="1.0" encoding="UTF-8"?><urlset><url><loc>https://vip.example.com/blog/1.html</loc></url></urlset>',
            "blog/1.html": "<html><body>CUSTOM_BLOG_POST</body></html>",
        }
        for rel, body in protected_contents.items():
            with open(os.path.join(site_dir, rel), "w", encoding="utf-8") as f:
                f.write(body)

        scaffold.run_scaffold(pid, overrides={"company_name": "试图强行覆盖的新名称"})
        scaffold.run_scaffold(pid, overrides={"custom_site": False, "company_name": "试图通过overrides解锁"})
        res_locked, _ = dispatch_job("build_site", pid, {"custom_site": False, "company_name": "试图通过worker零值解锁"})
        self.assertTrue(res_locked["custom_site"])

        for rel, expected in protected_contents.items():
            with open(os.path.join(site_dir, rel), "r", encoding="utf-8") as f:
                self.assertEqual(f.read(), expected, f"custom_site=true 未能保护 {rel}")
        self.assertTrue(os.path.isfile(os.path.join(site_dir, "robots.txt")))

        real_nextgeo_sitemap = os.path.join(
            geo_utils.PROJECT_ROOT, "projects", "nextgeo", "outputs", "site", "sitemap.xml"
        )
        real_nextgeo_index = os.path.join(
            geo_utils.PROJECT_ROOT, "projects", "nextgeo", "outputs", "site", "index.html"
        )
        if os.path.isfile(real_nextgeo_sitemap) and os.path.isfile(real_nextgeo_index):
            with open(real_nextgeo_sitemap, "r", encoding="utf-8") as f:
                self.assertGreater(len(f.readlines()), 20, "真实 nextgeo 多页 sitemap.xml 必须完好")

    def test_07_worker_handle_build_site_overrides_and_preview_switch(self):
        """Worker 集成断言：handle_build_site 透传结构化覆盖与 publish_preview，返回 sitemap 与预览链接且不冲洗存量词库"""
        pid = "worker_saas_88"
        self._create_project(
            pid,
            '''client_id: "worker_saas_88"
company_name: "存量精密仪器厂"
keywords:
  - "存量精修长尾问句不可丢失"
''',
        )
        params = {
            "brand_name": "华精仪器",
            "wechat": "huajing_wx",
            "address": "无锡市新吴区传感园 8 号",
            "company_profile": "专注高精度压力变送器研发制造。",
            "core_business": [{"name": "防爆差压变送器", "description": "0.075 级高精度工业测量"}],
            "faqs": [{"question": "防爆等级是多少？", "answer": "通过 Ex d IIC T6 Gb 国家防爆认证。"}],
            "publish_preview": True,
        }
        res, output_paths = dispatch_job("build_site", pid, params)
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["sitemap"], "site/sitemap.xml")
        self.assertEqual(res["preview_url"], f"https://claw.baicl.cc/{pid}/")
        self.assertTrue(res["preview_public"])
        self.assertTrue(scaffold.is_preview_public(pid))
        self.assertTrue(any(p.endswith("outputs/site/sitemap.xml") for p in output_paths))

        cfg_after = load_project_config(pid)
        self.assertEqual(cfg_after["keywords"], ["存量精修长尾问句不可丢失"])
        self.assertEqual(cfg_after["wechat"], "huajing_wx")

        site_html_path = os.path.join(self.projects_dir, pid, "outputs", "site", "index.html")
        with open(site_html_path, "r", encoding="utf-8") as f:
            html_text = f.read()
        self.assertIn("防爆差压变送器", html_text)
        self.assertIn("防爆等级是多少？", html_text)

    def test_08_preview_switch_idempotence_cli_and_negative_project_ids(self):
        """无状态公网开关：默认关闭、开启/关闭幂等、CLI 入口及非法 project_id 反向拦截"""
        pid = "switch_demo_01"
        self._create_project(pid, 'client_id: "switch_demo_01"\ncompany_name: "开关测试公司"\n')

        self.assertEqual(scaffold.main([pid]), 0)
        self.assertFalse(scaffold.is_preview_public(pid))

        r1 = scaffold.set_preview_public(pid, True)
        r2 = scaffold.set_preview_public(pid, True)
        self.assertTrue(r1["preview_public"])
        self.assertTrue(r2["preview_public"])
        self.assertTrue(os.path.isfile(r1["sentinel_path"]))

        r3 = scaffold.set_preview_public(pid, False)
        r4 = scaffold.set_preview_public(pid, False)
        self.assertFalse(r3["preview_public"])
        self.assertFalse(r4["preview_public"])
        self.assertFalse(os.path.exists(r3["sentinel_path"]))

        self.assertEqual(scaffold.main([pid, "--preview", "on"]), 0)
        self.assertTrue(scaffold.is_preview_public(pid))
        self.assertEqual(scaffold.main([pid, "--preview", "status"]), 0)
        self.assertEqual(scaffold.main([pid, "--preview", "off"]), 0)
        self.assertFalse(scaffold.is_preview_public(pid))

        for bad_id in ("", "_template", ".published", ".hidden", "../escape", "sub/dir"):
            with self.subTest(bad_id=bad_id):
                with self.assertRaises(ValueError):
                    scaffold.set_preview_public(bad_id, True)
                with self.assertRaises(ValueError):
                    scaffold.run_scaffold(bad_id)

    def test_09_nginx_claw_preview_conf_gatekeeper_rules(self):
        """验证 deploy/nginx_claw_preview.conf 的门禁规则顺序、括号闭合、无 alias 陷阱与保留前缀隔离"""
        conf_path = os.path.join(geo_utils.PROJECT_ROOT, "deploy", "nginx_claw_preview.conf")
        self.assertTrue(os.path.isfile(conf_path))
        with open(conf_path, "r", encoding="utf-8") as f:
            raw_conf = f.read()

        active_lines = [
            ln.strip() for ln in raw_conf.splitlines() if ln.strip() and not ln.strip().startswith("#")
        ]
        active_conf = "\n".join(active_lines)

        self.assertEqual(active_conf.count("{"), active_conf.count("}"), "Nginx 花括号必须严格平衡")
        self.assertIn("server_name claw.baicl.cc;", active_conf)
        self.assertIn("location = / {", active_conf)
        self.assertIn("location = /robots.txt {", active_conf)
        self.assertIn("Disallow: /", active_conf)
        self.assertNotIn("alias ", active_conf, "严禁使用 alias 与 try_files 混用")
        self.assertIn("root /Users/ne/apps/GEO/projects;", active_conf)
        self.assertIn("rewrite ^/([a-zA-Z0-9][a-zA-Z0-9_-]*)/(.*)$ /$1/outputs/site/$2 break;", active_conf)
        self.assertIn("try_files $uri $uri/index.html =404;", active_conf)
        self.assertIn("if (!-f /Users/ne/apps/GEO/projects/$1/outputs/site/.published)", active_conf)

        dot_pos = active_conf.index(r"location ~ /\.")
        proj_pos = active_conf.index("location ~ ^/([a-zA-Z0-9][a-zA-Z0-9_-]*)/(.*)$")
        self.assertLess(dot_pos, proj_pos, "点文件 404 规则必须排在客户目录正则之前以防 .published 泄露")

        slash_re = re.compile(r"^/([a-zA-Z0-9][a-zA-Z0-9_-]*)$")
        site_re = re.compile(r"^/([a-zA-Z0-9][a-zA-Z0-9_-]*)/(.*)$")
        self.assertIsNotNone(slash_re.match("/client_01"))
        self.assertIsNotNone(site_re.match("/client_01/llms.txt"))
        for rejected in ("/_template", "/_template/", "/.published", "/.git/config"):
            self.assertIsNone(slash_re.match(rejected))
            self.assertIsNone(site_re.match(rejected))


if __name__ == "__main__":
    unittest.main()
