# Tasks: 阶段零出题落盘与冒烟护栏

## 1. 共识

- [x] 1.1 review-log 确认方案：默认 **S0**（文案+提示词+冒烟），或改选 S1/S2；标 `[已达成共识]` 后再 apply

## 2. 落盘契约与人话

- [x] 2.1 更新 `plainCopy.qualityPromptText`：落盘口令、路径规则、禁止「未落盘却说管理台已有」；指向本 design（勿新建 docs/specs 旁路）
- [x] 2.2 B 区（ProbeStep2 / ScriptFileList 附近）增加固定说明：只显示已保存文件；聊天未落盘不会出现
- [x] 2.3 空态/错误态人话复查：禁止永久「清单加载中」

## 3. 冒烟护栏

- [x] 3.1 新增 `scripts/smoke_step0.sh`（或等价）+ 根目录 `npm run smoke:step0`
- [x] 3.2 覆盖：build、产物存在、可选 curl `/assets/step0/step0.js`、本地扫 `probe_script_*.json` 份数打印
- [x] 3.3 design/本 tasks 写明：改阶段零未跑冒烟不得宣称完成

## 4. 验证与停步

- [x] 4.1 对本机 nextgeo：走一遍「只列题不落盘 → B 区无新文件 → 可以落盘 → B 区出现」
- [x] 4.2 `npm run smoke:step0` 通过；删产物后失败可复现
- [x] 4.3 停步等产品验收；**禁止擅自归档**；**禁止擅自推生产**
