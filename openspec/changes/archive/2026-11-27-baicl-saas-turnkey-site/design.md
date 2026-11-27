# Design：基于 www.baicl.cc 母版的极简 SaaS 交钥匙官网与可控预览发布

## Context

详见 `proposal.md` 中的 Why 部分。当前 GEO 仓库内存在两个割裂的现状：
1. `projects/nextgeo/outputs/site/`（即 `www.baicl.cc`）已经打磨出高质感 B2B 视觉、内联防御性 CSS、普林斯顿 9 因子排版和完整大模型底座三件套，但它是为单一项目手写的；
2. 负责批量生成客户官网的 `src/tools/geo/scaffold.py` 仍然在使用一套老旧的、写死“徐州本地软件定制价格表”和 Emoji 图标的单页模板，既不能复用 `www.baicl.cc` 的外观，也会在客户资料缺失时塞入大量假数据。

同时，项目遵循“前店（小毛驴）+ 后厂（GEO 仓无状态计算车间）”架构红线：GEO 仓不连 MySQL、不新建管理后台界面，只产出静态母版、无状态编译引擎、Nginx 路由配置模板与规范文档。

---

## 用户核心原话与 AI 技术决定 1 对 1 映射推导链条表

| 序号 | 用户核心原话（第一真理源） | AI 理解与技术决定 | 对应落地点 |
|---|---|---|---|
| 1 | “希望这个网站是在我们 www.baicl.cc 官网基础上，做得一套 SAAS 网站，外观就统一一套” | 从 `projects/nextgeo/outputs/site/index.html` 提取统一色彩、字体、间距、卡片与防御性 CSS，沉淀为唯一母版 `templates/baicl-saas/index.html.tmpl` | `templates/baicl-saas/` |
| 2 | “每个客户上传自己的 LOGO 还有一些什么信息，多数直接通过前面建企业资料抓出来” | `scaffold.py` 优先读取 `projects/{id}/project.yaml` 及 `build_site` 传入参数，自动映射公司名、品牌名、定位、业务、FAQ、联系方式与 LOGO | `src/tools/geo/scaffold.py`、`src/tools/worker/handlers.py` |
| 3 | “如果客户没有自己的资料，就留白，也不要显示 logo，直接作为一个默认版，内容很少，只换个公司名、联系方式这些” | 采用条件区块渲染（空值直接不输出对应 HTML/Markdown/JSON-LD 节点），彻底删除旧模板里写死的软件外包价格表、虚构客户数与 Emoji | `src/tools/geo/scaffold.py` |
| 4 | “核心是要能被 AI 抓，同时也比较简单好维护” | 坚持“一套母版 + 纯静态编译”而非前端 JS 动态拉数据，同步输出 `index.html` + `llms.txt` + `schema.jsonld` + `robots.txt` + `sitemap.xml`，且全站使用相对路径 | `src/tools/geo/scaffold.py` |
| 5 | “刚开始就在我们域名下面生成一个带文件地址的链接，比如 claw.baicl.cc 带一套地址；手动开关，不需要展示点一下关，就不会被公网看到” | 设计 `https://claw.baicl.cc/<project_id>/` 统一路径托管；利用无状态哨兵文件 `outputs/site/.published` 配合 Nginx 校验实现毫秒级开关（无文件即返回 404，无需重启 Nginx） | `deploy/nginx_claw_preview.conf`、`src/tools/geo/scaffold.py` |
| 6 | “至于开关功能、自动发文章等，等需要时在静态页面处理，反重力 2.0 帮客户编辑就行，把提示词写好让 IDE 知道怎么改” | 不在后台过度开发可视化编辑器或模块开关；编写《SaaS 官网母版结构与精修指南》，明确区块 HTML 注释锚点、相对路径与 `custom_site: true` 防覆盖锁 | `docs/specs/saas-site-master-guide.md` |

---

## Goals / Non-Goals

**Goals:**
- 建立唯一统一的 `www.baicl.cc` 风格 SaaS 静态母版，全平台改样式只需改母版一处。
- 实现极简数据替换与严格的“无资料即留白”渲染，0 假数据、0 破图、0 Emoji。
- 保证 100% AI 爬虫友好（静态 HTML + 三重冗余底座 + 相对路径 + 尾斜杠 301）。
- 实现无需新增 DNS 解析的 `claw.baicl.cc/<project_id>/` 预览方案与秒级公网访问开关。
- 沉淀一份清晰、可直接喂给反重力 IDE 的母版精修提示词规范。

