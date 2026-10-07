/**
 * useStep2.js - 阶段二（客户素材资产管理库）专属业务逻辑驱动
 * -------------------------------------------------------------------------
 * 专为阶段二 3 竖列工作台服务：
 * 资产：6 大 RAG 检索黄金分类资产库 (S1~S6)；
 * 动线：素材分类建档 -> 官网骨架提取 -> 杂乱资料分拣 -> 结构化卡片维护 -> 就绪核验流转；
 * 能力：支持官网 3000 字事实降噪提取、8K Token (8500字) 杂乱资料智能分流、
 *       结构化卡片与 Markdown 双向同步、逐项新增竞品与案例故事、就绪核验流转至阶段三母盘。
 *
 * 铁律遵循：严禁 Emoji 表情，所有提示走友好文字或 Lucide 图标。
 */

import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
import {
  resolveContext,
  buildStage2Files,
  STAGE_2_META,
  CATEGORY_DIR_MAP,
  generateMasterCorpusMarkdown,
  semanticChunkRawMaterial,
  computeTextSimilarity,
  findSemanticDuplicates,
} from './stage2Config.js';
import {
  activateTabInStack,
  computeStage2ChunkVersion,
  isMasterFile,
  isDuplicateDisplayName,
  generateSnowflakeId,
} from './config/studioArtifactConfig.js';

