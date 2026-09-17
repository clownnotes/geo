# Tasks: 管理台阶段零 Vue3 组件岛

## 1. 规范与脚手架

- [ ] 1.1 本目录 proposal / design 经产品或跨 IDE 在 review-log 标 `[已达成共识]` 后再 apply
- [ ] 1.2 落地 Vite+Vue3 脚手架于 `web/step0-src/`；构建输出到 `web/assets/step0/`（或 design 最终选定路径）
- [ ] 1.3 `package.json` 脚本：`build:step0` / `dev:step0`；README 或本 design 写清本机命令（勿新建 docs/specs 旁路）

## 2. 组件迁入（行为对齐迁前）

- [ ] 2.1 挂载点：`index.html` 步骤 00 改为 `#step0-app`；壳侧切换步骤/项目时 mount/refresh/unmount
- [ ] 2.2 `ScriptFileList`：列表（时间、文件名、题数 peek）、选中、预览、删除；空态/失败态人话（禁止永久「清单加载中」）
- [ ] 2.3 `ScriptPreview` + `ProbeKickoff`（C+D 复制提示词、路径、附件提醒）
- [ ] 2.4 `ResultBackfill`：豆包答案文件列表 / 预览 / 确认写入；文案区分「问题清单」与「豆包答案已存进项目」
- [ ] 2.5 `plainCopy` 对齐工作区 plain-speak 对照表；界面无「基线/剧本」黑盒主文案
- [ ] 2.6 删除 `index.html` 内已迁走的阶段零大段 JS/HTML，禁止双轨

## 3. 护栏与静态托管

- [ ] 3.1 组件未加载 / 构建产物缺失时：挂载点显示人话错误，并 toast
- [ ] 3.2 确认 `server.py` 能正确提供 `web/assets/step0/**`（必要时最小改动）
- [ ] 3.3 可选：简易自检脚本或页面内断言（列表根节点存在）

## 4. 验证与停步

- [ ] 4.1 本机构建成功；Safari `127.0.0.1:8088` 走：有清单项目（如 nextgeo）列表可见、预览、刷新
- [ ] 4.2 切换项目不串数据；无清单项目空态正确
- [ ] 4.3 停步等产品验收；**禁止擅自归档**；**禁止擅自推生产**