**Non-Goals:**
- 不在 GEO 仓或旧 `:8088` 管理台开发任何新的前端可视化拖拽编辑器、配色器或页面开关 UI。
- 不连接 MySQL 数据库，不在 GEO 仓维护平行业务状态表（后续小毛驴前店若需界面开关，只需调用后厂接口同步标记即可）。
- 不在本变更中自动改动线上生产服务器 Nginx 或执行推生产操作（严格遵守生产发布触发协议）。

---

## Decisions

### 决策 1：母版存放位置与模板渲染方式
- **决定**：将统一母版存放在 `templates/baicl-saas/index.html.tmpl`，使用 Python 标准库（字符串占位符 + 结构化区块渲染函数，零新增第三方模板依赖）在 `src/tools/geo/scaffold.py` 中编译输出静态文件。
- **产物目录口径**：以 `projects/{project_id}/outputs/site/` 作为唯一静态托管与 `handle_build_site` 收集入口；为保持对既有脚本的向下兼容，保留对 `outputs/` 根目录同名底座文件（`llms.txt`、`schema.jsonld`、`robots.txt`、`index.html` 及新增 `sitemap.xml`）的同步写入，且两者均受同等 `custom_site: true` 防覆盖保护。
- **理由**：GEO 后厂要求极简好维护，不引入 Jinja2 等额外运行时强依赖也能清晰完成区块级条件渲染；同时将 HTML 骨架独立成模板文件而非硬编码在几百行 Python f-string 里，改外观时直接改模板文件即可，一目了然。
- **备选方案**：继续把 HTML 写在 Python 函数字符串里（缺点：难以维护样式、反重力 IDE 不好直接参考母版结构）。

### 决策 2：极简字段清单、YAML 字典列表解析升级与覆盖参数通道
1. **YAML 解析兼容升级（`src/tools/geo/utils.py`）**：
   - 现状 `parse_simple_yaml` 仅支持扁平键值与纯字符串列表（遇到缩进带 `:` 的行会重置 `current_list_key=None` 并错写为顶层键），无法解析 `projects/xuzhou_xuanyuan/project.yaml` 已有的 `core_business` 字典列表或 `faqs: [{question, answer}]`。
   - 升级方案：在零第三方依赖前提下，基于行缩进追踪升级 `parse_simple_yaml`：遇到顶层 `key:` 且值为空时记录列表/对象上下文；遇到 `- k: v` 及后续更大缩进的 `k2: v2` 时解析为 `dict` 元素并归入当前列表；遇到 `- "文本"` 则保持为 `str` 元素，确保 100% 向下兼容纯字符串列表与扁平标量。`scaffold.py` 消费 `core_business` / `faqs` 时统一兼容 `dict` 项与 `str` 项。
2. **`run_scaffold` 向下兼容签名与 `handle_build_site` 透传覆盖数据流**：
   - 签名：`run_scaffold(project_id: str, overrides: Optional[Dict[str, Any]] = None, publish_preview: Optional[bool] = None) -> Dict[str, Any]`（仅传 `project_id` 的旧调用与 CLI 入口保持 100% 兼容）。
   - `handlers.py` 通道：在 `PROFILE_KEYS` 中补齐 `wechat`、`address`、`company_profile`、`logo`、`logo_file`、`core_business`、`differences`、`core_values`、`faqs`（标量走 `_merge_scalar_fields` 幂等合并，非空结构化覆盖参数透传给 `build_site`）；`handle_build_site(project_id, params)` 从 `params` 提取可选覆盖字典（支持上述字段）及可选 `publish_preview`（`bool | None`），调用 `scaffold.run_scaffold(project_id, overrides=overrides, publish_preview=publish_preview)`。
   - 内存合并规则：`run_scaffold` 先通过 `load_project_config(project_id)` 读取 `project.yaml`，再将 `overrides` 中非空值（非 `None`、非纯空白字符串、非空列表）在内存中合并覆盖至本次编译上下文 `cfg`，不冲掉 `project.yaml` 中未传入的存量字段（如精修词库或 `custom_site`）。
3. **LOGO 路径安全边界**：
   - 仅允许读取经 `os.path.realpath` 解析后严格位于 `projects/{project_id}/raw_materials/` 或 `projects/{project_id}/outputs/site/assets/` 目录内的本地图片文件，且后缀必须属于白名单 `{".png", ".jpg", ".jpeg", ".webp", ".svg"}`；
   - 严禁接受含 `..` 路径穿越或指向项目目录之外的任意系统路径（如 `/etc/passwd`、`.env`）；
   - 合法文件统一复制到 `outputs/site/assets/`（若已在 `outputs/site/assets/` 则直接复用）并渲染 `<img src="assets/...">`；任何越界路径、非法后缀或不存在的文件，一律按“无 LOGO 留白”安全降级，绝不复制越界文件或输出破图。

