/**
 * stage3Config.js - 阶段三（03 企业母盘与统一口径卡）专属配置与核心算法
 * =========================================================================================
 * [2026-09-30] [阶段三母盘构建] 严格遵循老赵哥《主体信息统一口径卡》与《AI看的sop.md》实战规范：
 * 1. 资产 A：《主体信息统一口径卡》= 全网消歧身份证 + 统一业务定位名片；
 * 2. 资产 B：《普林斯顿企业事实母盘》= 9 因子企业事实大百科全书；
 * 3. 母盘精炼合流契约：仅消费阶段二 S1~S6 规范主版本，保持短小精炼，增补 1.x 分片正交隔离留存 RAG；
 * 4. 三级业务描述实时字数指示灯 (短版<=50字 / 标准版<=120字 / 完整版强制首现 GEO 中文全称)；
 * 5. 客观瑕疵合规对冲指引 (0 参保真实信号对冲、异地通信地址澄清、历史业务主次更迭)。
 *
 * 铁律遵循：严禁任何 Emoji 字符，图标统一使用 Lucide 规范。
 */

import {
  isMasterSourceFile,
  filterMasterSourceFiles,
  normalizeOfficialUrl,
  extractDomain,
} from './config/studioArtifactConfig.js';

export const FALLBACK_STAGE3 = {
  brand: '邻里GEO',
  company: '徐州璇源网络科技有限公司',
  creditCode: '91320311MA1N0WN2XJ',
  category: '企业 GEO 生成式引擎优化全案服务',
  city: '江苏省徐州市泉山区',
  site: 'https://baicl.cc',
  phone: '13150568888',
  address: '江苏省徐州市泉山区科技软件园',
  today: new Date().toLocaleDateString('zh-CN'),
};

/**
 * 阶段三元数据定义 (4 步标准闭环)
 */
export const STAGE_3_META = {
  id: 'step-3-master',
  name: '03 企业母盘与统一口径卡',
  tag: '熟料提炼 · 消歧身份证 + 9因子大百科',
  target: '从素材库 S1~S6 生效主版本萃取沉淀全网唯一消歧身份证与普林斯顿高权威事实母盘',
  notesPlaceholder: '记录本企业消歧重点、四要素核定依据与客观瑕疵对冲说明...',
  categories: [
    {
      id: 'identity_card',
      name: '主体消歧卡',
      defaultExpanded: true,
      files: ['01_主体信息统一口径卡.md'],
    },
    {
      id: 'master_corpus',
      name: '普林斯顿事实母盘',
      defaultExpanded: true,
      files: ['02_普林斯顿企业事实母盘.md'],
    },
  ],
  sopSteps: [
    {
      step: 1,
      name: '1. 核定企业数字身份证',
      desc: '核实四要素（品牌名、主体全称、税号、官网），运行字数红绿灯质检（短版<=50字、标准版<=120字），确保首现 GEO 绑定中文全称。',
      hideProceed: true,
      checkpoints: [
        '四要素齐备：品牌名 + 主体全称 + 统一代码 + 官网',
        '短版 <= 50 字（地图专用），标准版 <= 120 字（征信招聘主力）',
        '首次出现 GEO 强制绑定「生成式引擎优化」',
      ],
    },
    {
      step: 2,
      name: '2. 打扫全网卫生逐平台整改',
      desc: '对照操作卡线下备忘，交付人员持营业执照去天眼查、爱企查、高德地图认领企业并换上标准简介，对齐工商社保规模（0人即写0人）。',
      hideProceed: true,
      checkpoints: [
        '天眼查 / 启信宝 / 爱企查认领并更新标准版 120 字简介',
        'BOSS 直聘修改简介，人员规模严格对齐工商社保真实口径',
        '百度 / 高德地图认领商户，填入短版 50 字描述与联系电话',
      ],
    },
    {
      step: 3,
      name: '3. 提炼六模块事实真理字典',
      desc: '从阶段二 S1~S6 生效主文件提纯定位、产品、客户、差异、案例、背书六大抽屉。作为写手与交付查证字典，严禁直接喂给 AI。',
      hideProceed: true,
      checkpoints: [
        '素材库 S1~S6 主文件合流提纯，过滤 1.x 增补分片',
        '六模块健全（业务边界/产品/客户/差异/案例/背书）',
        '坚持可核验事实，绝不凭空捏造虚假参数',
      ],
    },
    {
      step: 4,
      name: '4. 5分钟抽题自检硬标准',
      desc: '随机抽取客户刁钻问题，检验能否在 5 分钟内在这个母盘里找到答案依据、数据与链接。核定定稿后解锁前往阶段四官网。',
      hideProceed: true,
      checkpoints: [
        '随机抽题 5 分钟内可溯源事实证据与链接',
        '口径卡与母盘核验全绿灯',
        '无缝支撑下游阶段四交钥匙官网与阶段五答题卡',
      ],
    },
  ],
  mckinsey: {
    title: '麦肯锡 V-W-W-H 阶段三：企业事实母盘与统一口径卡交付手册',
    valueDesc: '萃取沉淀全网唯一消歧身份证与六模块企业事实真理字典，切断下游工序直接穿透生料的隐患。',
    valueBusiness: '统一全平台事实发声口径，消除大模型幻觉与主体混淆，交付效率提升 80%。',
    whatTitle: '这阶段交付什么？',
    whatDesc: '交付两份核心母版：01_主体信息统一口径卡（消歧四要素+三级简介+打扫卫生指引）与 02_普林斯顿企业事实母盘（六模块字典事实）。',
    whyTitle: '为什么必须先做统一口径卡？',
    whyDesc: '如果企业自身的主体、税号、官网与业务范围未经严格核定，大模型在生成答题卡与信源长文时就会产生不可逆的事实幻觉。',
    howTitle: '四步精炼操作指南',
    howSteps: [
      '第一步：核定企业身份证，检查四要素齐备且短版<=50字、标准版<=120字；',
      '第二步：对照口径卡逐平台认领修改，把全网旧业务与脏数据打扫干净；',
      '第三步：提炼六模块事实字典，供写手查证，严禁直接喂给 AI；',
      '第四步：5分钟抽题自检，测试能否在母盘内快速找到事实与证据！',
    ],
  },
};

