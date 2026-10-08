#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""同事协作仓单向出包工具。

只读主仓，把白名单内容清洗后写到目标目录；主仓任何文件都不被改写。
用法：
    python3 scripts/export_partner_bundle.py --target /path/to/GEOChen [--dry-run]
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TERMS_FILE = os.path.join(REPO_ROOT, "scripts", "export-clean-terms.json")
ARTIFACT_DIR = os.path.join(REPO_ROOT, "openspec", "artifacts")
TEXT_EXT = {".py", ".js", ".mjs", ".ts", ".tsx", ".vue", ".html", ".css",
            ".json", ".yaml", ".yml", ".md", ".sh", ".go", ".mod", ".example", ".txt"}
COPY_SKIP_DIRS = {"node_modules", "__pycache__", ".git", ".DS_Store"}
COPY_SKIP_FILES = {"config.yaml"}
TARGET_PATTERN = re.compile(r"(GEOChen|geochen-(export|staging|check))$")


def load_terms():
    with open(TERMS_FILE, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    for rule in data["replace"]:
        if not rule["to"]:
            raise SystemExit("清洗规则禁止置空替换: %s" % rule["from"])
    return data


def should_skip_dir(name):
    return name in COPY_SKIP_DIRS


def copy_tree(src, dst, log):
    if not os.path.isdir(src):
        return
    os.makedirs(dst, exist_ok=True)
    for entry in sorted(os.listdir(src)):
        if should_skip_dir(entry):
            continue
        s, d = os.path.join(src, entry), os.path.join(dst, entry)
        if os.path.isdir(s):
            copy_tree(s, d, log)
        elif entry in COPY_SKIP_FILES:
            log.append("排除密钥实值文件: %s" % os.path.relpath(s, REPO_ROOT))
        elif os.path.isfile(s):
            shutil.copy2(s, d)


def iter_text_files(root):
    for base, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if not should_skip_dir(x)]
        for name in files:
            if os.path.splitext(name)[1] in TEXT_EXT:
                yield os.path.join(base, name)


def is_exempt(path, exemptions):
    rel = path.replace(os.sep, "/")
    return any(rel.endswith(x) for x in exemptions)


def clean_tree(root, terms, report):
    rules = [(re.compile(r["from"], re.IGNORECASE), r["to"], r.get("note", "")) for r in terms["replace"]]
    blacklist = terms["do_not_touch"]
    for path in iter_text_files(root):
        with open(path, "r", encoding="utf-8", errors="strict") as handle:
            original = handle.read()
        text, hits = original, []
        for pattern, to, note in rules:
            def _sub(match, to=to, note=note, frm=pattern.pattern):
                matched = match.group(0)
                if any(b in matched for b in blacklist):
                    return matched
                hits.append({"from": matched, "to": to, "rule": note})
                return to
            text = pattern.sub(_sub, text)
        if text != original:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(text)
            report.append({"file": os.path.relpath(path, root), "replacements": hits})
    return report


def write_scaffold_files(root):
    os.makedirs(os.path.join(root, "data"), exist_ok=True)
    os.makedirs(os.path.join(root, "storage"), exist_ok=True)
    os.makedirs(os.path.join(root, "reports"), exist_ok=True)
    for sub in ("data", "storage", "reports"):
        open(os.path.join(root, sub, ".gitkeep"), "a").close()


PARTNERS_SKELETON = """partners:
  - id: "partner_demo_0001"
    name: "示例渠道伙伴"
    status: "active"
    created_at: "2026-01-01"
"""

DEMO_PROJECT = """# 示例客户项目（虚构，仅供本地自测）
client_id: "demo-client"
company_name: "示例科技服务有限公司"
brand_name: "示例科技"
founder: "张三"
founder_title: "创始人"
slogan: "示例业务一句话描述"
official_url: "https://demo.example.com"
area_served: "示例市"
custom_site: true
"""


def write_env_example(root):
    """只导出键名，值一律留空；绝不把主仓真值带出。"""
    keys, source = [], os.path.join(REPO_ROOT, ".env")
    if os.path.isfile(source):
        with open(source, "r", encoding="utf-8", errors="ignore") as handle:
            for line in handle:
                if "=" in line and not line.strip().startswith("#"):
                    keys.append(line.split("=", 1)[0].strip())
    body = "# 上游服务凭证：由使用者自备，值留空即可启动，AI 生成类功能会返回未配置提示\n"
    body += "".join("%s=\n" % k for k in sorted(set(keys)))
    with open(os.path.join(root, ".env.example"), "w", encoding="utf-8") as handle:
        handle.write(body)


