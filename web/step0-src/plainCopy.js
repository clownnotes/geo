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
    '还没有要问豆包的问题清单文件。若刚在 Cursor 聊天中出了题，请先回复「可以落盘」保存文件，再点「刷新列表」。',
  scriptListError: (msg) => `读取问题清单失败：${msg}`,
  scriptKindEmpty: '还没有问题清单',
  resultListLoading: '正在读取结果列表…',
  resultListEmpty:
    '目前还没有任何结果文件。请先做完第 2 步让反重力落盘，再点「刷新列表」。',
  resultListError: '无法读取已存在结果列表。',
  guideLoadError: (msg) => `引导加载失败：${msg}`,
  noScriptSelected: '选中一份清单后，这里显示题目。',
  scriptQueriesLoading: '正在读取题目…',
  scriptQueriesEmpty: (err) => `这份清单里没有题目。${err || ''}`,
  step1Title: '1. 让 Cursor 写出要问的题',
  step2Title: '2. 反重力去豆包问完题（你要粘贴两次）',
  step3Title: '3. 把豆包问到的结果，存进这个客户项目',
  copyQualityFirst: '复制「第一次问」出题说明（给 Cursor）',
  copyQualityRetest: '复制「再测一遍」出题说明（给 Cursor）',
  genScript: '一键模板出题（保底）',
  genScriptRunning: '正在生成…',
  enterStep1: '进入阶段一体检',
  footerHint:
    '阶段零做完 = 第 2 步有豆包结果文件 + 第 3 步点过「确认写入项目」+ 这里变成绿色「豆包答案已存进项目」。',
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
        '<p class="text-emerald-900/80">复制出题说明会按「再测一遍」来写。右上角绿字 = 豆包答案已存进项目，不是 Cursor 写的题。</p>',
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
    ? '项目里已有豆包答案：提示词会让 Cursor 针对上次说错/漏掉的地方出「再测一遍」的题，并带上客户期望问题。先在对话框列题给人改，再说「可以落盘」。'
    : '项目里还没有豆包答案：提示词只会让 Cursor 写「第一次要问的题」，材料来自创建资料。不要瞎编「上次失败点」。先列题讨论，再说「可以落盘」。';
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

export function cursorPromptText(pid, geoCdCmd, geoRepoRoot, guide) {
  return [
    `请在终端执行下面两条命令（当前客户项目：${pid}）。这是【模板保底出题】，质量一般；能改自然口语请改。`,
    '',
    cdCmd(geoCdCmd, geoRepoRoot, guide),
    probeScriptCmd(pid),
    '',
    `跑完后打开 projects/${pid}/outputs/probe_script_draft.json。`,
  ].join('\n');
}

