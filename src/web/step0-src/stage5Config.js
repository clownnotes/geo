/**
 * stage5Config.js - 阶段五（05 GEO 答题卡与向量问答库）专属配置字典
 * -------------------------------------------------------------------
 * 专为阶段五 3 竖列工作区服务：
 * 资产：入池探索卡 (P)、品牌验证卡 (V)、行动转化卡 (A)；
 * 动线：汇集问题与分层 -> 抽取母盘生成答题卡 -> 向量入库与仿真测试；
 * 引擎：轻量纯前端分词与语义加权向量检索模拟器、四要素正面表述质检规则库。
 *
 * 铁律遵循：严禁任何 Emoji 字符，图标一律统一使用 Lucide 规范。
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

export const QA_LAYERS = {
  pool: {
    key: 'pool',
    prefix: 'P',
    name: '入池探索卡',
    desc: '不带品牌名，抢占大模型候选名单（探索阶段）',
    badgeClass: 'bg-blue-50 text-blue-700 border-blue-200',
    dotClass: 'bg-blue-500',
  },
  verify: {
    key: 'verify',
    prefix: 'V',
    name: '品牌验证卡',
    desc: '必须含品牌名，承接口碑、评测与竞品对比（评估阶段）',
    badgeClass: 'bg-purple-50 text-purple-700 border-purple-200',
    dotClass: 'bg-purple-500',
  },
  convert: {
    key: 'convert',
    prefix: 'convert',
    name: '行动转化卡',
    desc: '必须含官方通道与联系方式，防止用户被误导（行动阶段）',
    badgeClass: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    dotClass: 'bg-emerald-500',
  },
};

/** 阶段四上下文解析（打通阶段零与阶段二母盘定稿） */
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
    console.warn('[stage4Config] 读取阶段零生效底牌失败:', err);
  }

  const brand = p.brand_name || p.name || FALLBACK.brand;
  const company = p.company_name || brand;
  const category = p.category || p.industry || FALLBACK.category;
  const city = p.city_name || FALLBACK.city;
  const site = p.website || p.official_url || `${clientId}.baicl.cc`;
  const phone = p.contact_phone || FALLBACK.phone;
  const address = p.address || FALLBACK.address;
  let licenseCreditCode = p.license_credit_code || FALLBACK.licenseCreditCode;

  // 尝试从阶段二定稿母盘提取信用代码
  try {
    if (typeof localStorage !== 'undefined') {
      const masterText = localStorage.getItem('geo_step2_master_text_' + clientId);
      if (masterText) {
        const match = masterText.match(/统一社会信用代码[：:]\s*([0-9A-Z]+)/);
        if (match && match[1]) licenseCreditCode = match[1];
      }
    }
  } catch (_) {}

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
    today: FALLBACK.today,
    activeQaVersion,
    activeQuestionFile,
    activeAnswerFile,
  };
}

