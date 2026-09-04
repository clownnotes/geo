# Tasks: 全域动态知识热补丁聚合与一键落盘自愈流水线 (第 29 维)

- [ ] 1. 核心自愈中枢引擎实现 (`tools/geo/healer.py`)
  - [ ] 1.1 实现 `compile_healing_patches()`：扫描并聚合 20 维 (decay)、22 维 (rerank)、25 维 (robustness)、26 维 (moat) 与 07/08 维 (factual/schema) 策略产物，执行归一化提取与缺失包优雅降级
  - [ ] 1.2 实现 `backup_state()` 与 `rollback_healing()`：在 `.healer_backup/<timestamp>/` 创建原子备份，并支持一键无损还原覆盖
  - [ ] 1.3 实现 `apply_healing_patches()`：幂等回写 `llms.txt`/`llms-truth.txt`（事实段落）、`03_普林斯顿9因子高权威语料库.md`（独立自愈附录 FAQ）、`schema.jsonld`（实体字段与 FAQPage 合并），并输出 `self_healing_audit.json` 与结案报告
  - [ ] 1.4 实现 `verify_integrity()`：执行 JSON-LD 语法解析与 9 因子文档结构合规校验，发现异常立刻阻断回滚
- [ ] 2. CLI 命令挂载与交互实现 (`tools/geo/cli.py`)
  - [ ] 2.1 挂载 `geo heal` 子命令，支持参数 `--apply`、`--rollback`、`--verify`
  - [ ] 2.2 优化终端控制台彩色输出：呈现待自愈三类补丁概览、回写对账表与一键回滚提示
- [ ] 3. Web 后端路由与高管门户数据联动 (`tools/geo/server.py` & `tools/geo/share.py`)
  - [ ] 3.1 在 `server.py` 挂载 `/api/projects/{id}/heal/preview`、`/api/projects/{id}/heal/apply`、`/api/projects/{id}/heal/rollback` 接口
  - [ ] 3.2 在 `share.py` 的 `compile_portal_data()` 中追加 `self_healing_summary` 字段（自愈状态、累计修复长尾词数、最近自愈时间、健康度）
- [ ] 4. 单元测试与端到端回归 (`tests/test_self_healing.py`)
  - [ ] 4.1 编写策略包扫描提取与缺失维度优雅降级单测
  - [ ] 4.2 编写原子备份与 `--rollback` 一键无损恢复单测（SHA256 哈希精确比对）
  - [ ] 4.3 编写多次 `--apply` 幂等去重测试（断言同一补丁不重复追加）
  - [ ] 4.4 运行全库单元测试，确保全库测试秒绿通过，并验证 VitePress SSG 构建零报错

