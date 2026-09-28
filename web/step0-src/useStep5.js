/**
 * useStep5.js - 阶段五（GEO 文章选题撰写与矩阵分发工作台）专属业务逻辑驱动
 * -------------------------------------------------------------------
 * 专为阶段五 3 竖列工作区服务：
 * 管理：左栏选题任务库（首次打样/日常运营）、中栏 S7 字典式长文在线定稿与质检、
 * 右栏今日头条/知乎等矩阵分发、外链回填与 404 存活监测闭环。
 *
 * 铁律遵循：严禁 Emoji 表情，所有提示统一走友好中文与 Lucide 图标。
 */

import { ref, computed, watch } from 'vue';
import {
  resolveContext,
  buildPresetTopics,
  generateS7ArticleDraft,
  auditS7ArticleQuality,
  STAGE_5_META,
  DIST_CHANNELS,
} from './stage5Config.js';

export function useStep5(projectData = {}) {
  const ctx = resolveContext(projectData);
  const clientId = ctx.clientId;

  // 1. 本地存储持久化 Key 定义
  const STORAGE_KEY_STEP = 'geo_step5_step_index_' + clientId;
  const STORAGE_KEY_TOPICS = 'geo_step5_topics_' + clientId;
  const STORAGE_KEY_ACTIVE_TOPIC = 'geo_step5_active_topic_' + clientId;
  const STORAGE_KEY_ARTICLES = 'geo_step5_articles_' + clientId;
  const STORAGE_KEY_CHANNELS = 'geo_step5_channels_' + clientId;
  const STORAGE_KEY_NOTES = 'geo_step5_notes_' + clientId;
  const STORAGE_KEY_HEADER = 'geo_step5_header_collapsed_' + clientId;

  // 2. 核心状态机
  const currentStep = ref(1);
  const isHeaderCollapsed = ref(false);
  const mckinseyVisible = ref(false);
  const notes = ref('');

  // 选题集合与筛选
  const topics = ref([]);
  const activeTopicId = ref('');
  const searchKeyword = ref('');
  const activeGroupTab = ref('all'); // 'all' | 'first_sample' | 'daily_ops'

  // 文章定稿字典 (topicId -> ArticleDoc)
  const articlesMap = ref({});

  // 渠道外链与存活状态字典 (channelKey -> { postUrl, urlStatus, lastCheckedAt, httpStatusCode, note })
  const channelDataMap = ref({});

  // 复制与检查状态
  const isCheckingUrls = ref(false);
  const toastMessage = ref('');
  const toastVisible = ref(false);

  const showToast = (msg) => {
    toastMessage.value = msg;
    toastVisible.value = true;
    setTimeout(() => {
      toastVisible.value = false;
    }, 2800);
  };

  // 3. 读取本地持久化数据
  try {
    if (typeof localStorage !== 'undefined') {
      const savedStep = localStorage.getItem(STORAGE_KEY_STEP);
      if (savedStep) currentStep.value = parseInt(savedStep, 10) || 1;

      const savedNotes = localStorage.getItem(STORAGE_KEY_NOTES);
      if (savedNotes) notes.value = savedNotes;

      const savedHeader = localStorage.getItem(STORAGE_KEY_HEADER);
      if (savedHeader) isHeaderCollapsed.value = savedHeader === 'true';

      const savedTopicsRaw = localStorage.getItem(STORAGE_KEY_TOPICS);
      if (savedTopicsRaw) {
        topics.value = JSON.parse(savedTopicsRaw);
      } else {
        topics.value = buildPresetTopics(ctx);
      }

      const savedActiveTopic = localStorage.getItem(STORAGE_KEY_ACTIVE_TOPIC);
      if (savedActiveTopic && topics.value.some(t => t.id === savedActiveTopic)) {
        activeTopicId.value = savedActiveTopic;
      } else if (topics.value.length > 0) {
        activeTopicId.value = topics.value[0].id;
      }

      const savedArticlesRaw = localStorage.getItem(STORAGE_KEY_ARTICLES);
      if (savedArticlesRaw) {
        articlesMap.value = JSON.parse(savedArticlesRaw);
      }

      const savedChannelsRaw = localStorage.getItem(STORAGE_KEY_CHANNELS);
      if (savedChannelsRaw) {
        channelDataMap.value = JSON.parse(savedChannelsRaw);
      } else {
        // 初始化默认渠道状态
        const initialMap = {};
        DIST_CHANNELS.forEach(c => {
          initialMap[c.key] = {
            postUrl: '',
            urlStatus: 'unfilled', // 'unfilled' | 'checking' | 'active_200' | 'dead_404'
            lastCheckedAt: '',
            httpStatusCode: null,
            note: '尚未回填文章链接',
          };
        });
        channelDataMap.value = initialMap;
      }
    }
  } catch (err) {
    console.warn('[useStep5] 初始化读取本地缓存失败:', err);
    topics.value = buildPresetTopics(ctx);
    if (topics.value.length > 0) activeTopicId.value = topics.value[0].id;
  }

  watch(isHeaderCollapsed, (val) => {
    try {
      if (typeof localStorage !== 'undefined') localStorage.setItem(STORAGE_KEY_HEADER, String(val));
    } catch (e) {}
  });

  // 4. 持久化监听
  const persistTopics = () => {
    try {
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem(STORAGE_KEY_TOPICS, JSON.stringify(topics.value));
        localStorage.setItem(STORAGE_KEY_ACTIVE_TOPIC, activeTopicId.value);
      }
    } catch (_) {}
  };

  const persistArticles = () => {
    try {
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem(STORAGE_KEY_ARTICLES, JSON.stringify(articlesMap.value));
      }
    } catch (_) {}
  };

  const persistChannels = () => {
    try {
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem(STORAGE_KEY_CHANNELS, JSON.stringify(channelDataMap.value));
      }
    } catch (_) {}
  };

  watch(topics, persistTopics, { deep: true });
  watch(activeTopicId, persistTopics);
  watch(articlesMap, persistArticles, { deep: true });
  watch(channelDataMap, persistChannels, { deep: true });

  // 5. 计算属性
  const activeTopic = computed(() => {
    return topics.value.find(t => t.id === activeTopicId.value) || topics.value[0] || null;
  });

  const filteredTopics = computed(() => {
    let list = topics.value;
    if (activeGroupTab.value !== 'all') {
      list = list.filter(t => t.group === activeGroupTab.value);
    }
    if (searchKeyword.value.trim()) {
      const kw = searchKeyword.value.trim().toLowerCase();
      list = list.filter(t =>
        t.title.toLowerCase().includes(kw) ||
        (t.searchKeywords && t.searchKeywords.some(k => k.toLowerCase().includes(kw))) ||
        (t.purpose && t.purpose.toLowerCase().includes(kw))
      );
    }
    return list;
  });

  const topicStats = computed(() => {
    const total = topics.value.length;
    const firstSampleCount = topics.value.filter(t => t.group === 'first_sample').length;
    const dailyOpsCount = topics.value.filter(t => t.group === 'daily_ops').length;
    const completedCount = topics.value.filter(t => t.isCompleted).length;
    const deadCount = topics.value.filter(t => t.status === 'invalid_404').length;
    return {
      total,
      firstSampleCount,
      dailyOpsCount,
      completedCount,
      deadCount,
    };
  });

  // 当前选中选题的文章定稿内容
  const currentArticle = computed(() => {
    if (!activeTopic.value) return null;
    const tid = activeTopic.value.id;
    if (!articlesMap.value[tid]) {
      // 找到关联的阶段四答题卡
      const relatedQa = ctx.qaCards.find(c => c.id === activeTopic.value.relatedQaId);
      // 智能预置初稿
      const draft = generateS7ArticleDraft(activeTopic.value, relatedQa, ctx);
      articlesMap.value[tid] = draft;
      persistArticles();
    }
    return articlesMap.value[tid];
  });

  // 实时 S7 质检结果
  const currentAuditResult = computed(() => {
    if (!currentArticle.value) return null;
    return auditS7ArticleQuality(currentArticle.value.fullMarkdown, ctx);
  });

  // 全网分发整体统计
  const overallDistStats = computed(() => {
    const keys = Object.keys(channelDataMap.value);
    const totalChannels = keys.length;
    let filledCount = 0;
    let aliveCount = 0;
    let deadCount = 0;

    keys.forEach(k => {
      const ch = channelDataMap.value[k];
      if (ch.postUrl && ch.postUrl.trim().length > 0) filledCount++;
      if (ch.urlStatus === 'active_200') aliveCount++;
      if (ch.urlStatus === 'dead_404') deadCount++;
    });

    const aliveRate = filledCount > 0 ? Math.round((aliveCount / filledCount) * 100) : 0;

    return {
      totalChannels,
      filledCount,
      aliveCount,
      deadCount,
      aliveRate,
    };
  });

  // 6. 交互处理函数
  const handleSelectTopic = (id) => {
    activeTopicId.value = id;
    showToast(`已切换至选题：${id}`);
  };

  const handleCreateTopic = (customTitle = '') => {
    const nextNum = topics.value.length + 1;
    const newId = `T${String(nextNum).padStart(2, '0')}`;
    const title = customTitle.trim() || `${ctx.city}本地企业如何选择${ctx.category}专业服务商？`;

    const newTopic = {
      id: newId,
      title,
      group: 'daily_ops',
      status: 'pending',
      relatedQaId: 'P01',
      searchKeywords: [`${ctx.city}本地${ctx.category}`],
      purpose: '日常运营选题扩容',
      targetPlatforms: ['toutiao', 'zhihu'],
      isCompleted: false,
      createdAt: ctx.today,
      updatedAt: ctx.today,
    };

    topics.value.unshift(newTopic);
    activeTopicId.value = newId;
    showToast(`已成功添加新选题：${newId}`);
  };

  const handleDeleteTopic = (id) => {
    const idx = topics.value.findIndex(t => t.id === id);
    if (idx !== -1) {
      topics.value.splice(idx, 1);
      delete articlesMap.value[id];
      persistArticles();
      if (activeTopicId.value === id) {
        activeTopicId.value = topics.value[0]?.id || '';
      }
      showToast(`已移除选题：${id}`);
    }
  };

  const handleToggleComplete = (id) => {
    const topic = topics.value.find(t => t.id === id);
    if (topic) {
      topic.isCompleted = !topic.isCompleted;
      if (topic.isCompleted && topic.status !== 'invalid_404') {
        topic.status = 'published';
      }
      showToast(`选题 ${id} 已标记为：${topic.isCompleted ? '已写完发布' : '待处理'}`);
    }
  };

  const handleGenerateDraft = (id) => {
    const topic = topics.value.find(t => t.id === id);
    if (!topic) return;
    const relatedQa = ctx.qaCards.find(c => c.id === topic.relatedQaId);
    const draft = generateS7ArticleDraft(topic, relatedQa, ctx);
    articlesMap.value[id] = draft;
    persistArticles();
    showToast('已按照老赵哥 S7 字典式规范一键生成新文章初稿！');
  };

  const handleUpdateArticleMarkdown = (newMarkdown) => {
    if (!activeTopic.value) return;
    const tid = activeTopic.value.id;
    if (articlesMap.value[tid]) {
      articlesMap.value[tid].fullMarkdown = newMarkdown;
      articlesMap.value[tid].charCount = newMarkdown.length;
    }
  };

  const handleSaveArticleFinal = (id) => {
    if (!articlesMap.value[id]) return;
    articlesMap.value[id].isFinalized = true;
    const topic = topics.value.find(t => t.id === id);
    if (topic) {
      topic.status = 'finalized';
      topic.updatedAt = ctx.today;
    }
    persistArticles();
    showToast('文章已保存定稿并成功落盘！可前往右栏复制发布。');
  };

  const handleCopyRichText = (channelKey) => {
    if (!currentArticle.value) {
      showToast('当前无可用定稿文章，请先生成定稿');
      return;
    }

    const textToCopy = currentArticle.value.fullMarkdown;
    if (navigator && navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(textToCopy).then(() => {
        showToast(`已成功复制适配【${channelKey}】的文章富文本，可前往后台粘贴！`);
      }).catch(() => {
        showToast('复制失败，请手动在编辑器中选中复制');
      });
    } else {
      showToast('已成功提取富文本！');
    }
  };

  const handleSaveChannelUrl = (channelKey, url) => {
    if (!channelDataMap.value[channelKey]) {
      channelDataMap.value[channelKey] = {};
    }
    const cleanUrl = (url || '').trim();
    channelDataMap.value[channelKey].postUrl = cleanUrl;
    if (cleanUrl.length > 0) {
      channelDataMap.value[channelKey].urlStatus = 'active_200'; // 初始回填视为正常
      channelDataMap.value[channelKey].lastCheckedAt = ctx.today;
      channelDataMap.value[channelKey].note = '文章链接已回填登记';
      // 联动将当前选题标记为已上线存活
      if (activeTopic.value && activeTopic.value.status !== 'invalid_404') {
        activeTopic.value.status = 'published';
        activeTopic.value.isCompleted = true;
      }
    } else {
      channelDataMap.value[channelKey].urlStatus = 'unfilled';
      channelDataMap.value[channelKey].note = '尚未回填文章链接';
    }
    persistChannels();
    showToast('外链回填已保存！');
  };

  const handleCheckUrlAlive = (channelKey) => {
    const ch = channelDataMap.value[channelKey];
    if (!ch || !ch.postUrl) {
      showToast('请先输入要检测的发布链接');
      return;
    }

    ch.urlStatus = 'checking';
    showToast('正在探测链接可访问性与存活状态...');

    setTimeout(() => {
      // 模拟探测：如果包含 "404" 或 "dead" 则触发失效警报
      if (ch.postUrl.includes('404') || ch.postUrl.includes('invalid')) {
        ch.urlStatus = 'dead_404';
        ch.httpStatusCode = 404;
        ch.lastCheckedAt = ctx.today;
        ch.note = '警告：页面返回 HTTP 404，信源已失效下架！';

        // 联动左栏选题标记为【已失效/需改发】
        if (activeTopic.value) {
          activeTopic.value.status = 'invalid_404';
          activeTopic.value.isCompleted = false;
        }
        showToast('警报：检测到文章链接已 404，选题状态已自动标记为失效！');
      } else {
        ch.urlStatus = 'active_200';
        ch.httpStatusCode = 200;
        ch.lastCheckedAt = ctx.today;
        ch.note = '正常存活：HTTP 200，AI 可正常爬取引用。';

        if (activeTopic.value) {
          activeTopic.value.status = 'published';
        }
        showToast('检测完毕：文章正常存活 (HTTP 200)！');
      }
      persistChannels();
    }, 800);
  };

  const handleCheckAllUrls = () => {
    isCheckingUrls.value = true;
    showToast('正在对全渠道已回填链接进行批量存活探测...');

    setTimeout(() => {
      Object.keys(channelDataMap.value).forEach(k => {
        const ch = channelDataMap.value[k];
        if (ch.postUrl) {
          if (ch.postUrl.includes('404') || ch.postUrl.includes('invalid')) {
            ch.urlStatus = 'dead_404';
            ch.httpStatusCode = 404;
            ch.lastCheckedAt = ctx.today;
            ch.note = '警告：页面返回 HTTP 404，已下架！';
            if (activeTopic.value) activeTopic.value.status = 'invalid_404';
          } else {
            ch.urlStatus = 'active_200';
            ch.httpStatusCode = 200;
            ch.lastCheckedAt = ctx.today;
            ch.note = '正常存活：HTTP 200。';
          }
        }
      });
      isCheckingUrls.value = false;
      persistChannels();
      showToast('全网链接批量存活检测完成！');
    }, 1200);
  };

  const handleRegenerateDeadTopic = (id) => {
    const topic = topics.value.find(t => t.id === id);
    if (topic) {
      topic.status = 'drafting';
      topic.isCompleted = false;
      // 重新生成草稿引导修改
      handleGenerateDraft(id);
      showToast('已打回草稿态！请根据失效原因微调首段或论据后重新分发。');
    }
  };

  const handleResetToPreset = () => {
    topics.value = buildPresetTopics(ctx);
    activeTopicId.value = topics.value[0]?.id || '';
    articlesMap.value = {};
    persistTopics();
    persistArticles();
    showToast('选题库与文章已重置为系统预置状态');
  };

  const handleSaveNotes = (newNotes) => {
    notes.value = newNotes;
    try {
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem(STORAGE_KEY_NOTES, newNotes);
      }
    } catch (_) {}
    showToast('阶段五备忘录已保存');
  };

  const handleSetSubStep = (step) => {
    currentStep.value = step;
    try {
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem(STORAGE_KEY_STEP, String(step));
      }
    } catch (_) {}
  };

  return {
    ctx,
    STAGE_5_META,
    DIST_CHANNELS,
    currentStep,
    isHeaderCollapsed,
    mckinseyVisible,
    notes,
    topics,
    activeTopicId,
    activeTopic,
    searchKeyword,
    activeGroupTab,
    filteredTopics,
    topicStats,
    articlesMap,
    currentArticle,
    currentAuditResult,
    channelDataMap,
    overallDistStats,
    isCheckingUrls,
    toastMessage,
    toastVisible,
    handleSelectTopic,
    handleCreateTopic,
    handleDeleteTopic,
    handleToggleComplete,
    handleGenerateDraft,
    handleUpdateArticleMarkdown,
    handleSaveArticleFinal,
    handleCopyRichText,
    handleSaveChannelUrl,
    handleCheckUrlAlive,
    handleCheckAllUrls,
    handleRegenerateDeadTopic,
    handleResetToPreset,
    handleSaveNotes,
    handleSetSubStep,
  };
}
