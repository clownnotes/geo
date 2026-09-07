# Tasks: 站点技术底座交付与大模型爬虫双保险工程规范

- [x] 1. 规范文档沉淀与框架标准固化
  - [x] 1.1 创建技术规范文档 `docs/specs/site-scaffold-standard.md`，沉淀 5 大技术底座标准与页面类型合规矩阵
  - [x] 1.2 在 `AGENTS.md` 中新增“第 7 章：站点技术底座与大模型爬虫工程规范”（精炼条目 + 指向 specs）
- [x] 2. 脚手架防覆盖机制加固
  - [x] 2.1 在 `tools/geo/scaffold.py` 中增加保护锁：当 `custom_site: true` 时跳过覆盖 `index.html` 与定制子目录
  - [x] 2.2 在 `projects/nextgeo/project.yaml` 中显式添加 `custom_site: true` 标记
- [x] 3. 自动化合规体检工具研发 (`scripts/check_site_standard.py`)
  - [x] 3.1 编写 `scripts/check_site_standard.py` 脚本，实现按页面类型矩阵的分级检测（首页阻断 Error / 存量页 Warn 台账）
  - [x] 3.2 脚本内置静态路由 301 尾部斜杠自动化断言与底座 3 件套完整性校验
  - [x] 3.3 运行脚本对 `projects/nextgeo/outputs/site` 进行全量回归测试，确保 Block 项 100% 通过（exit 0）
- [x] 4. 跨 IDE 联合审查与共识对齐
  - [x] 4.1 在 `review-log.md` 中响应 Cursor 评审意见并更新为 `[已达成共识]`