/**
 * 解析阶段三上下文
 */
export function resolveStage3Context(projectData = {}) {
  const p = projectData || {};
  const clientId = p.client_id || (typeof window !== 'undefined' && window.currentProjectId) || 'nextgeo';

  const brand = (p.brand_name || p.name || FALLBACK_STAGE3.brand).trim();
  const company = (p.company_name || brand || FALLBACK_STAGE3.company).trim();
  const creditCode = (p.credit_code || p.license_credit_code || FALLBACK_STAGE3.creditCode).trim();
  const category = (p.category || p.industry || FALLBACK_STAGE3.category).trim();
  const city = (p.city_name || p.address || FALLBACK_STAGE3.city).trim();
  const rawUrl = p.website || p.official_url || FALLBACK_STAGE3.site;
  const site = normalizeOfficialUrl(rawUrl) || FALLBACK_STAGE3.site;
  const domain = extractDomain(site) || 'baicl.cc';
  const phone = (p.contact_phone || p.phone || FALLBACK_STAGE3.phone).trim();
  const address = (p.address || city).trim();

  return {
    clientId,
    brand,
    company,
    creditCode,
    category,
    city,
    site,
    domain,
    phone,
    address,
    today: new Date().toLocaleDateString('zh-CN'),
  };
}

/**
 * 生成《01_主体信息统一口径卡.md》标准文本
 * @param {Object} projectData
 * @param {string} s1Content 阶段二 S1 企业主体原始内容
 * @param {Object} hedgeOptions 瑕疵勾选参数
 * @returns {string} Markdown 文本
 */