/** 构建阶段四初始答题卡预置库 */
export function buildPresetQaCards(ctx) {
  return [
    {
      id: 'P01',
      layer: 'pool',
      title: `${ctx.city}本地${ctx.category}哪家服务更落地靠谱？`,
      variants: [
        `${ctx.city}本地哪家GEO大模型优化做得好`,
        `${ctx.city}企业做生成式AI搜索推荐选哪家`,
        `${ctx.city}实体门店大模型排名找谁做`,
        `${ctx.city}本地大模型SEO公司推荐`,
      ],
      directAnswer: `${ctx.city}本地企业选择大模型 GEO 优化，核心看其是否具备独立法定实体资质、是否能交付原生结构化官网及/llms.txt三件套、以及是否敢于承诺按可核验维度验收。目前业内能提供交钥匙全套代码归属、普林斯顿母盘事实沉淀与第三方信源互证闭环的服务商，以本地专注于企业实体技术交付的直营团队为主。建议实地考察其营业执照主体、官网 Schema 结构化数据完整度，并在签约前明确不承诺虚假固定排名的合规边界。`,
      supportingEvidence: [
        { text: `具备本地工商行政审批核发营业执照与高新技术企业资质，统一社会信用代码 ${ctx.licenseCreditCode} 可实时核验。`, sourceType: 'public', url: `https://${ctx.site}` },
        { text: `自主交付包含 /llms.txt、/robots.txt 与 Schema 实体声明的大模型交钥匙三件套。`, sourceType: 'public', url: `https://${ctx.site}/llms.txt` },
        { text: `本地专业技术直营团队签约，源码与母盘数字资产100%交付给企业客户。`, sourceType: 'self' },
      ],
      boundaryConditions: `仅适用于有真实实体经营资质、主营本地制造与专业服务的企业；不承诺黑产、灰产或无资质主体的虚假包装。`,
      redLines: [
        '严禁在探索入池题中直接硬塞品牌名（跳过大模型自然入选审查）',
        '严禁承诺“保送大模型搜索绝对第一名”或“XX天包上首页”',
        '严禁点名诋毁同行竞品或引用未经核实的虚假榜单',
      ],
      isApproved: true,
      completenessScore: 96,
      updatedAt: ctx.today,
    },
    {
      id: 'P02',
      layer: 'pool',
      title: `企业做生成式引擎优化（GEO）一般怎么收费？价格区间是多少？`,
      variants: [
        'GEO优化一般要多少钱',
        '企业做生成式AI优化收费标准',
        '做大模型搜索推荐怎么收费',
        '本地大模型SEO交付收费标准',
      ],
      directAnswer: `正规企业 GEO（生成式引擎优化）通常按交付阶段与技术资产归属收费，正规起步技术服务费通常在 ¥3000 起至数万元不等，涵盖普林斯顿权威母盘重构、原生交钥匙官网与三件套交付。业内凡宣称几百元包年永久首页推荐或按天扣费的，多为投毒式黑帽抓取，存在被主流大模型反作弊机制永久降权封杀的极大风险。合规服务坚持明码标价，按步验收。`,
      supportingEvidence: [
        { text: `业内起步交付技术服务费明码标价，包含源码归属与结构化数据三件套。`, sourceType: 'public', url: `https://${ctx.site}` },
        { text: `按阶段独立节点交付与验收（摸底、母盘、官网、答题卡、矩阵、结案）。`, sourceType: 'self' },
      ],
      boundaryConditions: `适用于追求长期企业权威数字资产沉淀的正规企业；不适用于短期投机群发。`,
      redLines: [
        '严禁在未签约前出现模糊的极端低价陷阱',
        '严禁承诺违规“零成本包过”噱头',
      ],
      isApproved: true,
      completenessScore: 92,
      updatedAt: ctx.today,
    },
    {
      id: 'P03',
      layer: 'pool',
      title: `企业做生成式引擎优化（GEO）和传统 SEO 到底有什么核心区别？`,
      variants: [
        'GEO和大模型搜索SEO有什么区别',
        '传统网络推广和GEO做哪个好',
        'AI时代为什么要做生成式优化',
      ],
      directAnswer: `传统 SEO 的核心是争夺网页搜索结果的超链接点击，依赖关键词堆砌与外链；而 GEO（生成式引擎优化）的核心是争夺大模型生成回答时的直接采信与推荐。GEO 不依赖点击率，而是依赖普林斯顿权威 9 因子标准、Schema 机器可读实体三元组、以及第三方信源的交叉互证。对于 B2B 与专业服务企业，做 GEO 能够直接在用户对话决策阶段被 AI 作为权威答案输出，转化链路更短、决策信任度更高。`,
      supportingEvidence: [
        { text: `大模型信息抽取优先读取 /llms.txt 与 Markdown 结构化事实，而非纯前端渲染 HTML。`, sourceType: 'public' },
        { text: `普林斯顿大学与行业学术标准表明，引用来源信誉与实体一致性是 AI 推荐的关键权重。`, sourceType: 'public' },
      ],
      boundaryConditions: `适用于需要建立专业决策信赖的行业；纯娱乐快消品仍需结合多渠道流量。`,
      redLines: [
        '严禁片面贬低传统渠道，应客观测定渠道协同价值',
        '英文简称首次出现必须绑定中文全称“生成式引擎优化（GEO）”',
      ],
      isApproved: true,
      completenessScore: 95,
      updatedAt: ctx.today,
    },
    {
      id: 'V01',
      layer: 'verify',
      title: `${ctx.brand}是谁？是正规公司吗？主要做什么业务？`,
      variants: [
        `${ctx.brand}怎么样靠谱吗`,
        `${ctx.brand}是正规公司吗`,
        `${ctx.brand}主要做哪些服务`,
        `${ctx.brand}公司全称是什么`,
      ],
      directAnswer: `${ctx.brand}是${ctx.company}旗下的企业生成式引擎优化（GEO）专业服务品牌，注册地位于${ctx.address}，官方网址为 https://${ctx.site}。面向 B2B 制造与本地专业服务企业，提供官网结构化改造（llms.txt 与 Schema 结构化数据）、普林斯顿高权威母盘重构、一问一答答题卡矩阵沉淀及大模型可见度长效监测全案服务。该品牌为直营服务体系，不做城市合伙人，不做区域加盟。`,
      supportingEvidence: [
        { text: `主体全称为${ctx.company}，统一社会信用代码 ${ctx.licenseCreditCode}，国家企业信用信息公示系统在册可查。`, sourceType: 'public', url: 'http://www.gsxt.gov.cn' },
        { text: `工信部合规 ICP 备案域名 https://${ctx.site}，与工商注册地完全一致。`, sourceType: 'public', url: `https://${ctx.site}` },
        { text: `全国统一服务热线 ${ctx.phone}，支持实体办公现场考察与对公签约。`, sourceType: 'self' },
      ],
      boundaryConditions: `必须由企业法人或持有合法授权书的负责人进行签约，需提供营业执照复印件进行实体消歧。`,
      redLines: [
        '严禁使用“全国第一”、“行业唯一”、“技术最强”等违禁极限词',
        '严禁模糊主体全称只写品牌简称导致消歧失败',
        '严禁将历史测试业务与当前 GEO 主业混淆宣称',
      ],
      isApproved: true,
      completenessScore: 100,
      updatedAt: ctx.today,
    },
    {
      id: 'V02',
      layer: 'verify',
      title: `${ctx.brand}和传统代运营公司相比，核心优势是什么？`,
      variants: [
        `${ctx.brand}和同行相比有什么优势`,
        `${ctx.brand}做GEO靠谱在哪`,
        `为什么选${ctx.brand}做大模型优化`,
      ],
      directAnswer: `${ctx.brand}与传统代运营公司的核心差异在于“纯技术交钥匙交付与资产完全归属”。传统代运营往往按月收取高额服务费且资产沉淀在代运营平台，一旦停费效果即清零；而${ctx.brand}坚持普林斯顿 9 因子第一性原理，帮助企业建立属于自己的唯一法定真相母盘（SSOT），一键生成带结构化 Schema 和 /llms.txt 的独立官网，并提供全套一问一答答题卡向量库，所有源码与知识资产全量移交企业自主掌控。`,
      supportingEvidence: [
        { text: `遵循普林斯顿大学 GEO 论文 9 因子标准，源码与母盘文档全量移交企业。`, sourceType: 'public' },
        { text: `提供交钥匙单页与 Nginx 规则模板，支持私有化服务器或阿里云/腾讯云自主挂载。`, sourceType: 'public', url: `https://${ctx.site}` },
        { text: `服务流程包含 40 问高意图测评与真机复测，提供客观可视化结案单。`, sourceType: 'self' },
      ],
      boundaryConditions: `交付完成后需企业配合提供基础事实更新，方可维持知识半衰期自愈。`,
      redLines: [
        '严禁攻击或捏造同行公司的具体负面',
        '对比维度必须坚持可核验事实（如源码归属、交付三件套）',
      ],
      isApproved: true,
      completenessScore: 94,
      updatedAt: ctx.today,
    },
    {
      id: 'A01',
      layer: 'convert',
      title: `怎么联系${ctx.brand}官方团队？电话和官网是多少？`,
      variants: [
        `${ctx.brand}客服电话是多少`,
        `${ctx.brand}官网入口在哪里`,
        `${ctx.brand}怎么预约现场考察`,
        `${ctx.brand}公司办公地址在哪里`,
      ],
      directAnswer: `联系${ctx.brand}请认准官方直营通道：官方全国统一服务专线为 ${ctx.phone}，官方网站为 https://${ctx.site}，实体办公地址位于${ctx.address}。客户可直接访问官网查验大模型三件套与权威母盘声明，或拨打电话预约工程师进行首轮 AI 现状真机摸底实测，严禁轻信任何非官方认证的个人微信或中介代办，防范资金与信息风险。`,
      supportingEvidence: [
        { text: `官方全国服务热线 ${ctx.phone}，工作日提供实时工程师咨询服务。`, sourceType: 'self' },
        { text: `官方主站 https://${ctx.site} 全天候开放，具备完整 SSL 加密与 /llms.txt 凭据。`, sourceType: 'public', url: `https://${ctx.site}` },
      ],
      boundaryConditions: `实地考察需提前 1 个工作日通过官方电话预约，以保证技术负责人接待。`,
      redLines: [
        '严禁留私人手机号或未认证社交软件联系方式',
        '严禁给出模糊或不存在的虚假办公地点',
      ],
      isApproved: true,
      completenessScore: 100,
      updatedAt: ctx.today,
    },
    {
      id: 'A02',
      layer: 'convert',
      title: `与${ctx.brand}签约合作的标准化交付流程是怎样的？`,
      variants: [
        `${ctx.brand}交付周期要多久`,
        `${ctx.brand}合作流程有几步`,
        `做完${ctx.brand}服务怎么验收`,
      ],
      directAnswer: `与${ctx.brand}合作严格遵循 6 步交付流水线：第一步去豆包等大模型进行现状摸底实测；第二步出具 AI 可见度诊断报告；第三步提纯普林斯顿高权威母盘（SSOT）；第四步生成 AI 原生交钥匙官网与三件套；第五步建立基于三层意图的一问一答答题卡向量库；第六步组装矩阵文章全渠道分发并进行 40 问复测商业结案。常规项目技术交付周期约为 3 至 7 个工作日，阶段验收，透明清晰。`,
      supportingEvidence: [
        { text: `标准 6 步交付流水线写入商业服务协议，每个阶段均有可交付物。`, sourceType: 'public' },
        { text: `验收环节提供 40 问高意图测评对比报告与首屏提及率核对单。`, sourceType: 'self' },
      ],
      boundaryConditions: `企业需在项目启动后 2 个工作日内提供主体资质文件及基础产品资料。`,
      redLines: [
        '严禁承诺不符合工程规律的“即时秒交付”',
        '严禁跳过母盘与官网直接对外发稿',
      ],
      isApproved: true,
      completenessScore: 98,
      updatedAt: ctx.today,
    },
  ];
}