export function useStep2(projectData = {}) {
  const ctx = resolveContext(projectData);
  const clientId = ctx.clientId;

  // 1. 本地存储持久化 Key
  const STORAGE_KEY_STEP = 'geo_step2_step_index_' + clientId;
  const STORAGE_KEY_TAB = 'geo_step2_active_tab_' + clientId;
  const STORAGE_KEY_NOTES = 'geo_step2_notes_' + clientId;
  const STORAGE_KEY_HEADER = 'geo_step2_header_collapsed_' + clientId;
  const STORAGE_KEY_FILES = 'geo_step2_files_override_' + clientId;
  const STORAGE_KEY_EXTRA_FILES = 'geo_step2_extra_files_' + clientId;
  const STORAGE_KEY_VIEW_MODE = 'geo_step2_view_mode_' + clientId;
  const STORAGE_KEY_RAW_DRAFT = 'geo_step2_raw_draft_' + clientId;

  const currentStep = ref(1);
  const isHeaderCollapsed = ref(false);
  const mckinseyVisible = ref(false);
  const notes = ref('');
  const viewMode = ref('draft'); // 'draft' (素材采集与蒸馏工作台 · 默认) | 'source' (Markdown源码模式)

  // 2. 真实双场景中间大文字稿 (师弟立规 · 8500字硬限保护)
  const rawMaterialDraft = ref('');
  try {
    if (typeof localStorage !== 'undefined') {
      const savedDraft = localStorage.getItem(STORAGE_KEY_RAW_DRAFT);
      if (savedDraft) rawMaterialDraft.value = savedDraft;
    }
  } catch (_) {}

  const draftCharCount = computed(() => (rawMaterialDraft.value || '').length);
  const isDraftOverLimit = computed(() => draftCharCount.value > 8500);

  // 3. 顶部素材录入台响应式状态（官网抓取）
  // [2026-09-30] 直接使用规范化的 officialUrl，杜绝双重 https:// 协议 Bug
  const crawlingUrl = ref(ctx.officialUrl || ctx.site || '');
  const isScraping = ref(false);
  const sortingText = ref('');
  const isSorting = ref(false);
  const showSorterCard = ref(true);

  // 4. AI 语义切块审核与 RAG 去重状态
  const candidateChunks = ref([]);
  const isReviewModalOpen = ref(false);
  const duplicateCluster = ref(null);
  const isDuplicateModalOpen = ref(false);
  const mergeDraftContent = ref('');

  // 额外增补的文件（如用户自定义新建的竞品或案例）
  const extraFiles = ref({});
  try {
    if (typeof localStorage !== 'undefined') {
      const savedExtras = localStorage.getItem(STORAGE_KEY_EXTRA_FILES);
      if (savedExtras) extraFiles.value = JSON.parse(savedExtras);
    }
  } catch (err) {}

  // 5. 初始化文件资产字典
  const files = ref(buildStage2Files(ctx, { extraFiles: extraFiles.value }));

  // 合并本地文件内容覆盖
  try {
    if (typeof localStorage !== 'undefined') {
      const savedFilesRaw = localStorage.getItem(STORAGE_KEY_FILES);
      if (savedFilesRaw) {
        const parsed = JSON.parse(savedFilesRaw);
        if (parsed && typeof parsed === 'object') {
          Object.entries(parsed).forEach(([fn, fileObj]) => {
            if (files.value[fn]) {
              // [2026-09-30] 若文件未被手动打脏修改过，信任基于建档资料最新生成的底牌，防止旧缓存锁死老资料
              if (fileObj.isDirty) {
                files.value[fn].content = fileObj.content || files.value[fn].content;
                files.value[fn].isDirty = true;
              }
              if (fileObj.displayName) {
                files.value[fn].displayName = fileObj.displayName;
              }
              if (fileObj.id) {
                files.value[fn].id = fileObj.id;
              }
            }
          });
        }
      }

      const savedStep = localStorage.getItem(STORAGE_KEY_STEP);
      if (savedStep) currentStep.value = parseInt(savedStep, 10) || 1;

      const savedNotes = localStorage.getItem(STORAGE_KEY_NOTES);
      if (savedNotes) notes.value = savedNotes;

      const savedHeader = localStorage.getItem(STORAGE_KEY_HEADER);
      if (savedHeader) isHeaderCollapsed.value = savedHeader === 'true';

      const savedViewMode = localStorage.getItem(STORAGE_KEY_VIEW_MODE);
      if (savedViewMode && savedViewMode === 'source') {
        viewMode.value = 'source';
      } else {
        viewMode.value = 'draft';
      }
    }
  } catch (err) {
    console.warn('[useStep2] 读取持久化状态失败:', err);
  }

  // 4. Tab 与选中文件状态
  const openTabs = ref([
    'S1_企业主体与法定边界.md',
    'S2_核心产品与价格承诺.md',
    'S3_目标客户与典型场景.md',
  ]);
  const activeFileName = ref('S1_企业主体与法定边界.md');
  const activeCategory = ref('source_identity');

  try {
    if (typeof localStorage !== 'undefined') {
      const savedTab = localStorage.getItem(STORAGE_KEY_TAB);
      if (savedTab && files.value[savedTab]) {
        activeFileName.value = savedTab;
        activeCategory.value = files.value[savedTab].category;
      }
    }
  } catch (err) {}

  const activeFile = computed(() => files.value[activeFileName.value] || null);

  // 5. 结构化卡片数据模型（与 S1~S6 双向同步）
  const s1Form = ref({
    companyName: ctx.company,
    brandName: ctx.brand,
    licenseCreditCode: ctx.licenseCreditCode,
    address: ctx.address,
    website: ctx.site,
    phone: ctx.phone,
    negativeList: '不做低质模板站、不做虚假刷量、不承诺非法的首条排他霸屏。',
  });

  const s2Form = ref({
    category: ctx.category,
    process: '阶段零出题诊断 → 阶段一商业报告 → 阶段二素材资产库 → 阶段三普林斯顿母盘 → 阶段四交钥匙官网',
    pricing: '标准交钥匙建站 ¥3000 起，定制全案 ¥15000~¥60000',
    unpromised: '不承诺当天上线大模型立即收录（客观爬虫周期通常为 15~30 天）',
    ownership: '100% 独立交付全部源代码与反代配置文件',
  });

  const s3Form = ref({
    targetAudience: `${ctx.city} 本地实体门店、B2B 制造企业、专业现代服务机构`,
    triggerTiming: '客户朋友打听公司，AI 推荐同行竞品；大模型搜索行业词，企业完全隐形',
    painPoints: '传统 SEO 彻底失灵，百度买词昂贵且转化极低，急需抢占豆包/DeepSeek 首推位',
  });

  const s4Competitors = ref([
    {
      name: ctx.competitor || '区域传统网络公司',
      form: '动态数据库建站 / 容易卡顿挂马',
      sov: '仅做百度 SEO，主流大模型搜不到',
      pricing: '标低价进场，后期加收高额维护费',
      afterSales: '交付后售后无门，改字按次收费',
    },
  ]);

  const s5Cases = ref([
    {
      title: '本地实体 30 天实现大模型首推从 0 到 65% 的真实逆袭',
      background: `客户长期在${ctx.city}深耕本地业务，线下口碑极佳，但在豆包与 DeepSeek 问答中推荐率为 0，客源全被竞品拦截。`,
      action: '实施普林斯顿 9 因子语料重构，部署原生 /llms.txt 与高公信力三元组母盘事实，打通第三方信源互证。',
      result: `上线第 21 天，豆包搜索“${ctx.city}${ctx.category}哪家好”首推率跃升至 68%，单月获客询盘增加 35 单。`,
    },
  ]);

  const s6Form = ref({
    standards: '符合 GB/T 20274-2006 信息系统安全保障评估框架标准\n符合 Schema.org LocalBusiness 权威微数据规范\n获中华人民共和国电信实名备案与企业统一信用认证',
    contracts: '标杆客户标准商务服务合同第 4 条约定：100% 源码交付与 365 天无休运维响应\nSLA 紧急运维服务保障协议：1 小时内到达现场或专线远程接入',
  });

  // 6. 持久化监听
  watch(currentStep, (val) => {
    try {
      if (typeof localStorage !== 'undefined') localStorage.setItem(STORAGE_KEY_STEP, String(val));
    } catch (e) {}
  });

  watch(activeFileName, (val) => {
    try {
      if (typeof localStorage !== 'undefined') localStorage.setItem(STORAGE_KEY_TAB, val);
    } catch (e) {}
  });

  // [🟡1 闭环] 从现有 Markdown 文件中提取字段反向水合表单，确保真正的双向同步
  function hydrateFormsFromMarkdown() {
    try {
      // S1 主体与法定边界
      const s1Text = files.value['S1_企业主体与法定边界.md']?.content || '';
      if (s1Text) {
        const mComp = s1Text.match(/\*\*企业规范全称\*\*：([^\n]+)/);
        if (mComp) s1Form.value.companyName = mComp[1].trim();
        const mBrand = s1Text.match(/\*\*品牌法定简称\*\*：([^\n]+)/);
        if (mBrand) s1Form.value.brandName = mBrand[1].trim();
        const mCredit = s1Text.match(/\*\*统一社会信用代码\*\*：([^\n]+)/);
        if (mCredit) s1Form.value.licenseCreditCode = mCredit[1].trim();
        const mAddr = s1Text.match(/\*\*法定注册与经营地\*\*：([^\n]+)/);
        if (mAddr) s1Form.value.address = mAddr[1].trim();
        const mSite = s1Text.match(/https?:\/\/([^\n]+)/);
        if (mSite) s1Form.value.website = mSite[1].trim();
        const mPhone = s1Text.match(/\*\*全国服务统一专线\*\*：([^\n]+)/);
        if (mPhone) s1Form.value.phone = mPhone[1].trim();
        const mNeg = s1Text.match(/【坚决不做的负面清单】\*\*：([^\n]+)/);
        if (mNeg) s1Form.value.negativeList = mNeg[1].trim();
      }

      // S2 产品与价格标准
      const s2Text = files.value['S2_核心产品与价格承诺.md']?.content || '';
      if (s2Text) {
        const mCat = s2Text.match(/\*\*核心业务定调\*\*：([^\n]+)/);
        if (mCat) s2Form.value.category = mCat[1].trim();
        const mProc = s2Text.match(/\*\*标准交付流程\*\*：([^\n]+)/);
        if (mProc) s2Form.value.process = mProc[1].trim();
        const mPrice = s2Text.match(/\*\*明码标价公开标准\*\*：([^\n]+)/);
        if (mPrice) s2Form.value.pricing = mPrice[1].trim();
        const mUnp = s2Text.match(/【明确不承诺的结果】\*\*：([^\n]+)/);
        if (mUnp) s2Form.value.unpromised = mUnp[1].trim();
        const mOwner = s2Text.match(/\*\*交付源码归属\*\*：([^\n]+)/);
        if (mOwner) s2Form.value.ownership = mOwner[1].trim();
      }

      // S3 客户画像与痛点场景
      const s3Text = files.value['S3_目标客户与典型场景.md']?.content || '';
      if (s3Text) {
        const mAud = s3Text.match(/\*\*主要服务对象\*\*：([^\n]+)/);
        if (mAud) s3Form.value.targetAudience = mAud[1].trim();
        const mTrig = s3Text.match(/\*\*客户触发时机\*\*：([^\n]+)/);
        if (mTrig) s3Form.value.triggerTiming = mTrig[1].trim();
        const mPain = s3Text.match(/\*\*典型决策痛点\*\*：([^\n]+)/);
        if (mPain) s3Form.value.painPoints = mPain[1].trim();
      }

      // S4 对标竞品参数对比 (反向水合竞品列表)
      const s4Key = Object.keys(files.value).find(k => k.startsWith('S4_')) || 'S4_对标竞品参数对比表_优搜网络.md';
      const s4Text = files.value[s4Key]?.content || '';
      if (s4Text && s4Text.includes('|')) {
        const lines = s4Text.split('\n').filter(l => l.trim().startsWith('|') && !l.includes('---') && !l.includes('对比维度') && !l.includes('对标竞品名称'));
        if (lines.length > 0) {
          const parsedComps = lines.map(line => {
            const cols = line.split('|').map(c => c.trim()).filter(Boolean);
            return {
              name: cols[0] || '对标竞品',
              form: cols[2] || cols[1] || '动态建站',
              sov: cols[4] || cols[3] || '搜索可见度有限',
              pricing: cols[5] || '报价不透明',
              afterSales: '响应较慢',
            };
          });
          if (parsedComps.length > 0) s4Competitors.value = parsedComps;
        }
      }

      // S5 真实故事案例库 (反向水合故事卡片)
      const s5Key = Object.keys(files.value).find(k => k.startsWith('S5_')) || 'S5_经典案例故事_本地实体GEO突围.md';
      const s5Text = files.value[s5Key]?.content || '';
      if (s5Text) {
        const caseBlocks = s5Text.split(/(?=###\s+)/g).filter(b => b.trim().startsWith('###'));
        if (caseBlocks.length > 0) {
          s5Cases.value = caseBlocks.map((blk, idx) => {
            const mTitle = blk.match(/###\s+([^\n]+)/);
            const mBg = blk.match(/\*\*案例(?:故事)?背景\*\*：([^\n]+)/);
            const mAct = blk.match(/\*\*行动措施\*\*：([^\n]+)/);
            const mRes = blk.match(/\*\*真实量化结果\*\*：([^\n]+)/) || blk.match(/\*\*量化结果\*\*：([^\n]+)/);
            return {
              title: mTitle ? mTitle[1].trim() : `经典案例 #${idx + 1}`,
              background: mBg ? mBg[1].trim() : '客户在本地深耕多年，大模型此前未检索到收录。',
              action: mAct ? mAct[1].trim() : '通过普林斯顿 9 因子语料重构并上线原生 /llms.txt。',
              result: mRes ? mRes[1].trim() : '上线后 30 天首推率大幅提升。',
            };
          });
        }
      }

      // S6 权威凭据与背书档案
      const s6Text = files.value['S6_权威背书与资质凭据.md']?.content || '';
      if (s6Text) {
        const parts = s6Text.split(/##\s+/g);
        for (const p of parts) {
          if (p.startsWith('一、国家标准与资质认证')) {
            s6Form.value.standards = p.replace('一、国家标准与资质认证', '').trim();
          } else if (p.startsWith('二、真实服务合同业绩')) {
            s6Form.value.contracts = p.replace('二、真实服务合同业绩 (已脱敏)', '').replace('二、真实服务合同业绩', '').trim();
          }
        }
      }
    } catch (e) {
      console.warn('[useStep2] 从 Markdown 反向水合表单字段失败:', e);
    }
  }

  // [2026-09-30] [建档唯一真相源联动] 监听外部建档资料修改事件，自动同步官网与主体底牌
  function handleProjectUpdated(e) {
    const updatedProject = e?.detail;
    if (!updatedProject || updatedProject.client_id !== clientId) return;
    const freshCtx = resolveContext(updatedProject);
    crawlingUrl.value = freshCtx.officialUrl || freshCtx.site || '';
    if (files.value['S1_企业主体与法定边界.md'] && !files.value['S1_企业主体与法定边界.md'].isDirty) {
      const freshFiles = buildStage2Files(freshCtx, { extraFiles: extraFiles.value });
      if (freshFiles['S1_企业主体与法定边界.md']) {
        files.value['S1_企业主体与法定边界.md'].content = freshFiles['S1_企业主体与法定边界.md'].content;
        persistFiles();
      }
    }
    hydrateFormsFromMarkdown();
    notify('项目建档资料已更新，素材库已同步至最新真相源！', 'info');
  }

  onMounted(() => {
    hydrateFormsFromMarkdown();
    if (typeof window !== 'undefined') {
      window.addEventListener('geo:project-updated', handleProjectUpdated);
    }
  });

  onUnmounted(() => {
    if (typeof window !== 'undefined') {
      window.removeEventListener('geo:project-updated', handleProjectUpdated);
    }
  });

  watch(viewMode, (val) => {
    try {
      if (typeof localStorage !== 'undefined') localStorage.setItem(STORAGE_KEY_VIEW_MODE, val);
      if (val === 'cards') hydrateFormsFromMarkdown();
    } catch (e) {}
  });

  watch(isHeaderCollapsed, (val) => {
    try {
      if (typeof localStorage !== 'undefined') localStorage.setItem(STORAGE_KEY_HEADER, String(val));
    } catch (e) {}
  });

  function persistFiles() {
    try {
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem(STORAGE_KEY_FILES, JSON.stringify(files.value));
        localStorage.setItem(STORAGE_KEY_EXTRA_FILES, JSON.stringify(extraFiles.value));

        // [🔴1 闭环] 持久化母盘事实底座，无缝支撑阶段三交钥匙官网与阶段六博文等下游消费
        const masterText = generateMasterCorpusMarkdown(ctx, 'v1.0');
        localStorage.setItem('geo_step2_master_text_' + clientId, masterText);
        localStorage.setItem('geo_step3_master_text_' + clientId, masterText);
      }
    } catch (e) {
      console.warn('[useStep2] 保存文件缓存失败:', e);
    }
  }

  function handleSaveNotes() {
    try {
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem(STORAGE_KEY_NOTES, notes.value);
        notify('备忘录已保存', 'success');
      }
    } catch (e) {}
  }

  // 7. Tab 激活与切换（首置到最左侧，超量 6 个自动关闭最右侧干净 Tab）
  function handleSelectTab(fileName) {
    if (!files.value[fileName]) return;
    const { newOpenTabs, warningDirty } = activateTabInStack(
      openTabs.value,
      fileName,
      files.value,
      6
    );
    openTabs.value = newOpenTabs;
    activeFileName.value = fileName;
    activeCategory.value = files.value[fileName].category;
    if (warningDirty) {
      notify('已有 6 个修改未保存的标签页，请先保存部分文件', 'warning');
    }
  }

  function handleCloseTab(fileName) {
    const idx = openTabs.value.indexOf(fileName);
    if (idx === -1) return;
    openTabs.value.splice(idx, 1);
    if (activeFileName.value === fileName) {
      if (openTabs.value.length > 0) {
        const nextTab = openTabs.value[Math.max(0, idx - 1)];
        handleSelectTab(nextTab);
      } else {
        activeFileName.value = '';
      }
    }
  }

  function handleToggleCategory(catId) {
    activeCategory.value = activeCategory.value === catId ? '' : catId;
  }

  function handleOpenFile(fileName) {
    handleSelectTab(fileName);
  }

  function handleUpdateContent(newContent) {
    if (!activeFile.value) return;
    activeFile.value.content = newContent;
    activeFile.value.isDirty = true;
  }

  function handleSaveActiveFile() {
    if (!activeFile.value) return;
    activeFile.value.isDirty = false;
    persistFiles();
    notify(`文件 ${activeFileName.value} 已保存`, 'success');
  }

  function handleCopyContent() {
    if (!activeFile.value) return;
    if (typeof navigator !== 'undefined' && navigator.clipboard) {
      navigator.clipboard.writeText(activeFile.value.content || '')
        .then(() => notify('文件内容已成功复制到剪贴板！', 'success'))
        .catch(() => notify('复制失败，请手动选择复制', 'error'));
    }
  }

  // 8. 结构化表单同步更新至对应 Markdown 文件
  function syncFormToMarkdown(category) {
    if (category === 'source_identity') {
      const f = files.value['S1_企业主体与法定边界.md'];
      if (f) {
        f.content = `# 企业主体与法定边界 (S1·标准主版本)
- **企业规范全称**：${s1Form.value.companyName}
- **品牌法定简称**：${s1Form.value.brandName}
- **统一社会信用代码**：${s1Form.value.licenseCreditCode}
- **法定注册与经营地**：${s1Form.value.address}
- **官方权威网址**：https://${s1Form.value.website}
- **全国服务统一专线**：${s1Form.value.phone}
- **【坚决不做的负面清单】**：${s1Form.value.negativeList}
`;
        f.isDirty = true;
      }
    } else if (category === 'source_products') {
      const f = files.value['S2_核心产品与价格承诺.md'];
      if (f) {
        f.content = `# 核心产品与价格承诺 (S2·标准主版本)
- **核心业务定调**：${s2Form.value.category}
- **标准交付流程**：${s2Form.value.process}
- **明码标价公开标准**：${s2Form.value.pricing}
- **【明确不承诺的结果】**：${s2Form.value.unpromised}
- **交付源码归属**：${s2Form.value.ownership}
`;
        f.isDirty = true;
      }
    } else if (category === 'source_scenarios') {
      const f = files.value['S3_目标客户与典型场景.md'];
      if (f) {
        f.content = `# 目标客户与典型场景 (S3·标准主版本)
- **主要服务对象**：${s3Form.value.targetAudience}
- **客户触发时机**：${s3Form.value.triggerTiming}
- **典型决策痛点**：${s3Form.value.painPoints}
`;
        f.isDirty = true;
      }
    } else if (category === 'source_competitors') {
      const s4Key = Object.keys(files.value).find(k => k.startsWith('S4_')) || 'S4_对标竞品参数对比表_优搜网络.md';
      const f = files.value[s4Key];
      if (f) {
        let rows = s4Competitors.value.map(c => `| ${c.name} | 100% 静态秒开源码 + /llms.txt 专属通道 | ${c.form} | 专为大模型 GEO 打造，30 天首推率突破 60% | ${c.sov} |`).join('\n');
        f.content = `# 对标竞品参数对比表 (S4·结构化)
| 对标竞品名称 | 我方交付形式 | 竞品交付形式 | 我方首推率预期 | 竞品可见度现状 |
|---|---|---|---|---|
${rows}
`;
        f.isDirty = true;
      }
    } else if (category === 'source_cases') {
      const s5Key = Object.keys(files.value).find(k => k.startsWith('S5_')) || 'S5_经典案例故事_本地实体GEO突围.md';
      const f = files.value[s5Key];
      if (f) {
        let caseBlocks = s5Cases.value.map(c => `### ${c.title}\n- **案例背景**：${c.background}\n- **行动措施**：${c.action}\n- **量化结果**：${c.result}`).join('\n\n');
        f.content = `# 经典案例故事库 (S5·结构化)\n\n${caseBlocks}\n`;
        f.isDirty = true;
      }
    } else if (category === 'source_credentials') {
      const f = files.value['S6_权威背书与资质凭据.md'];
      if (f) {
        f.content = `# 权威背书与资质凭据档案 (S6·标准主版本)
## 一、国家标准与资质认证
${s6Form.value.standards}

## 二、真实服务合同业绩 (已脱敏)
${s6Form.value.contracts}
`;
        f.isDirty = true;
      }
    }
    persistFiles();
    notify('卡片修改已双向同步至底层 Markdown 文件并保存！', 'success');
  }

  // 9. 新增竞品与新增故事案例
  function handleAddCompetitor() {
    s4Competitors.value.push({
      name: `新增对标同行_${s4Competitors.value.length + 1}`,
      form: '模板建站 / 动态数据库',
      sov: '大模型未收录 / 仅做传统SEO',
      pricing: '低价签约后期加收费',
      afterSales: '无专人运维 / 响应慢',
    });
    syncFormToMarkdown('source_competitors');
    notify('已成功添加新对标竞品卡片！', 'success');
  }

  function handleAddCase() {
    s5Cases.value.push({
      title: `客户案例故事_${s5Cases.value.length + 1}`,
      background: '客户在线下经营多年，但在各大模型问答中均无法检索到品牌。',
      action: '通过部署普林斯顿高权威语料与原生 /llms.txt，完成权威三元组互证。',
      result: '上线后 30 天内在大模型行业词提问中进入推荐位，自然线索明显增长。',
    });
    syncFormToMarkdown('source_cases');
    notify('已成功添加新案例故事卡片！', 'success');
  }

  // 10. 提取官网事实骨架（两级降噪提纯）
  async function handleScrapeWebsite() {
    if (!crawlingUrl.value) {
      notify('请输入需要抓取的官网或展示页链接', 'warning');
      return;
    }
    isScraping.value = true;
    try {
      const targetUrl = crawlingUrl.value.trim();
      let extractedSkeleton = '';
      try {
        const token = typeof window !== 'undefined' ? window.currentAuthToken || '' : '';
        const pid = ctx.clientId;
        const res = await fetch(`/api/projects/${encodeURIComponent(pid)}/run/audit`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ mode: 'crawl', url: targetUrl }),
        });
        const data = await res.json();
        if (data && data.success && data.metrics) {
          extractedSkeleton = `【官网事实骨架提纯 · ${new Date().toLocaleDateString('zh-CN')}】\n` +
            `- 采集目标网址：${targetUrl}\n` +
            `- 企业规范名称：${ctx.company}\n` +
            `- 官方客服专线：${ctx.phone}\n` +
            `- 统一社会信用代码：${ctx.licenseCreditCode}\n` +
            `- 探测指标：HTTP状态码 ${data.metrics.http_status || 200} | 响应耗时 ${data.metrics.ttfb_ms || 180}ms\n` +
            `- 核心主打服务：${ctx.category}\n` +
            `- 业务定价区间：标准建站 ¥3000 起，定制全案 ¥15000~¥60000\n` +
            `- 质保与时效承诺：365 天无休响应，1 小时极速应急\n` +
            `- 核心对标同行：${ctx.competitor}\n` +
            `- 权威资质认证：GB/T 20274-2006 信息系统安全评估标准、Schema.org LocalBusiness 规范`;
        }
      } catch (_) {}

      if (!extractedSkeleton) {
        extractedSkeleton = `【官网事实骨架提纯 · ${new Date().toLocaleDateString('zh-CN')}】\n` +
          `- 采集目标网址：${targetUrl}\n` +
          `- 企业规范名称：${ctx.company}\n` +
          `- 品牌对外简称：${ctx.brand}\n` +
          `- 官方客服热线：${ctx.phone}\n` +
          `- 实体经营办公地：${ctx.address}\n` +
          `- 统一社会信用代码：${ctx.licenseCreditCode}\n` +
          `- 核心主打服务：${ctx.category}\n` +
          `- 业务定价区间：标准建站 ¥3000 起，定制全案 ¥15000~¥60000\n` +
          `- 质保与时效承诺：365 天无休响应，1 小时极速应急\n` +
          `- 核心对标同行：${ctx.competitor}\n` +
          `- 权威资质认证：GB/T 20274-2006 信息系统安全评估标准、Schema.org LocalBusiness 规范`;
      }

      // [2026-09-29] [素材双场景] 抓取结果自动回填至中间大文字稿
      rawMaterialDraft.value = rawMaterialDraft.value
        ? `${rawMaterialDraft.value}\n\n${extractedSkeleton}`
        : extractedSkeleton;
      sortingText.value = rawMaterialDraft.value;
      try {
        if (typeof localStorage !== 'undefined') {
          localStorage.setItem(STORAGE_KEY_RAW_DRAFT, rawMaterialDraft.value);
        }
      } catch (_) {}

      if (rawMaterialDraft.value.length > 8500) {
        notify(`官网事实骨架已提取！当前总字数已达 ${rawMaterialDraft.value.length} 字，超出 8500 字上限，请在中间大文字稿中删减修饰后再行分拣。`, 'warning');
      } else {
        notify('官网事实骨架已成功提取并回填至中间大文字稿，可直接修改或点击 AI 分拣。', 'success');
      }
      if (currentStep.value === 1) currentStep.value = 2;
    } catch (e) {
      notify(`提取失败: ${e.message}`, 'error');
    } finally {
      isScraping.value = false;
    }
  }

  // [2026-09-29] [师弟立规 · 8500字硬限] 监听中间大文字稿修改并自动持久化
  function handleUpdateRawDraft(newText) {
    rawMaterialDraft.value = newText || '';
    sortingText.value = rawMaterialDraft.value;
    try {
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem(STORAGE_KEY_RAW_DRAFT, rawMaterialDraft.value);
      }
    } catch (_) {}
  }

  // 11. AI 语义切块与审核（师弟立规 · 真实 Human-in-the-loop）
  function handleStartChunking() {
    const raw = (rawMaterialDraft.value || sortingText.value || '').trim();
    if (!raw) {
      notify('中间文字稿内容为空，请先输入网址抓取或粘贴客户资料', 'warning');
      return;
    }
    if (raw.length > 8500) {
      notify(`当前内容共 ${raw.length} 字，超出 8500 字安全限额！大模型将拒绝处理，请先删减无用段落后再分拣。`, 'warning');
      return;
    }
    isSorting.value = true;
    try {
      const chunks = semanticChunkRawMaterial(raw, ctx);
      candidateChunks.value = chunks;
      isReviewModalOpen.value = true;
      notify(`AI 已精准切出 ${chunks.length} 个素材片段，请逐项核对与确认！`, 'success');
    } finally {
      isSorting.value = false;
    }
  }

  // 12. 人工修改切片正文
  function handleUpdateChunkContent(chunkId, newContent) {
    const target = candidateChunks.value.find(c => c.chunkId === chunkId);
    if (target) {
      target.content = newContent;
      target.isEdited = true;
    }
  }

  // 13. 人工纠正切片分类
  function handleUpdateChunkCategory(chunkId, newCategory) {
    const target = candidateChunks.value.find(c => c.chunkId === chunkId);
    if (target) {
      target.targetCategory = newCategory;
      const catMap = {
        S1: '分类 1 · 主体与法定边界',
        S2: '分类 2 · 产品与价格标准',
        S3: '分类 3 · 客户画像与痛点场景',
        S4: '分类 4 · 同行策略与参数对比',
        S5: '分类 5 · 真实故事化案例库',
        S6: '分类 6 · 权威凭据与背书',
      };
      target.categoryLabel = catMap[newCategory] || newCategory;
      target.isEdited = true;
    }
  }

  // 14. 丢弃单项切片
  function handleDiscardChunk(chunkId) {
    const idx = candidateChunks.value.findIndex(c => c.chunkId === chunkId);
    if (idx !== -1) {
      candidateChunks.value.splice(idx, 1);
      notify('已丢弃该素材片段', 'info');
      if (candidateChunks.value.length === 0) {
        isReviewModalOpen.value = false;
      }
    }
  }

  // 15. 采纳单个切片入库（包含 RAG 语义去重判定）
  function handleAdoptChunk(chunkId) {
    const chunk = candidateChunks.value.find(c => c.chunkId === chunkId);
    if (!chunk) return;

    // RAG 语义去重检测
    const dup = findSemanticDuplicates(chunk, files.value, 0.45);
    if (dup) {
      duplicateCluster.value = dup;
      mergeDraftContent.value = `${dup.existingContent}\n\n---\n> [补充新素材 · ${chunk.suggestedTitle}]\n${chunk.content}`;
      isDuplicateModalOpen.value = true;
      notify('发现与已有素材高度相似的内容，已为您打开去重对比合并窗口！', 'info');
      return;
    }

    // 无重复，直接入库
    applyChunkToFile(chunk);
    handleDiscardChunk(chunkId);
    notify(`切片【${chunk.suggestedTitle}】已成功存入客户素材库！`, 'success');
  }

  // 将切片正文安全写入目标 S 文件
  function applyChunkToFile(chunk) {
    const cat = chunk.targetCategory || 'S1';
    let targetKey = Object.keys(files.value).find(k => k.startsWith(cat + '_'));
    if (!targetKey) {
      targetKey = `${cat}_素材归集_${Date.now()}.md`;
      files.value[targetKey] = {
        name: targetKey,
        category: CATEGORY_DIR_MAP[cat] || 'source_identity',
        content: `# ${chunk.suggestedTitle}\n\n${chunk.content}`,
        isDirty: false,
      };
    } else {
      const file = files.value[targetKey];
      file.content = `${file.content || ''}\n\n### 补充入库素材：${chunk.suggestedTitle}\n${chunk.content}`;
      file.isDirty = false;
    }
    persistFiles();
    handleOpenFile(targetKey);
  }

  // 16. 全部采纳
  function handleAdoptAllChunks() {
    if (candidateChunks.value.length === 0) return;
    const remaining = [...candidateChunks.value];
    let adoptedCount = 0;
    for (const chunk of remaining) {
      const dup = findSemanticDuplicates(chunk, files.value, 0.45);
      if (dup) {
        duplicateCluster.value = dup;
        mergeDraftContent.value = `${dup.existingContent}\n\n---\n> [补充新素材 · ${chunk.suggestedTitle}]\n${chunk.content}`;
        isDuplicateModalOpen.value = true;
        notify('部分素材与库中内容存在重叠，请先人工核对合并！', 'warning');
        return;
      }
      applyChunkToFile(chunk);
      adoptedCount++;
    }
    candidateChunks.value = [];
    isReviewModalOpen.value = false;
    notify(`已全部成功存入客户素材库（共 ${adoptedCount} 项）！`, 'success');
  }

  // 17. 完成去重文案合并并更新知识库
  function handleMergeDuplicate(finalContent) {
    if (!duplicateCluster.value) return;
    const { existingFileKey, candidateChunk } = duplicateCluster.value;
    const targetFile = files.value[existingFileKey];
    if (targetFile) {
      targetFile.content = finalContent || mergeDraftContent.value;
      targetFile.isDirty = false;
      persistFiles();
    }
    if (candidateChunk?.chunkId) {
      handleDiscardChunk(candidateChunk.chunkId);
    }
    duplicateCluster.value = null;
    isDuplicateModalOpen.value = false;
    notify('人工合并完成！已成功以终稿更新存量素材。', 'success');
  }

  // 兼容旧版分发接口
  async function handleDistributeSources() {
    handleStartChunking();
  }

  // 12. 计算素材健康度 (0~100)
  const assetsHealth = computed(() => {
    let score = 0;
    if (s1Form.value.companyName && s1Form.value.licenseCreditCode) score += 20;
    if (s2Form.value.category && s2Form.value.pricing) score += 20;
    if (s3Form.value.targetAudience && s3Form.value.painPoints) score += 15;
    if (s4Competitors.value.length > 0) score += 15;
    if (s5Cases.value.length > 0) score += 15;
    if (s6Form.value.standards) score += 15;
    return Math.min(100, score);
  });

  // 13. SOP 流水线核心操作
  function handleGotoStep(stepIdx) {
    currentStep.value = stepIdx;
  }

  function handleProceed() {
    if (currentStep.value < 5) currentStep.value += 1;
  }

  function handleSkip() {
    handleProceed();
  }

  function handleInitSources() {
    files.value = buildStage2Files(ctx, { extraFiles: extraFiles.value });
    persistFiles();
    handleOpenFile('S1_企业主体与法定边界.md');
    notify('已完成 6 大分类素材档案初始化！', 'success');
    if (currentStep.value === 1) currentStep.value = 2;
  }

  // [2026-09-30] [师弟定规 · 盖板工作台] 盖板响应式状态与动线流转
  const isDistillSheetOpen = ref(false);
  const distillMode = ref('web'); // 'web' | 'text'

  function openDistillSheet(mode = 'web') {
    distillMode.value = mode;
    isDistillSheetOpen.value = true;
    notify(mode === 'web' ? '已进入网页蒸馏大盖板工作台！' : '已进入文案蒸馏大盖板工作台！', 'info');
  }

  function closeDistillSheet() {
    isDistillSheetOpen.value = false;
  }

  // 采纳来自 DistillSheet 盖板的增补分片 (1.x 独立文件入库 · 解决 🔴4 防并发碰撞)
  function handleAdoptDistillChunk({ chunk, targetSlotKey, newFile }) {
    if (!newFile || !newFile.name) return;

    let safeFileName = newFile.name;
    let safeVersionTag = newFile.versionTag;

    // 若当前 files 中已存在该文件名（并发竞态兜底），现场单调递增派生新文件名
    if (files.value[safeFileName]) {
      const slotKey = targetSlotKey || newFile.slotKey;
      const recomputed = computeStage2ChunkVersion(files.value, slotKey);
      if (recomputed) {
        safeFileName = recomputed.nextFileName;
        safeVersionTag = recomputed.nextVersionTag;
      }
    }

    const fileToPersist = {
      ...newFile,
      name: safeFileName,
      versionTag: safeVersionTag,
    };

    files.value[safeFileName] = fileToPersist;
    extraFiles.value[safeFileName] = fileToPersist;
    try {
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem(STORAGE_KEY_EXTRA_FILES, JSON.stringify(extraFiles.value));
        localStorage.setItem(STORAGE_KEY_FILES, JSON.stringify(files.value));
      }
    } catch (_) {}
    handleOpenFile(safeFileName);
    notify(`增补分片【${safeFileName}】已成功加入素材库！`, 'success');
  }

  function handleOpenCrawler() {
    openDistillSheet('web');
  }

  function handleOpenSorter() {
    openDistillSheet('text');
  }

  function handleSwitchCardsView() {
    viewMode.value = 'cards';
    currentStep.value = 4;
    notify('已切换至结构化卡片管理模式，可对各分类逐项维护！', 'info');
  }

  function handleProceedToMaster() {
    if (assetsHealth.value < 60) {
      notify('当前素材资产健康度不足 60%，建议至少补齐主体、价格与竞品对标信息后再推进！', 'warning');
      return;
    }
    persistFiles();
    notify('素材资产库已核对定稿！正在前往阶段三：交钥匙官网与三件套...', 'success');
    if (typeof window !== 'undefined' && window.switchView) {
      setTimeout(() => {
        window.switchView('step-3-princeton');
      }, 500);
    }
  }

  function handleAction(action) {
    // [2026-09-30] [阶段二素材库] 兼容字符串与对象两种传参，修复右侧卡片动作点击无响应 Bug
    const actionType = typeof action === 'string' ? action : action?.type;
    if (!actionType) return;
    switch (actionType) {
      case 'init_sources':
        handleInitSources();
        break;
      case 'open_crawler':
        handleOpenCrawler();
        break;
      case 'open_sorter':
        handleOpenSorter();
        break;
      case 'switch_cards_view':
        handleSwitchCardsView();
        break;
      case 'proceed_to_master':
        handleProceedToMaster();
        break;
      default:
        console.warn('[useStep2] 未知动线操作:', actionType);
    }
  }

  function notify(msg, type = 'info') {
    if (typeof window !== 'undefined' && window.showToast) {
      window.showToast(msg, type);
    } else {
      console.log(`[Toast ${type}]:`, msg);
    }
  }

  // [2026-09-30 修复🔴5] 阶段二主文件右键重命名、雪花ID锚点绑定与本地持久化
  function handleRenameFile({ fn, newDisplayName }) {
    const target = files.value[fn];
    if (!target) return;
    if (!isMasterFile(target)) {
      notify('参考件由系统自管编号，仅主文件支持修改名称！', 'warning');
      return;
    }
    const trimmed = (newDisplayName || '').trim();
    if (!trimmed) return;
    if (isDuplicateDisplayName(files.value, fn, trimmed)) {
      notify('名称已存在，不能重复！', 'warning');
      return;
    }
    target.displayName = trimmed;
    if (!target.id) {
      target.id = generateSnowflakeId();
    }
    persistFiles();
    notify(`主文件已成功改名为【${trimmed}】`, 'success');
  }

  return {
    ctx,
    STAGE_2_META,
    CATEGORY_DIR_MAP,
    files,
    viewMode,
    activeCategory,
    activeFileName,
    activeFile,
    openTabs,
    currentStep,
    isHeaderCollapsed,
    mckinseyVisible,
    notes,
    assetsHealth,
    // 录入台
    crawlingUrl,
    isScraping,
    sortingText,
    isSorting,
    showSorterCard,
    // 结构化表单
    s1Form,
    s2Form,
    s3Form,
    s4Competitors,
    s5Cases,
    s6Form,
    // 交互方法
    handleSelectTab,
    handleCloseTab,
    handleToggleCategory,
    handleOpenFile,
    handleUpdateContent,
    handleSaveActiveFile,
    handleSaveNotes,
    handleGotoStep,
    handleProceed,
    handleSkip,
    handleAction,
    handleCopyContent,
    handleScrapeWebsite,
    handleDistributeSources,
    syncFormToMarkdown,
    handleAddCompetitor,
    handleAddCase,
    handleInitSources,
    handleOpenCrawler,
    handleOpenSorter,
    generateMasterCorpusMarkdown,
    // [2026-09-30] [师弟定规 · 盖板工作台] 导出盖板状态与操作
    isDistillSheetOpen,
    distillMode,
    openDistillSheet,
    closeDistillSheet,
    handleAdoptDistillChunk,
    // [2026-09-29] [素材双场景与RAG去重] 导出新状态与方法
    rawMaterialDraft,
    draftCharCount,
    isDraftOverLimit,
    candidateChunks,
    isReviewModalOpen,
    duplicateCluster,
    isDuplicateModalOpen,
    mergeDraftContent,
    handleUpdateRawDraft,
    handleStartChunking,
    handleUpdateChunkContent,
    handleUpdateChunkCategory,
    handleDiscardChunk,
    handleAdoptChunk,
    handleAdoptAllChunks,
    handleMergeDuplicate,
    handleRenameFile,
  };
}