def write_partner_files(root):
    os.makedirs(os.path.join(root, "config"), exist_ok=True)
    with open(os.path.join(root, "config", "geo_partners.yaml"), "w", encoding="utf-8") as handle:
        handle.write(PARTNERS_SKELETON)
    demo = os.path.join(root, "projects", "demo-client", "outputs")
    os.makedirs(demo, exist_ok=True)
    with open(os.path.join(root, "projects", "demo-client", "project.yaml"), "w", encoding="utf-8") as handle:
        handle.write(DEMO_PROJECT)
    write_env_example(root)
    with open(os.path.join(root, ".gitignore"), "w", encoding="utf-8") as handle:
        handle.write(".env\nsrc/gateway/config.yaml\nnode_modules/\n__pycache__/\n*.pyc\n"
                     "data/*.json\nstorage/\nprojects/*/outputs/\nserver.log\n.DS_Store\n")


def sha256_of(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest(root):
    entries = []
    for path in sorted(iter_text_files(root)) :
        rel = os.path.relpath(path, root).replace(os.sep, "/")
        with open(path, "r", encoding="utf-8", errors="ignore") as handle:
            lines = sum(1 for _ in handle)
        entries.append({"path": rel, "sha256": sha256_of(path), "lines": lines})
    payload = {"schema": 1, "repo": "GEOChen", "files": entries}
    with open(os.path.join(root, "delivery-manifest.json"), "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=1)
    return len(entries)


def scan_forbidden(root, terms):
    problems = []
    for path in iter_text_files(root):
        if is_exempt(path, terms["example_key_exemptions"]):
            continue
        with open(path, "r", encoding="utf-8", errors="ignore") as handle:
            text = handle.read()
        for word in terms["forbidden_scan"]:
            if re.search(word, text, re.IGNORECASE):
                problems.append("%s :: %s" % (os.path.relpath(path, root), word))
    return problems


def verify_python_syntax(root):
    """清洗后硬闸：任何 .py 语法被改坏都立即报错，绝不带病出包。"""
    import ast
    broken = []
    for base, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if not should_skip_dir(x)]
        for name in files:
            if not name.endswith(".py"):
                continue
            path = os.path.join(base, name)
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    ast.parse(handle.read(), filename=path)
            except SyntaxError as exc:
                broken.append("%s:%s %s" % (os.path.relpath(path, root), exc.lineno, exc.msg))
    return broken


README_BODY = """# GEO 前后端源码工作仓

全站界面、后端服务与网关都在这个仓库里，由你独立编辑；改完提 PR，我方审核合并后回灌主仓再部署。

## 目录结构
- `src/tools/geo/`：Python 后端（管理台服务 `server.py`、命令行 `cli.py`、各业务模块）
- `src/web/`：前端（`index.html` 管理工作台、`step0-src/` Vue3 组件岛、`login/share` 等页面、`assets/step0/` 构建产物）
- `src/gateway/`：Go 网关与 `client/` 前端 SDK
- `tests/`：自动化测试；`config/geo_partners.yaml` 与 `projects/demo-client/` 是示例数据

## 起服务
```bash
cp .env.example .env          # 上游大模型凭证自备；不填也能启动，AI 生成类按钮会返回"未配置"提示，属预期
pip3 install -r requirements.txt
PYTHONPATH=src python3 -m tools.geo web --port 8088
```
浏览器打开 http://127.0.0.1:8088 ，用示例项目 `demo-client` 点界面。

## 提 PR 前必须自测（顺序照抄）
```bash
npm install && npm run build:step0
PYTHONPATH=src python3 -m unittest discover -s tests -t . -p "test_*.py"
cd src/gateway && go test ./...
```
标准是**不新增红**（下面有现状说明）。PR 描述里附上上面命令的输出末尾 20 行；没附测试输出的 PR 一律退回。

## 测试现状（先看清，别误判成你环境坏了）
包里 63 个测试模块：**26 个绿，37 个红**。红的绝大多数原因是这个包**故意不带真实客户数据**
（`projects/` 下只有一个虚构的 `demo-client`），那些测试去读真实客户交付物就读不到；另有 2 个
（`test_console_gate_leak_prevention`、`test_site_crawler_and_gate`）要先起服务才有意义。
网关 `go test` 另有 2 个断言与现状不符，也已备案。

**你的门槛是"不新增红"**：上面 26 个绿模块保持绿；改动导致它们变红，PR 退回。
全量回归由我方在主仓侧执行，你不需要修这 37 个历史红，也**不要**为了让它们变绿去改断言或造假数据。

## 别动这些
- `src/gateway/config.yaml` 不存在是故意的，凭证走环境变量；需要网关配置请照 `config.yaml.example` 自己建，不要提交进仓库。
- 源码里的默认客户 ID、行业词库是业务现状，可以改，但必须在 PR 描述里单列说明。
"""

PROJECT_GUIDE_BODY = """# 这个项目是怎么跑起来的（30 秒版）

一条交付流水线，八个阶段，全部在管理台 `src/web/index.html` 里点：
建档 ➔ 现状体检 ➔ 素材语料 ➔ 事实母盘 ➔ 官网建站 ➔ 答题卡 ➔ 矩阵分发 ➔ 验收结案。

- 前端两轨并存：`index.html` 是老的大屏（含全部内联脚本），`step0-src/` 是新拆出的 Vue3 组件岛，
  由 `npm run build:step0` 打包成 `src/web/assets/step0/step0.js`，`index.html` 用
  `window.__GEO_STEP0__.mount('#step0-app-root', { projectData, isDeveloper })` 挂载。
- 后端入口 `src/tools/geo/server.py`（约 6400 行、215 条路由），命令行入口 `src/tools/geo/cli.py`，
  统一用 `PYTHONPATH=src python3 -m tools.geo <子命令>`。
- 数据落盘：客户项目在各目录下的 `projects/{客户ID}/`，运行态写在 `data/`，音频缓存在 `storage/`。
- 网关 `src/gateway/main.go` 负责把前端的对话与伴读音频请求转发到上游服务，前端不持有任何凭证。
- 权限：登录鉴权走统一用户中心；`isDeveloper` 决定开发者视图与写手视图两套文案。
"""


def write_docs(root):
    with open(os.path.join(root, "README.md"), "w", encoding="utf-8") as handle:
        handle.write(README_BODY)
    with open(os.path.join(root, "PROJECT_GUIDE.md"), "w", encoding="utf-8") as handle:
        handle.write(PROJECT_GUIDE_BODY)


def main_repo_untouched():
    out = subprocess.run(["git", "-C", REPO_ROOT, "status", "--porcelain", "--", "src", "tests"],
                         capture_output=True, text=True).stdout.strip()
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    target = os.path.abspath(os.path.expanduser(args.target))
    if not TARGET_PATTERN.search(target):
        raise SystemExit("中止：目标路径 %s 不在允许清单（GEOChen 或 geochen-export/staging/check），拒绝写入。" % target)

    terms = load_terms()
    before = main_repo_untouched()

    plan = [
        ("src/tools", "src/tools"), ("src/web", "src/web"), ("src/gateway", "src/gateway"),
        ("tests", "tests"),
    ]
    log = []
    print("== 目标: %s%s ==" % (target, "  [dry-run 只列清单不写入]" if args.dry_run else ""))
    for rel, _ in plan:
        src = os.path.join(REPO_ROOT, rel)
        print("  复制 %s/  ->  %s/%s/" % (rel, target.split("/")[-1], rel))
    for rel in ("geo", "requirements.txt", "package.json"):
        print("  复制 %s" % rel)
    if args.dry_run:
        return 0

    if os.path.isdir(target):
        for name in ("src", "tests"):
            shutil.rmtree(os.path.join(target, name), ignore_errors=True)
    os.makedirs(target, exist_ok=True)
    for rel, _ in plan:
        copy_tree(os.path.join(REPO_ROOT, rel), os.path.join(target, rel), log)
    for rel in ("geo", "requirements.txt", "package.json"):
        shutil.copy2(os.path.join(REPO_ROOT, rel), os.path.join(target, rel))

    write_partner_files(target)
    write_scaffold_files(target)
    write_docs(target)

    report = []
    clean_tree(target, terms, report)
    broken = verify_python_syntax(target)
    if broken:
        print("清洗后 Python 语法自检失败 %d 处，已中止出包:" % len(broken))
        for line in broken[:10]:
            print("    - " + line)
        return 3

    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    with open(os.path.join(ARTIFACT_DIR, "cleaning-map.json"), "w", encoding="utf-8") as handle:
        json.dump({"schema": 1, "repo": "GEO", "files": report}, handle, ensure_ascii=False, indent=1)

    count = build_manifest(target)
    problems = scan_forbidden(target, terms)

    after = main_repo_untouched()
    print("\n== 出包结果 ==")
    print("  清单文件数: %d" % count)
    print("  清洗文件数: %d（明细存主仓 openspec/artifacts/cleaning-map.json）" % len(report))
    print("  排除项: %s" % ("; ".join(log) or "无"))
    pending = len([x for x in before.splitlines() if x.strip()])
    drift_ok = (after == before)
    print("  主仓零污染: %s（出包前待提交 %d 项，出包后保持 %s）"
          % ("通过，出包过程未改动主仓" if drift_ok else "异常：出包过程改动了主仓，立即排查", pending, "一致" if drift_ok else "不一致"))
    if problems:
        print("  出厂扫描命中 %d 处（必须清零）:" % len(problems))
        for line in problems[:20]:
            print("    - " + line)
        return 1
    print("  出厂扫描: 违禁词 0 命中，通过")
    return 0 if drift_ok else 2


if __name__ == "__main__":
    sys.exit(main())