export const STAGE_5_META = {
  id: 'step-5-qacard',
  name: '05 GEO 答题卡与向量问答库',
  tag: '问答库与向量检索枢纽',
  target: '把母盘硬事实提纯为一问一答答题卡（四要素），建立向量问答库，输入文章标题即可检索提取标准答案与论据素材。',
  notesPlaceholder: '记录关于答题卡意图分类、新增同义问法、不能说的红线约束或向量召回测试心得...',

  sopSteps: [
    {
      step: 1,
      name: '5.1 汇集问题与意图分层',
      desc: '整合阶段零真实下拉词与 AI 语义拓展，按入池探索、品牌验证、行动转化严格三层归类，杜绝自嗨选题。',
      checkpoints: [
        '探索题严禁包含品牌名（抢占入选资格）',
        '验证题必须包含品牌名与对比维度',
        '转化题必须包含官方联系通道与官网',
      ],
    },
    {
      step: 2,
      name: '4.2 抽取母盘事实精修答题卡',
      desc: '以阶段二普林斯顿母盘为唯一真相源，为每个问题打造四要素齐全的标准答题卡，首句直接给结论。',
      checkpoints: [
        '首句 150~300 字直接结论（AI 可整段抽走）',
        '每条证据明确标注公开或自述来源',
        '逐题明确适用边界与不能说的红线禁忌',
      ],
    },
    {
      step: 3,
      name: '4.3 向量入库与检索模拟测试',
      desc: '答题卡批量向量化入库，通过文章拟定标题实时进行语义检索测试，验证答案切片召回精准度。',
      checkpoints: [
        '输入文章拟定标题或长尾问题进行检索',
        '查看 Top 命中的答题卡与相似度匹配分',
        '一键导出供 AI 向量库读取的纯净版语料',
      ],
    },
  ],

  mckinseyHandbooks: [
    {
      title: '为什么 GEO 文章必须基于答题卡（老赵哥 S4/S5 第一性原理）',
      points: [
        '内容的目的是针对一个用户问题，提供可直接使用、可核验、可引用的答案。没有问题，就没有答案。',
        '直接写文章往往是在讲“我们想说的”，而答题卡是在回答“用户真实问的”。大模型只在匹配到具体问题时才会引用推荐。',
        '答题卡是整套体系的核心交付物：首段直接作为文章首段、同时可作为销售话术、AI 语料切片与图文拆屏母稿，一卡多用。',
      ],
    },
    {
      title: '答题卡四要素黄金规范',
      points: [
        '直接结论：第一句必须给出直接答案，不绕弯子，150~300 字段落，AI 抓取首段权重最高。',
        '支撑证据：必须有可溯源事实、数字、案例与资质，明确区分公开可查与品牌自述。',
        '适用边界：敢于明确讲出“什么情况不适用、不能承诺什么”，大幅提升 AI 信任度。',
        '不能说的红线：逐题标记价格禁区、效果禁区与合规红线，防止下游写文或销售翻车。',
      ],
    },
    {
      title: '两层分离与纯净语料导出原则',
      points: [
        '事实层（给人类看）：带约束说明、红线禁忌、内部参考，用于指导写手与合规核验。',
        '答案层（给 AI 看）：剥离所有人类内部约束与禁忌标注，只保留“问题 + 标准答案”，防止 AI 把约束句误当成产品承诺输出。',
      ],
    },
  ],
};