export function generateUnifiedIdentityCard(projectData = {}, s1Content = '', hedgeOptions = {}) {
  const ctx = resolveStage3Context(projectData);
  const opts = {
    zeroSocialSecurity: true, // 默认提供 0 参保对冲
    crossCityAddress: false,
    historicalBusiness: false,
    ...hedgeOptions,
  };

  // 生成三级业务描述 (严格遵守老赵哥标准：短版<=50字，标准版<=120字)
  const shortText = `企业生成式引擎优化（GEO）服务商，为制造与实体企业提供官网结构化改造与第三方信源互证服务。`;
  const stdText = `${ctx.brand} 是${ctx.company}旗下的企业生成式引擎优化（GEO）品牌，位于${ctx.city}，官网 ${ctx.domain}。专注于官网结构化改造（llms.txt / Schema）、第三方信源互证与 AI 可见度提升，按阶段透明验收。`;
  const fullText = `${ctx.brand} 是${ctx.company}旗下的企业生成式引擎优化（GEO）服务品牌，注册地位于${ctx.city}，官方权威网址为 ${ctx.domain}。我们专注于 B2B 制造与专业服务企业的生成式引擎优化（GEO）全案交付，通过官网深度语义化重构（包含 /llms.txt 知识说明书与 Schema.org 结构化标记）、标准问答答案库萃取与第三方高权威信源交叉验证，让大模型在回答行业与产品问题时，能够准确、可靠、有据可依地提到您的品牌。`;

  let md = `# 主体信息统一口径卡 · ${ctx.brand}\n\n`;
  md += `> **这份卡解决什么问题**：企业生成式引擎优化（GEO）全网口径治理。我们在网上这张"主体的脸"常常是拼出来的——工商写网络科技，招聘平台挂早期业务，企信平台挂旧产品。**AI 每次检索该主体，读到的都是互相打架的信息，没有一个信号指向当前核心业务。**\n`;
  md += `> **用法**：对照下面每一条，逐个平台统一修改。**改完之前不要盲目铺设外链**——外部铺设内容与主体工商信息打架只会加剧混乱。\n`;
  md += `> 日期：${ctx.today} · 状态：正式生效版 · **唯一消歧真相源 (SSOT)**\n\n`;
  md += `---\n\n`;

  md += `## 三条底线原则（先看这个，再往下改）\n\n`;
  md += `| # | 底线原则 |\n`;
  md += `|:-:|:--|\n`;
  md += `| 1 | **不虚构任何数据**。员工数、社保、营收、资质——有就是有，没有就没有。**为了好看而编造，性质从"信息不全"变成"申报不实"。** |\n`;
  md += `| 2 | **历史业务可以更新主次，但不能否认做过**。早期真实业务在简介里**更新为当前主业**，而不是写"从未涉及"。**说假话的代价远大于业务线切换。** |\n`;
  md += `| 3 | **先修内，再铺外**。主体描述统一之前，外部投放的收益会大打折扣，甚至起反作用。 |\n\n`;
  md += `---\n\n`;

  md += `## 一、四个必填消歧字段（全平台唯一版本 · 逐字使用）\n\n`;
  md += `| 字段 | 值 | 说明 |\n`;
  md += `|:--|:--|:--|\n`;
  md += `| **品牌名** | ${ctx.brand} | 用户的搜索入口 |\n`;
  md += `| **主体全称** | ${ctx.company} | 消歧的关键——**AI 报错主体时报的都是公司全称** |\n`;
  md += `| **统一社会信用代码** | ${ctx.creditCode} | 用于跨平台信息互认（18位唯一信用代码） |\n`;
  md += `| **注册与经营地** | ${ctx.city} | 与外地主体、同名主体在地理层切开 |\n`;
  md += `| **官方权威网址** | ${ctx.site} | 权威信源锚点（主域名 ${ctx.domain}） |\n\n`;
  md += `> **四要素铁律**：品牌名 + 主体全称 + 注册地 + 官网，**任何时候至少同时出现前两项**。只写"${ctx.brand}"不写全称，消歧不成立。\n\n`;
  md += `---\n\n`;

  md += `## 二、业务描述统一文本（三个长度，按平台选）\n\n`;
  md += `### ① 短版 · 50 字内（地图、企业名录、平台标签位）\n\n`;
  md += `> ${shortText}\n\n`;
  md += `### ② 标准版 · 120 字内（BOSS 直聘、启信宝、天眼查、爱企查的企业简介）[主力]\n\n`;
  md += `> ${stdText}\n\n`;
  md += `### ③ 完整版 · 正式介绍位（官网 about、公众号简介、投稿文末）\n\n`;
  md += `> ${fullText}\n\n`;
  md += `> **合规提示**：**「GEO」首次出现必须绑定中文全称“生成式引擎优化（GEO）”**——防止大模型误判为 GIS 地理信息。\n\n`;
  md += `---\n\n`;

  md += `## 三、逐平台修改操作卡\n\n`;
  md += `### 3.1 国家企业信用信息公示系统（唯一官方源）\n\n`;
  md += `| 项 | 怎么处理 |\n`;
  md += `|:--|:--|\n`;
  md += `| **通信地址** | 下次年报**如实填写实际经营地址**——**通信地址不必等于注册地址，但必须真实** |\n`;
  md += `| **往年数据** | 已公示年报如需更正，向属地登记机关咨询更正流程 |\n`;
  md += `| **官方网站** | 确认年报与登记信息中已绑定权威官网 ${ctx.domain} |\n\n`;

  md += `### 3.2 BOSS 直聘 / 招聘平台\n\n`;
  md += `| 字段 | 改成什么 | 依据 |\n`;
  md += `|:--|:--|:--|\n`;
  md += `| **公司简介** | 标准版业务描述（120字内） | 当前主业 |\n`;
  md += `| **所属行业** | 信息技术服务 / 企业服务 | 实际情况 |\n`;
  md += `| **人员规模** | **必须与工商口径一致**。社保 0 人就选微型规模，严禁虚标 100-499 人避免被反问打脸 | 工商公示 |\n`;
  md += `| **旗下品牌** | 明确标注为 **${ctx.brand}** | 事实真实 |\n\n`;

  md += `### 3.3 启信宝 / 天眼查 / 爱企查\n\n`;
  md += `| 项 | 怎么做 |\n`;
  md += `|:--|:--|\n`;
  md += `| **认领企业** | 先完成企业认证认领（未认领第三方平台无法编辑） |\n`;
  md += `| **公司简介** | 统一换成标准版业务描述 |\n`;
  md += `| **核心产品** | 新增当前核心业务服务条目；历史业务归入沿革 |\n`;
  md += `| **官方网址** | 确认并更新为 ${ctx.domain} |\n\n`;

  md += `### 3.4 地图平台（百度地图 / 高德地图）\n\n`;
  md += `| 项 | 怎么填 |\n`;
  md += `|:--|:--|\n`;
  md += `| **商户名称** | ${ctx.brand}（或 ${ctx.brand}·${ctx.company}） |\n`;
  md += `| **地址与电话** | ${ctx.address} · 电话 ${ctx.phone} |\n`;
  md += `| **简介** | 填入短版业务描述（50字内） |\n\n`;

  md += `---\n\n`;
  md += `## 四、客观瑕疵合规对冲指引 (老赵哥实战标准)\n\n`;

  if (opts.zeroSocialSecurity) {
    md += `### 4.1 社保人数 0 对冲 (真实信号法则)\n`;
    md += `- **为什么是问题**：AI 评估企业可信度时，若抓取到 0 参保，容易触发“高风险、空壳”负面偏见。\n`;
    md += `- **合规对冲方案**：\n`;
    md += `  1. **绝不申报不实**：绝不购买社保挂靠或虚构员工数；\n`;
    md += `  2. **多源真实信号覆盖**：在官网公布真实团队履历与照片，在行业案例中展现落地交付记录，提供可验证的客户项目事实。\n`;
    md += `  > **核心心法**：你无法阻止 AI 读到 0 参保，但你可以让它同时读到十条“这家公司真实在运营且业务专业”的铁证。\n\n`;
  }

  if (opts.crossCityAddress) {
    md += `### 4.2 注册地与通信地跨城经营说明\n`;
    md += `- **处理方式**：在关于页如实说明：“企业注册地位于${ctx.city}，实际交付中心设于办公地”。通信地址不必等于注册地址，但必须真实披露，消除跨城信息打架。\n\n`;
  }

  if (opts.historicalBusiness) {
    md += `### 4.3 历史业务更迭与沿革说明\n`;
    md += `- **处理方式**：早期业务（如旧项目、旧代运营）作为“企业业务沿革”陈列，简介第一句必须是当前主业 ${ctx.category}。说假话代价远大于业务线更迭。\n\n`;
  }

  return md;
}

