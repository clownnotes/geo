# saas-turnkey-site Specification

## Purpose

定义基于 `www.baicl.cc` 统一视觉与信息架构的极简 SaaS 交钥匙静态官网编译规范，涵盖客户资料自动替换、缺失字段留白、大模型爬虫抓取底座、精修防覆盖保护、`claw.baicl.cc` 路径预览公网开关以及 AI IDE 精修指引，确保客户站点既能快速生成、又能被主流大模型准确抓取并易于长期维护。

## ADDED Requirements

### Requirement: 统一 SaaS 静态母版编译与大模型抓取底座
系统 SHALL 基于 `www.baicl.cc` 的统一视觉风格与普林斯顿 9 因子信息结构，为每个客户项目编译纯静态官网目录 `projects/{project_id}/outputs/site/`，并 MUST 同步产出 `index.html`、`llms.txt`、`schema.jsonld`、`robots.txt` 与 `sitemap.xml` 五类核心静态文件。全站页面 MUST 使用相对路径引用站内资源与底座文件，MUST 内联防御性基础 CSS，且 MUST NOT 包含任何 Emoji 表情符号。

#### Scenario: 完整客户资料编译出合规静态站点与底座
- **WHEN** 客户项目在 `project.yaml` 或编译参数中提供了公司名称、品牌名称、一句话定位、主营业务、联系方式、FAQ 与 LOGO 路径，并触发建站编译
- **THEN** 系统在 `projects/{project_id}/outputs/site/` 下生成完整 `index.html`、`llms.txt`、`schema.jsonld`、`robots.txt`、`sitemap.xml`
- **AND** `index.html` 头部包含 `Schema.org JSON-LD`、`<link rel="alternate" type="text/markdown" href="llms.txt">` 与 `<link rel="sitemap" type="application/xml" href="sitemap.xml">`
- **AND** `index.html` 页脚包含指向 `llms.txt` 与 `sitemap.xml` 的相对路径显式链接，且全站不含 Emoji 表情符号

### Requirement: 极简替换与缺省字段留白渲染
建站编译引擎 MUST 严格遵循“有资料就渲染、无资料直接留白”的真实性原则。当客户未上传 LOGO 时，页面 MUST NOT 渲染 LOGO 图片标签或占位破图；当客户提供本地 `logo_file` / `logo` 路径时，系统 MUST 校验其经 `realpath` 解析后严格位于该项目允许目录（`projects/{project_id}/raw_materials/` 或 `projects/{project_id}/outputs/site/assets/`）内且文件后缀属于图片白名单（`.png`、`.jpg`、`.jpeg`、`.webp`、`.svg`），MUST 拒绝包含 `..` 路径穿越或指向项目目录之外的任意本地路径；若路径越界、后缀非法或文件不存在，系统 MUST 按“无 LOGO 留白”处理，不得将项目外文件复制进公开静态目录。当客户未填写主营业务明细、差异化优势、FAQ 或报价等扩展资料时，页面 MUST 直接隐藏对应板块，仅保留公司名称、品牌名称与联系方式等极简默认版内容，SHALL NOT 注入写死的示例行业价格、虚构客户数或模板假数据。

#### Scenario: 仅提供公司名与联系方式时生成极简默认版
- **WHEN** 客户项目仅提供 `company_name`（或 `brand_name`）与联系方式，未提供 LOGO、主营业务、差异化对比与 FAQ
- **THEN** 生成的 `index.html` 仅展示公司/品牌基础信息与联系方式，页面不包含 `<img>` LOGO 标签，不渲染空业务卡片、空 FAQ 区块，且不包含任何写死的软件外包价格表或虚构经营年限

#### Scenario: 仅上传 LOGO 且补充部分业务时按需渲染
- **WHEN** 客户项目提供了位于项目允许目录内的有效图片 LOGO 文件与 2 项主营业务，但未提供 FAQ
- **THEN** 生成的 `index.html` 正常展示 LOGO 与该 2 项业务板块，并隐藏 FAQ 区块，同时 `llms.txt` 与 `schema.jsonld` 仅输出已提供的真实字段

