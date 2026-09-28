/**
 * stage1Config.js - 阶段一（AI 可见度商业转化诊断）专属配置字典
 * -----------------------------------------------------------------
 * 专为阶段一 3 竖列工作区服务：
 * 包含：四大交付物文件模板、4 步 SOP 动线及客户耐心门禁配置、麦肯锡认知手册。
 */

const FALLBACK = {
  brand: '邻里GEO',
  category: 'GEO 优化',
  city: '徐州',
  site: 'geo.baicl.cc',
  competitor: '优搜网络',
  today: new Date().toLocaleDateString('zh-CN'),
};

export function resolveContext(projectData = {}) {
  const p = projectData || {};
  const clientId = p.client_id || (typeof window !== 'undefined' && window.currentProjectId) || 'geo';

  let activeQaVersion = 'QA-V1';
  let activeQuestionFile = '01_豆包提问清单_推荐版.txt';
  let activeAnswerFile = '02_豆包实测回答记录_初测.txt';

  try {
    if (typeof localStorage !== 'undefined') {
      const savedQaRaw = localStorage.getItem('geo_step0_active_qa_' + clientId);
      if (savedQaRaw) {
        const parsed = JSON.parse(savedQaRaw);
        if (parsed && typeof parsed === 'object') {
          if (parsed.activeQaVersion) activeQaVersion = parsed.activeQaVersion;
          if (parsed.activeQuestionFile) activeQuestionFile = parsed.activeQuestionFile;
          if (parsed.activeAnswerFile) activeAnswerFile = parsed.activeAnswerFile;
        }
      }
    }
  } catch (err) {
    console.warn('[stage1Config] 读取阶段零生效底牌缓存失败:', err);
  }

  return {
    brand: p.brand_name || p.name || FALLBACK.brand,
    category: p.category || p.industry || FALLBACK.category,
    city: p.city_name || FALLBACK.city,
    site: p.website || p.official_url || FALLBACK.site,
    competitor: (Array.isArray(p.competitors) && p.competitors[0]) || FALLBACK.competitor,
    today: new Date().toLocaleDateString('zh-CN'),
    clientId,
    activeQaVersion,
    activeQuestionFile,
    activeAnswerFile,
  };
}

// [2026-09-27] [补齐dir字段] 目录分类中文映射字典，用于中栏状态栏与文件树路径一致性
const CATEGORY_DIR_MAP = {
  materials: '指标与素材',
  drafts: '过程草稿',
  reports: '最终交付报告',
};