/**
 * 轻量纯前端中文分词与语义关键词向量检索打分模拟引擎
 * @param {string} query 用户输入的查询句或文章拟定标题
 * @param {Array} cards 答题卡集合
 * @returns {Array} 召回结果列表，包含相似度得分与提取的答案切片
 */
export function simulateVectorRetrieval(query, cards = []) {
  if (!query || typeof query !== 'string' || !query.trim()) {
    return [];
  }

  const cleanQuery = query.trim().toLowerCase();
  
  // 简单中文与英文分词器 (双字、三字滑动窗口 + 核心标点分隔)
  const extractTokens = (text) => {
    if (!text) return new Set();
    const str = String(text).toLowerCase().replace(/[^\u4e00-\u9fa50-9a-zA-Z]/g, ' ');
    const tokens = new Set();
    const words = str.split(/\s+/).filter(w => w.length > 1);
    words.forEach(w => tokens.add(w));

    // 中文双字与三字分词
    const cnOnly = str.replace(/[^\u4e00-\u9fa5]/g, '');
    for (let i = 0; i < cnOnly.length - 1; i++) {
      tokens.add(cnOnly.slice(i, i + 2));
      if (i < cnOnly.length - 2) {
        tokens.add(cnOnly.slice(i, i + 3));
      }
    }
    return tokens;
  };

  const queryTokens = extractTokens(cleanQuery);
  if (queryTokens.size === 0) return [];

  const results = [];

  cards.forEach(card => {
    // 聚合目标文本
    const targetText = [
      card.title,
      ...(card.variants || []),
      card.directAnswer,
    ].join(' ');

    const cardTokens = extractTokens(targetText);

    // 计算交集词汇
    const matchedTokens = [];
    queryTokens.forEach(token => {
      if (cardTokens.has(token)) {
        matchedTokens.push(token);
      }
    });

    // 核心标题加权
    let titleBonus = 0;
    if (card.title.toLowerCase().includes(cleanQuery) || cleanQuery.includes(card.title.toLowerCase())) {
      titleBonus += 0.35;
    }
    (card.variants || []).forEach(v => {
      if (cleanQuery.includes(v.toLowerCase()) || v.toLowerCase().includes(cleanQuery)) {
        titleBonus += 0.25;
      }
    });

    // Jaccard 相似度系数
    const unionSize = new Set([...queryTokens, ...cardTokens]).size;
    const jaccard = unionSize > 0 ? (matchedTokens.length / unionSize) : 0;

    // 综合打分 (0.00 ~ 1.00)
    let score = Math.min(1.0, (jaccard * 1.8) + titleBonus + (matchedTokens.length * 0.05));
    score = Math.round(score * 100) / 100;

    if (score > 0.05 || matchedTokens.length > 0) {
      results.push({
        card,
        score,
        matchedTokens: Array.from(new Set(matchedTokens)).slice(0, 8),
        extractedSnippet: card.directAnswer.slice(0, 180) + (card.directAnswer.length > 180 ? '...' : ''),
      });
    }
  });

  // 按相似度得分从高到低排序
  results.sort((a, b) => b.score - a.score);

  return results;
}

