/** Plain-speak UI copy and prompt builders for stage 0. */

export const UI = {
  title: '阶段零：先去豆包摸底',
  subtitle:
    '先问豆包几句真人会问的话：它认不认识你们、推谁、有没有说错。这是摸底，不是一次塞满词库。',
  hintTwoThings:
    '右上角会分开显示两件事：问题清单（要问豆包什么）和豆包答案是否已存进项目（问完并点过确认）。不要当成一回事。',
  refreshProgress: '重新检查进度',
  modeBannerLoading: '现在该做什么：加载中…',
  workflowTitle: '按这个顺序做（新建客户也一样）',
  qlistBadgeChecking: '问题清单检查中…',
  qlistReady: (n) => `要问豆包的问题清单已就绪（${n} 题）`,
  qlistEmpty: '还没有要问豆包的问题清单',
  answersSaved: '豆包答案已存进项目',
  answersNotSaved: '还没把豆包答案存进项目',
  retestChip: '再测一遍',
  firstChip: '第一次问',
  awaitingRetest: '该再测一遍',
  sitePending: '由我方全托管 / 待客户域名',
  scriptListLoading: '正在读取问题清单…',
  scriptListEmpty:
    '还没有要问豆包的问题清单文件。请先在本页生成问题清单，再点「刷新列表」。',
  scriptListError: (msg) => `读取问题清单失败：${msg}`,
  scriptKindEmpty: '还没有问题清单',
  resultListLoading: '正在读取结果列表…',
  resultListEmpty:
    '目前还没有任何结果文件。请先做完第 2 步，再点「刷新列表」。',
  resultListError: '无法读取已存在结果列表。',
  guideLoadError: (msg) => `引导加载失败：${msg}`,
  noScriptSelected: '选中一份清单后，这里显示题目。',
  scriptQueriesLoading: '正在读取题目…',
  scriptQueriesEmpty: (err) => `这份清单里没有题目。${err || ''}`,
  step1Title: '1. 在本页准备要问的题',
  step2Title: '2. 拿着问题清单去豆包问',
  step3Title: '3. 把豆包问到的结果，存进这个客户项目',
  copyQualityFirst: '在本页生成第一次要问的题',
  copyQualityRetest: '在本页生成再测一遍的题',
  genScript: '一键模板出题（保底）',
  genScriptRunning: '正在生成…',
  enterStep1: '进入阶段一体检',
  footerHint:
    '阶段零做完 = 第 2 步有豆包结果文件 + 第 3 步点过「确认写入项目」+ 这里变成绿色「豆包答案已存进项目」。',
  refuseExternalCopy: '这一步已改成在网页里做，不用复制出去',
};

export function hasBaseline(status) {
  const s = String(status || 'unprobed').trim() || 'unprobed';
  return s === 'baseline_ready' || s === 'awaiting_retest';
}

export function resolveProbeStatus(guide, projectData) {
  const raw =
    (guide && guide.probe_status) ||
    (projectData && projectData.probe_status) ||
    'unprobed';
  return String(raw || 'unprobed').trim() || 'unprobed';
}

export function uniqueKeywords(projectData) {
  const raw = Array.isArray(projectData && projectData.keywords)
    ? projectData.keywords
    : [];
  const seen = new Set();
  const out = [];
  for (const x of raw) {
    const s = String(x || '').trim();
    if (!s || seen.has(s)) continue;
    seen.add(s);
    out.push(s);
  }
  return out;
}

export function shellQuote(path) {
  const s = String(path || '');
  if (!s) return "''";
  if (/^[A-Za-z0-9_./:-]+$/.test(s)) return s;
  return `'${s.replace(/'/g, `'\"'\"'`)}'`;
}

export function todayYmd(guide) {
  if (guide && guide.today_ymd) return guide.today_ymd;
  const d = new Date();
  return `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, '0')}${String(d.getDate()).padStart(2, '0')}`;
}

export function scriptKindLabel(file, status) {
  const fn = String(file || '');
  if (fn.includes('retest')) return '再测一遍';
  if (fn.includes('remaining')) return '补问几题';
  if (String(status || '') === 'unprobed') return '第一次问';
  return '问题清单';
}

