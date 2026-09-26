#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
inject_voice_player.py
批量为全站专文（blog, ai-search, case-studies, geo）注入 AI 语音伴读条骨架与前端驱动脚本。
遵循 docs/specs/article-template-standard.md Section 5 标准规范：
1. 0 Emoji 违规检查
2. 爬虫绝对隔离 (data-crawler-ignore="true" role="region")
3. 严格成对闭合，维持 open_divs == close_divs 绝对平衡
4. 部署 assets/js/voice-player.js 驱动，只走 /api/voice/article-chunk 专用切片路由
"""

import os
import re
import sys
import glob

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CATEGORIES = ['blog', 'ai-search', 'case-studies', 'geo']

OUTPUTS_DIRS = [
    os.path.join(ROOT_DIR, 'projects/nextgeo/outputs'),
    os.path.join(ROOT_DIR, 'projects/nextgeo/outputs/site')
]

EMOJI_PATTERN = re.compile(r'[\U0001F300-\U0001F9FF]|[\U0001FA00-\U0001FAFF]|[\u2600-\u26FF]|[\u2700-\u27BF]')

PLAYER_TEMPLATE = """          <!-- [标准伴读条首屏黄金挂载位: 位于文章大标题/元数据下方，在结论先行导读卡之前] -->
          <div id="geo-voice-player-container" class="my-6" data-crawler-ignore="true" role="region" aria-label="文章智能伴读" data-article-id="{slug}">
            <div class="bg-white border border-slate-200/80 rounded-xl p-4 shadow-xs">
              <div class="flex items-center justify-between gap-3 pb-3 border-b border-slate-100">
                <div class="flex items-center gap-2">
                  <span class="px-2 py-0.5 rounded text-xs font-medium bg-purple-50 text-[#7c5bf5] border border-purple-100">
                    AI 语音伴读
                  </span>
                  <span class="text-xs text-slate-400" id="voice-chunk-indicator">准备就绪</span>
                </div>
                <div class="flex items-center gap-2">
                  <label for="voice-select" class="text-xs text-slate-500 font-medium">音色</label>
                  <select id="voice-select" class="text-xs text-slate-700 bg-slate-50 border border-slate-200 rounded px-2 py-1">
                    <option value="standard_female_warm">温婉知性 · 佳悦</option>
                    <option value="standard_male_magnetic">磁性沉稳 · 晨阳</option>
                  </select>
                </div>
              </div>
              <div class="flex items-center justify-between gap-4 pt-3">
                <button type="button" id="voice-play-btn" class="w-8 h-8 rounded-full bg-[#7c5bf5] text-white flex items-center justify-center hover:bg-[#6b4ae6]">
                  <svg class="w-4 h-4 ml-0.5" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                </button>
                <div class="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                  <div id="voice-progress-bar" class="h-full bg-[#7c5bf5] w-0"></div>
                </div>
                <div class="flex items-center gap-1 border-l border-slate-200 pl-3">
                  <button type="button" data-rate="1.0" class="voice-rate-btn px-2 py-0.5 text-xs rounded bg-purple-100 text-[#7c5bf5] font-semibold">1.0x</button>
                  <button type="button" data-rate="1.25" class="voice-rate-btn px-2 py-0.5 text-xs rounded text-slate-500 hover:text-slate-700">1.25x</button>
                  <button type="button" data-rate="1.5" class="voice-rate-btn px-2 py-0.5 text-xs rounded text-slate-500 hover:text-slate-700">1.5x</button>
                </div>
              </div>
            </div>
          </div>
"""

SCRIPT_TAG = '  <script src="../assets/js/voice-player.js"></script>\n'

def fix_tables_safely(content):
    # 安全修复历史表格包裹问题，防止悬空 </div> 导致双栏栅格破坏
    pattern = r'(?<!<div class="overflow-x-auto my-6">)(<table class="content-table">.*?</table>(?:\s*</div>)?)'
    def replace_table(match):
        full = match.group(0)
        table_html = re.sub(r'</table>\s*</div>', '</table>', full)
        return f'<div class="overflow-x-auto my-6">{table_html}</div>'
    return re.sub(pattern, replace_table, content, flags=re.DOTALL)

def extract_and_remove_existing_player(content):
    """
    通过标签平衡算法精确剥离已存在的伴读条容器及可能附带的前置注释，
    绝不破坏页面原有的 open_divs == close_divs 平衡。
    """
    while True:
        idx = content.find('id="geo-voice-player-container"')
        if idx == -1:
            break
        div_start = content.rfind('<div', 0, idx)
        if div_start == -1:
            break

        # 向前探测是否有伴读条前置注释
        prefix_slice = content[:div_start]
        comment_match = re.search(r'(?:\s*<!--\s*\[标准伴读条挂载位.*?-->\s*)$', prefix_slice)
        start_pos = comment_match.start() if comment_match else div_start

        # 平衡计数闭合整个 player div 块
        pos = div_start
        depth = 0
        end_pos = -1
        while pos < len(content):
            if content[pos:pos+4].lower() == '<div':
                depth += 1
                pos += 4
            elif content[pos:pos+6].lower() == '</div>':
                depth -= 1
                pos += 6
                if depth == 0:
                    end_pos = pos
                    break
            else:
                pos += 1

        if end_pos != -1:
            content = content[:start_pos] + content[end_pos:]
        else:
            break

    return content

def process_file(fpath):
    fname = os.path.basename(fpath)
    slug = fname.replace('.html', '')
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. 规范化表格闭合，保证原文档基准 div 平衡
    content = fix_tables_safely(content)

    # 2. 彻底剥离全页可能存在的旧伴读条（旧 Section 5 或配图下旧位）
    content = extract_and_remove_existing_player(content)

    player_html = PLAYER_TEMPLATE.format(slug=slug)

    # 3. 首屏黄金位注入锚点（优先级：结论先行导读卡前 -> article-meta后 -> h1后）
    inserted = False

    # 优先级 1: 在「结论先行导读卡」之前插入 (全站专文标准锚点)
    exec_comment_m = re.search(r'(\s*)(<!--\s*结论先行导读卡|<div\b[^>]*\bborder-l-brand-600\b)', content)
    if exec_comment_m:
        indent = exec_comment_m.group(1)
        insert_idx = exec_comment_m.start()
        content = content[:insert_idx] + f"\n{player_html.strip()}\n" + indent + content[insert_idx + len(indent):]
        inserted = True

    # 优先级 2: 若未找到结论先行，在 article-meta 容器之后插入
    if not inserted:
        meta_m = re.search(r'(pb-6\s+border-b\s+border-slate-200[\s\S]*?</div>)', content)
        if meta_m:
            insert_idx = meta_m.end()
            content = content[:insert_idx] + f"\n\n{player_html.strip()}\n" + content[insert_idx:]
            inserted = True

    # 优先级 3: 兜底退化至 </h1> 之后
    if not inserted:
        h1_m = re.search(r'(</h1>)', content)
        if h1_m:
            insert_idx = h1_m.end()
            content = content[:insert_idx] + f"\n\n{player_html.strip()}\n" + content[insert_idx:]
            inserted = True
        else:
            print(f"  [WARN] {fname} 找不到任何首屏挂载锚点！")
            return False

    # 4. 注入 JS 脚本标签 (在 </body> 之前)
    if 'assets/js/voice-player.js' not in content:
        if '</body>' in content:
            content = content.replace('</body>', f"{SCRIPT_TAG}</body>")
        else:
            content += f"\n{SCRIPT_TAG}"

    # 5. 严格校验 div 标签闭合平衡
    open_divs = len(re.findall(r'<div\b', content))
    close_divs = len(re.findall(r'</div>', content))
    if open_divs != close_divs:
        print(f"  [ERROR] {fname} div 标签不平衡: open={open_divs}, close={close_divs} (差值 {open_divs - close_divs})")
        return False

    # 6. 0 Emoji 校验
    emojis = EMOJI_PATTERN.findall(player_html)
    if emojis:
        print(f"  [ERROR] {fname} 包含违规 Emoji: {emojis}")
        return False

    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(content)

    return True

def main():
    print("🚀 开始批量为全站专文注入 Section 5 AI 语音伴读骨架...")
    total_processed = 0
    total_errors = 0

    for base_dir in OUTPUTS_DIRS:
        dir_name = os.path.relpath(base_dir, ROOT_DIR)
        print(f"\n📂 正在扫描目录: {dir_name}")
        for cat in CATEGORIES:
            cat_dir = os.path.join(base_dir, cat)
            if not os.path.exists(cat_dir):
                continue
            html_files = sorted(glob.glob(os.path.join(cat_dir, '*.html')))
            articles = [f for f in html_files if not f.endswith('index.html')]
            print(f"  📁 {cat}: {len(articles)} 篇专文")

            for fpath in articles:
                if process_file(fpath):
                    total_processed += 1
                else:
                    total_errors += 1

    print(f"\n✨ 处理完成！成功处理: {total_processed} 篇文件，错误: {total_errors} 篇。")
    if total_errors > 0:
        sys.exit(1)

if __name__ == '__main__':
    main()
