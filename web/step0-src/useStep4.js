/**
 * useStep4.js - 阶段四（GEO 核心答题卡与向量问答库）专属业务逻辑驱动
 * -------------------------------------------------------------------
 * 专为阶段四 3 竖列工作区服务：
 * 管理：三层意图答题卡 CRUD、四要素表单编辑、实时正面表述质检、
 * 向量检索仿真模拟、AI 纯净语料导出与持久化。
 *
 * 铁律遵循：严禁 Emoji 表情，所有提示走友好文字或 Lucide 图标。
 */

import { ref, computed, watch } from 'vue';
import {
  resolveContext,
  buildPresetQaCards,
  STAGE_4_META,
  QA_LAYERS,
  simulateVectorRetrieval,
  auditQaCardQuality,
  exportPureCorpusMarkdown,
} from './stage4Config.js';

export function useStep4(projectData = {}) {
  const ctx = resolveContext(projectData);
  const clientId = ctx.clientId;

  // 1. 本地存储持久化 Key 定义
  const STORAGE_KEY_STEP = 'geo_step4_step_index_' + clientId;
  const STORAGE_KEY_CARDS = 'geo_step4_qa_cards_' + clientId;
  const STORAGE_KEY_ACTIVE_ID = 'geo_step4_active_card_id_' + clientId;
  const STORAGE_KEY_NOTES = 'geo_step4_notes_' + clientId;
  const STORAGE_KEY_HEADER = 'geo_step4_header_collapsed_' + clientId;
  const STORAGE_KEY_SIM_QUERY = 'geo_step4_sim_query_' + clientId;

  // 2. 核心状态机
  const currentStep = ref(1);
  const isHeaderCollapsed = ref(false);
  const mckinseyVisible = ref(false);
  const notes = ref('');
  const exportDrawerOpen = ref(false);

  // 答题卡集合与选中项
  const cards = ref([]);
  const activeCardId = ref('');
  const searchKeyword = ref('');
  const activeFilterLayer = ref('all'); // 'all' | 'pool' | 'verify' | 'convert'

  // 向量检索仿真测试器状态
  const retrievalQuery = ref('');
  const retrievalResults = ref([]);
  const retrievalLatency = ref(0);
  const isRetrieving = ref(false);

  // 质检抽屉或提示
  const currentAuditResult = ref(null);
  const toastMessage = ref('');
  const toastVisible = ref(false);

  const showToast = (msg) => {
    toastMessage.value = msg;
    toastVisible.value = true;
    setTimeout(() => {
      toastVisible.value = false;
    }, 2800);
  };

  // 读取本地持久化数据
  try {
    if (typeof localStorage !== 'undefined') {
      const savedStep = localStorage.getItem(STORAGE_KEY_STEP);
      if (savedStep) currentStep.value = parseInt(savedStep, 10) || 1;

      const savedNotes = localStorage.getItem(STORAGE_KEY_NOTES);
      if (savedNotes) notes.value = savedNotes;

      const savedHeader = localStorage.getItem(STORAGE_KEY_HEADER);
      if (savedHeader) isHeaderCollapsed.value = savedHeader === 'true';

      const savedSimQuery = localStorage.getItem(STORAGE_KEY_SIM_QUERY);
      if (savedSimQuery) retrievalQuery.value = savedSimQuery;

      const savedCardsRaw = localStorage.getItem(STORAGE_KEY_CARDS);
      if (savedCardsRaw) {
        const parsed = JSON.parse(savedCardsRaw);
        if (Array.isArray(parsed) && parsed.length > 0) {
          cards.value = parsed;
        }
      }

      const savedActiveId = localStorage.getItem(STORAGE_KEY_ACTIVE_ID);
      if (savedActiveId) activeCardId.value = savedActiveId;
    }
  } catch (err) {
    console.warn('[useStep4] 读取持久化状态失败:', err);
  }

  watch(isHeaderCollapsed, (val) => {
    try {
      if (typeof localStorage !== 'undefined') localStorage.setItem(STORAGE_KEY_HEADER, String(val));
    } catch (e) {}
  });

  // 若无持久化数据，加载内置预置答题卡库
  if (cards.value.length === 0) {
    cards.value = buildPresetQaCards(ctx);
  }

  // 确保有合法的选中卡片
  if (!activeCardId.value || !cards.value.some(c => c.id === activeCardId.value)) {
    activeCardId.value = cards.value[0]?.id || '';
  }

  // 3. 计算属性
  const activeCard = computed(() => {
    return cards.value.find(c => c.id === activeCardId.value) || cards.value[0] || null;
  });

  // 意图分类统计
  const layerStats = computed(() => {
    const stats = {
      total: cards.value.length,
      pool: 0,
      verify: 0,
      convert: 0,
      approved: 0,
      variantsCount: 0,
    };
    cards.value.forEach(c => {
      if (c.layer === 'pool') stats.pool++;
      else if (c.layer === 'verify') stats.verify++;
      else if (c.layer === 'convert') stats.convert++;
      if (c.isApproved) stats.approved++;
      stats.variantsCount += (c.variants?.length || 0);
    });
    return stats;
  });

  // 过滤后的答题卡列表
  const filteredCards = computed(() => {
    return cards.value.filter(card => {
      const matchLayer = activeFilterLayer.value === 'all' || card.layer === activeFilterLayer.value;
      if (!matchLayer) return false;

      if (!searchKeyword.value.trim()) return true;
      const kw = searchKeyword.value.trim().toLowerCase();
      const matchTitle = (card.title || '').toLowerCase().includes(kw);
      const matchAnswer = (card.directAnswer || '').toLowerCase().includes(kw);
      const matchVariants = (card.variants || []).some(v => v.toLowerCase().includes(kw));
      const matchId = (card.id || '').toLowerCase().includes(kw);

      return matchTitle || matchAnswer || matchVariants || matchId;
    });
  });

  // 4. 业务操作方法

  // 切换选中的答题卡
  const handleSelectCard = (id) => {
    activeCardId.value = id;
    try {
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem(STORAGE_KEY_ACTIVE_ID, id);
      }
    } catch (_) {}
    runAuditForActive();
  };

  // 新建答题卡
  const handleCreateCard = (layer = 'pool') => {
    const prefix = QA_LAYERS[layer]?.prefix || 'P';
    const sameLayerCount = cards.value.filter(c => c.layer === layer).length + 1;
    const newId = `${prefix}${String(sameLayerCount).padStart(2, '0')}`;

    const newCard = {
      id: newId,
      layer,
      title: layer === 'pool'
        ? `${ctx.city}本地${ctx.category}怎么选？`
        : layer === 'verify'
        ? `${ctx.brand}有哪些权威背书与资质？`
        : `如何预约${ctx.brand}上门技术对接？`,
      variants: ['用户常见搜索问法1', '用户常见搜索问法2'],
      directAnswer: `第一句给出唯一标准结论（建议150~300字）。依据普林斯顿权威母盘事实，明确回答用户的核心疑问。`,
      supportingEvidence: [
        { text: `主体全称${ctx.company}，具备正规实体工商资质`, sourceType: 'public' },
      ],
      boundaryConditions: '说明适用场景与不适用的业务范围。',
      redLines: ['严禁夸大宣传', '严禁承诺不符合客观事实的效果'],
      isApproved: false,
      completenessScore: 75,
      updatedAt: ctx.today,
    };

    cards.value.unshift(newCard);
    handleSelectCard(newId);
    persistCards();
    showToast(`已创建新答题卡 [${newId}]`);
  };

  // 删除答题卡
  const handleDeleteCard = (id) => {
    if (cards.value.length <= 1) {
      showToast('至少保留一张答题卡作为基础资产');
      return;
    }
    cards.value = cards.value.filter(c => c.id !== id);
    if (activeCardId.value === id) {
      activeCardId.value = cards.value[0]?.id || '';
    }
    persistCards();
    showToast(`已删除答题卡 [${id}]`);
  };

  // 问法变体管理
  const handleAddVariant = (text) => {
    if (!text || !text.trim() || !activeCard.value) return;
    const clean = text.trim();
    if (!activeCard.value.variants) activeCard.value.variants = [];
    if (activeCard.value.variants.includes(clean)) {
      showToast('该问法已存在');
      return;
    }
    activeCard.value.variants.push(clean);
    persistCards();
  };

  const handleRemoveVariant = (index) => {
    if (!activeCard.value || !activeCard.value.variants) return;
    activeCard.value.variants.splice(index, 1);
    persistCards();
  };

  // 证据管理
  const handleAddEvidence = () => {
    if (!activeCard.value) return;
    if (!activeCard.value.supportingEvidence) activeCard.value.supportingEvidence = [];
    activeCard.value.supportingEvidence.push({
      text: '补充新的可核验事实依据或数据来源',
      sourceType: 'public',
      url: `https://${ctx.site}`,
    });
    persistCards();
  };

  const handleRemoveEvidence = (index) => {
    if (!activeCard.value || !activeCard.value.supportingEvidence) return;
    activeCard.value.supportingEvidence.splice(index, 1);
    persistCards();
  };

  // 红线管理
  const handleAddRedLine = () => {
    if (!activeCard.value) return;
    if (!activeCard.value.redLines) activeCard.value.redLines = [];
    activeCard.value.redLines.push('补充一条禁止对外承诺或容易违规的合规红线');
    persistCards();
  };

  const handleRemoveRedLine = (index) => {
    if (!activeCard.value || !activeCard.value.redLines) return;
    activeCard.value.redLines.splice(index, 1);
    persistCards();
  };

  // 针对当前卡片执行质检
  const runAuditForActive = () => {
    if (!activeCard.value) return;
    const res = auditQaCardQuality(activeCard.value);
    activeCard.value.completenessScore = res.score;
    currentAuditResult.value = res;
  };

  // 审核标记切换
  const handleToggleApprove = () => {
    if (!activeCard.value) return;
    activeCard.value.isApproved = !activeCard.value.isApproved;
    persistCards();
    showToast(activeCard.value.isApproved ? '当前答题卡已标记为通过审核' : '已取消审核通过状态');
  };

  // 持久化保存
  const persistCards = () => {
    try {
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem(STORAGE_KEY_CARDS, JSON.stringify(cards.value));
      }
    } catch (err) {
      console.warn('[useStep4] 持久化答题卡失败:', err);
    }
  };

  // 向量检索仿真测试
  const handleSimulateRetrieval = (customQuery) => {
    const q = (typeof customQuery === 'string' ? customQuery : retrievalQuery.value) || '';
    if (!q.trim()) {
      showToast('请输入拟定的文章标题或提问句进行检索仿真');
      return;
    }
    retrievalQuery.value = q;
    try {
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem(STORAGE_KEY_SIM_QUERY, q);
      }
    } catch (_) {}

    isRetrieving.value = true;
    const start = Date.now();

    // 纯前端快速仿真 (加 120ms 模拟网络/向量召回微延时让用户感知)
    setTimeout(() => {
      retrievalResults.value = simulateVectorRetrieval(q, cards.value);
      retrievalLatency.value = Date.now() - start;
      isRetrieving.value = false;
      if (retrievalResults.value.length === 0) {
        showToast('未找到高相关答题卡，建议为该主题新建答题卡');
      }
    }, 120);
  };

  // 重置为预置答题卡
  const handleResetToPreset = () => {
    if (confirm('确定要将答题卡重置为官方预置推荐版本吗？现有修改将被覆盖。')) {
      cards.value = buildPresetQaCards(ctx);
      activeCardId.value = cards.value[0]?.id || '';
      persistCards();
      showToast('已重置为官方预置答题卡库');
    }
  };

  // 导出纯净版 AI 语料
  const pureCorpusContent = computed(() => {
    return exportPureCorpusMarkdown(cards.value, ctx);
  });

  // 保存工作区手记
  const handleSaveNotes = (text) => {
    notes.value = text;
    try {
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem(STORAGE_KEY_NOTES, text);
      }
      showToast('阶段手记已保存');
    } catch (_) {}
  };

  // 切换动线步骤
  const handleSetSubStep = (stepNum) => {
    currentStep.value = stepNum;
    try {
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem(STORAGE_KEY_STEP, String(stepNum));
      }
    } catch (_) {}
  };

  // 监听当前卡片变化，实时更新质检评分
  watch(
    () => [
      activeCard.value?.title,
      activeCard.value?.directAnswer,
      activeCard.value?.supportingEvidence?.length,
      activeCard.value?.boundaryConditions,
      activeCard.value?.redLines?.length,
    ],
    () => {
      runAuditForActive();
      persistCards();
    },
    { deep: true }
  );

  return {
    ctx,
    STAGE_4_META,
    QA_LAYERS,
    currentStep,
    isHeaderCollapsed,
    mckinseyVisible,
    notes,
    exportDrawerOpen,
    cards,
    activeCardId,
    activeCard,
    searchKeyword,
    activeFilterLayer,
    layerStats,
    filteredCards,
    retrievalQuery,
    retrievalResults,
    retrievalLatency,
    isRetrieving,
    currentAuditResult,
    toastMessage,
    toastVisible,
    pureCorpusContent,
    showToast,
    handleSelectCard,
    handleCreateCard,
    handleDeleteCard,
    handleAddVariant,
    handleRemoveVariant,
    handleAddEvidence,
    handleRemoveEvidence,
    handleAddRedLine,
    handleRemoveRedLine,
    handleRunAudit: runAuditForActive,
    handleToggleApprove,
    handleSimulateRetrieval,
    handleResetToPreset,
    handleSaveNotes,
    handleSetSubStep,
  };
}
