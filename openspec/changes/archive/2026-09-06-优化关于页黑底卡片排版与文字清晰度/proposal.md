# Proposal: 优化关于页黑底卡片排版与文字清晰度

## Why (为什么做)
1. **用户明确反馈**：
   - 当前 `/about/` 页面中左侧黑底核心卡片“排版很奇怪”：内部元素过多，多层框套框，强行塞入的微流程在狭窄列宽内出现恶性折行（单个字或两字断行），严重破坏了卡片的秩序感与呼吸感；
   - “黑底内的文字清晰度很差，看不清楚”：深色背景上大量使用了暗沉的深灰字（`text-slate-400`, `text-slate-500`, `text-slate-600`）和超小字号（`text-[10px]`, `text-[11px]`），对比度严重不足，导致可读性极差。

## What Changes (改动了什么)
1. **清理多余容器，恢复优雅的呼吸感排版**：
   - 移除在狭窄列宽下恶性折行的“采购初筛决策路径微流程框”，消灭框套框的视觉拥挤感；
   - 将卡片重构为清晰的三段式垂直韵律（顶部大标题 ➔ 中部场景阐述与【防丢单真相】金珀高光卡 ➔ 底部双数据统计），与右侧 6 宫格形成规整均衡的 Bento Grid 比例；
2. **文字高对比度锐利化重塑（字字清晰）**：
   - 正文与引言全面提亮为高对比度的白亮色系（`text-white`, `text-slate-100`, `text-slate-200`, `text-amber-200`），彻底取缔暗沉灰字；
   - 字号全面升级至清晰的 `text-xs (12px)`、`text-[13px]` 与 `text-sm (14px)`；
   - 【防丢单真相】采用明亮金珀微透底色与 `border-l-4 border-amber-400` 金色强调色标，搭配纯黑字金色 Badge 与高对比亮白文案，一目了然；
   - 底部数据说明从 10px 灰字提亮为 `text-xs text-slate-200 font-medium`，数字加大为 `text-2xl sm:text-3xl`。

## Capabilities (对外能力)
- 访客在查阅关于页时，黑底大卡片清晰通透、字迹锐利醒目，【防丢单真相】核心商业痛点一眼穿透，彻底消除任何阅读障碍。

## Impact (影响范围)
- `projects/nextgeo/outputs/about/index.html`
- `projects/nextgeo/outputs/site/about/index.html`
- `web/index.html`
