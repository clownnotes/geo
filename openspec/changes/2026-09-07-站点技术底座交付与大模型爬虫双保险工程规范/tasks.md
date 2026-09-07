# Tasks: 站点技术底座交付与大模型爬虫双保险工程规范

- [ ] 1. 规范文档沉淀与框架标准固化
  - [ ] 1.1 创建技术规范文档 `docs/specs/site-scaffold-standard.md`，沉淀 5 大技术底座标准
  - [ ] 1.2 在 `AGENTS.md` 中新增“第 7 章：站点技术底座与大模型爬虫工程规范”
- [ ] 2. 脚手架防覆盖机制加固
  - [ ] 2.1 在 `tools/geo/scaffold.py` 中增加项目定制保护锁逻辑（支持 `custom_site: true`）
  - [ ] 2.2 在 `projects/nextgeo/project.yaml` 中显式标记 `custom_site: true`
- [ ] 3. 自动化合规体检工具研发
  - [ ] 3.1 编写 `scripts/check_site_standard.py` 脚本，支持对站点底座规范的全量扫描
  - [ ] 3.2 运行工具对 `projects/nextgeo/outputs/site` 进行全量回归体检
- [ ] 4. 跨 IDE 联合审查与共识对齐
  - [ ] 4.1 由 Cursor IDE 参与审查 `proposal.md`、`design.md` 与 `tasks.md`
  - [ ] 4.2 在 `review-log.md` 记录跨端审查结论并形成共识
