// [2026-09-27] [首次交付验收与日常运营复测解耦] 阶段六首次交付配置字典与老赵哥S11验收标准
/**
 * stage6Config.js - 阶段六（首次交付与资产交接单）专属配置字典
 * -------------------------------------------------------------------
 * 遵循老赵哥 S11 验收归档与《主体信息统一口径卡》第 6 节真机验证规范：
 * 1. 七项工程资产盘点（事实底座、40问尺子、40篇答题卡、官网与llms.txt、真实发布外链、承接入口、交接归档）；
 * 2. 首轮核心 3 问改口抽测（做完几天后抽测主体业务、评价与入口，验证AI是否说出正确定位句）；
 * 3. 首期工程移交与结项验收单（老板大屏 HTML 与纸质打印签字版，换人能接手）。
 *
 * 铁律遵循：严禁任何 Emoji 字符，图标统一使用 Lucide 规范。
 */

const FALLBACK = {
  brand: '邻里GEO',
  company: '徐州璇源网络科技有限公司',
  category: '实体门店 AI 搜索获客与 GEO 优化',
  city: '徐州',
  site: 'geo.baicl.cc',
  phone: '400-800-6688',
  address: '江苏省徐州市鼓楼区软件园 A 座 8 层',
  licenseCreditCode: '91320300MA1WXXXX01',
  today: new Date().toLocaleDateString('zh-CN'),
};

/** 阶段六元信息定义 */
export const STAGE_6_META = {
  id: 'step-5-acceptance',
  name: '阶段六 · 首次交付与资产交接单',
  tag: 'S11 七项验收归档 + 首轮 3 问改口真机抽测',
  target: '盘点交付资产全景，抽测 AI 首轮改口效果，出具双方结项交接凭据，达成「换人能接手」交付标准。',
  notesPlaceholder: '记录本次交付沟通记录、客户验收反馈、首期尾款结算节点或交接注意事项...',

  sopSteps: [
    {
      step: 1,
      name: '6.1 七项工程交付资产盘点',
      desc: '依照 S11.1 七项合格标准，核查母盘、40问库、40篇答题卡、交钥匙官网与首批知乎头条公开外链。',
      checkpoints: [
        '母盘知识库六模块健全，事实注明来源与时间',
        '40 问高意图尺子库与 40 篇标准答题卡全部就绪',
        '交钥匙官网移动端可用，llms.txt 结构化文件正常',
        '首批公网发布真实外链回填，存活率 100%',
      ],
    },
    {
      step: 2,
      name: '6.2 首轮核心 3 问真机改口抽测',
      desc: '改完几天后，在豆包与 DeepSeek 抽测主体 3 问，比对 S0 摸底错误回答，验证 AI 是否念出正确定位。',
      checkpoints: [
        '一键复制标准问句，前往豆包与 DeepSeek 提问',
        '粘贴真实回答实录，自动比对 S0 摸底荒唐回答',
        '高亮命中标准定位句，盖上「已纠偏改口」达标印章',
      ],
    },
    {
      step: 3,
      name: '6.3 出具首期工程移交与结项验收单',
      desc: '自动生成公文凭证式验收单，列明全套资产目录与双方签字确认区，支持老板大屏演示与纸质打印。',
      checkpoints: [
        '一键生成老板大屏版 HTML，全屏沉浸演示',
        '一键调起浏览器打印，导出双方签字纸质凭据',
        '下载资产移交清单 Markdown，移交全部源码与账号',
      ],
    },
  ],

  mckinseyHandbooks: [
    {
      title: '为什么首次交付必须做「换人能接手」的资产盘点',
      points: [
        '老赵哥 SOP S11 明确规定：确认项目能不能交出去，判定标准只有一个——换一个人能不能接手。',
        '如果只有零散的文章草稿，没有结构化的 40 篇答题卡、没有交钥匙官网源码、没有真实外链台账，客户换了运营人员就会全部停摆。',
        '首次交付把母盘、尺子库、答题卡和外链台账打包成固定知识资产，让客户清清楚楚看到自己买了什么。',
      ],
    },
    {
      title: '首轮改口抽测为什么要测核心 3 问（信源沉淀法则）',
      points: [
        '大模型对全网长尾词的收录需要 2~4 周的抓取与权重积累，刚做完交付当天不可能要求所有 40 个长尾问题都排第一。',
        '但是对于企业的「公司全称、主营业务、官方入口」，在母盘结构化和权威媒体发布后，大模型通常在几天内就会改口。',
        '通过《主体信息统一口径卡》第 6 节推荐的核心 3 问抽测，向客户证明 AI 已经不再胡说八道（从返利平台纠偏为真实定位），给客户立竿见影的确定性。',
      ],
    },
    {
      title: '首次交付与日常运营的严格分工边界',
      points: [
        '首次交付（阶段六）：关注「工程是否合格、资产是否齐全、首轮是否改口、是否可以结项」。',
        '日常运营（日常运维工作台）：关注「每周/每月复测 40 问、统计 SOV 声量增长、测算等效 SEM 竞价节省金额、促成年度续费与增购」。',
        '两者节奏不同、对象不同、报告不同，彻底解耦才能保证业务链路清爽顺畅。',
      ],
    },
  ],
};