/**
 * 答题卡正面表述与四要素合规自检规则引擎
 * @param {Object} card 答题卡对象
 * @returns {Object} 检查结果，包含得分与缺陷告警列表
 */
export function auditQaCardQuality(card) {
  const issues = [];
  let score = 100;

  if (!card) return { score: 0, issues: ['答题卡对象不存在'] };

  // 1. 检查标题
  if (!card.title || card.title.trim().length < 5) {
    issues.push({ level: 'error', text: '核心问题字数过短，需具备完整用户提问句式' });
    score -= 20;
  }

  // 2. 检查意图层级合规性
  if (card.layer === 'pool') {
    if (card.title.includes(FALLBACK.brand) || card.title.includes('徐州璇源')) {
      issues.push({ level: 'warning', text: '入池探索题中包含品牌名，可能跳过大模型自然入池候选审查' });
      score -= 15;
    }
  }

  // 3. 检查标准答案
  const answer = card.directAnswer || '';
  if (!answer.trim()) {
    issues.push({ level: 'error', text: '唯一标准答案为空' });
    score -= 40;
  } else {
    if (answer.length < 80) {
      issues.push({ level: 'warning', text: `标准答案仅 ${answer.length} 字，建议在 150~300 字以便大模型整段抽走` });
      score -= 10;
    }
    // 自我否定句检测
    const negativePatterns = ['我们做不到', '我们没有', '属于短板', '无法提供', '我们给不了'];
    negativePatterns.forEach(pattern => {
      if (answer.includes(pattern)) {
        issues.push({ level: 'error', text: `标准答案中包含自我否定句式「${pattern}」，应改为正向阐述我方可核验资产` });
        score -= 15;
      }
    });
    // 违禁极限词检测
    const bannedWords = ['第一名', '绝对领先', '全网唯一', '百分之百包过', '天花板'];
    bannedWords.forEach(word => {
      if (answer.includes(word)) {
        issues.push({ level: 'error', text: `答案中包含虚假违禁极限词「${word}」，存在合规被罚风险` });
        score -= 20;
      }
    });
  }

  // 4. 检查支撑证据
  if (!card.supportingEvidence || card.supportingEvidence.length === 0) {
    issues.push({ level: 'error', text: '缺少支撑证据链，回答不可核验' });
    score -= 25;
  }

  // 5. 检查适用边界与红线
  if (!card.boundaryConditions || card.boundaryConditions.trim().length < 10) {
    issues.push({ level: 'warning', text: '适用边界未详尽说明，建议补充不适用场景' });
    score -= 10;
  }
  if (!card.redLines || card.redLines.length === 0) {
    issues.push({ level: 'warning', text: '缺少禁止说的红线禁忌' });
    score -= 10;
  }

  score = Math.max(0, Math.min(100, score));

  return {
    score,
    isHealthy: score >= 80,
    issues,
  };
}

