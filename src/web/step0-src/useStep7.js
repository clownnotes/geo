// [2026-09-30] [00~07 全流水线顺延] 阶段七状态驱动与本地持久化 Hook
import { ref, computed, watch, onMounted } from 'vue';
import {
  STAGE_7_META,
  S11_CHECKLIST_TEMPLATE,
  getPresetProbeQuestions,
  resolveContext,
} from './stage7Config.js';

export function useStep7(bridgeOrData = {}) {
  const currentStep = ref(3); // 阶段六默认全亮
  const isHeaderCollapsed = ref(false);
  const mckinseyVisible = ref(false);
  const toastMessage = ref('');
  const toastVisible = ref(false);

  // 项目基础上下文 (解决 🟡6: 兼容 bridge.projectData 与直接传入的 projectData)
  const pData = bridgeOrData?.projectData || bridgeOrData || {};
  const projectContext = ref(resolveContext(pData));

  // 1. 七项验收资产清单状态
  const checklist = ref(
    S11_CHECKLIST_TEMPLATE.map((item) => ({
      ...item,
      passed: true,
      currentCount: item.minRequired,
      assetName: item.defaultAssetDesc,
      statusLabel: '达标通过',
    }))
  );

  // 2. 首轮核心 3 问抽测状态
  const probeQuestions = ref(getPresetProbeQuestions(projectContext.value));
  const activeQuestionId = ref('q1-identity');

  const activeQuestion = computed(() => {
    return probeQuestions.value.find((q) => q.id === activeQuestionId.value) || probeQuestions.value[0];
  });

  // 3. 验收结案签署表单
  const signoffForm = ref({
    clientSigner: '客户负责人',
    vendorSigner: '邻里GEO 交付负责人',
    signDate: projectContext.value.today,
    comments: '七项工程资产已核验交接，核心三问真机改口抽测达标，同意首期结项，后续进入日常运营维护期。',
    isSigned: false,
  });

  const notes = ref('');

  // LocalStorage 缓存 Key
  const STORAGE_KEY_STEP6 = `geo_step6_state_${projectContext.value.clientId}`;

  // 弹出轻量 Toast
  function showToast(msg) {
    toastMessage.value = msg;
    toastVisible.value = true;
    setTimeout(() => {
      toastVisible.value = false;
    }, 2400);
  }

  // 读取与恢复本地持久化数据
  function restoreState() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY_STEP6);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed.probeQuestions && parsed.probeQuestions.length) {
          probeQuestions.value = parsed.probeQuestions;
        }
        if (parsed.signoffForm) {
          signoffForm.value = { ...signoffForm.value, ...parsed.signoffForm };
        }
        if (parsed.notes) {
          notes.value = parsed.notes;
        }
      }
    } catch (e) {
      console.warn('[useStep6] 恢复缓存异常:', e);
    }
  }

  // 保存本地持久化数据
  function persistState() {
    try {
      const payload = {
        probeQuestions: probeQuestions.value,
        signoffForm: signoffForm.value,
        notes: notes.value,
        updatedAt: new Date().toISOString(),
      };
      localStorage.setItem(STORAGE_KEY_STEP6, JSON.stringify(payload));
    } catch (e) {
      console.warn('[useStep6] 保存缓存异常:', e);
    }
  }

  // 切换中栏选中的问句
  function handleSelectQuestion(qid) {
    activeQuestionId.value = qid;
  }

  // 复制问句到剪贴板去大模型提问
  function handleCopyQuestion(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(() => {
        showToast('问句已复制，请前往各大模型提问并取回答案');
      }).catch(() => {
        showToast('复制失败，请手动选择复制');
      });
    } else {
      showToast('当前环境不支持快捷剪贴板，请手动选中文本');
    }
  }

  // 更新真机回答
  function handleUpdateActualAnswer(qid, val) {
    const target = probeQuestions.value.find((q) => q.id === qid);
    if (target) {
      target.defaultActual = val;
      // 简单智能规则：如果包含品牌名或核心词，自动标记为已纠偏
      if (val && (val.includes(projectContext.value.brand) || val.includes(projectContext.value.company))) {
        target.corrected = true;
      }
      persistState();
    }
  }

  // 切换单题改口判定
  function handleToggleCorrected(qid) {
    const target = probeQuestions.value.find((q) => q.id === qid);
    if (target) {
      target.corrected = !target.corrected;
      persistState();
      showToast(target.corrected ? '已标记为：改口达标' : '已取消达标标记');
    }
  }

  // 保存结案签字
  function handleSaveSignoff() {
    signoffForm.value.isSigned = true;
    persistState();
    showToast('结项验收签署信息已保存！');
  }

  // 重置结项签署状态
  function handleResetSignoff() {
    signoffForm.value.isSigned = false;
    persistState();
    showToast('已重置为待签署状态');
  }

  // 调起浏览器原生打印（导出纸质签字凭单或另存为 PDF）
  function handlePrintSignoff() {
    window.print();
  }

  // 导出交付资产清册 Markdown 文件
  function handleExportChecklistMarkdown() {
    const ctx = projectContext.value;
    const lines = [
      `# 《${ctx.brand}》GEO 项目首次交付工程资产移交清册`,
      ``,
      `> 交付主体：${ctx.company} | 官方主站：${ctx.site} | 交付日期：${ctx.today}`,
      `> 验收依据：老赵哥 SOP S11 验收归档规范 | 判定标准：换人能接手`,
      ``,
      `---`,
      ``,
      `## 一、S11.1 七项工程交付物清单`,
      ``,
      `| 序号 | 交付项 | 对应阶段 | 合格标准 | 交付数量 | 验收判定 |`,
      `|:---:|:---|:---|:---|:---:|:---:|`,
    ];

    checklist.value.forEach((item) => {
      lines.push(
        `| ${item.no} | ${item.name} | ${item.stageName} | ${item.standard} | ${item.currentCount} | 达标通过 |`
      );
    });

    lines.push(``);
    lines.push(`---`);
    lines.push(``);
    lines.push(`## 二、首轮核心 3 问改口抽测实录`);
    lines.push(``);

    probeQuestions.value.forEach((q) => {
      lines.push(`### 问题 ${q.questionNumber}：${q.question}（${q.shortTitle}）`);
      lines.push(`- **测试大模型**：${q.targetBot}`);
      lines.push(`- **S0 摸底错误回答**：${q.baselineError}`);
      lines.push(`- **标准预期口径**：${q.standardAnswer}`);
      lines.push(`- **当前实测回答**：${q.defaultActual || '（未回填）'}`);
      lines.push(`- **改口判定结果**：${q.corrected ? '【合格已纠偏】' : '【待继续优化】'}`);
      lines.push(``);
    });

    lines.push(`---`);
    lines.push(``);
    lines.push(`## 三、双方结项交接签署凭据`);
    lines.push(`- **交付团队**：${signoffForm.value.vendorSigner}`);
    lines.push(`- **客户代表**：${signoffForm.value.clientSigner}`);
    lines.push(`- **签署日期**：${signoffForm.value.signDate}`);
    lines.push(`- **验收评语**：${signoffForm.value.comments}`);
    lines.push(``);
    lines.push(`（本清单经双方签署后生效，随源码与线上知识库一同交接归档）`);

    const blob = new Blob([lines.join('\n')], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${ctx.brand}_GEO首次交付资产移交清册_${ctx.today.replace(/\//g, '-')}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showToast('已导出《首次交付资产移交清册.md》');
  }

  // 保存备注
  function handleSaveNotes() {
    persistState();
    showToast('阶段备注已保存');
  }

  // 统计完成度
  const allProbePassed = computed(() => {
    return probeQuestions.value.every((q) => q.corrected);
  });

  const passedChecklistCount = computed(() => {
    return checklist.value.filter((i) => i.passed).length;
  });

  onMounted(() => {
    restoreState();
  });

  return {
    STAGE_6_META,
    currentStep,
    isHeaderCollapsed,
    mckinseyVisible,
    toastMessage,
    toastVisible,
    projectContext,
    checklist,
    passedChecklistCount,
    probeQuestions,
    activeQuestionId,
    activeQuestion,
    allProbePassed,
    signoffForm,
    notes,
    handleSelectQuestion,
    handleCopyQuestion,
    handleUpdateActualAnswer,
    handleToggleCorrected,
    handleSaveSignoff,
    handleResetSignoff,
    handlePrintSignoff,
    handleExportChecklistMarkdown,
    handleSaveNotes,
  };
}

export const useStep6 = useStep7;

