# Tasks：基于 www.baicl.cc 母版的极简 SaaS 交钥匙官网与可控预览发布

## 1. 统一 SaaS 静态母版抽离

- [x] 1.1 以 `projects/nextgeo/outputs/site/index.html` 为视觉与排版基准，创建 `templates/baicl-saas/index.html.tmpl` 统一母版（内联防御性 CSS、全站相对路径、带 `SAAS_SECTION:*` 区块注释锚点、0 Emoji），并通过校验确认所有占位符与 HTML 标签闭合平衡。

## 2. 极简编译与缺省留白引擎重构

- [x] 2.1 升级 `src/tools/geo/utils.py` 中的 `parse_simple_yaml`（在零第三方依赖下支持缩进字典列表与纯字符串列表解析，如 `core_business`、`faqs`），并重构 `src/tools/geo/scaffold.py`：提供向下兼容签名 `run_scaffold(project_id, overrides=None, publish_preview=None)`，基于 `templates/baicl-saas/index.html.tmpl` 编译生成 `outputs/site/index.html`（同步保留 `outputs/` 根底座双写兼容），实现“有则渲染、无则留白”条件区块、LOGO 路径安全白名单校验（仅限 `raw_materials/` 或 `outputs/site/assets/` 内图片后缀，越界按无 LOGO 留白）、`sitemap.xml` 生成以及覆盖 `index.html`/`llms.txt`/`schema.jsonld`/`sitemap.xml`/定制子目录的 `custom_site: true` 防覆盖保护。
- [x] 2.2 更新 `src/tools/worker/handlers.py` 中的 `PROFILE_KEYS`（补齐 `wechat`、`address`、`company_profile`、`logo`、`logo_file`、`core_business`、`differences`、`core_values`、`faqs` 等）与 `handle_build_site`，提取可选覆盖参数及 `publish_preview` 透传给 `scaffold.run_scaffold` 做内存合并，在返回结果中附带 `site/sitemap.xml` 成品路径及 `claw.baicl.cc/{project_id}/` 预览链接，并编写单元测试验证“字典列表 YAML 解析”、“完整资料生成”、“仅公司名与联系方式极简默认版留白”、“无 LOGO 与越界 LOGO 路径安全拒绝”、“`custom_site: true` 防覆盖保护（含 `sitemap.xml`）”全部通过。

## 3. claw.baicl.cc 路径预览与手动公网开关

- [x] 3.1 在 `src/tools/geo/scaffold.py` 中新增无状态预览公网开关能力（`set_preview_public(project_id, enabled)` 与 CLI 命令行入口），通过创建/删除 `projects/{project_id}/outputs/site/.published` 哨兵文件控制公开状态，默认新建项目为关闭态，并补充单元测试验证开启/关闭状态切换与幂等性。
- [x] 3.2 新增 `deploy/nginx_claw_preview.conf` 配置模板，实现 `location ~ /\. { return 404; }` 拦截 `.published` 等点文件、限制 `project_id` 首字符为 `[a-zA-Z0-9]` 排除 `_template` 保留目录、`claw.baicl.cc/{project_id}` 尾斜杠 301 重定向、使用 `root + rewrite ... break` 规避 `alias + try_files` 坑并在 `.published` 缺失时返回 HTTP 404，以及根路径 `/` 返回 404、根级 `/robots.txt` 返回 `Disallow: /`（站点内 `outputs/site/robots.txt` 保持 AI 爬虫放行），并检查 Nginx 语法规则完整性。

## 4. 反重力 IDE 母版精修提示词规范

- [x] 4.1 编写 `docs/specs/saas-site-master-guide.md`，清晰记录统一母版文件位置、区块锚点清单、相对路径红线、普林斯顿 9 因子增补规范、零 Emoji 要求以及精修完成后锁定 `custom_site: true` 的标准操作步骤，并核对文档中所有路径与锚点名称与实际母版 100% 一致。

## 5. 全链路回归校验

- [x] 5.1 使用隔离临时测试项目执行端到端编译、预览开关启停及样式合规检查（确认 0 Emoji、DOM 标签闭合、相对路径、`llms.txt`/`schema.jsonld`/`robots.txt`/`sitemap.xml` 齐全），并确认 `projects/nextgeo/`（`www.baicl.cc`）因 `custom_site: true` 100% 未被修改。