export function buildModeBanner(isRetest, projectData, kwCount, esc) {
  const e = esc || ((x) => String(x ?? ''));
  if (isRetest) {
    return {
      className:
        'text-[11px] rounded-lg px-3 py-2.5 border space-y-1.5 bg-emerald-50/80 border-emerald-200 text-emerald-950',
      html: [
        '<p class="font-semibold">现在该做：再测一遍（豆包答案已经存进过项目）</p>',
        `<p>会用到：① 创建时的资料和客户期望问题（去重 ${kwCount} 条）；② 上次存档编号 <code class="text-[10px] px-1 rounded bg-white border">${e(projectData.probe_baseline_id || '（见项目文件）')}</code>${projectData.probe_baseline_at ? ` · ${e(projectData.probe_baseline_at)}` : ''}；③ 上次豆包答错/漏掉的地方（品牌说错、人搞混、官网找不到等）。</p>`,
        '<p class="text-emerald-900/80">点「在本页生成问题清单」会按「再测一遍」出题。右上角绿字 = 豆包答案已存进项目。</p>',
      ].join(''),
    };
  }
  return {
    className:
      'text-[11px] rounded-lg px-3 py-2.5 border space-y-1.5 bg-amber-50/80 border-amber-200 text-amber-950',
    html: [
      '<p class="font-semibold">现在该做：第一次去问豆包（项目里还没有豆包答案）</p>',
      '<p>能用的材料<strong>只有</strong>创建时填的：品牌、一句话业务、地域、官网，以及（如果有）客户说过想搜什么。这时还没有豆包回答，不要编「上次答错了什么」。</p>',
      '<p class="text-amber-900/80">新建客户就停在这一档。等第 2 步问完、第 3 步点确认存进项目后，才会变成「再测一遍」。</p>',
    ].join(''),
  };
}

export function step1Blurb(isRetest) {
  return isRetest
    ? '项目里已有豆包答案：在本页生成「再测一遍」的题，针对上次说错/漏掉的地方，并带上客户期望问题。'
    : '项目里还没有豆包答案：在本页生成「第一次要问的题」，材料来自创建资料。不要瞎编「上次失败点」。';
}

export function scriptHint(isRetest, pid, esc) {
  const e = esc || ((x) => String(x ?? ''));
  return isRetest
    ? '复测问题清单优先落 probe_script_retest_roundN.json；落盘后点 B 区「刷新列表」。'
    : `首轮问题清单落盘到 projects/${e(pid)}/outputs/probe_script_draft.json 后，点 B 区「刷新列表」。`;
}

export function baselineMeta(isRetest, projectData) {
  if (isRetest) {
    return `存档编号：${projectData.probe_baseline_id || '—'} · ${projectData.probe_baseline_at || '—'}`;
  }
  return '存档编号：还没有（要等第 3 步确认写入之后才有）';
}

export function cdCmd(geoCdCmd, geoRepoRoot, guide) {
  if (geoCdCmd) return geoCdCmd;
  if (geoRepoRoot) return `cd ${shellQuote(geoRepoRoot)}`;
  if (guide && guide.cd_cmd) return guide.cd_cmd;
  return 'cd /path/to/GEO';
}

export function probeScriptCmd(pid) {
  return `python3 -m tools.geo probe-script ${pid}`;
}

export function expectedResultAbs(guide, geoRepoRoot, pid) {
  if (guide && guide.expected_result && guide.expected_result.abs) {
    return guide.expected_result.abs;
  }
  const name = `competitor_probe_doubao_${todayYmd(guide)}.json`;
  return geoRepoRoot
    ? `${geoRepoRoot}/projects/${pid}/outputs/${name}`
    : `projects/${pid}/outputs/${name}`;
}

export function outputsAbs(guide, geoRepoRoot, pid) {
  if (guide && guide.outputs_abs) return guide.outputs_abs;
  return geoRepoRoot
    ? `${geoRepoRoot}/projects/${pid}/outputs`
    : `projects/${pid}/outputs`;
}

export function cursorPromptText() {
  return '';
}

export function qualityPromptText() {
  return '';
}

export function antigravityPromptText() {
  return '';
}

export function antigravitySavePromptText() {
  return '';
}