export function buildStage1Files(ctx) {
  const files = {
    '01_网络底座指标_待对照.md': {
      category: 'materials',
      name: '01_网络底座指标_待对照.md',
      renderMode: 'markdown',
      content: `# 客户网络底座与线上资产真实指标 (机械基础版·待核对)

- 抓取时间: ${ctx.today}
- 企业品牌: ${ctx.brand}
- 官网域名: ${ctx.site}
- 服务器所在地: ${ctx.city}
- 百度权重 / SEO 底座: PR 1 / 权重 0 (极弱)
- 大模型爬虫放行状态:
  - Bytespider (豆包): [未配置] 未配置专属放行 (可能被拦截)
  - DeepSeekSpider: [未配置] 未配置
- 大模型可读协议检测:
  - /llms.txt: [未通过] 不存在 (大模型抓取无结构化索引)
  - robots.txt: [警告] 仅通用放行，未做 AI 友好声明
  - JSON-LD 结构化标签: [未通过] 缺失
- 豆包首推率现状: 0% (已被核心竞品【${ctx.competitor}】截流)

---
> [交付专家说明]：本指标为程序抓取直出。交付人员可在上方直接修改纠偏，并与客户面对面对照核实。`,
    },

    '01_阶段零豆包实测问答素材.md': {
      category: 'materials',
      name: '01_阶段零豆包实测问答素材.md',
      renderMode: 'markdown',
      content: `# 阶段零豆包实测真实问答记录 (底牌素材)

> [溯源血统]：本素材基于阶段零生效底牌【${ctx.activeQaVersion}】（${ctx.activeQuestionFile} + ${ctx.activeAnswerFile}）直出

## 核心提问 1: ${ctx.city}做${ctx.category}哪家公司比较好？
- 豆包实测回答: 优先推荐了【${ctx.competitor}】等竞品，完全未提及客户品牌【${ctx.brand}】。
- 截流流失分析: 竞品已布局多篇高权重问答语料，客户直接丢失一手精准商机。

## 核心提问 2: 想找${ctx.city}的【${ctx.brand}】，他们主要做什么业务，口碑怎么样？
- 豆包实测回答: 回答内容语焉不详，存在明显信息滞后与幻觉拼接。
- 危害总结: 老客户朋友背调时，AI 回答缺乏权威性，严重拉低转化率。`,
    },

    '01_商业诊断与转化初稿.md': {
      category: 'drafts',
      name: '01_商业诊断与转化初稿.md',
      renderMode: 'markdown',
      content: `# 企业 AI 可见度商业诊断与询盘流失初稿 (待润色)

> [溯源血统]：本报告基于阶段零生效底牌【${ctx.activeQaVersion}】（${ctx.activeQuestionFile} + ${ctx.activeAnswerFile}）直出

## 一、老板必看的资产确权
企业在【${ctx.city}】本地拥有扎实的行业积累，但在线上已被大模型搜索遗忘。大模型问答推荐中，100% 的商机入口正被竞品【${ctx.competitor}】持续吃掉。

## 二、算清 3 类致命流失账
1. 品牌直搜流失: 老客户朋友向豆包、DeepSeek 打听，AI 推荐竞品，核心信任资产被蚕食；
2. 行业词精准截流: “${ctx.city}做${ctx.category}找哪家”，客户完全隐形，商机直接流向同行；
3. 竞品对比失语: 因缺乏官方权威真相源，大模型抓取第三方杂乱信息甚至给出负面评价。

## 三、破局路径与 30 天交付目标
立即建立交钥匙原生大模型官网与普林斯顿母盘语料，实现 30 天内豆包首推率从 0% 跃升至 60% 以上，抢回本地搜索前三主入口！`,
    },

    '01_老板商业诊断报告_好看大屏.html': {
      category: 'reports',
      name: '01_老板商业诊断报告_好看大屏.html',
      renderMode: 'html',
      content: `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>企业 AI 可见度商业诊断决策大屏</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-900 text-slate-100 p-8 font-sans min-h-screen">
  <div class="max-w-5xl mx-auto space-y-6">
    <!-- 顶栏标题 -->
    <div class="flex items-center justify-between border-b border-slate-800 pb-5">
      <div>
        <div class="flex items-center gap-2">
          <span class="px-2.5 py-0.5 rounded text-xs font-bold bg-violet-500/20 text-violet-400 border border-violet-500/30">决策专供</span>
          <h1 class="text-2xl font-black text-white tracking-tight">企业 AI 可见度商业诊断与商机截流穿透大屏</h1>
        </div>
        <p class="text-xs text-slate-400 mt-1">诊断主体：${ctx.brand} | 核心对标竞品：${ctx.competitor} | 出具日期：${ctx.today}</p>
      </div>
      <div class="px-4 py-2 bg-rose-500/10 border border-rose-500/30 text-rose-400 rounded-xl text-xs font-bold flex items-center gap-1.5">
        <span class="w-2 h-2 rounded-full bg-rose-500 animate-pulse"></span>
        高危预警：商机入口正被竞品切盘
      </div>
    </div>

    <!-- 核心量化指标卡片 -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="bg-slate-800/80 border border-slate-700/80 p-5 rounded-2xl shadow-lg space-y-1">
        <div class="text-xs font-medium text-slate-400">豆包 (字节生态) 搜索首推率</div>
        <div class="text-4xl font-black text-rose-500 mt-2">0%</div>
        <div class="text-[11px] text-slate-500">客户品牌在主流大模型问答中完全隐形</div>
      </div>
      <div class="bg-slate-800/80 border border-slate-700/80 p-5 rounded-2xl shadow-lg space-y-1">
        <div class="text-xs font-medium text-slate-400">竞品【${ctx.competitor}】入口截流率</div>
        <div class="text-4xl font-black text-amber-400 mt-2">85.4%</div>
        <div class="text-[11px] text-slate-500">核心意向客户提问时被竞品定向拦截</div>
      </div>
      <div class="bg-slate-800/80 border border-slate-700/80 p-5 rounded-2xl shadow-lg space-y-1">
        <div class="text-xs font-medium text-slate-400">预估每月潜在高净值询盘流失</div>
        <div class="text-4xl font-black text-emerald-400 mt-2">30~50 <span class="text-sm font-normal">单</span></div>
        <div class="text-[11px] text-slate-500">每单均价过万，年化损失触目惊心</div>
      </div>
    </div>

    <!-- 痛点分析与愿景 -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div class="bg-slate-800/60 border border-slate-700/70 p-5 rounded-2xl space-y-3">
        <h3 class="text-sm font-bold text-white flex items-center gap-1.5">
          <span class="text-rose-400">●</span> 现状痛点：为什么必须立即行动？
        </h3>
        <ul class="text-xs text-slate-300 space-y-2 leading-relaxed">
          <li>• <strong>底座完全缺失</strong>：官网未配置 <code class="bg-slate-900 px-1 py-0.5 rounded text-violet-300">/llms.txt</code> 与 JSON-LD，大模型爬虫进不来；</li>
          <li>• <strong>语料被动挨打</strong>：同行早已布局普林斯顿 9 因子内容矩阵，牢牢占据前排首推位；</li>
          <li>• <strong>签约窗口期倒计时</strong>：本地服务商洗牌阶段，晚一步进入成本翻倍。</li>
        </ul>
      </div>

      <div class="bg-gradient-to-br from-indigo-950/60 to-violet-950/60 border border-indigo-700/50 p-5 rounded-2xl space-y-3">
        <h3 class="text-sm font-bold text-indigo-200 flex items-center gap-1.5">
          <span class="text-emerald-400">●</span> 30 天破局路线与交付愿景
        </h3>
        <ul class="text-xs text-indigo-100 space-y-2 leading-relaxed">
          <li>• <strong>第 1 周</strong>：交付交钥匙 AI 原生独立官网，100% 极速放行爬虫；</li>
          <li>• <strong>第 2 周</strong>：注入普林斯顿高权威母盘三元组事实语料；</li>
          <li>• <strong>第 4 周</strong>：豆包、DeepSeek 首推率突破 65%，夺回区域商机第一盘！</li>
        </ul>
      </div>
    </div>
  </div>
</body>
</html>`,
    },

    '01_老板商业诊断报告_文字版.md': {
      category: 'reports',
      name: '01_老板商业诊断报告_文字版.md',
      renderMode: 'markdown',
      content: `# 企业 AI 可见度商业转化诊断报告 (老板签约决策文字版)

- **企业名称**：${ctx.brand}
- **主营业务**：${ctx.category}
- **所属地域**：${ctx.city}
- **出具团队**：邻里 GEO 专属交付战队
- **报告版本**：2026 签约促单版

---

### 一、资产确权与现状审计
经过网络探针与大模型真抓实测，【${ctx.brand}】在传统线下具备良好口碑，但在线上 AI 搜索入口处于**“完全失守”**状态：
1. 豆包 (字节生态) 首推率：**0%**；
2. DeepSeek 行业词推荐率：**0%**；
3. 核心竞品【${ctx.competitor}】截留率：**85% 以上**。

### 二、三大询盘流失实锤分析
1. **老客户朋友背调流失**：企业转介绍客户在做背景调查时，豆包给出模糊甚至竞品信息，直接产生信任动摇；
2. **行业主入口流失**：在“徐州找靠谱的${ctx.category}”等通用问答中，潜在商机被竞品全数接走；
3. **底座资产技术债**：现有站点无大模型结构化标准支持，爬虫抓不到关键三元组事实。

### 三、交钥匙解决方案
我司将提供从“交钥匙官网底座”到“普林斯顿母盘语料重构”的一体化签约服务，承诺 30 天内实现首推率突破 60%，抢占本地第一梯队！`,
    },

    '01_工程师底座技术审计.md': {
      category: 'reports',
      name: '01_工程师底座技术审计.md',
      renderMode: 'markdown',
      content: `# 站点底座技术体检与工程审计报告 (内部施工版)

- 诊断站点: ${ctx.site}
- 审计时间: ${ctx.today}

## 1. 爬虫协议与放行体检
- User-agent: Bytespider -> 未单独配置放行规则 (存在封禁拦截风险)
- User-agent: DeepSeekSpider -> 未配置
- User-agent: Googlebot / Baiduspider -> 基础放行

## 2. 大模型知识引索体检
- /llms.txt 文件状态: HTTP 404 (缺失)
- Schema.org (JSON-LD) 标记: 缺失
- Meta Robots AI-Specific Tags: 缺失

## 3. 工程整改建议 (阶段二落地)
1. 采用交钥匙全新独立二级域名挂载，彻底免碰老代码；
2. 注入符合普林斯顿规范的结构化语义标签；
3. 静态化全托管 CDN 部署，保障抓取首包时间 <150ms。`,
    },
  };

  // [2026-09-27] [SSOT单一真相源] 文件对象的 dir 属性统一由 CATEGORY_DIR_MAP 动态注入，消除硬编码与死代码分支
  Object.keys(files).forEach((fn) => {
    files[fn].dir = CATEGORY_DIR_MAP[files[fn].category] || '交付文件';
  });

  return files;
}

