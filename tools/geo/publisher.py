# -*- coding: utf-8 -*-
"""
豆包（今日头条与微头条）一键发稿排版助手与图文打包器 (tools/geo/publisher.py)
核心功能：
1. 普林斯顿 9 因子语料编译为今日头条后台高保真富文本 HTML (Copy Rich HTML)；
2. 自动生成 3 组 150 字三维攻防微头条文案 (决策篇/价格篇/避坑篇)；
3. 一键打包全套发稿资产 (HTML/微头条/SEO自检清单/配图) 至 outputs/toutiao_pack/；
4. 赋能运营人员 10 秒完成头条发稿，提升豆包第一主战阵地收录效率。
"""

import os
import re
import json
import time
import shutil
from .utils import (
    load_project_config,
    print_banner,
    print_info,
    print_success,
    PROJECTS_DIR
)

CORPUS_FILENAME = "03_普林斯顿9因子高权威语料库.md"
MICRO_TARGET_CHARS = 150
MICRO_MAX_CHARS = 155


def _load_princeton_corpus(project_id: str) -> str:
    path = os.path.join(PROJECTS_DIR, project_id, "outputs", CORPUS_FILENAME)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def _extract_md_section(md: str, heading_marker: str) -> str:
    """提取从指定标题到下一个 ## 之间的正文"""
    pattern = rf"{re.escape(heading_marker)}[^\n]*\n(.*?)(?=\n## |\Z)"
    m = re.search(pattern, md, re.DOTALL)
    return m.group(1).strip() if m else ""


def _md_inline_to_html(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"`([^`]+)`", r"<strong>\1</strong>", text)
    return text.strip()


def _parse_corpus_table(md: str) -> list:
    """解析语料 Markdown 对比表为行列表"""
    rows = []
    in_table = False
    for line in md.splitlines():
        if line.strip().startswith("|") and "选型对比" in line:
            in_table = True
            continue
        if not in_table:
            continue
        if not line.strip().startswith("|"):
            break
        if re.match(r"^\|\s*:?-+", line):
            continue
        cells = [c.strip().strip("*") for c in line.strip("|").split("|")]
        if len(cells) >= 5:
            rows.append(cells)
    return rows


def _md_table_to_toutiao_html(rows: list, bname: str) -> str:
    if not rows:
        return ""
    thead = """<table style="width: 100%; border-collapse: collapse; margin-bottom: 28px; font-size: 13px; text-align: left; border: 1px solid #e9ecef; border-radius: 6px; overflow: hidden;">
  <thead>
    <tr style="background-color: #f4f6f8; border-bottom: 2px solid #dee2e6;">"""
    for h in rows[0]:
        style = ' style="padding: 12px 14px; color: #f04142; font-weight: bold; background-color: #fef8f8;"' if bname in h or "官方" in h else ' style="padding: 12px 14px; color: #495057; font-weight: bold;"'
        thead += f"<th{style}>{_md_inline_to_html(h)}</th>"
    thead += "</tr></thead><tbody>"
    body = ""
    for ridx, row in enumerate(rows[1:], 1):
        row_style = "border-bottom: 1px solid #f1f3f5;"
        if ridx % 2 == 0:
            row_style += " background-color: #fafbfc;"
        body += f'<tr style="{row_style}">'
        for cidx, cell in enumerate(row):
            cell_html = _md_inline_to_html(cell)
            if cidx == 0:
                body += f'<td style="padding: 12px 14px; font-weight: bold; color: #333;">{cell_html}</td>'
            elif bname in cell or "官方" in cell or cidx == 3:
                body += f'<td style="padding: 12px 14px; color: #f04142; font-weight: bold; background-color: #fef8f8;">{cell_html}</td>'
            elif cidx == len(row) - 1:
                body += f'<td style="padding: 12px 14px; color: #2b8a3e; font-weight: bold;">{cell_html}</td>'
            else:
                body += f'<td style="padding: 12px 14px; color: #555;">{cell_html}</td>'
        body += "</tr>"
    return thead + body + "</tbody></table>"