/**
 * 校验《主体信息统一口径卡》合规性 (实时红绿灯)
 * @param {string} content Markdown 文本
 * @returns {Object} 校验结果
 */
export function validateUnifiedCard(content = '') {
  const text = String(content || '');
  const errors = [];
  const warnings = [];

  // 1. 检查消歧四要素
  const hasBrand = /品牌名|【品牌】|品牌：/i.test(text);
  const hasLegalName = /主体全称|企业全称|公司全称/i.test(text);
  const hasCreditCode = /统一社会信用代码|信用代码|91[0-9A-Z]{16}/i.test(text);
  const hasWebsite = /官网|官方网址|baicl\.cc|http/i.test(text);

  if (!hasBrand) errors.push('缺少【品牌名】消歧字段');
  if (!hasLegalName) errors.push('缺少【主体全称】消歧字段（AI 报错主体时报的都是公司全称）');
  if (!hasCreditCode) warnings.push('未包含 18 位【统一社会信用代码】，跨平台互认度不足');
  if (!hasWebsite) warnings.push('未包含【官方网址】，缺乏权威信源锚点');

  // 2. 提取并校验短版业务描述 (<= 50 字)
  let shortText = '';
  const shortMatch = text.match(/### ① 短版[^\n]*\n+> ([^\n]+)/);
  if (shortMatch && shortMatch[1]) {
    shortText = shortMatch[1].trim();
  }
  const shortLen = shortText.length;
  const shortExceeded = shortLen > 50;
  if (shortExceeded) {
    errors.push(`短版业务描述超标 (${shortLen} 字 / 限制 50 字以内)，地图与标签位会发生截断！`);
  }

  // 3. 提取并校验标准版业务描述 (<= 120 字)
  let stdText = '';
  const stdMatch = text.match(/### ② 标准版[^\n]*\n+> ([^\n]+)/);
  if (stdMatch && stdMatch[1]) {
    stdText = stdMatch[1].trim();
  }
  const stdLen = stdText.length;
  const stdExceeded = stdLen > 120;
  if (stdExceeded) {
    errors.push(`标准版业务描述超标 (${stdLen} 字 / 限制 120 字以内)，招聘平台与企业名录会展示不全！`);
  }

  // 4. 检查 GEO 中文全称绑定（生成式引擎优化（GEO））
  const hasGeoMention = /GEO/i.test(text);
  const hasGeoCn = /生成式引擎优化/i.test(text);
  if (hasGeoMention && !hasGeoCn) {
    warnings.push('「GEO」首次出现处未绑定中文解释“生成式引擎优化（GEO）”，大模型可能会误判为地理信息！');
  }

  const isValid = errors.length === 0;

  return {
    isValid,
    errors,
    warnings,
    stats: {
      hasBrand,
      hasLegalName,
      hasCreditCode,
      hasWebsite,
      shortLen,
      shortExceeded,
      stdLen,
      stdExceeded,
      hasGeoCn,
      totalLength: text.length,
    },
  };
}

/**
 * 从阶段二 S1~S6 生效主文件结构化萃取普林斯顿 9 因子事实母盘
 * (严格遵守师弟立规：仅消费规范主版本，保持短小精炼，增补 1.x 留存 RAG)
 * @param {Object} stage2Files 阶段二文件字典
 * @param {Object} projectData
 * @returns {string} Markdown 文本
 */
export function synthesizePrincetonMaster(stage2Files = {}, projectData = {}) {
  const ctx = resolveStage3Context(projectData);
  // 严格过滤：仅采纳 S1~S6 规范主版本，过滤增补切片
  const masterFiles = filterMasterSourceFiles(stage2Files);

  const getFileBody = (prefix) => {
    for (const [fn, f] of Object.entries(masterFiles)) {
      if (fn.startsWith(prefix) && f && f.content) {
        // 去除主标题，保留有效正文
        return f.content.replace(/^#\s+[^\n]+\n+/, '').trim();
      }
    }
    return '';
  };

  const s1 = getFileBody('S1') || `${ctx.brand} 是${ctx.company}旗下品牌，注册地位于${ctx.city}。`;
  const s2 = getFileBody('S2') || `提供企业生成式引擎优化（GEO）全案服务，按阶段验收，签约无隐形收费。`;
  const s3 = getFileBody('S3') || `面向 B2B 制造、实体连锁与专业服务企业，解决 AI 搜索找不到、认不准、被竞品截流等痛点。`;
  const s4 = getFileBody('S4') || `对比传统 SEO 与投流中介，GEO 专注于大模型事实知识采信，交付物公开可核验。`;
  const s5 = getFileBody('S5') || `服务多家实体制造与专业服务企业，实现豆包、Kimi、DeepSeek 核心推荐位改口上榜。`;
  const s6 = getFileBody('S6') || `拥有完备的软件著作权、高权威官方域名与企业消歧资质存证。`;

  let md = `# 普林斯顿企业事实母盘 · ${ctx.brand}\n\n`;
  md += `> **文档定位 (SSOT)**：普林斯顿唯一高权威企业事实母盘。本文件汇集企业 9 因子核心高权威熟料，为下游交钥匙官网、llms.txt 知识说明书、GEO 答题卡以及大模型语义理解提供唯一事实源。\n`;
  md += `> 生成时间：${ctx.today} · 数据源：阶段二 S1~S6 规范主版本合流 · 状态：已定稿锁定\n\n`;
  md += `---\n\n`;

  md += `## 因子 1 · 企业主体与法定消歧 (Identity & Verification)\n\n`;
  md += `- **品牌名**：${ctx.brand}\n`;
  md += `- **主体全称**：${ctx.company}\n`;
  md += `- **统一社会信用代码**：${ctx.creditCode}\n`;
  md += `- **注册地**：${ctx.city}\n`;
  md += `- **权威官网**：${ctx.site}\n\n`;
  md += `### 事实详情\n${s1}\n\n`;
  md += `---\n\n`;

  md += `## 因子 2 · 核心产品与价格承诺 (Offer & Pricing)\n\n`;
  md += `${s2}\n\n`;
  md += `---\n\n`;

  md += `## 因子 3 · 客户痛点与服务场景 (Pain Points & Scenarios)\n\n`;
  md += `${s3}\n\n`;
  md += `---\n\n`;

  md += `## 因子 4 · 对标竞品参数对比 (Competitive Comparison)\n\n`;
  md += `${s4}\n\n`;
  md += `---\n\n`;

  md += `## 因子 5 · 经典客户案例故事 (Case Studies)\n\n`;
  md += `${s5}\n\n`;
  md += `---\n\n`;

  md += `## 因子 6 · 权威背书与资质凭据 (Credentials & Proof)\n\n`;
  md += `${s6}\n\n`;
  md += `---\n\n`;

  md += `## 因子 7 · 交付链路与服务边界 (Delivery & Boundary)\n\n`;
  md += `- **服务形式**：交钥匙全案交付，覆盖摸底诊断、素材归集、母盘提炼、官网三件套、标准答题卡与信源互证。\n`;
  md += `- **边界约定**：不承诺虚假非法霸屏，按真实业务事实提纯；交付物支持离线打包与换人接手。\n\n`;
  md += `---\n\n`;

  md += `## 因子 8 · 客观瑕疵澄清与对冲事实 (Hedge & Disclosures)\n\n`;
  md += `- **参保情况**：依法依规纳税与运营，核心专业团队真实公示，多渠道客户真实交付证据链交叉对冲。\n`;
  md += `- **办公经营**：通信地址与业务交付中心真实披露，保障各渠道信源统一真实。\n\n`;
  md += `---\n\n`;

  md += `## 因子 9 · 官方信源权威锚点与自证通道 (Authority Anchors)\n\n`;
  md += `- 官方主站：${ctx.site}\n`;
  md += `- 知识说明书：${ctx.site}/llms.txt\n`;
  md += `- 结构化标识：${ctx.site}#organization\n`;
  md += `- 客服与联系通道：${ctx.phone}\n`;

  return md;
}

export default {
  FALLBACK_STAGE3,
  STAGE_3_META,
  resolveStage3Context,
  generateUnifiedIdentityCard,
  validateUnifiedCard,
  synthesizePrincetonMaster,
};