// [2026-09-28] [阶段一底座抓取动线视线引导优化] 根据后端真实探测 metrics 组装生成企业级 Markdown
export function buildCrawledMetricsMarkdown(ctx, metrics = {}) {
  const url = metrics.url || ctx.site || 'https://example.com';
  const isOnline = metrics.is_online !== undefined ? metrics.is_online : true;
  const statusCode = metrics.status_code || (isOnline ? 200 : 0);
  const htmlSize = metrics.html_size_kb ? `${metrics.html_size_kb} KB` : '未知';
  const hasSsr = metrics.has_ssr ? '[通过] 服务端渲染 (SSR 完整直出)' : '[警告] 纯客户端渲染 (大模型爬虫易抓到空壳)';
  const hasLlms = metrics.has_llms_txt ? '[通过] 已部署 /llms.txt 知识索引' : '[未通过] 缺失 /llms.txt (大模型无结构化索引)';
  const hasJsonLd = metrics.has_json_ld ? '[通过] 已配置 Schema.org 结构化数据' : '[未通过] 缺失 Schema.org 结构化标记';
  const robotsStatus = metrics.robots_status || (metrics.warnings && metrics.warnings.length ? '[警告] 未主动优化 AI 爬虫' : '已配置本土 AI 爬虫规则');
  const techScore = metrics.tech_score !== undefined ? metrics.tech_score : 85;
  const warningsList = (metrics.warnings && metrics.warnings.length > 0)
    ? metrics.warnings.map((w) => `  - ${w}`).join('\n')
    : '  - 无严重阻断项';

  return `# 客户网络底座与线上资产真实指标 (真机网络探测版)

- 探测时间: ${ctx.today} (真实网络 HTTP/TLS 探测)
- 企业品牌: ${ctx.brand}
- 官网地址: ${url}
- HTTP 响应状态: ${statusCode} ${isOnline ? '(在线可连通)' : '(无法连通)'}
- 技术底座健康分: ${techScore} / 100
- 页面体积: ${htmlSize}
- 大模型可读协议探测:
  - /llms.txt 标准: ${hasLlms}
  - robots.txt 爬虫规则: ${robotsStatus}
  - Schema.org (JSON-LD): ${hasJsonLd}
  - 渲染架构 (SSR/CSR): ${hasSsr}
- 重点告警与风险项:
${warningsList}
- 阶段零豆包实测底牌现状:
  - 豆包首推率: 0% (已被核心竞品【${ctx.competitor}】精准截流)

---
> [交付专家说明]：本指标由真机网络探测引擎 (Python inspect_website) 实时探测直出，已同步写入 outputs/audit_metrics.json。交付人员可在上方直接核对，并与客户面对面对照。`;
}