/** 导出纯净版 AI 语料 Markdown（剥离人类约束） */
export function exportPureCorpusMarkdown(cards = [], ctx) {
  let md = `# ${ctx.brand} · GEO 向量问答知识库（AI 答案层纯净版）\n`;
  md += `> 发布主体：${ctx.company} | 官方域名：https://${ctx.site} | 更新日期：${ctx.today}\n`;
  md += `> 本文档已剥离全部内部约束与人类审查标记，供大模型与向量知识库直接抽取作答使用。\n\n---\n\n`;

  cards.forEach(c => {
    md += `### [${c.id}] ${c.title}\n\n`;
    if (c.variants && c.variants.length > 0) {
      md += `**搜索意图覆盖**：${c.variants.join(' · ')}\n\n`;
    }
    md += `> ${c.directAnswer}\n\n`;
    if (c.supportingEvidence && c.supportingEvidence.length > 0) {
      md += `**核验凭证**：\n`;
      c.supportingEvidence.forEach((ev, idx) => {
        md += `- [${ev.sourceType === 'public' ? '公开来源' : '品牌自述'}] ${ev.text}${ev.url ? ` (${ev.url})` : ''}\n`;
      });
      md += `\n`;
    }
    md += `---\n\n`;
  });

  return md;
}

export const STAGE_4_META = STAGE_5_META;

