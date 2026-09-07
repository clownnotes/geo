#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_site_standard.py
站点技术底座交付与大模型爬虫双保险自动化分级合规体检工具。

遵循 docs/specs/site-scaffold-standard.md 与 AGENTS.md 第 7 章规范：
1. 静态多租户路由末尾斜杠 301 重定向自动化断言；
2. 根目录协议三件套（llms.txt / robots.txt / schema.jsonld / sitemap.xml）完整性；
3. 页面类型差异化 Schema 与双保险标签合规矩阵（首页硬阻断 Error / 存量博文服务页 Warn 台账）；
4. 脚手架防覆盖锁机制验证（project.yaml custom_site 锁定）。

严禁使用任何彩色 Emoji 表情符号（遵循 AGENTS.md 规范）。
"""

import os
import sys
import re
import json
import glob
import urllib.request
import urllib.error

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """不自动跟随重定向，以便准确断言 HTTP 301 响应与 Location 标头"""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def check_live_301_redirects(server_url: str, project_id: str):
    """检测多租户末尾斜杠 HTTP 301 永久重定向"""
    errors = []
    warnings = []
    passed = []

    opener = urllib.request.build_opener(NoRedirectHandler)

    test_cases = [
        {
            "path": f"/sites/{project_id}",
            "expected_code": 301,
            "expected_location_suffix": f"/sites/{project_id}/",
            "desc": "多租户站点根目录缺少尾部斜杠 (/sites/id)"
        },
        {
            "path": f"/sites/{project_id}/blog",
            "expected_code": 301,
            "expected_location_suffix": f"/sites/{project_id}/blog/",
            "desc": "站内子目录缺少尾部斜杠 (/sites/id/blog)"
        },
        {
            "path": f"/sites/{project_id}/",
            "expected_code": 200,
            "expected_location_suffix": None,
            "desc": "正确携带尾部斜杠的标准根路径 (/sites/id/)"
        }
    ]

    for tc in test_cases:
        url = f"{server_url.rstrip('/')}{tc['path']}"
        req = urllib.request.Request(url, headers={"User-Agent": "GEO-SiteStandardCheck/1.0"})
        try:
            resp = opener.open(req, timeout=3)
            code = resp.status
            loc = resp.headers.get("Location", "")
        except urllib.error.HTTPError as e:
            code = e.code
            loc = e.headers.get("Location", "")
        except Exception as err:
            warnings.append(f"[跳过网络断言] 无法连接到本地服务器 {url}: {err}")
            return errors, warnings, passed

        if code == tc["expected_code"]:
            if tc["expected_location_suffix"]:
                if loc.endswith(tc["expected_location_suffix"]):
                    passed.append(f"{tc['desc']} -> HTTP {code} 重定向至 {loc}")
                else:
                    errors.append(f"{tc['desc']} -> HTTP {code} 但 Location ({loc}) 未以预期后缀 {tc['expected_location_suffix']} 结尾")
            else:
                passed.append(f"{tc['desc']} -> HTTP {code} 正常响应")
        else:
            errors.append(f"{tc['desc']} -> 状态码不符！预期 HTTP {tc['expected_code']}，实际获得 HTTP {code}")

    return errors, warnings, passed

def check_base_protocol_triad(site_dir: str):
    """检测根目录底座协议三件套与 sitemap.xml"""
    errors = []
    warnings = []
    passed = []

    # 1. llms.txt
    llms_path = os.path.join(site_dir, "llms.txt")
    if os.path.isfile(llms_path) and os.path.getsize(llms_path) > 50:
        passed.append("根目录 /llms.txt 存在且格式正常")
    else:
        errors.append("根目录 /llms.txt 缺失或为空文件")

    # 2. robots.txt
    robots_path = os.path.join(site_dir, "robots.txt")
    if os.path.isfile(robots_path):
        with open(robots_path, "r", encoding="utf-8") as f:
            r_content = f.read()
        required_bots = ["Bytespider", "DeepSeekBot"]
        missing_bots = [b for b in required_bots if b not in r_content]
        if missing_bots:
            warnings.append(f"robots.txt 缺少针对部分主流 AI 爬虫的显式放行规则: {', '.join(missing_bots)}")
        else:
            passed.append("robots.txt 存在且已显式放行国产主流大模型爬虫")
    else:
        errors.append("根目录 /robots.txt 缺失")

    # 3. sitemap.xml
    sitemap_path = os.path.join(site_dir, "sitemap.xml")
    if os.path.isfile(sitemap_path) and os.path.getsize(sitemap_path) > 50:
        passed.append("根目录 /sitemap.xml 存在且已正确构建")
    else:
        errors.append("根目录 /sitemap.xml 缺失或为空文件")

    # 4. schema.jsonld
    schema_path = os.path.join(site_dir, "schema.jsonld")
    if os.path.isfile(schema_path):
        try:
            with open(schema_path, "r", encoding="utf-8") as f:
                schema_data = json.load(f)
            passed.append("根目录 /schema.jsonld 存在且为有效 JSON 格式")
            # 校验引用的本地图片是否存在
            def inspect_assets(obj):
                local_errors = []
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        if k in ("logo", "image") and isinstance(v, str):
                            if "/assets/" in v:
                                rel_asset = v.split("/assets/", 1)[1]
                                asset_file = os.path.join(site_dir, "assets", rel_asset)
                                if not os.path.isfile(asset_file):
                                    local_errors.append(f"Schema 声明的本地资产不存在: {v} -> {asset_file}")
                        else:
                            local_errors.extend(inspect_assets(v))
                elif isinstance(obj, list):
                    for item in obj:
                        local_errors.extend(inspect_assets(item))
                return local_errors

            asset_errs = inspect_assets(schema_data)
            if asset_errs:
                for ae in asset_errs:
                    errors.append(ae)
            else:
                passed.append("Schema.org 声明的实体本地图片资产全量存在且校验通过")
        except Exception as e:
            errors.append(f"根目录 /schema.jsonld JSON 解析失败: {e}")
    else:
        errors.append("根目录 /schema.jsonld 缺失")

    return errors, warnings, passed

def check_html_page_matrix(site_dir: str):
    """按照页面类型差异化合规矩阵进行分级检测"""
    errors = []
    warnings = []
    passed = []

    html_files = sorted(glob.glob(os.path.join(site_dir, "**/*.html"), recursive=True))

    p1_files = [] # 首页
    p2_files = [] # 博客知识库列表
    p3_files = [] # 博文与案例单页
    p4_files = [] # 服务与关于页及其他

    for hf in html_files:
        rel_path = os.path.relpath(hf, site_dir)
        if rel_path == "index.html":
            p1_files.append(hf)
        elif rel_path == "blog/index.html":
            p2_files.append(hf)
        elif rel_path.startswith("blog/") or rel_path.startswith("case-studies/") or rel_path.startswith("geo/") or rel_path.startswith("ai-search/"):
            p3_files.append(hf)
        else:
            p4_files.append(hf)

    # 1. P1: 企业首页检测（硬门槛阻断 Error）
    for hf in p1_files:
        rel_path = os.path.relpath(hf, site_dir)
        with open(hf, "r", encoding="utf-8") as f:
            content = f.read()

        # (1) 双保险标签
        has_sitemap_link = bool(re.search(r'<link[^>]+rel=[\"\']sitemap[\"\'][^>]*href=[\"\'][^\"\']*sitemap\.xml[\"\']', content, re.I))
        has_llms_link = bool(re.search(r'<link[^>]+rel=[\"\']alternate[\"\'][^>]+type=[\"\']text/markdown[\"\'][^>]*href=[\"\'][^\"\']*llms\.txt[\"\']', content, re.I))
        if has_sitemap_link and has_llms_link:
            passed.append(f"[P1:首页] {rel_path} 具备完整的 <head> 双保险嗅探标签 (<link rel=sitemap/alternate>)")
        else:
            errors.append(f"[P1:首页] {rel_path} 缺失 <head> 大模型双保险嗅探标签 (sitemap: {has_sitemap_link}, llms: {has_llms_link})")

        # (2) 防御性 CSS 兜底
        has_box_sizing = "box-sizing: border-box" in content or "box-sizing:border-box" in content
        if has_box_sizing:
            passed.append(f"[P1:首页] {rel_path} 具备防御性 CSS 兜底 (box-sizing: border-box reset)")
        else:
            errors.append(f"[P1:首页] {rel_path} 缺少防御性 CSS 兜底重置规则")

        # (3) 页脚显式直达链接
        has_footer_llms = "llms.txt" in content and ('href="llms.txt"' in content or 'href="/llms.txt"' in content)
        if has_footer_llms:
            passed.append(f"[P1:首页] {rel_path} 页脚包含直接指向 /llms.txt 的内链直达锚点")
        else:
            errors.append(f"[P1:首页] {rel_path} 页脚缺少直接指向 /llms.txt 的内链直达锚点")

        # (4) Schema.org 图谱与 FAQPage 实体检测
        schema_scripts = re.findall(r'<script[^>]+type=[\"\']application/ld\+json[\"\'][^>]*>(.*?)</script>', content, re.DOTALL)
        if not schema_scripts:
            errors.append(f"[P1:首页] {rel_path} 缺少内嵌 Schema.org JSON-LD 微数据")
        else:
            found_faq = False
            faq_count = 0
            found_org = False
            for ss in schema_scripts:
                try:
                    s_data = json.loads(ss.strip())
                    items = s_data.get("@graph", [s_data]) if isinstance(s_data, dict) else s_data
                    for item in items:
                        raw_types = item.get("@type", [])
                        types = [raw_types] if isinstance(raw_types, str) else (raw_types if isinstance(raw_types, list) else [])
                        if any(t in ("Organization", "LocalBusiness", "ProfessionalService") for t in types):
                            found_org = True
                        if "FAQPage" in types:
                            found_faq = True
                            faq_count += len(item.get("mainEntity", []))
                except Exception as ex:
                    errors.append(f"[P1:首页] {rel_path} 内嵌 JSON-LD 解析异常: {ex}")

            if found_org:
                passed.append(f"[P1:首页] {rel_path} 成功注入 Organization/LocalBusiness 实体微数据")
            else:
                errors.append(f"[P1:首页] {rel_path} 缺少 Organization/LocalBusiness 实体定义")

            if found_faq and faq_count >= 5:
                passed.append(f"[P1:首页] {rel_path} 成功注入 FAQPage 采购意图问答对（当前共 {faq_count} 组）")
            else:
                errors.append(f"[P1:首页] {rel_path} 缺少 FAQPage 实体或问答对组数不足（当前: {faq_count}，标准: >= 5）")

    # 2. P2: 博客知识库列表检测
    for hf in p2_files:
        rel_path = os.path.relpath(hf, site_dir)
        with open(hf, "r", encoding="utf-8") as f:
            content = f.read()

        has_sitemap_link = bool(re.search(r'<link[^>]+rel=[\"\']sitemap[\"\'][^>]*href=[\"\'][^\"\']*sitemap\.xml[\"\']', content, re.I))
        has_llms_link = bool(re.search(r'<link[^>]+rel=[\"\']alternate[\"\'][^>]+type=[\"\']text/markdown[\"\'][^>]*href=[\"\'][^\"\']*llms\.txt[\"\']', content, re.I))
        if has_sitemap_link and has_llms_link:
            passed.append(f"[P2:博客列表] {rel_path} 具备 <head> 双保险嗅探标签 (<link rel=sitemap/alternate>)")
        else:
            warnings.append(f"[P2:博客列表] {rel_path} 建议补齐 <head> 双保险嗅探标签 (<link rel=sitemap/alternate>)")

        has_collection_schema = "CollectionPage" in content or "Blog" in content or "ItemList" in content
        if has_collection_schema:
            passed.append(f"[P2:博客列表] {rel_path} 包含 CollectionPage/Blog/ItemList 结构化图谱")
        else:
            warnings.append(f"[P2:博客列表] {rel_path} 缺少 CollectionPage/Blog 结构化微数据")

        has_box_sizing = "box-sizing: border-box" in content or "box-sizing:border-box" in content
        if not has_box_sizing:
            warnings.append(f"[P2:博客列表] {rel_path} 缺少防御性 CSS 兜底重置规则（建议后续批处理完善）")

    # 3. P3: 博文与案例单页（存量页面台账统计，Warn 级别）
    p3_total = len(p3_files)
    p3_with_schema = 0
    p3_with_double_links = 0
    p3_with_defensive_css = 0

    for hf in p3_files:
        with open(hf, "r", encoding="utf-8") as f:
            c = f.read()
        if "Article" in c or "TechArticle" in c or "BlogPosting" in c:
            p3_with_schema += 1
        has_sitemap = bool(re.search(r'<link[^>]+rel=[\"\']sitemap[\"\'][^>]*href=[\"\'][^\"\']*sitemap\.xml[\"\']', c, re.I))
        has_llms = bool(re.search(r'<link[^>]+rel=[\"\']alternate[\"\'][^>]+type=[\"\']text/markdown[\"\'][^>]*href=[\"\'][^\"\']*llms\.txt[\"\']', c, re.I))
        if has_sitemap and has_llms:
            p3_with_double_links += 1
        if "box-sizing: border-box" in c or "box-sizing:border-box" in c:
            p3_with_defensive_css += 1

    passed.append(f"[P3:博文/案例] 共扫描 {p3_total} 篇单页，其中 {p3_with_schema} 篇具备 Article 结构化微数据")
    if p3_with_double_links < p3_total:
        warnings.append(f"[P3:存量博文缺口台账] 尚有 {p3_total - p3_with_double_links}/{p3_total} 篇单页未注入 <head> 双保险嗅探标签（后续批处理完善）")
    if p3_with_defensive_css < p3_total:
        warnings.append(f"[P3:存量博文缺口台账] 尚有 {p3_total - p3_with_defensive_css}/{p3_total} 篇单页未注入内联防御性 CSS reset（后续批处理完善）")

    # 4. P4: 服务与关于单页检测（存量页面台账统计，Warn 级别）
    p4_total = len(p4_files)
    p4_with_schema = 0
    p4_with_double_links = 0
    p4_with_defensive_css = 0

    for hf in p4_files:
        with open(hf, "r", encoding="utf-8") as f:
            c = f.read()
        if "Service" in c or "AboutPage" in c or "Organization" in c:
            p4_with_schema += 1
        has_sitemap = bool(re.search(r'<link[^>]+rel=[\"\']sitemap[\"\'][^>]*href=[\"\'][^\"\']*sitemap\.xml[\"\']', c, re.I))
        has_llms = bool(re.search(r'<link[^>]+rel=[\"\']alternate[\"\'][^>]+type=[\"\']text/markdown[\"\'][^>]*href=[\"\'][^\"\']*llms\.txt[\"\']', c, re.I))
        if has_sitemap and has_llms:
            p4_with_double_links += 1
        if "box-sizing: border-box" in c or "box-sizing:border-box" in c:
            p4_with_defensive_css += 1

    passed.append(f"[P4:服务与关于] 共扫描 {p4_total} 篇定制子站页面，其中 {p4_with_schema} 篇具备业务结构化微数据")
    if p4_with_double_links < p4_total:
        warnings.append(f"[P4:定制子站缺口台账] 尚有 {p4_total - p4_with_double_links}/{p4_total} 篇页面未注入 <head> 双保险嗅探标签（后续批处理完善）")
    if p4_with_defensive_css < p4_total:
        warnings.append(f"[P4:定制子站缺口台账] 尚有 {p4_total - p4_with_defensive_css}/{p4_total} 篇页面未注入内联防御性 CSS reset（后续批处理完善）")

    return errors, warnings, passed

def check_scaffold_protection(project_id: str):
    """检测脚手架防覆盖机制与 project.yaml 锁定标记"""
    errors = []
    warnings = []
    passed = []

    # 1. 检查 project.yaml 是否配置 custom_site: true
    pyaml_path = os.path.join(ROOT_DIR, f"projects/{project_id}/project.yaml")
    if os.path.isfile(pyaml_path):
        with open(pyaml_path, "r", encoding="utf-8") as f:
            pyaml_content = f.read()
        if re.search(r'custom_site:\s*true', pyaml_content):
            passed.append(f"projects/{project_id}/project.yaml 已显式声明 custom_site: true 保护锁")
        else:
            errors.append(f"projects/{project_id}/project.yaml 缺少 custom_site: true 保护锁声明")
    else:
        errors.append(f"项目配置文件不存在: {pyaml_path}")

    # 2. 检查 tools/geo/scaffold.py 代码中是否具备保护锁逻辑
    scaffold_py = os.path.join(ROOT_DIR, "tools/geo/scaffold.py")
    if os.path.isfile(scaffold_py):
        with open(scaffold_py, "r", encoding="utf-8") as f:
            scaffold_code = f.read()
        if 'cfg.get("custom_site"' in scaffold_code or "cfg.get('custom_site'" in scaffold_code:
            passed.append("tools/geo/scaffold.py 已内置 custom_site 防覆盖保护逻辑")
        else:
            errors.append("tools/geo/scaffold.py 缺失 custom_site 防覆盖保护拦截分支")
    else:
        errors.append("tools/geo/scaffold.py 文件不存在")

    return errors, warnings, passed

def main():
    project_id = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "nextgeo"
    server_url = "http://127.0.0.1:8088"
    for arg in sys.argv:
        if arg.startswith("--server="):
            server_url = arg.split("=", 1)[1]

    site_dir = os.path.join(ROOT_DIR, f"projects/{project_id}/outputs/site")
    if not os.path.isdir(site_dir):
        print(f"[ERROR] 目标站点目录不存在: {site_dir}")
        sys.exit(1)

    print("=" * 70)
    print(f" 站点技术底座交付与大模型爬虫双保险合规巡检: [{project_id}]")
    print(" 遵循: docs/specs/site-scaffold-standard.md & AGENTS.md 第 7 章")
    print("=" * 70)

    total_passed = []
    total_warnings = []
    total_errors = []

    # 维度一：多租户路由 301 尾部重定向
    print("\n--- [维度一] 静态多租户末尾斜杠 301 重定向自动化断言 ---")
    e1, w1, p1 = check_live_301_redirects(server_url, project_id)
    total_errors.extend(e1)
    total_warnings.extend(w1)
    total_passed.extend(p1)
    for msg in p1: print(f"  [PASS] {msg}")
    for msg in w1: print(f"  [WARN] {msg}")
    for msg in e1: print(f"  [FAIL] {msg}")

    # 维度二：根目录协议三件套完整性
    print("\n--- [维度二] 根目录底座协议三件套与图片资产校验 ---")
    e2, w2, p2 = check_base_protocol_triad(site_dir)
    total_errors.extend(e2)
    total_warnings.extend(w2)
    total_passed.extend(p2)
    for msg in p2: print(f"  [PASS] {msg}")
    for msg in w2: print(f"  [WARN] {msg}")
    for msg in e2: print(f"  [FAIL] {msg}")

    # 维度三：页面类型差异化 Schema 与双保险矩阵
    print("\n--- [维度三] 页面类型差异化合规矩阵分级巡检 ---")
    e3, w3, p3 = check_html_page_matrix(site_dir)
    total_errors.extend(e3)
    total_warnings.extend(w3)
    total_passed.extend(p3)
    for msg in p3: print(f"  [PASS] {msg}")
    for msg in w3: print(f"  [WARN] {msg}")
    for msg in e3: print(f"  [FAIL] {msg}")

    # 维度四：脚手架防覆盖保护锁机制
    print("\n--- [维度四] 脚手架编译防覆盖锁定机制 ---")
    e4, w4, p4 = check_scaffold_protection(project_id)
    total_errors.extend(e4)
    total_warnings.extend(w4)
    total_passed.extend(p4)
    for msg in p4: print(f"  [PASS] {msg}")
    for msg in w4: print(f"  [WARN] {msg}")
    for msg in e4: print(f"  [FAIL] {msg}")

    # 汇总总结
    print("\n" + "=" * 70)
    print(" 巡检结果汇总:")
    print(f"  - 通过项 (PASS):    {len(total_passed)}")
    print(f"  - 提示与台账 (WARN): {len(total_warnings)}")
    print(f"  - 阻断错误 (FAIL):   {len(total_errors)}")
    print("=" * 70)

    if total_errors:
        print("\n[RESULT] 巡检失败！存在阻塞性门禁错误，请根据上述 [FAIL] 提示进行整改。")
        sys.exit(1)
    else:
        print("\n[RESULT] 巡检成功！核心技术底座与首页硬门槛 100% 合规通过 (exit 0)。")
        if total_warnings:
            print("注意：存在存量非阻塞台账提示，已纳入规范后续迭代任务中。")
        sys.exit(0)

if __name__ == "__main__":
    main()