为保证“有资料就填、没资料就留白”，母版将页面拆为 1 个必填骨架 + 5 个条件留白区块：

| 区块 | 对应字段（来源：`project.yaml` / `overrides`） | 有值时行为 | 缺失/非法时行为（留白规则） |
|---|---|---|---|
| **基础骨架（必有）** | `company_name`、`brand_name`、`telephone` / `wechat` / `address` | 渲染顶部导航品牌名、首屏标题、底部主体与联系方式 | 若未填 `brand_name` 则回退 `company_name`；未填电话/微信/地址中某一项则隐藏该行，不填假号码 |
| **企业 LOGO** | `logo_file` / `logo`（经安全校验后复制到 `outputs/site/assets/`） | 在顶部导航与页脚渲染 `<img src="assets/...">` | **完全不输出 `<img>` 标签**，只显示简洁纯文字品牌名；越界或非法后缀直接留白 |
| **一句话定位与简介** | `slogan`、`company_profile`、`area_served` | 在首屏展示定位副标题与企业简介 | 缺失则不渲染对应 `<p>` 或标签徽章，不拼接假口号 |
| **核心业务区块** | `core_business`（字典列表或字符串列表） | 渲染多列业务卡片（按真实字段渲染，不强塞假价格） | **整块 `<section>` 不输出** |
| **差异化优势区块** | `differences` / `core_values`（列表） | 渲染结构化优势要点卡片 | **整块 `<section>` 不输出** |
| **常见问题 FAQ 区块** | `faqs`（`[{question, answer}]` 或字符串问答列表） | 渲染 FAQ 问答区块，并同步写入 `schema.jsonld` 的 `FAQPage` 与 `llms.txt` | **整块 `<section>` 不输出**，且 `schema.jsonld` 不生成空 `FAQPage` |

### 决策 3：`claw.baicl.cc/<project_id>/` 路径预览与无状态公网开关
- **决定**：采用 **Nginx + 目录哨兵文件 `.published`** 实现公网开关，配合简单命令/函数控制启停：
  - 每个客户站点仍落盘在 `projects/{project_id}/outputs/site/`；
  - 开关开启时：写入 `projects/{project_id}/outputs/site/.published`（内容记录开启时间）；
  - 开关关闭时：删除 `projects/{project_id}/outputs/site/.published`；
  - `deploy/nginx_claw_preview.conf` 配置 `server_name claw.baicl.cc;` 严格门禁规则：
    1. **拦截点文件与隐藏路径**：最优先配置 `location ~ /\. { return 404; }`，确保 `/{project_id}/.published` 等点文件绝对不可被公网直接读取；
    2. **保留前缀隔离**：正则强制 `project_id` 首字符为字母或数字（`[a-zA-Z0-9][a-zA-Z0-9_-]*`），与 `handlers.py:165` 禁 `_` / `.` 开头规则一致，直接拦截 `_template` 等保留目录并返回 404；
    3. **尾斜杠 301 重定向**：匹配 `^/([a-zA-Z0-9][a-zA-Z0-9_-]*)$` → 返回 `301 /$1/`；
    4. **哨兵校验与静态映射（规避 `alias + try_files` 陷阱）**：匹配 `^/([a-zA-Z0-9][a-zA-Z0-9_-]*)/(.*)$`，先校验 `/Users/ne/apps/GEO/projects/$1/outputs/site/.published` 是否存在，**不存在直接 `return 404;`**；存在时采用 `root /Users/ne/apps/GEO/projects;` 配合 `rewrite ^/([a-zA-Z0-9][a-zA-Z0-9_-]*)/(.*)$ /$1/outputs/site/$2 break;` 与 `try_files $uri $uri/index.html =404;`（彻底规避 Nginx `alias` 与 `try_files` 联用引发的路径拼接缺陷）；
    5. **根路径防遍历**：`location = / { return 404; }`，`location = /robots.txt` 返回 `User-agent: *\nDisallow: /`，防止预览域根目录被遍历或收录，而项目内 `/{project_id}/robots.txt` 保持 AI 爬虫放行配置不变。
  - 默认策略：新编译站点默认**关闭**公网展示（仅当显式传入 `publish_preview=True` 或手动开启开关时生成 `.published`），防止半成品默认暴露给公网和爬虫。