export function qualityPromptText(pid, status, projectData) {
  const isRetest = status === 'baseline_ready' || status === 'awaiting_retest';
  const outRel = `projects/${pid}/outputs`;
  const draftPath = `${outRel}/probe_script_draft.json`;
  const kw = uniqueKeywords(projectData);
  const kwBlock = kw.length
    ? [
        `创建时「客户期望完善的问题库」（来自 project.yaml keywords，去重后 ${kw.length} 条）——必须优先纳入题单：`,
        ...kw.slice(0, 40).map((q, i) => `${i + 1}. ${String(q).trim()}`),
        kw.length > 40 ? `…另有 ${kw.length - 40} 条见 project.yaml` : '',
        '规则：像真人长问的保留；短词/SEO 渣词在对话里说明后丢掉，不要默默塞进问题清单。',
      ]
        .filter(Boolean)
        .join('\n')
    : '创建时「客户期望完善的问题库」目前为空：题单全部由你按失败点/维度新写，仍须像真人会问的话。';
  const modeLock = [
    '【模式已锁定 · IDE 禁止改判】',
    `本提示词已按项目状态写死：${isRetest ? '【再测一遍】（项目里已有豆包答案存档）' : '【第一次去问豆包】（项目里还没有豆包答案）'}。内部字段 probe_status=${status}。`,
    '不要因为磁盘上有旧文件，就自己改成另一种模式；有疑问先问人。',
  ].join('\n');
  const retestHint = isRetest
    ? [
        '作业要求：写出 6～10 条「再测一遍」的题（定稿后优先写入 probe_script_retest_roundN.json；也可写 ' +
          draftPath +
          '）。',
        `- 先读 ${outRel}/ 下最新 competitor_probe_*.json 与已有 probe_script_*.json（尤其 retest / remaining）。`,
        '- 针对已有失败点出题：品牌误解、人物串台、URL 缺失、竞品占位等；期望问题库里合格长问仍须并入。',
        '- 复测题干仍【不要】点名竞品（除非人明确要求对比某家）；竞品从模型回答里抽。',
        '- 可含 baseline_note / pass_hints / compare_fields（参考已有 retest 结构）。',
      ].join('\n')
    : [
        `作业要求：写出 6～10 条「第一次要问豆包」的题（定稿后写入 ${draftPath}）。`,
        '- 首轮【不要】在题干里点名竞品；竞品从模型回答里抽。',
      ].join('\n');
  return [
    '【GEO 阶段 0 · 高质量必测题】（任意 IDE 均可）',
    `客户项目：${pid}`,
    '仓库根目录请先确认，再读写文件。',
    '',
    modeLock,
    '',
    '请先阅读：',
    `- projects/${pid}/project.yaml（含一句话业务、客户期望问题库 keywords、probe_status）`,
    '- docs/specs/llm-browser-probe-sop.md',
    '- openspec/changes/2026-09-17-阶段零出题落盘与冒烟护栏/design.md（落盘契约与人话规范）',
    '- openspec/changes/archive/2026-09-16-创建与阶段零先探活再长问选题/design.md 第 C/E 节（人味长问、先聊后盘）',
    `- ${outRel}/ 下已有 probe_script_*.json / competitor_probe_*.json（若有）`,
    '',
    kwBlock,
    '',
    retestHint,
    '',
    '【工作方式 · 强制落盘契约】',
    '1. 【未落盘阶段】：必须先在对话框列出拟问清单（编号、问句、维度、为何要问）。并在回复末尾明确注明：【注意：以上题目仅在对话框列出，尚未保存进项目；管理台目前看不到新题目】。严禁未写文件却宣称「已进入管理台」。',
    '2. 【落盘口令】：只有当用户明确说「可以落盘」、「直接落盘」或「写入 roundN」后，你才允许写入磁盘 UTF-8 JSON 文件！',
    '3. 【落盘路径规则】：',
    isRetest
      ? `   - 复测：必须写入 ${outRel}/probe_script_retest_roundN.json（N 取现有最大序号+1，或按用户指定）`
      : `   - 首轮：必须写入 ${draftPath}（或按用户指定）`,
    '4. 【落盘后回复】：写完文件后，必须在回复中明确告知：① 保存的具体文件路径；② 题数；③ 提示用户【请在管理台 B 区点“刷新列表”即可看到新题目】。',
    '',
    '【问句质量 · 强制】',
    '1. 像真人会说的话（可带场景/角色，如老板/采购「我想…」）；禁止 SEO 关键词串、禁止把行业长描述塞进一句搜索框。',
    '2. 「徐州GEO优化公司哪家好」这类模板可作维度参考，但须改写成更有人味的说法再用作主问句（除非客户期望库原文就是这样且人确认保留）。',
    '3. 维度尽量覆盖：品类选型、价格/坑、品牌认知、官网、人物锚点、场景；凑维度不能牺牲人味。',
    '4. 每条含 query；尽量含 follow_up（短、可执行）；dimension 可用中文。',
    '5. 朋友竞品 SOP 里的榜单检索式、geoScore 表不要写成探活题。',
    '',
    'JSON 最低结构：',
    `{ "project_id": "${pid}", "items": [ { "query": "...", "dimension": "...", "follow_up": "..." } ] }`,
    '',
    '写完落盘后：人在管理台重新加载问题清单，再交反重力用「怎么问」说明去豆包实战。',
  ].join('\n');
}

