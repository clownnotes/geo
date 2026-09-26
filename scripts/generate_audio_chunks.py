#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_audio_chunks.py
为全站官网文章自动化提取纯净正文，并按自然断句切片生成静态索引 assets/audio_meta/{slug}.json。
严格约束：单切片 <= 280 字符，100% 走小毛驴 <= 300 字符同步毫秒直出通道。
"""

import os
import sys
import re
import json
import glob
from html.parser import HTMLParser

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SITE_DIR = os.path.join(ROOT_DIR, 'projects/nextgeo/outputs/site')
OUTPUTS_DIR = os.path.join(ROOT_DIR, 'projects/nextgeo/outputs')

CATEGORIES = ['blog', 'ai-search', 'case-studies', 'geo']

class ArticleTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_article = False
        self.ignore_depth = 0
        self.text_chunks = []
        self.current_block = []
        self.title = ""
        self.in_h1 = False
        self.h1_text = []

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        if tag == 'article':
            self.in_article = True
        if tag == 'h1' and not self.title:
            self.in_h1 = True
            self.h1_text = []
        
        # 爬虫隔离区与无关标签忽略
        if attr_dict.get('data-crawler-ignore') == 'true' or tag in ('script', 'style', 'nav', 'aside', 'footer'):
            self.ignore_depth += 1
        elif tag in ('p', 'h2', 'h3', 'li'):
            self.current_block = []

    def handle_endtag(self, tag):
        if tag == 'article':
            self.in_article = False
        if tag == 'h1' and self.in_h1:
            self.in_h1 = False
            self.title = ''.join(self.h1_text).strip()
            
        if self.ignore_depth > 0:
            if tag in ('script', 'style', 'nav', 'aside', 'footer'):
                self.ignore_depth -= 1
        elif tag in ('p', 'h2', 'h3', 'li'):
            t = ''.join(self.current_block).strip()
            # 过滤按钮文字或导航遗留
            if t and not t.startswith('←') and not t.startswith('与老白探讨'):
                self.text_chunks.append(t)
            self.current_block = []

    def handle_data(self, data):
        if self.in_h1:
            self.h1_text.append(data)
        if self.in_article and self.ignore_depth == 0:
            self.current_block.append(data)

def slice_text(paragraphs, max_chars=280):
    chunks = []
    current_chunk = []
    current_len = 0

    for p in paragraphs:
        # 按句号、叹号、问号切分句子
        sentences = re.split(r'([。！？!?\n]+)', p)
        merged_sentences = []
        for i in range(0, len(sentences)-1, 2):
            merged_sentences.append(sentences[i] + sentences[i+1])
        if len(sentences) % 2 == 1 and sentences[-1]:
            merged_sentences.append(sentences[-1])

        for s in merged_sentences:
            s = s.strip()
            if not s:
                continue
            
            # 超长单句（> max_chars）按逗号分句二次拆分
            if len(s) > max_chars:
                sub_parts = re.split(r'([，,；;]+)', s)
                sub_merged = []
                for i in range(0, len(sub_parts)-1, 2):
                    sub_merged.append(sub_parts[i] + sub_parts[i+1])
                if len(sub_parts) % 2 == 1 and sub_parts[-1]:
                    sub_merged.append(sub_parts[-1])
                    
                for part in sub_merged:
                    part = part.strip()
                    if not part:
                        continue
                    while len(part) > max_chars:
                        chunks.append(part[:max_chars])
                        part = part[max_chars:]
                    if part:
                        if current_len + len(part) <= max_chars:
                            current_chunk.append(part)
                            current_len += len(part)
                        else:
                            if current_chunk:
                                chunks.append(''.join(current_chunk))
                            current_chunk = [part]
                            current_len = len(part)
                continue

            if current_len + len(s) <= max_chars:
                current_chunk.append(s)
                current_len += len(s)
            else:
                if current_chunk:
                    chunks.append(''.join(current_chunk))
                current_chunk = [s]
                current_len = len(s)

    if current_chunk:
        chunks.append(''.join(current_chunk))
    return chunks

def process_all_articles():
    out_meta_site = os.path.join(SITE_DIR, 'assets/audio_meta')
    out_meta_outputs = os.path.join(OUTPUTS_DIR, 'assets/audio_meta')
    os.makedirs(out_meta_site, exist_ok=True)
    os.makedirs(out_meta_outputs, exist_ok=True)

    processed_count = 0
    total_chunks_count = 0
    catalog = {}

    for cat in CATEGORIES:
        cat_dir = os.path.join(SITE_DIR, cat)
        if not os.path.exists(cat_dir):
            continue
        html_files = sorted(glob.glob(os.path.join(cat_dir, '*.html')))
        for html_path in html_files:
            slug = os.path.splitext(os.path.basename(html_path))[0]
            if slug in ('index', 'voice-demo'):
                continue
                
            with open(html_path, 'r', encoding='utf-8') as f:
                content = f.read()

            extractor = ArticleTextExtractor()
            extractor.feed(content)
            
            raw_title = extractor.title or slug
            chunks = slice_text(extractor.text_chunks, max_chars=280)
            
            if not chunks:
                continue

            chunk_records = []
            for idx, text in enumerate(chunks):
                chunk_records.append({
                    "index": idx,
                    "text": text,
                    "char_count": len(text)
                })

            meta_data = {
                "slug": slug,
                "category": cat,
                "title": raw_title,
                "total_chunks": len(chunk_records),
                "chunks": chunk_records
            }

            # 双端落盘
            target_file_site = os.path.join(out_meta_site, f"{slug}.json")
            target_file_outputs = os.path.join(out_meta_outputs, f"{slug}.json")
            with open(target_file_site, 'w', encoding='utf-8') as f:
                json.dump(meta_data, f, ensure_ascii=False, indent=2)
            with open(target_file_outputs, 'w', encoding='utf-8') as f:
                json.dump(meta_data, f, ensure_ascii=False, indent=2)

            catalog[slug] = {
                "category": cat,
                "title": raw_title,
                "total_chunks": len(chunk_records)
            }
            processed_count += 1
            total_chunks_count += len(chunk_records)

    # 写入总索引
    catalog_site = os.path.join(out_meta_site, "index.json")
    catalog_outputs = os.path.join(out_meta_outputs, "index.json")
    with open(catalog_site, 'w', encoding='utf-8') as f:
        json.dump({"total_articles": processed_count, "total_chunks": total_chunks_count, "articles": catalog}, f, ensure_ascii=False, indent=2)
    with open(catalog_outputs, 'w', encoding='utf-8') as f:
        json.dump({"total_articles": processed_count, "total_chunks": total_chunks_count, "articles": catalog}, f, ensure_ascii=False, indent=2)

    print(f"✅ 切片索引生成完毕: 共处理 {processed_count} 篇文章, 生成 {total_chunks_count} 个切片 (单片均 <= 280 字符)")
    return processed_count, total_chunks_count

if __name__ == '__main__':
    process_all_articles()
