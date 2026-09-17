import { computed, reactive, ref } from 'vue';
import * as api from './api.js';
import {
  UI,
  hasBaseline,
  resolveProbeStatus,
  uniqueKeywords,
  buildModeBanner,
  step1Blurb,
  scriptHint,
  baselineMeta,
  cdCmd,
  probeScriptCmd,
  expectedResultAbs,
  outputsAbs,
  cursorPromptText,
  qualityPromptText,
  antigravityPromptText,
  antigravitySavePromptText,
  buildPreviewCopyText,
  syncExpectedResultUI,
  uploadExpectedText,
  scriptKindLabel,
} from './plainCopy.js';

function defaultEscapeHtml(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

export function useStep0(bridge) {
  const guide = ref(null);
  const geoRepoRoot = ref('');
  const geoCdCmd = ref('');
  const loading = ref(false);
  const guideError = ref('');
  const scriptListState = ref('idle'); // idle | loading | loaded | empty | error
  const resultListState = ref('idle');
  const selectedScriptFile = ref('');
  const activeScript = ref(null);
  const selectedResultFile = ref('');
  const diskPreviewReady = ref(false);
  const previewData = ref(null);
  const previewCopyText = ref('');
  const pendingProbe = ref(null);
  const merge = ref(true);
  const writeTopics = ref(true);
  const checkingDisk = ref(false);
  const generatingScript = ref(false);

  const esc = (...args) => {
    const fn = bridge.escapeHtml || defaultEscapeHtml;
    return fn(...args);
  };

  // [2026-09-17] [阶段零Vue3组件岛] 解决Vue计算属性无法感知外壳非响应式全局变量变更的Bug，建立响应式桥接与切换重置
  const internalProjectId = ref(bridge.getProjectId ? bridge.getProjectId() || '' : '');
  const internalProjectData = ref(bridge.getProjectData ? bridge.getProjectData() || {} : {});
  const internalAuthToken = ref(
    (bridge.getAuthToken ? bridge.getAuthToken() || '' : '') ||
    (typeof localStorage !== 'undefined' ? localStorage.getItem('geo_token') || '' : '')
  );

  function resetProjectState() {
    selectedScriptFile.value = '';
    activeScript.value = null;
    selectedResultFile.value = '';
    previewData.value = null;
    previewCopyText.value = '';
    diskPreviewReady.value = false;
    guide.value = null;
    guideError.value = '';
  }

  function syncBridgeState() {
    const oldPid = internalProjectId.value;
    const newPid = bridge.getProjectId ? bridge.getProjectId() || '' : '';
    if (newPid !== oldPid) {
      internalProjectId.value = newPid;
      resetProjectState();
    }
    if (bridge.getProjectData) {
      internalProjectData.value = bridge.getProjectData() || {};
    }
    if (bridge.getAuthToken) {
      const t = bridge.getAuthToken() || '';
      if (t) internalAuthToken.value = t;
      else if (typeof localStorage !== 'undefined') {
        internalAuthToken.value = localStorage.getItem('geo_token') || '';
      }
    }
  }

  const projectId = computed(() => internalProjectId.value);
  const projectData = computed(() => internalProjectData.value);
  const authToken = computed(() => internalAuthToken.value);

  const probeStatus = computed(() => resolveProbeStatus(guide.value, projectData.value));

  const isRetest = computed(() => hasBaseline(probeStatus.value));

  const kwCount = computed(() => uniqueKeywords(projectData.value).length);

  const modeBanner = computed(() =>
    buildModeBanner(isRetest.value, projectData.value, kwCount.value, esc),
  );

  const step1BlurbText = computed(() => step1Blurb(isRetest.value));

  const copyPromptLabel = computed(() =>
    isRetest.value ? UI.copyQualityRetest : UI.copyQualityFirst,
  );

  const baselineMetaText = computed(() =>
    baselineMeta(isRetest.value, projectData.value),
  );

  const scriptHintText = computed(() =>
    scriptHint(isRetest.value, projectId.value, esc),
  );

  const cdCmdText = computed(() => cdCmd(geoCdCmd.value, geoRepoRoot.value, guide.value));

  const scriptCmdText = computed(() => probeScriptCmd(projectId.value));

  const cursorPrompt = computed(() =>
    cursorPromptText(projectId.value, geoCdCmd.value, geoRepoRoot.value, guide.value),
  );

  const scripts = computed(() =>
    guide.value && Array.isArray(guide.value.scripts) ? guide.value.scripts : [],
  );

  const results = computed(() =>
    guide.value && Array.isArray(guide.value.results) ? guide.value.results : [],
  );

  // 合并 guide.expected_result（exists/file/rel）与人话同步态（badgeText/hint），避免 F 区永远「尚未生成」
  const expectedResult = computed(() => {
    const expect = (guide.value && guide.value.expected_result) || {};
    const sync = syncExpectedResultUI(guide.value, projectData.value, false);
    return {
      ...sync,
      exists: !!expect.exists,
      file: expect.file || '',
      rel: expect.rel || '',
      abs: expect.abs || '',
    };
  });

  const uploadExpected = computed(() =>
    uploadExpectedText(guide.value, expectedResult.value),
  );

  const scriptPathRel = computed(() => {
    if (activeScript.value && activeScript.value.rel) return activeScript.value.rel;
    return `projects/${projectId.value}/outputs/probe_script_draft.json`;
  });

  const scriptPathAbs = computed(() => {
    if (activeScript.value && activeScript.value.abs) return activeScript.value.abs;
    return `${outputsAbs(guide.value, geoRepoRoot.value, projectId.value)}/probe_script_draft.json`;
  });

  const scriptKindText = computed(() => {
    if (!activeScript.value) return UI.scriptKindEmpty;
    const status = probeStatus.value;
    const fn = activeScript.value.file || selectedScriptFile.value;
    const items = activeScript.value.items || [];
    const kind = scriptKindLabel(fn, status);
    return items.length ? `${kind} · ${items.length} 题` : kind;
  });

  const qlistBadge = computed(() => {
    const n = activeScript.value && Array.isArray(activeScript.value.items)
      ? activeScript.value.items.length
      : 0;
    if (scriptListState.value === 'loading' || loading.value) {
      return { text: UI.qlistBadgeChecking, className: 'bg-amber-50 text-amber-900 border-amber-200' };
    }
    if (n > 0) {
      return {
        text: UI.qlistReady(n),
        className: 'bg-sky-50 text-sky-900 border-sky-200',
      };
    }
    return { text: UI.qlistEmpty, className: 'bg-amber-50 text-amber-900 border-amber-200' };
  });

  const writeStatusBadge = computed(() => {
    if (hasBaseline(projectData.value.probe_status)) {
      return {
        text: UI.answersSaved,
        className: 'bg-emerald-50 text-emerald-800 border-emerald-200',
      };
    }
    return {
      text: UI.answersNotSaved,
      className: 'bg-rose-50 text-rose-800 border-rose-200',
    };
  });

  const cmdPreview = computed(() => {
    const latest = guide.value && guide.value.latest_result;
    const fileArg = latest
      ? latest.rel
      : '<请先完成第二步落盘，再选已存在的 competitor_probe_*.json>';
    return `python3 -m tools.geo probe-preview ${projectId.value} --file ${fileArg}`;
  });

  const cmdApply = computed(() => {
    const latest = guide.value && guide.value.latest_result;
    const fileArg = latest
      ? latest.rel
      : '<请先完成第二步落盘，再选已存在的 competitor_probe_*.json>';
    return `python3 -m tools.geo probe-apply ${projectId.value} --file ${fileArg} --merge --yes`;
  });

  function toast(msg, type = 'success') {
    if (bridge.onToast) bridge.onToast(msg, type);
  }

  function refreshLucide() {
    const lucide = bridge.getLucide ? bridge.getLucide() : null;
    if (lucide && lucide.createIcons) lucide.createIcons();
  }

  async function ensureRepoPath() {
    if (geoCdCmd.value && geoRepoRoot.value) return;
    try {
      const data = await api.fetchAuthStatus(authToken.value);
      if (data.repo_root) geoRepoRoot.value = data.repo_root;
      if (data.cd_cmd) geoCdCmd.value = data.cd_cmd;
    } catch {
      /* ignore */
    }
  }

  async function fetchGuide() {
    const pid = projectId.value;
    if (!pid || pid === 'PROJECT_ID') {
      guide.value = null;
      guideError.value = '请先选择项目';
      scriptListState.value = 'error';
      resultListState.value = 'error';
      return null;
    }
    const token =
      authToken.value ||
      (bridge.getAuthToken ? bridge.getAuthToken() : '') ||
      (typeof localStorage !== 'undefined' ? localStorage.getItem('geo_token') || '' : '');
    const data = await api.fetchProbeGuide(pid, token);
    if (!data.success) throw new Error(data.message || 'probe/guide 失败');
    guide.value = data;
    if (data.repo_root) geoRepoRoot.value = data.repo_root;
    if (data.cd_cmd) geoCdCmd.value = data.cd_cmd;
    guideError.value = '';
    return data;
  }

  async function loadScriptContent(filename, meta, opts = {}) {
    const wantToast = !!opts.toast;
    const pid = projectId.value;
    const status = probeStatus.value;
    const expect = (guide.value && guide.value.expected_result) || {};
    const rel = (meta && meta.rel) || `projects/${pid}/outputs/${filename}`;
    const abs =
      (meta && meta.abs) ||
      `${outputsAbs(guide.value, geoRepoRoot.value, pid)}/${filename}`;

    try {
      const data = await api.fetchOutputFile(pid, filename, authToken.value);
      let items = [];
      let loadErr = '';
      if (data.success && data.content) {
        try {
          const parsed = JSON.parse(data.content);
          items = Array.isArray(parsed.items) ? parsed.items : [];
        } catch {
          loadErr = '文件不是合法 JSON。';
        }
      } else {
        loadErr = (data && data.message) ? String(data.message) : '读文件失败。';
      }
      const kind = scriptKindLabel(filename, status) + (items.length ? ` · ${items.length} 题` : '');
      activeScript.value = {
        file: filename,
        kind,
        abs,
        rel,
        items,
        resultAbs: expect.abs || expectedResultAbs(guide.value, geoRepoRoot.value, pid),
        resultRel: expect.rel || '',
      };
      if (wantToast) {
        toast(
          items.length
            ? `已选用：${filename}（${items.length} 题）`
            : `已选中 ${filename}，但里面没有题目`,
          items.length ? 'success' : 'error',
        );
      }
      return activeScript.value;
    } catch (e) {
      activeScript.value = null;
      if (wantToast) toast('读取问题清单失败', 'error');
      throw e;
    }
  }

  async function loadProbeScriptFromGuide() {
    const pid = projectId.value;
    const outAbs = outputsAbs(guide.value, geoRepoRoot.value, pid);

    const list = scripts.value;
    let pick = selectedScriptFile.value;
    if (!pick || !list.some((s) => s && s.file === pick)) {
      pick =
        (guide.value &&
          guide.value.recommended_script &&
          guide.value.recommended_script.file) ||
        (list[0] && list[0].file) ||
        '';
    }
    selectedScriptFile.value = pick || '';

    if (!pick) {
      activeScript.value = null;
      scriptListState.value = list.length ? 'loaded' : 'empty';
      return null;
    }

    scriptListState.value = 'loading';
    const meta =
      list.find((s) => s && s.file === pick) ||
      (guide.value && guide.value.recommended_script) ||
      null;
    try {
      await loadScriptContent(pick, meta, { toast: false });
      scriptListState.value = 'loaded';
    } catch {
      scriptListState.value = 'error';
    }
    return activeScript.value;
  }

  function pickDefaultResultFile(list) {
    if (!list.length) {
      selectedResultFile.value = '';
      diskPreviewReady.value = false;
      previewData.value = null;
      return;
    }
    if (
      selectedResultFile.value &&
      list.some((r) => r.file === selectedResultFile.value)
    ) {
      return;
    }
    const prefer =
      (guide.value &&
        guide.value.expected_result &&
        guide.value.expected_result.exists &&
        guide.value.expected_result.file) ||
      (guide.value && guide.value.latest_result && guide.value.latest_result.file) ||
      list[0].file;
    selectedResultFile.value = prefer || list[0].file;
    diskPreviewReady.value = false;
    previewData.value = null;
  }

  async function renderPanel() {
    // [2026-09-17] [阶段零Vue3组件岛] 每次渲染前同步外部外壳状态（projectId/projectData/token）
    syncBridgeState();
    loading.value = true;
    scriptListState.value = 'loading';
    resultListState.value = 'loading';
    guideError.value = '';

    await ensureRepoPath();

    try {
      await fetchGuide();
      const resList = results.value;
      pickDefaultResultFile(resList);
      resultListState.value = resList.length ? 'loaded' : 'empty';
      await loadProbeScriptFromGuide();
      if (selectedResultFile.value && !diskPreviewReady.value) {
        await previewFromDisk({ silent: true }).catch(() => {});
      }
    } catch (e) {
      guideError.value = UI.guideLoadError(e.message || e);
      scriptListState.value = 'error';
      resultListState.value = 'error';
    } finally {
      loading.value = false;
      refreshLucide();
    }
  }

  async function refresh(opts = {}) {
    // [2026-09-17] [阶段零Vue3组件岛] 刷新前同步外部外壳状态
    syncBridgeState();
    const silent = !!opts.silent;
    const asDiskCheck = !!opts.asDiskCheck;
    const asScriptCheck = !!opts.asScriptCheck;
    const pid = projectId.value;
    if (!pid) return;

    try {
      const data = await api.fetchProject(pid, authToken.value);
      if (!data.success) {
        toast(data.message || '刷新失败', 'error');
        return;
      }
      if (bridge.setProjectData && data.project) {
        bridge.setProjectData(data.project);
      }
      await renderPanel();
      if (bridge.onPipelineGate) bridge.onPipelineGate();

      const hasAnswersSaved = hasBaseline(projectData.value.probe_status);
      const hasQuestionList = !!(
        activeScript.value && (activeScript.value.items || []).length
      );

      if (asDiskCheck) {
        const sync = syncExpectedResultUI(guide.value, projectData.value, true);
        if (sync.kind === 'today_ready') {
          toast('落盘成功：今天的目标文件已在磁盘上', 'success');
        } else if (sync.kind === 'history_only') {
          toast(
            `今日文件未写；历史摸底结果仍在（${sync.histName || '已有 JSON'}）`,
            'warning',
          );
        } else {
          toast('还没有豆包结果文件：请先让反重力问完并写文件', 'error');
        }
      } else if (asScriptCheck) {
        if (hasQuestionList) {
          toast(
            `要问豆包的问题清单已就绪（${activeScript.value.items.length} 题）`,
            'success',
          );
        } else {
          toast('还没有要问豆包的问题清单。请先做第 1 步让 Cursor 写题并保存。', 'error');
        }
      } else if (!silent) {
        const q = hasQuestionList
          ? `要问豆包的问题清单已就绪（${activeScript.value.items.length} 题）`
          : '还没有要问豆包的问题清单';
        const a = hasAnswersSaved ? UI.answersSaved : UI.answersNotSaved;
        toast(`${q}；${a}`, hasQuestionList || hasAnswersSaved ? 'success' : 'error');
      }
      refreshLucide();
    } catch {
      toast('重新检查进度失败', 'error');
    }
  }

  async function selectScriptFile(filename) {
    const name = String(filename || '').trim();
    if (!name) return;
    selectedScriptFile.value = name;
    const meta = scripts.value.find((s) => s && s.file === name) || null;
    // 选中时不要把整份列表打成 loading（否则列表会闪没）；只更新题目预览
    try {
      await loadScriptContent(name, meta, { toast: true });
      if (scriptListState.value !== 'loaded' && scripts.value.length) {
        scriptListState.value = 'loaded';
      }
    } catch {
      scriptListState.value = 'error';
    }
    refreshLucide();
  }

  async function deleteScriptFile(filename) {
    const name = String(filename || '').trim();
    if (!name) return;
    if (
      !window.confirm(
        `确定删除这份问题清单？\n\n${name}\n\n删了就找不回来（只删这一份文件）。`,
      )
    ) {
      return;
    }
    try {
      const data = await api.deleteOutputFile(projectId.value, name, authToken.value);
      if (!data.success) {
        toast(data.message || '删除失败', 'error');
        return;
      }
      if (selectedScriptFile.value === name) selectedScriptFile.value = '';
      if (activeScript.value && activeScript.value.file === name) activeScript.value = null;
      toast(`已删除 ${name}`, 'success');
      await refresh({ asScriptCheck: true });
    } catch {
      toast('删除失败', 'error');
    }
  }

  async function selectResultFile(filename) {
    selectedResultFile.value = filename || '';
    diskPreviewReady.value = false;
    previewData.value = null;
    pendingProbe.value = null;
    if (selectedResultFile.value) {
      await previewFromDisk({ silent: true }).catch(() => {});
    }
  }

  async function copyQualityPrompt() {
    try {
      await fetchGuide();
    } catch {
      /* fallback to projectData */
    }
    const st = resolveProbeStatus(guide.value, projectData.value);
    const mode = st === 'baseline_ready' || st === 'awaiting_retest' ? '复测' : '首轮';
    const text = qualityPromptText(projectId.value, st, projectData.value);
    await copyText(text, `已复制：高质量出题提示词（${mode} · probe_status=${st}）`);
  }

  async function generateScript(btnState) {
    if (!projectId.value) return;
    generatingScript.value = true;
    try {
      const data = await api.generateScript(projectId.value, authToken.value);
      if (!data.success) {
        toast(data.message || '出题失败', 'error');
        return;
      }
      toast(data.message || '已生成必测题');
      await renderPanel();
    } catch {
      toast('出题请求异常', 'error');
    } finally {
      generatingScript.value = false;
      refreshLucide();
    }
  }

  async function previewFromDisk(opts = {}) {
    const silent = !!(opts && opts.silent);
    if (!projectId.value) return;
    if (!selectedResultFile.value) {
      if (!silent) toast('请先在列表中选择一个结果文件', 'error');
      return;
    }
    try {
      const data = await api.previewProbeDisk(
        projectId.value,
        selectedResultFile.value,
        authToken.value,
      );
      if (!data.success) {
        if (!silent) toast(data.message || '预览失败', 'error');
        return;
      }
      diskPreviewReady.value = true;
      previewData.value = data.preview || {};
      previewCopyText.value = buildPreviewCopyText(previewData.value, projectId.value);
      if (!silent) toast(`已预览 ${selectedResultFile.value}`);
    } catch {
      if (!silent) toast('预览请求异常', 'error');
    }
  }

  async function applyFromDisk() {
    if (!projectId.value) return;
    if (!selectedResultFile.value) {
      toast('请先选择结果文件', 'error');
      return;
    }
    if (!diskPreviewReady.value) {
      toast('请先预览再确认回填', 'error');
      return;
    }
    try {
      const data = await api.applyProbeDisk(
        projectId.value,
        {
          file: selectedResultFile.value,
          merge: merge.value,
          write_topics: writeTopics.value,
        },
        authToken.value,
      );
      if (!data.success) {
        toast(data.message || '回填失败', 'error');
        return;
      }
      if (bridge.setProjectData && data.project) {
        bridge.setProjectData(data.project);
      }
      const rej = data.rejected_short || [];
      let msg = data.message || `确认已写入 ${selectedResultFile.value}`;
      if (rej.length) msg += `（拒收短词 ${rej.length}）`;
      toast(msg, rej.length ? 'error' : 'success');
      diskPreviewReady.value = false;
      previewData.value = null;
      await renderPanel();
      if (bridge.onPipelineGate) bridge.onPipelineGate();
    } catch {
      toast('回填请求异常', 'error');
    }
  }

  async function readProbeFile(fileInput) {
    const file = fileInput && fileInput.files && fileInput.files[0];
    if (!file) {
      toast('请先选择 probe JSON 文件', 'error');
      return null;
    }
    const fname = String(file.name || '');
    if (/^probe_script/i.test(fname)) {
      toast('选错了：这是「要问的题」文件。请选 competitor_probe_*.json（豆包答完的结果）', 'error');
      return null;
    }
    if (!/^competitor_probe/i.test(fname) && !/probe/i.test(fname)) {
      toast('请选择 competitor_probe_*.json（第二步落盘结果）', 'error');
      return null;
    }
    const text = await file.text();
    try {
      const data = JSON.parse(text);
      if (!data || typeof data !== 'object' || !Array.isArray(data.items)) {
        toast('文件需为含 items[] 的 probe JSON', 'error');
        return null;
      }
      return data;
    } catch {
      toast('JSON 解析失败，请检查文件', 'error');
      return null;
    }
  }

  async function previewUpload(fileInput) {
    if (!projectId.value) return;
    const probe = await readProbeFile(fileInput);
    if (!probe) return;
    try {
      const data = await api.previewProbeUpload(projectId.value, probe, authToken.value);
      if (!data.success) {
        toast(data.message || '预览失败', 'error');
        return;
      }
      pendingProbe.value = probe;
      previewData.value = data.preview || {};
      previewCopyText.value = buildPreviewCopyText(previewData.value, projectId.value);
      diskPreviewReady.value = true;
      toast('预览已生成，确认无误后再回填');
    } catch {
      toast('预览请求异常', 'error');
    }
  }

  async function applyUpload(fileInput) {
    if (!projectId.value) return;
    const probe = pendingProbe.value || (await readProbeFile(fileInput));
    if (!probe) return;
    const tip = merge.value
      ? '会把豆包结果合并进项目（选题/竞品）。确认存进项目？'
      : '会用这份豆包结果盖掉项目里现有选题/竞品。若已有精修好的内容，请改用合并。仍要覆盖？';
    if (!window.confirm(tip)) return;
    try {
      const data = await api.applyProbeUpload(
        projectId.value,
        { probe, merge: merge.value, only_real: true },
        authToken.value,
      );
      if (!data.success) {
        toast(data.message || '回填失败', 'error');
        return;
      }
      if (bridge.setProjectData && data.project) {
        bridge.setProjectData(data.project);
      }
      pendingProbe.value = null;
      diskPreviewReady.value = false;
      previewData.value = null;
      await renderPanel();
      if (bridge.onPipelineGate) bridge.onPipelineGate();
      const fname = fileInput && fileInput.files && fileInput.files[0];
      const name = fname ? fname.name : '侦察结果';
      toast(`确认已写入 ${name}`, 'success');
      refreshLucide();
    } catch {
      toast('回填请求异常', 'error');
    }
  }

  async function checkResultOnDisk() {
    checkingDisk.value = true;
    try {
      await refresh({ asDiskCheck: true });
    } finally {
      checkingDisk.value = false;
      refreshLucide();
    }
  }

  async function copyText(text, toastMsg) {
    if (!text) return;
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.left = '-9999px';
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
      }
      toast(toastMsg || '已复制');
    } catch {
      toast('复制失败', 'error');
    }
  }

  async function copyCmd(text) {
    await copyText(text, '已复制命令');
  }

  async function copyAntigravityPrompt() {
    const text = antigravityPromptText(projectId.value, activeScript.value);
    await copyText(text, '已复制①怎么问 → 贴反重力后，务必再 @ 问题清单文件');
  }

  async function copyAntigravitySavePrompt() {
    const text = antigravitySavePromptText(
      projectId.value,
      activeScript.value,
      guide.value,
      geoRepoRoot.value,
    );
    await copyText(text, '已复制②收工说明书 → 再贴同一反重力对话，等它写完文件');
  }

  async function copyCursorPrompt() {
    await copyText(cursorPrompt.value, '已复制：给 Cursor 执行该命令');
  }

  async function copyPreviewForIde() {
    if (!previewCopyText.value) {
      toast('还没有可复制的预览，先选文件并刷新预览', 'error');
      return;
    }
    await copyText(previewCopyText.value, '已复制侦察摘要 → 可直接贴给 IDE');
  }

  function goStep1() {
    if (bridge.onGoStep1) bridge.onGoStep1();
  }

  return {
    guide,
    loading,
    guideError,
    scriptListState,
    resultListState,
    selectedScriptFile,
    activeScript,
    selectedResultFile,
    diskPreviewReady,
    previewData,
    previewCopyText,
    merge,
    writeTopics,
    checkingDisk,
    generatingScript,
    esc,
    projectId,
    projectData,
    probeStatus,
    isRetest,
    modeBanner,
    step1BlurbText,
    copyPromptLabel,
    baselineMetaText,
    scriptHintText,
    cdCmdText,
    scriptCmdText,
    cursorPrompt,
    scripts,
    results,
    expectedResult,
    uploadExpected,
    scriptPathRel,
    scriptPathAbs,
    scriptKindText,
    qlistBadge,
    writeStatusBadge,
    cmdPreview,
    cmdApply,
    renderPanel,
    refresh,
    selectScriptFile,
    deleteScriptFile,
    selectResultFile,
    copyQualityPrompt,
    generateScript,
    previewFromDisk,
    applyFromDisk,
    previewUpload,
    applyUpload,
    checkResultOnDisk,
    copyCmd,
    copyAntigravityPrompt,
    copyAntigravitySavePrompt,
    copyCursorPrompt,
    copyPreviewForIde,
    goStep1,
    refreshLucide,
    qualityPromptText: () =>
      qualityPromptText(
        projectId.value,
        resolveProbeStatus(guide.value, projectData.value),
        projectData.value,
      ),
    antigravityPromptText: () => antigravityPromptText(projectId.value, activeScript.value),
    antigravitySavePromptText: () =>
      antigravitySavePromptText(
        projectId.value,
        activeScript.value,
        guide.value,
        geoRepoRoot.value,
      ),
  };
}