export function antigravityPromptText(pid, activeScript) {
  const s = activeScript;
  const scriptAbs = (s && s.abs) || '';
  if (!s || !(s.items || []).length) {
    return [
      '【GEO 侦察第二步 · C 开工】',
      `当前客户：${pid}`,
      '请先确认管理台已加载到问题清单，再执行。',
    ].join('\n');
  }
  const lines = s.items.map((it, i) => {
    const q = String(it.query || '').trim();
    const fu = String(it.follow_up || '').trim();
    return fu ? `${i + 1}. ${q}\n   追问：${fu}` : `${i + 1}. ${q}`;
  });
  return [
    '【GEO 侦察第二步 · 怎么问（贴反重力）】',
    '你是执行者：用已登录 Safari 操作豆包网页，按题实战并记录，不要编造未看到的回答。',
    '',
    '【开工前必须齐的两样】',
    '1. 本条「怎么问」说明（你正在读的这段）',
    `2. 问题清单文件（用户会用 @ / 附件交给你）：${scriptAbs || '（见管理台 C+D 里的问题清单路径）'}`,
    '缺文件就先别开始问，提醒用户附上问题清单。',
    '',
    `当前客户：${pid}`,
    `题数：${s.items.length}`,
    '',
    '执行规则（强制）：',
    // [2026-09-17] [防上下文污染] 强制要求每题开新对话独立实战，严禁多题混聊
    '1. 豆包必须已登录；每测一题必须新开一个聊天窗口（一题一清空上下文，防止上一题的记忆干扰下一题的搜索结果）。',
    '2. 严格按题单顺序逐条提问：若该题有追问，在当前窗口追问完；记下完整回答后，立即点击【新对话】再问下一题。',
    '3. 每题记录：query、follow_up（若有）、mentioned_self、url_present、citation_to_self、standpoint、hallucination_detected、competitors_extracted[{name,url,is_real}]、doubao_verdict、answer_full（豆包完整回答原文，建议≥80字）。',
    '4. standpoint 用：推荐 / 中性 / 负面 / 不认识 / 误解。',
    '5. 本回合先问完并在对话汇总；【禁止现在落盘】。等用户再发【收工说明书】后再写文件。',
    '',
    '题单：',
    ...lines,
  ].join('\n');
}

export function antigravitySavePromptText(pid, activeScript, guide, geoRepoRoot) {
  const s = activeScript;
  const resultAbs = expectedResultAbs(guide, geoRepoRoot, pid);
  const outAbs = outputsAbs(guide, geoRepoRoot, pid);
  const n = s && s.items ? s.items.length : '题单条数';
  const exists = !!(guide && guide.expected_result && guide.expected_result.exists);
  return [
    '【GEO 侦察第二步 · F 收工落盘】（强制执行，不可省略）',
    '请把刚才豆包实战结果写成【一个】UTF-8 JSON 文件，不要只给 Markdown 摘要。',
    '',
    'outputs 文件夹（一定存在）：',
    outAbs,
    '',
    '目标文件绝对路径（若尚不存在请新建写入）：',
    resultAbs,
    exists
      ? '（管理台检测：该目标文件当前已存在，可覆盖写入本轮复测）'
      : '（管理台检测：该目标文件当前尚不存在，这是正常的——请新建写入）',
    '',
    '硬性要求：',
    `1. 顶层必须有 items 数组；items.length 必须 = ${n}。`,
    '2. 顶层必须含：probed_at、operator=antigravity、browser=safari、model_ui=doubao。',
    '3. 每条至少含：query、mentioned_self、url_present；并尽量含 standpoint、competitors_extracted、hallucination_detected、doubao_verdict。',
    '3b. 【②深化报告必需】每条必须另含 answer_full：豆包该题完整回答原文（建议 ≥80 字；不要只写勾选字段或一句话摘要）。',
    '4. 写完后只读打开该文件自检，并在回复里给出：绝对路径 + items 条数 + 是否提到我方品牌的一句话结论。',
    '5. 禁止改 project.yaml；回填由管理台第三步完成。',
    '',
    '字段骨架见 docs/specs/llm-browser-probe-sop.md 第 3.3 节。',
  ].join('\n');
}

export function buildPreviewCopyText(preview, pid) {
  const briefs = Array.isArray(preview.answer_briefs) ? preview.answer_briefs : [];
  const comps = preview.suggested_competitors || [];
  const kws = preview.suggested_keywords || [];
  const halls = preview.hallucinations || [];
  const summary = preview.summary || {};
  const lines = [
    '【GEO 侦察结果摘要 · 可给 IDE】',
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
      ? '结果：还没有侦察结果文件。请确认已把「②收工说明书」贴给反重力，并等它写完后再点检查。'
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