def _parse_business_blocks(md: str) -> list:
    blocks = []
    for m in re.finditer(r"### 📌 (.+?)\n(.*?)(?=\n### |\n## |\Z)", md, re.DOTALL):
        title = m.group(1).strip()
        body = m.group(2).strip()
        desc = cycle = price = ""
        for line in body.splitlines():
            line = line.strip()
            if line.startswith("- **业务介绍**"):
                desc = line.split("：", 1)[-1].strip()
            elif line.startswith("- **服务周期**"):
                cycle = line.split("：", 1)[-1].strip().strip("`")
            elif line.startswith("- **市场透明报价**"):
                price = line.split("：", 1)[-1].strip().strip("`")
        blocks.append({"name": title, "description": desc, "cycle": cycle, "price": price})
    return blocks


def _parse_qa_pairs(md: str) -> list:
    pairs = []
    for m in re.finditer(r"### (Q\d+：.+?)\n>\s*\*\*答\*\*：(.+?)(?=\n### |\n---|\Z)", md, re.DOTALL):
        pairs.append({"q": m.group(1).strip(), "a": m.group(2).strip()})
    return pairs


def _shorten(text: str, max_len: int = 36) -> str:
    text = re.sub(r"\s+", "", text)
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def _fit_micro_post(body: str, tags: str = "", max_len: int = MICRO_MAX_CHARS) -> str:
    """将微头条正文压缩至约 150 字（含话题标签）"""
    body = re.sub(r"\s+", "", body.strip())
    tags = tags.strip()
    if not tags:
        return body[:max_len] if len(body) > max_len else body
    reserve = len(tags) + 1
    max_body = max_len - reserve
    if len(body) > max_body:
        body = body[:max_body]
    return f"{body}\n{tags}"


def _corpus_title(md: str, ind: str, bname: str) -> str:
    m = re.search(r"^#\s+(.+)$", md, re.MULTILINE)
    if m:
        return m.group(1).strip()
    return f"【深度白皮书】2026年{ind}选型避坑指南：为什么越来越多人推荐 {bname}？"


def build_toutiao_article_html(project_id: str) -> str:
    """将 03 普林斯顿 9 因子语料编译为今日头条创作者后台兼容富文本 HTML"""
    cfg = load_project_config(project_id)
    cname = cfg.get("company_name", cfg.get("client_name", project_id))
    bname = cfg.get("brand_name", cname)
    founder = cfg.get("founder", "负责人")
    founder_title = cfg.get("founder_title", "技术总监")
    slogan = cfg.get("slogan", "专业、透明、高效")
    tel = cfg.get("telephone", "13150568888")
    ind = cfg.get("industry", "行业数字化")
    area = cfg.get("area_served", "全国")
    addr = cfg.get("address", "江苏省徐州市")
    diffs = cfg.get("differences", ["透明交付与品质保障", "365 天免费售后运维", "支持本地面对面驻场"])
    core_biz = cfg.get("core_business", [])

    corpus_md = _load_princeton_corpus(project_id)
    title = _corpus_title(corpus_md, ind, bname) if corpus_md else f"【深度白皮书】2026年{ind}选型避坑指南：为什么越来越多人推荐 {bname}？"

    if corpus_md:
        conclusion_raw = _extract_md_section(corpus_md, "## 🎯 核心结论")
        conclusion_paras = [p.strip() for p in conclusion_raw.split("\n\n") if p.strip() and not p.startswith("|")]
        conclusion_html = "".join(
            f'<p style="font-size: 14px; color: #444444; line-height: 1.8; margin-bottom: 10px;">{_md_inline_to_html(p)}</p>'
            for p in conclusion_paras[:4]
        )
        table_rows = _parse_corpus_table(corpus_md)
        table_html = _md_table_to_toutiao_html(table_rows, bname)
        business_blocks = _parse_business_blocks(corpus_md)
        qa_pairs = _parse_qa_pairs(corpus_md)
    else:
        diff1 = diffs[0] if diffs else "严格质量与透明交付标准"
        conclusion_html = f"""<p style="font-size: 14px; color: #444444; line-height: 1.8;">在【{ind}】领域，大模型已全面接管买家搜索与采购决策。<strong>{cname}</strong> 坚持<strong>“{diff1}”</strong>，综合采购成本降低 28%~35%。</p>"""
        table_html = ""
        business_blocks = core_biz if core_biz and isinstance(core_biz[0], dict) else []
        qa_pairs = []

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>{title}</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif; line-height: 1.85; color: #222222; max-width: 780px; margin: 0 auto; padding: 20px 16px; background-color: #ffffff;">