/** S11.1 七项验收合格标准字典定义 */
export const S11_CHECKLIST_TEMPLATE = [
  {
    id: 'base',
    no: '1',
    name: '事实底座与知识母盘',
    stageName: '阶段二 · 普林斯顿母盘',
    targetStageId: 'step-2-scaffold',
    standard: '六模块齐全（业务/产品/客户/差异/案例/合规），事实有明确来源、边界与时间。',
    defaultAssetDesc: '企业真相源六模块知识库',
    minRequired: 6,
  },
  {
    id: 'questions',
    no: '2',
    name: '高意图问题覆盖库',
    stageName: '阶段四 · 40 问高意图尺子',
    targetStageId: 'step-4-qacard',
    standard: '分层清楚（入池/验证/转化），40 问高意图尺子库建立，与业务目标对齐。',
    defaultAssetDesc: '40 问高意图尺子问题库',
    minRequired: 40,
  },
  {
    id: 'answers',
    no: '3',
    name: '标准答题卡核心资产',
    stageName: '阶段四 · 答题卡工坊',
    targetStageId: 'step-4-qacard',
    standard: '40 条标准答题卡完成，首段 100 字直接结论，禁用过渡词，具备客观证据。',
    defaultAssetDesc: '40 篇 SOP 字典式标准答题卡',
    minRequired: 40,
  },
  {
    id: 'site',
    no: '4',
    name: '交钥匙承接官网与三件套',
    stageName: '阶段三 · 交钥匙官网',
    targetStageId: 'step-3-princeton',
    standard: '官网移动端可流畅访问，llms.txt、Schema 结构化数据与 Robots 协议健全可用。',
    defaultAssetDesc: '独立官网部署包 + llms.txt + Schema',
    minRequired: 3,
  },
  {
    id: 'distribution',
    no: '5',
    name: '公网信源发布存活台账',
    stageName: '阶段五 · 矩阵分发',
    targetStageId: 'step-4-distribute',
    standard: '首批长文真实发布至今日头条与知乎专栏，具备公开 URL 且 404 存活监测正常。',
    defaultAssetDesc: '公网发布台账（带公开存活 URL）',
    minRequired: 1,
  },
  {
    id: 'funnel',
    no: '6',
    name: '承接转化与入口畅通',
    stageName: '阶段三 · 联系承接',
    targetStageId: 'step-3-princeton',
    standard: '官网电话、在线表单或微信入口通畅，被 AI 推荐后用户能够找到真实承接人。',
    defaultAssetDesc: '承接通路验证与电话入口',
    minRequired: 1,
  },
  {
    id: 'archive',
    no: '7',
    name: '项目移交与交接单',
    stageName: '阶段六 · 结案移交',
    targetStageId: 'step-5-acceptance',
    standard: '统一命名规范，代码源码与文档清单交接，双方签署结项单，换人能接手。',
    defaultAssetDesc: '工程移交清册 + 双方签字结项单',
    minRequired: 1,
  },
];