- **理由**：不依赖 MySQL、不依赖常驻 Python 网关、不需要每次开关都 reload Nginx，删/建一个空标记文件毫秒级生效，最符合“简单好维护”与“后厂无状态”双重要求。
- **备选方案**：为每个客户配泛解析子域名 `*.baicl.cc`（缺点：泛域名 HTTPS 证书申请与 DNS 管理麻烦，且师弟明确否决）；或者每次改 Nginx 配置文件并 reload（缺点：有误操作把整个 Nginx 搞挂的风险）。

### 决策 4：相对路径、防覆盖保护与平滑迁移至客户独立域名
- **决定**：母版及生成的 `index.html` 中，所有站内链接（`llms.txt`、`sitemap.xml`、`assets/logo.*`）一律使用**相对路径**；`canonical` 与 `sitemap.xml` 中的绝对 URL 仅在配置了真实 `official_url` 时写入，未配置时使用 `https://claw.baicl.cc/{project_id}/`。
- **防覆盖保护（含 `sitemap.xml`）**：当 `project.yaml` 设置 `custom_site: true` 时，`run_scaffold` 必须跳过覆盖已存在的 `index.html`、定制子目录以及已存在的 `llms.txt`、`schema.jsonld`、**`sitemap.xml`**（仅在文件缺失时补齐，并按需刷新 `robots.txt`），确保 `projects/nextgeo/outputs/site/sitemap.xml`（91 行多页地图）等精修资产不被误覆盖。
- **理由**：同一份 `outputs/site/` 文件，先挂在 `claw.baicl.cc/{project_id}/` 预览，将来客户签单后直接拷到他自己的 `ai.客户域名.com/` 下，页面图片和链接 100% 正常不 404。

### 决策 5：面向反重力 IDE 的母版精修规范
- **决定**：在母版 HTML 的每个核心区块前后保留清晰的语义化 HTML 注释锚点（例如 `<!-- SAAS_SECTION:HERO -->`、`<!-- SAAS_SECTION:SERVICES -->`、`<!-- SAAS_SECTION:FAQ -->`、`<!-- SAAS_SECTION:FOOTER -->`），并在 `docs/specs/saas-site-master-guide.md` 写明：
  1. 改哪个目录（`projects/{project_id}/outputs/site/`）；
  2. 怎么新增板块或文章而不破坏视觉风格和相对路径；
  3. 精修完成后必须把 `projects/{project_id}/project.yaml` 设为 `custom_site: true`，确保以后重跑编译不会覆盖精修成果。

---

## Risks / Trade-offs

- **[Risk] 部分老测试脚本或 `nextgeo_ab_noprobe` 等测试项目可能依赖旧 `scaffold.py` 产出的特定字符串** → Mitigation：先检查现有测试对 `scaffold.py` 的断言，保留 `run_scaffold(project_id, overrides=None, publish_preview=None)` 向下兼容入口签名和原有 4 个产物文件名（并新增 `sitemap.xml`），保留 `outputs/` 根文件同步双写兼容（受同等 `custom_site: true` 保护）。
- **[Risk] 客户传入的 `logo_file` / `logo` 可能是不存在路径、远程 URL 或恶意路径穿越（如 `/etc/passwd`、`.env`）** → Mitigation：严格经 `realpath` 校验源路径必须位于 `projects/{project_id}/raw_materials/` 或 `outputs/site/assets/` 内且后缀为 `.png/.jpg/.jpeg/.webp/.svg`；越界、非法后缀或文件不存在时一律按“无 LOGO”安全留白，绝不复制越界文件或输出破图。
- **[Risk] `claw.baicl.cc` 预览链接开启期间如果被公网转发，可能被搜索引擎临时收录** → Mitigation：通过 `.published` 手动开关随时一键关闭（立刻全站 404），并由 `claw.baicl.cc` 网关根级 `/robots.txt` 返回 `Disallow: /` 限制整站根域爬取；站点内部 `outputs/site/robots.txt` 与 `index.html` 保持 AI 爬虫放行配置，确保同一份 `outputs/site/` 签单后直接拷入客户正式域名即可正常被 AI 收录，职责清晰无冲突。

---

## Migration Plan

1. 在 GEO 仓内新增统一母版、重构 `scaffold.py` 与 `handlers.py`、新增 `deploy/nginx_claw_preview.conf` 与 `docs/specs/saas-site-master-guide.md` 并通过单测验证；
2. 保持已有 `custom_site: true` 的项目（如 `projects/nextgeo/` 即 `www.baicl.cc`）100% 不受影响；
3. 生产/验证机（NE1 / VPS）的 Nginx 挂载 `claw.baicl.cc` 仅在师弟明确下达部署指令后执行，不在开发阶段自动修改线上 Nginx。