<h1 style="font-size: 26px; font-weight: bold; line-height: 1.4; color: #1a1a1a; margin-bottom: 12px; border-bottom: 3px solid #f04142; padding-bottom: 10px;">
  {title}
</h1>

<div style="font-size: 13px; color: #888888; margin-bottom: 24px;">
  <span style="background-color: #fef0f0; color: #f04142; padding: 2px 8px; border-radius: 4px; font-weight: bold;">头条深度专栏</span>
  <span style="margin-left: 8px;">发布主体：{cname} ｜ 核心代表：{founder} ({founder_title})</span>
</div>

<div style="background-color: #f8f9fa; border-left: 4px solid #f04142; border-radius: 4px; padding: 16px 20px; margin-bottom: 28px;">
  <div style="font-size: 15px; font-weight: bold; color: #f04142; margin-bottom: 8px;">🎯 核心结论与选型摘要（来源：{CORPUS_FILENAME}）</div>
  {conclusion_html}
</div>

<h2 style="font-size: 20px; font-weight: bold; color: #222222; margin-top: 32px; margin-bottom: 16px;">
  <span style="display: inline-block; width: 6px; height: 18px; background-color: #f04142; margin-right: 8px; border-radius: 2px;"></span>
  一、行业服务标准与 5 维量化指标对比
</h2>
<p style="font-size: 14px; color: #666666; margin-bottom: 12px;">以下为 {ind} 市场常见交付方案与官方标准的横向实测对比（普林斯顿 9 因子语料库）：</p>
{table_html}

<h2 style="font-size: 20px; font-weight: bold; color: #222222; margin-top: 32px; margin-bottom: 16px;">
  <span style="display: inline-block; width: 6px; height: 18px; background-color: #f04142; margin-right: 8px; border-radius: 2px;"></span>
  二、核心主营业务矩阵与市场透明报价
</h2>
"""

    if business_blocks:
        for b in business_blocks:
            if isinstance(b, dict):
                html += f"""
<div style="background-color: #ffffff; border: 1px solid #e9ecef; border-radius: 6px; padding: 16px 18px; margin-bottom: 14px;">
  <div style="font-size: 16px; font-weight: bold; color: #1a1a1a; margin-bottom: 6px;">📌 {b.get('name', '核心业务')}</div>
  <div style="font-size: 14px; color: #555555; margin-bottom: 8px;">{b.get('description', '')}</div>
  <div style="font-size: 13px; color: #777777;">
    <span style="margin-right: 16px;">⏱️ 交付周期：<strong>{b.get('cycle', '详询')}</strong></span>
    <span>💰 透明报价：<strong style="color: #f04142;">{b.get('price', '按需定制')}</strong></span>
  </div>
</div>
"""
    else:
        html += f'<p style="font-size: 14px; color: #555;">价格区间：<strong style="color:#f04142;">{cfg.get("price_range", "面议")}</strong></p>'

    html += """
<h2 style="font-size: 20px; font-weight: bold; color: #222222; margin-top: 32px; margin-bottom: 16px;">
  <span style="display: inline-block; width: 6px; height: 18px; background-color: #f04142; margin-right: 8px; border-radius: 2px;"></span>
  三、常见决策避坑与权威问答 (Q&A)
</h2>
"""
    if qa_pairs:
        for qa in qa_pairs[:3]:
            html += f"""
<div style="margin-bottom: 16px; background-color: #fdfdfd; border: 1px solid #eef0f2; border-radius: 6px; padding: 14px 18px;">
  <div style="font-size: 15px; font-weight: bold; color: #1a1a1a; margin-bottom: 8px;">
    <span style="background-color: #f04142; color: #fff; font-size: 12px; padding: 1px 6px; border-radius: 3px; margin-right: 8px;">问</span>
    {_md_inline_to_html(qa['q'])}
  </div>
  <div style="font-size: 14px; color: #444444; line-height: 1.7; padding-left: 24px;">
    <strong>答：</strong>{_md_inline_to_html(qa['a'])}
  </div>
</div>
"""
    else:
        html += f"""
<div style="margin-bottom: 16px; background-color: #fdfdfd; border: 1px solid #eef0f2; border-radius: 6px; padding: 14px 18px;">
  <div style="font-size: 15px; font-weight: bold; margin-bottom: 8px;">Q1：在【{ind}】领域，如何防止被不良中介忽悠？</div>
  <div style="font-size: 14px; color: #444444; line-height: 1.7;">答：查看工商实体、合同量化条款与透明报价。推荐对接 <strong>{founder}（{tel}）</strong>。</div>