export function buildPreviewCopyText(preview, pid) {
  const briefs = Array.isArray(preview.answer_briefs) ? preview.answer_briefs : [];
  const comps = preview.suggested_competitors || [];
  const kws = preview.suggested_keywords || [];
  const halls = preview.hallucinations || [];
  const summary = preview.summary || {};
  const lines = [
    '【GEO 侦察结果摘要 · 仅本页预览】',
    `项目：${preview.project_id || pid}`,
    `来源：${preview.source_probe || ''}`,
    `文件：${preview.probe_path || ''}`,
    `题数：${preview.item_count != null ? preview.item_count : briefs.length}`,
    '',
    '说明：这不是豆包聊天全文。每题存的是结构化结论（是否提我们、立场、一句话 verdict、抽出的竞品）。',
    '第三步「确认写入」只会把下面「准备写入」的竞品/问句写进 project；不会把 verdict 全文贴进 yaml。',
    '',
    '—— 每题豆包怎么说 ——',
  ];
  if (!briefs.length) {
    lines.push('（没有读到题目结论）');
  } else {
    briefs.forEach((b, i) => {
      lines.push(`${i + 1}. 问：${b.query || ''}`);
      lines.push(
        `   提我们：${b.mentioned_self ? '是' : '否'} · 官网链接：${b.url_present ? '有' : '无'} · 立场：${b.standpoint || '（未标）'}`,
      );
      if (b.doubao_verdict) lines.push(`   结论：${b.doubao_verdict}`);
      else lines.push('   结论：（本条未写 doubao_verdict，多半是名单题，重点在竞品列表）');
      if ((b.competitors || b.competitor_names || []).length) {
        lines.push(`   抽出竞品：${(b.competitors || b.competitor_names || []).join('、')}`);
      }
      if (b.hallucination_detected) lines.push('   标记：含幻觉/张冠李戴风险');
      lines.push('');
    });
  }
  if (preview.chat_url) {
    lines.push(`豆包会话（若还在）：${preview.chat_url}`);
    lines.push('');
  }
  if (summary.brand_status || summary.founder_status) {
    lines.push('—— 总览 ——');
    if (summary.brand_status) lines.push(`品牌：${summary.brand_status}`);
    if (summary.founder_status) lines.push(`人物：${summary.founder_status}`);
    lines.push('');
  }
  lines.push('—— 若点「确认写入」会进项目 ——');
  lines.push(`竞品：${comps.join('、') || '（无）'}`);
  lines.push('监测问句：');
  (kws.length ? kws : ['（无）']).forEach((q, i) => lines.push(`${i + 1}. ${q}`));
  if (halls.length) {
    lines.push('');
    lines.push('需要留意：');
    halls.forEach((h) => lines.push(`- ${h}`));
  }
  return lines.join('\n');
}

export function syncExpectedResultUI(guide, projectData, asDiskCheck) {
  const expect = (guide && guide.expected_result) || {};
  const latest = (guide && guide.latest_result) || null;
  const results = guide && Array.isArray(guide.results) ? guide.results : [];
  const status = String(
    (guide && guide.probe_status) || (projectData && projectData.probe_status) || '',
  );
  const hasHistory = !!(latest || results.length);
  const todayLine = expect.abs || '';
  const histLine = latest && latest.abs
    ? `\n历史最新（仍在）：${latest.abs}`
    : hasHistory
      ? `\n历史侦察文件：仍有 ${results.length} 份在 outputs/`
      : '';
  const resultPathText = todayLine + histLine;

  if (expect.exists) {
    return {
      kind: 'today_ready',
      hasHistory,
      badgeText: '已生成',
      badgeClass:
        'px-1.5 py-0.5 rounded text-[10px] font-semibold border bg-emerald-50 text-emerald-800 border-emerald-200',
      hint: asDiskCheck
        ? '结果：今天的目标文件已经写好了。可以去做第 3 步：选中该文件 → 预览 → 确认回填。'
        : '今天的目标文件已在磁盘上。',
      resultPathText,
    };
  }
  if (hasHistory) {
    const histName = (latest && latest.file) || (results[0] && results[0].file) || '已有侦察 JSON';
    return {
      kind: 'history_only',
      hasHistory,
      histName,
      badgeText: '今日未写（历史已有）',
      badgeClass:
        'px-1.5 py-0.5 rounded text-[10px] font-semibold border bg-sky-50 text-sky-800 border-sky-200',
      hint: asDiskCheck
        ? `结果：今天这份「${expect.file || '今日目标'}」还没有——这不等于第 0 步资料丢了。磁盘上仍有「${histName}」，项目存档状态：${status || '未知'}。只有今天又跑了一轮侦察，才需要生成今日这份。`
        : `今天的新文件还没写；历史侦察「${histName}」仍在（存档状态：${status || '未知'}）。不要当成资料丢失。`,
      resultPathText,
    };
  }
  return {
    kind: 'missing',
    hasHistory: false,
    badgeText: '尚未生成',
    badgeClass:
      'px-1.5 py-0.5 rounded text-[10px] font-semibold border bg-amber-50 text-amber-800 border-amber-100',
    hint: asDiskCheck
      ? '结果：还没有侦察结果文件。请先按第 2 步去豆包问完，再点检查。'
      : '点「检查有没有落盘」后，这里会用白话告诉你：今日文件有没有、历史文件还在不在。',
    resultPathText,
  };
}

export function uploadExpectedText(guide, sync) {
  const expect = (guide && guide.expected_result) || {};
  if (expect.exists) {
    return `本轮新结果已写好，建议优先选它：${expect.file || expect.abs || ''}`;
  }
  if (sync && sync.hasHistory) {
    return `今天的新文件「${expect.file || ''}」还没有（正常）。请在下方列表选历史已有结果回填；不要理解为第 0 步资料丢失。`;
  }
  return `本轮还在等的新文件（现在没有，列表里选不到它）：${expect.file || ''}。你可以先选列表里已有的旧结果，或等第 2 步落盘后再刷新。`;
}
