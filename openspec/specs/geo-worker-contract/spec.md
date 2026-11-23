# geo-worker-contract Specification

## Purpose
定义 GEO 后厂 Python 无状态计算引擎对外暴露给小毛驴 Go 后端的异步任务接口契约与同机旁挂安全约束，确保长耗时爬虫和建站任务不超时卡死且前后端日常开发不跨工作区。

## Requirements

### Requirement: 后厂计算引擎同机旁挂与统一客户端调用
GEO 后厂 Python 工具服务 SHALL 绑定内网回环地址（`127.0.0.1`）并与小毛驴 Go 后端同机旁挂常驻运行，仅接收带内部服务凭证的 Go 客户端请求；小毛驴 Vue 3 前端 MUST NOT 绕过 Go 后端直接请求 GEO 后厂服务。

#### Scenario: 合法内部调用与未授权拦截
- **WHEN** 小毛驴 Go 后端携带有效内部服务凭证向 `127.0.0.1` 后厂端口发起请求
- **THEN** 后厂服务校验凭证通过并受理任务；若请求缺少凭证或凭证非法，后厂服务 MUST 返回 HTTP 401 拒绝执行

### Requirement: 异步任务提交与状态查询模型
由于官网抓取与大模型问答采样属于长耗时操作，GEO 后厂引擎 MUST 提供异步任务提交接口（`POST /worker/jobs`）与任务状态查询接口（`GET /worker/jobs/{job_id}`），支持全部 9 类任务（基础 4 类 `diagnose` 官网诊断、`probe` 问答采样、`build_site` 静态建站、`build_blog` 博客构建，以及交付与对客 5 类 `boss_report` 老板诊断单文件报告、`share_portal` 免密分享大屏生成、`distribute_pack` 多平台排版分发包、`acceptance_report` 07 交接确认单与 A4 证书、`pitch_roi` 售前建议书与 ROI 测算），SHALL NOT 通过长连接同步阻塞等待结果。

#### Scenario: 提交异步任务并立即返回任务标识
- **WHEN** 小毛驴 Go 后端向 `POST /worker/jobs` 提交任务类型（如 `diagnose` 或 `build_site`）、客户标识与输入参数
- **THEN** 后厂引擎立即校验参数并返回 HTTP 202 与全局唯一 `job_id`，在后台异步执行计算任务

#### Scenario: 查询异步任务结果与失败透传
- **WHEN** 小毛驴 Go 后端轮询 `GET /worker/jobs/{job_id}`
- **THEN** 后厂引擎返回当前状态（`queued`、`running`、`succeeded` 或 `failed`）；成功时附带标准结果 JSON 与成品路径，失败时返回明确底层报错信息供前店入库与界面展示