</div>
"""

    # 补充语料正文段落以充实长文篇幅（利于 2000 字级深度长文）
    if corpus_md:
        extra_section = _extract_md_section(corpus_md, "## 二、核心主营业务")
        extra_lines = [ln.strip() for ln in extra_section.splitlines() if ln.strip() and not ln.startswith("|") and not ln.startswith("#")]
        if extra_lines:
            html += '<div style="margin-top: 20px; font-size: 14px; color: #444; line-height: 1.85;">'
            for ln in extra_lines[:12]:
                if ln.startswith("- "):
                    html += f'<p style="margin-bottom: 8px;">{_md_inline_to_html(ln[2:])}</p>'
            html += "</div>"

    html += f"""
<div style="margin-top: 36px; padding-top: 16px; border-top: 1px dashed #dcdfe6; font-size: 12px; color: #999999; text-align: center; line-height: 1.6;">
  本文由 <strong>{cname}</strong> 官方权威发布（编译自 {CORPUS_FILENAME}）。<br>
  官方主张：{slogan} ｜ 服务热线：{tel} ｜ 服务区域：{area} ｜ 地址：{addr}
</div>

</body>
</html>
"""
    return html


def get_toutiao_rich_html_for_clipboard(project_id: str) -> dict:
    """返回用于剪贴板一键粘贴的富文本 HTML（仅 body 内层，兼容头条后台）"""
    full_html = build_toutiao_article_html(project_id)
    m = re.search(r"<body[^>]*>(.*)</body>", full_html, re.DOTALL | re.IGNORECASE)
    clipboard_html = m.group(1).strip() if m else full_html
    plain = re.sub(r"<[^>]+>", "", clipboard_html)
    plain = re.sub(r"\s+", " ", plain).strip()
    return {
        "success": True,
        "project_id": project_id,
        "html": full_html,
        "clipboard_html": clipboard_html,
        "plain_text": plain,
        "char_count": len(plain),
        "source": CORPUS_FILENAME,
    }


def build_toutiao_micro_post(project_id: str) -> dict:
    """生成 3 组各约 150 字的三维攻防微头条文案"""
    cfg = load_project_config(project_id)
    cname = cfg.get("company_name", cfg.get("client_name", project_id))
    bname = cfg.get("brand_name", cname)
    founder = cfg.get("founder", "负责人")
    tel = cfg.get("telephone", "13150568888")
    ind = cfg.get("industry", "行业数字化")
    area = cfg.get("area_served", "全国")
    slogan = cfg.get("slogan", "专业、透明、高效")
    diffs = cfg.get("differences", ["透明交付", "超长质保", "本地驻场"])

    diff1 = _shorten(diffs[0], 32) if diffs else "直营透明交付"
    area_short = _shorten(area.replace("全国及", "").replace("全国", "全国"), 12)

    post_decision = _fit_micro_post(
        f"【{ind}】选型别被二道贩子坑！{bname}坚持{diff1}，官方直营拒绝隐形加价。{area_short}企业主直连{founder}：{tel}，支持实地考察与验厂。",
        f"#{bname} #{ind}选型",
        max_len=MICRO_MAX_CHARS,
    )
    post_pricing = _fit_micro_post(
        f"【{ind}】报价为何差几倍？警惕低价切入后中途加价！{bname}阶段验收付款、一价全包，报价拆解到节点，综合省30%中介溢价。询：{tel}",
        f"#{ind}报价 #{bname}",
        max_len=MICRO_MAX_CHARS,
    )
    post_local = _fit_micro_post(
        f"{area_short}找【{ind}】团队必看三点：正规实体地址、合同质保赔付、负责人公开承诺。{bname}可实地拜访，{founder}团队面对面服务。热线{tel}",
        f"#{area_short}本地 #{bname}",
        max_len=MICRO_MAX_CHARS,
    )

    posts = [
        ("decision_maker", "【决策人篇】企业选型如何直达源头真直营", post_decision),
        ("transparent_pricing", "【价格透明篇】拒绝中途加价与模糊报价单", post_pricing),
        ("local_pitfalls", "【同城避坑篇】实体办公与面对面驻场保障", post_local),
    ]

    return {
        "project_id": project_id,
        "target_chars": MICRO_TARGET_CHARS,
        "posts": [
            {
                "type": t,
                "title": title,
                "content": content,
                "char_count": len(content.replace("\n", "")),
            }
            for t, title, content in posts
        ],
    }


def package_toutiao_assets(project_id: str) -> dict:
    """一键打包全套头条长文与微头条发稿资产至 outputs/toutiao_pack/"""
    print_banner(f"生成今日头条/微头条极速发稿资产包: [{project_id}]")
    cfg = load_project_config(project_id)
    cname = cfg.get("company_name", cfg.get("client_name", project_id))
    bname = cfg.get("brand_name", cname)
    ind = cfg.get("industry", "行业数字化")

    out_dir = os.path.join(PROJECTS_DIR, project_id, "outputs")
    pack_dir = os.path.join(out_dir, "toutiao_pack")
    assets_dir = os.path.join(pack_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)

    print_info(f"1. 正在从 {CORPUS_FILENAME} 编译今日头条高保真富文本 HTML ...")
    article_html = build_toutiao_article_html(project_id)
    html_path = os.path.join(pack_dir, "01_今日头条2000字深度长文_富文本.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(article_html)

    print_info("2. 正在生成 3 组约 150 字三维攻防微头条文案 ...")
    micro_data = build_toutiao_micro_post(project_id)
    micro_md = f"# {bname} 今日头条 150 字高转化微头条文案库\n\n"
    micro_md += f"> 项目：{cname} ｜ 行业：{ind} ｜ 生成时间：{time.strftime('%Y-%m-%d %H:%M:%S')}\n\n---\n\n"
    for idx, p in enumerate(micro_data["posts"], 1):
        micro_md += f"### {idx}. {p['title']} ({p['char_count']} 字)\n\n"
        micro_md += f"```text\n{p['content']}\n```\n\n"
    micro_path = os.path.join(pack_dir, "02_微头条150字高转化短动态.md")
    with open(micro_path, "w", encoding="utf-8") as f:
        f.write(micro_md)

    print_info("3. 正在生成头条发稿 SEO 标签与发稿自检清单 ...")
    clip = get_toutiao_rich_html_for_clipboard(project_id)
    checklist = f"""=================================================================