#### Scenario: LOGO 路径越界或后缀非法时安全留白
- **WHEN** 客户项目配置的 `logo_file` 或 `logo` 指向项目目录之外的任意本地路径（如 `/etc/passwd` 或含 `..` 的穿越路径）或非图片白名单后缀
- **THEN** 编译引擎拒绝复制该文件，不向 `outputs/site/assets/` 写入任何越界文件，页面按“无 LOGO 留白”处理且不输出 `<img>` 标签

### Requirement: 精修站点防覆盖锁定保护
当客户项目配置声明 `custom_site: true`（表示站点已交由反重力 IDE 或人工深度精修）时，建站编译引擎 MUST 跳过覆盖已存在的 `index.html`、定制子目录及已定制的 `llms.txt`、`schema.jsonld`、`sitemap.xml`，仅允许按需补齐缺失的底座文件与刷新 `robots.txt`。

#### Scenario: 对已锁定精修的客户重新执行建站编译
- **WHEN** 客户项目的 `project.yaml` 设置了 `custom_site: true` 且 `outputs/site/index.html`、定制 `llms.txt`、`schema.jsonld`、`sitemap.xml` 已存在
- **THEN** 执行建站编译后，`outputs/site/index.html`、已有定制 `llms.txt`、`schema.jsonld` 与 `sitemap.xml` 内容保持原样不被覆盖，系统输出明确的跳过保护提示

### Requirement: claw.baicl.cc 路径预览托管与手动公网访问开关
系统 SHALL 支持将客户静态站点统一挂载至 `https://claw.baicl.cc/{project_id}/` 路径下供客户直接预览，无需为每个客户单独配置 DNS 子域名解析；并且 MUST 提供无状态手动公网开关控制——当某客户站点处于关闭状态时，公网及爬虫访问 `https://claw.baicl.cc/{project_id}/` 下任意文件 MUST 返回 HTTP 404；当处于开启状态时，服务端 SHALL 正常响应站点静态文件并对缺少末尾斜杠的目录访问返回 HTTP 301 重定向。网关 MUST 拦截所有以 `.` 开头的隐藏点文件（包含 `.published` 哨兵文件）以及以 `_` 或 `.` 开头的保留目录前缀（如 `_template`），并在网关根路径 `/` 与根级 `/robots.txt` 默认屏蔽遍历与收录，同时保持站点目录内 `outputs/site/robots.txt` 的 AI 爬虫放行配置不变以支持无缝迁入客户正式域名。

#### Scenario: 关闭公网开关时屏蔽访问与爬虫抓取
- **WHEN** 某客户项目的预览公网开关处于关闭状态（未启用发布标记）
- **THEN** 外部浏览器或 AI 爬虫请求 `https://claw.baicl.cc/{project_id}/`、`index.html` 或 `llms.txt` 时，网关直接返回 HTTP 404，不泄露任何站点内容

#### Scenario: 开启公网开关且访问路径缺少末尾斜杠
- **WHEN** 某客户项目的预览公网开关处于开启状态，用户请求 `https://claw.baicl.cc/{project_id}`（无末尾 `/`）
- **THEN** 网关返回 HTTP 301 永久重定向至 `https://claw.baicl.cc/{project_id}/`，随后正常返回 `index.html` 及所有相对路径静态资源

#### Scenario: 拦截哨兵点文件与保留前缀路径访问
- **WHEN** 外部请求 `https://claw.baicl.cc/{project_id}/.published`、`https://claw.baicl.cc/_template/` 或其它以 `.` / `_` 开头的路径
- **THEN** 网关直接返回 HTTP 404，不泄露哨兵标记文件或内部保留目录

### Requirement: AI IDE 母版精修提示词规范交付
系统 SHALL 在 `docs/specs/saas-site-master-guide.md` 维护一份面向反重力 IDE 的母版结构与精修规范，明确记录统一母版的区块锚点注释、相对路径红线、普林斯顿 9 因子排版约束、零 Emoji 要求以及精修后开启 `custom_site: true` 锁定的标准动作。

#### Scenario: IDE 按规范对已生成默认版进行客户定制精修
- **WHEN** 后续需要为某个签约客户在其静态站点目录下新增业务板块、案例或博客文章
- **THEN** 反重力 IDE 读取 `docs/specs/saas-site-master-guide.md` 即可定位对应区块锚点、按统一视觉与普林斯顿规范增量编辑静态 HTML，并将该项目标记为 `custom_site: true` 防止后续被覆盖