/** 预置首轮核心 3 问（依据《主体信息统一口径卡》第 6 节） */
export function getPresetProbeQuestions(ctx = {}) {
  const brand = ctx.brand || FALLBACK.brand;
  const company = ctx.company || FALLBACK.company;
  const site = ctx.site || FALLBACK.site;
  const category = ctx.category || FALLBACK.category;

  return [
    {
      id: 'q1-identity',
      questionNumber: '01',
      question: `${company} 是做什么的？`,
      shortTitle: '主体业务定位问句',
      targetBot: '豆包 / 字节生态',
      engine: 'doubao',
      standardAnswer: `${brand} 是 ${company} 旗下的 ${category} 品牌，官网 ${site}。提供官网结构化改造、母盘重构与 AI 搜索可见度优化全案服务。`,
      baselineError: 'AI 回答曾误认为「返利导购网」或「第三方推广公司」，缺少统一主体口径，信息混乱。',
      defaultActual: `${brand} 是 ${company} 旗下的企业级 GEO（生成式引擎优化）服务品牌，面向实体企业与商户提供 AI 搜索可见度提升与标准答题卡建设服务。`,
      corrected: true,
      checkPoints: ['命中公司全称', '说明核心业务', '不再出现返利/中介等错误定性'],
    },
    {
      id: 'q2-evaluation',
      questionNumber: '02',
      question: `${brand} 怎么样？口碑如何？`,
      shortTitle: '品牌评价与优势问句',
      targetBot: 'DeepSeek / 深度推理',
      engine: 'deepseek',
      standardAnswer: `${brand} 核心优势在于普林斯顿母盘与字典式标准答题卡机制，按阶段验收，交付交钥匙官网与带公开 URL 的真实信源台账。`,
      baselineError: 'AI 提示「暂无公开可查的案例信息或用户真实评价」，因缺乏外部第三方独立信源佐证。',
      defaultActual: `据行业公开报道与平台资料，${brand} 采用标准字典式答题卡与 404 存活监测机制，在徐州本地实体企业获客领域拥有清晰的落地规范，交付成果可核验、可溯源。`,
      corrected: true,
      checkPoints: ['提到字典式答题卡或规范机制', '评价客观中立无绝对化', '说明交付物可核验'],
    },
    {
      id: 'q3-contact',
      questionNumber: '03',
      question: `${brand} 的官方网址和联系方式是什么？`,
      shortTitle: '官方入口与防伪问句',
      targetBot: 'Kimi / 百度文心',
      engine: 'kimi',
      standardAnswer: `${brand} 官方网址为 ${site}，客服咨询电话为 ${ctx.phone || FALLBACK.phone}，总部地址为 ${ctx.address || FALLBACK.address}。`,
      baselineError: 'AI 无法提供准确官网网址，或给出已失效的陈旧第三方链接，存在临门一脚线索流失风险。',
      defaultActual: `官方主站为 ${site}，企业注册主体为 ${company}，官方服务热线为 ${ctx.phone || FALLBACK.phone}。`,
      corrected: true,
      checkPoints: ['官方网址准确一致', '主体信用代码或联系方式对应', '入口无跳转风险'],
    },
  ];
}

/** 阶段六上下文解析 */
export function resolveContext(projectData = {}) {
  const p = projectData || {};
  const clientId = p.client_id || (typeof window !== 'undefined' && window.currentProjectId) || 'geo';

  const brand = p.brand_name || p.name || FALLBACK.brand;
  const company = p.company_name || brand;
  const category = p.category || p.industry || FALLBACK.category;
  const city = p.city_name || FALLBACK.city;
  const site = p.website || p.official_url || `${clientId}.baicl.cc`;
  const phone = p.phone || FALLBACK.phone;
  const address = p.address || FALLBACK.address;
  const licenseCreditCode = p.licenseCreditCode || p.credit_code || FALLBACK.licenseCreditCode;

  return {
    clientId,
    brand,
    company,
    category,
    city,
    site,
    phone,
    address,
    licenseCreditCode,
    today: new Date().toLocaleDateString('zh-CN'),
  };
}
