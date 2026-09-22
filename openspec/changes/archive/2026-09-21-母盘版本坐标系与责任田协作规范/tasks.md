# Tasks: 母盘版本坐标系与责任田协作规范

- [x] 1. 坐标字段
  - [x] 1.1 `projects/_template/project.yaml` 增加 `master_version: "1.0.0"`。不要加 `owner`
  - [x] 1.2 读取项目时，缺 `master_version` 就当成 `1.0.0`。不要批量改已有客户的 `project.yaml`

- [x] 2. 母盘只读
  - [x] 2.1 非 GET 的 `/api/projects/{id}/raw_materials` 仅开发者。GET 写文同事仍可看
  - [x] 2.2 不要把该路径放进不区分方法的开发者后缀表；不要收走整个 `article:edit`
  - [x] 2.3 写文同事界面去掉「保存母盘」按钮（若有）— 现码无 POST `/raw_materials` 的保存按钮，仅 GET 列表

- [x] 3. 文章坐标与列表
  - [x] 3.1 `scripts/create_article.py` 把当时的 `master_version` 写进现有 JSON-LD（和 `datePublished` 一起）。不要另起 HTML 注释
  - [x] 3.2 文章列表默认只显示当前 X，或没有坐标的旧文。其余归「历史封存」
  - [x] 3.3 不新造永久删除按钮

- [x] 4. 测试
  - [x] 4.1 写文同事 POST 母盘 → 403；GET 母盘 → 200；改稿类 `article:edit` 接口仍 200
  - [x] 4.2 无坐标旧文仍出现在当前列表