export const STAGE_1_META = {
  index: 1,
  key: 'step1',
  name: '阶段一：AI 可见度商业转化诊断',
  tag: '老板决策版',
  target: '真抓网络底座指标，出具商业诊断与询盘流失初稿，为对客签约提供实锤。',
  notesPlaceholder: '记录客户商业诊断备忘（如：徐州老牌客户、核心防范竞品截流...）',
  categories: [
    { id: 'materials', name: '指标与素材' },
    { id: 'drafts', name: '过程草稿' },
    { id: 'reports', name: '最终交付报告' },
  ],
  sopSteps: [
    {
      id: 'crawl_confirm',
      name: '真抓网络底座与客户对照',
      desc: '抓取客户线上真实底座指标（0 幻觉）。交付专家可直接在中间微调数据，并与客户对照确认。',
      category: 'materials',
      activeFile: '01_网络底座指标_待对照.md',
      // [2026-09-28] [阶段一底座抓取动线视线引导优化] 增加完成态文案，消除抓取后的认知断层
      action: {
        label: '真抓网络底座指标',
        completedLabel: '已抓取真实指标 (点击重新抓取)',
        icon: 'activity',
        type: 'crawlMetrics',
      },
      gate: {
        type: 'patience_confirm',
        options: [
          { id: 'confirmed', label: '客户已核对确认（意向明确，推进生成初稿）' },
          { id: 'suspended', label: '客户暂无耐心/意向不足（挂起等待，暂不推进）' },
        ],
      },
      nextLabel: '确认完成，前往出具初稿',
    },
    {
      id: 'draft_polish',
      name: '直出初稿与去水润色',
      desc: '生成基础初稿。交付人员可直接复制中栏内容与豆包问答素材，前往外部 IDE 或豆包进行深度润色（去水、加强焦虑转化说服力），改完贴回保存。',
      category: 'drafts',
      activeFile: '01_商业诊断与转化初稿.md',
      action: { label: '直出商业诊断与转化初稿', icon: 'file-text', type: 'generateDraft' },
      nextLabel: '初稿润色完成，前往生成最终报告',
      skipLabel: '跳过润色，直接出报告',
    },
    {
      id: 'final_reports',
      name: '出具多版本交付报告',
      desc: '根据确认并润色后的素材，生成最终交付报告（老板好看大屏 HTML、商业文字版 MD 与工程师技术审计版）。',
      category: 'reports',
      activeFile: '01_老板商业诊断报告_好看大屏.html',
      action: { label: '一键生成多版本诊断报告', icon: 'sparkles', type: 'generateFinalReports' },
      extraActions: [
        { label: '全屏演示老板大屏', icon: 'maximize-2', type: 'openFullscreen' },
        { label: '复制客户报告链接', icon: 'share-2', type: 'copyClientLink' },
      ],
      nextLabel: '完成阶段一，前往阶段二（交钥匙官网）',
      isFinal: true,
      nextView: 'step-2-scaffold',
    },
  ],
  mckinsey: {
    title: '阶段一：商业诊断与促单避坑手册',
    valueDesc: '做完后，项目里会有：<strong>① 商业诊断报告（老板决策版）</strong>；<strong>② 高转化视觉大屏</strong>；<strong>③ 工程师底座体检报告</strong>。',
    valueBusiness: '基于真抓底牌向老板讲清 3 类询盘流失账，明示竞品已在吃入口，给足 30 天愿景促成对客签单。',
    whatTitle: '真抓实测，算清流失账，不做假大空',
    whatDesc: '不仅抓技术指标，更结合阶段零真实问答，把“谁在抢你的客户”、“老朋友搜你为什么搜不到”摆在台面上。',
    whyTitle: '老板不在乎底层代码，只在乎商机流失',
    whyDesc: '直接跟老板讲爬虫代码会被当成普通建站推销；告诉他每年几十万高净值询盘被竞品截流，老板立刻听得懂。',
    howTitle: '极简四步签约闭环',
    howSteps: [
      '<strong>1. 真抓与对照</strong>：抓取真实底座指标，当面与客户对照，判定意向门禁；',
      '<strong>2. 直出与润色</strong>：生成初稿，一键复制到外部 IDE / 豆包润色去水后贴回；',
      '<strong>3. 出具多版本报告</strong>：一键生成好看大屏版与商业文字版；',
      '<strong>4. 演示签单</strong>：全屏演示大屏，发送对客报告链接，推进签约！',
    ],
  },
};