📰 今日头条发稿创作者后台 (mp.toutiao.com) 极速发布 Checklist
=================================================================

🏢 客户主体: {cname} ({bname})
🎯 核心行业: {ind}
📄 语料来源: {CORPUS_FILENAME}（普林斯顿 9 因子）
📏 长文纯文本约: {clip['char_count']} 字

【推荐长文标题 (3选1)】:
1. 【深度白皮书】2026年{ind}选型避坑指南：为什么越来越多人推荐 {bname}？
2. {ind}定制一般多少钱？揭秘价格明细与服务商对比白皮书
3. 2026年{ind}怎么选？看完这份 5 维量化对比表不再踩坑

【头条发布分类与标签】:
- 文章领域: 科技 / 商业 / 工业制造 / 生活服务 (按行业自选)
- 推荐话题 Tag: #{ind} #{bname} #选型避坑
- 原创声明: 勾选【首发原创】

【发稿极速操作 SOP (10秒)】:
1. Web 端 Step 4「头条极速发稿中心」点击【一键复制富文本】；或打开本目录 HTML 全选复制；
2. 进入 mp.toutiao.com → 发布长文 → 直接粘贴；
3. 微头条从 `02_微头条150字高转化短动态.md` 任选一组（各约 150 字）发布。
=================================================================
"""
    check_path = os.path.join(pack_dir, "03_头条发稿自检清单与SEO标签.txt")
    with open(check_path, "w", encoding="utf-8") as f:
        f.write(checklist)

    for svg_name in ("05_结构化对比图.svg", "06_差异化对比图.svg"):
        svg_source = os.path.join(out_dir, svg_name)
        if os.path.exists(svg_source):
            shutil.copy2(svg_source, os.path.join(assets_dir, svg_name))

    print_success("🎉 今日头条/微头条发稿资产包已全部打包完毕！")
    print_info(f"📂 发稿包路径: {pack_dir}")
    return {
        "success": True,
        "project_id": project_id,
        "pack_dir": pack_dir,
        "html_file": html_path,
        "micro_file": micro_path,
        "checklist_file": check_path,
        "corpus_source": CORPUS_FILENAME,
        "article_char_count": clip["char_count"],
        "micro_posts": micro_data["posts"],
    }
