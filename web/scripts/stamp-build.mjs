#!/usr/bin/env node
/**
 * stamp-build.mjs - 组件岛构建产物版本戳写入器
 * ------------------------------------------------------------------
 * 每次 vite build 之后运行，把 index.html 里引用的组件岛产物
 * （step0.js / geo-step0-island.css）后面追加上新的时间戳版本号，
 * 强制 Safari 丢弃旧缓存，避免出现「代码改了界面没变」的假象。
 *
 * 内置断言检查：若目标引用在 index.html 中缺失，显式告警并中断退出（R8-5）。
 *
 * 用法：node scripts/stamp-build.mjs
 */

import { readFileSync, writeFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const INDEX = resolve(__dirname, '../index.html');

// 版本号取构建时刻，精确到秒
const stamp = new Date()
  .toISOString()
  .replace(/[-:T]/g, '')
  .slice(0, 14);

const targets = ['assets/step0/step0.js', 'assets/step0/geo-step0-island.css'];

let html = readFileSync(INDEX, 'utf8');
let changed = 0;
const missing = [];

for (const asset of targets) {
  const esc = asset.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const reWith = new RegExp(`(\\.\\/${esc})\\?v=[^"'\\s]*`, 'g');
  const reWithout = new RegExp(`(\\.\\/${esc})(?=["'])`, 'g');

  if (html.includes(`./${asset}?v=`)) {
    html = html.replace(reWith, `$1?v=${stamp}`);
    changed++;
  } else if (reWithout.test(html)) {
    html = html.replace(reWithout, `$1?v=${stamp}`);
    changed++;
  } else {
    missing.push(asset);
  }
}

if (missing.length > 0) {
  console.error(`[stamp-build] 错误: 在 index.html 中未找到以下产物的引用链接（R8-5 断言拦截）:`);
  for (const m of missing) {
    console.error(`  - ./${m}`);
  }
  process.exitCode = 1;
} else if (changed > 0) {
  writeFileSync(INDEX, html, 'utf8');
  console.log(`[stamp-build] 已把 ${changed} 个产物引用刷新到版本 ${stamp}`);
} else {
  console.log('[stamp-build] 未找到需要刷新的产物引用，请检查 index.html');
}
