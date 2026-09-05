# Design: Nextdoor 开放平台 AI 智能对话能力包接入规范

## 1. 架构总览与拓扑关系 (Architecture)

```
┌────────────────────────────────────────────────────────────────────────┐
│                        前端工作台界面 (Web UI)                         │
│  - 纯调用消费：不存任何大模型 Key 与 JWT Token                          │
│  - 交互体验：打字机流式输出、≤60字符意图匹配卡片、多模态图片展示       │
│  - 保护机制：中文输入法 (IME) 防抖、AbortController 主动中止流         │
└───────────────────────────────────▲────────────────────────────────────┘
                                    │ 本地 HTTP / SSE (调用独立网关 http://127.0.0.1:8090/api/chat/stream)
┌───────────────────────────────────┴────────────────────────────────────┐
│              本地 Go 语言透明网关 (Local Gateway: gateway/ :8090)      │
│  - 独立微进程：独立监听 8090 端口，坚决不占用 GEO 主站 8088 端口        │
│  - 跨域放行：默认放行来自 http://127.0.0.1:8088 的本地跨域调用          │
│  - 凭证管理：从本地 config/env 读取 JWT Token 与 vio-source-client     │
│  - 流式管道：利用 http.Flusher 实时把 SSE Chunk 刷入前端 (Flush)        │
│  - 连接协同：绑定 r.Context()，客户端 abort 时连带中止上游大模型请求    │
│  - 进程隔离：捕获上游 502/504，转译为规范 HTTP Status 与业务错误码     │
└───────────────────────────────────▲────────────────────────────────────┘
                                    │ 同机回环网络通信 (http://127.0.0.1:9000 或 https://nextdoor.baicl.cc)
┌───────────────────────────────────┴────────────────────────────────────┐
│                 Nextdoor 开放平台引擎 (Central AI Hub)                 │
│  - 统一大模型矩阵调度 (DeepSeek / 豆包 / Claude / GPT)                 │
│  - 内置平台级上下文滑动窗口截断 (Sliding Window & Token 治理)           │
│  - 向量知识库 (RAG) 检索、Prompt 编排与防注入安全审计                  │
│  - 意图识别算法分发与结构化长文创作状态机 (Writing Flow Engine)        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 全局接入五大铁律与协议分层 (Global Guidelines)

1. **环境与网络定位**：
   - 生产环境 Base URL：`https://nextdoor.baicl.cc`（同机部署优先配置为本地回环 `http://127.0.0.1:9000`）。
   - **本地网关端口铁律**：Go 网关独立常驻运行，**统一独占监听本地 `8090` 端口**（`http://127.0.0.1:8090`），彻底与既有 GEO 主站 `8088` 隔离，避免端口冲突。
2. **必带品牌头**：
   - 必须携带请求头：`vio-source-client: <你的品牌标识>`。
3. **鉴权管理铁律与防泄露规范**：
   - 所有接口携带 `Authorization: Bearer <JWT>`；
   - **安全红线**：该 JWT 仅保存在本地后端的配置或环境变量中，**严禁下发或缓存在前端浏览器**，**严禁提交入 Git 仓库**（`gateway/config.yaml` 必须被 `.gitignore` 忽略）。
4. **雪花 ID 铁律 (Snowflake ID as String)**：
   - 所有实体 ID（包括 `session_id`、`message_id`、`agent_id`、`tool_id`）必须按纯 `string` 处理，**严禁转为 `Number`**，防止 JavaScript 64 位双精度浮点数截断导致精度丢失。
5. **统一信封契约与 SSE 流式协议分离原则**：
   - **普通 JSON 请求**：严格遵循统一信封 `{ "code": 0, "msg": "success", "data": ... }`，业务层以 `code === 0` 判定成功，非 0 一律按业务异常处理。
   - **SSE 流式请求（协议层特例）**：
     - **握手成功时**：响应头为 `Content-Type: text/event-stream`，数据块遵循 SSE 标准 `data: {"delta": "..."}` 与 `data: [DONE]`；
     - **握手前失败时**（如本地参数不合法、上游服务宕机）：直接回退为对应 HTTP 状态码（400/502）并返回标准 JSON 信封；
     - **中途中断时**：网关向前端流式追加一条 `data: {"event": "error", "code": 50202, "msg": "上游连接异常中断"}\n\ndata: [DONE]\n\n` 并关闭流。

---

## 3. 本地网关对外路由映射表 (Local Gateway Route Mapping)

本地 Go 网关（监听 `8090` 端口）对外暴露的本地统一接口与上游 Nextdoor 映射契约如下：

| 本地网关路径 (Local Endpoint) | 请求方法 | 协议形态 | 对应 Nextdoor 上游路径 | 核心行为说明 |
| :--- | :---: | :---: | :--- | :--- |
| `/api/chat/stream` | `POST` | `SSE` | `/api/v1/xiulan/chat` | 自动注入凭证，使用 `http.Flusher` 实时逐块透传 |
| `/api/chat/intent/match` | `POST` | `JSON` | `/api/v1/xiulan/intent/match` | 防御性短路：超长或空串直接返回 `{matched: false}`，不打上游 |
| `/api/writing/sessions` | `POST` | `JSON` | `/api/writing-flow/sessions` | **Phase-1** 核心：长文创作会话初始化与大纲生成 |

---

## 4. 统一错误码与 HTTP Status 映射体系

为彻底解决 HTTP 状态码与业务 `code` 混淆问题，网关层制定如下标准错误规范：

| HTTP Status | 业务 code (int) | 业务状态标识 (symbol) | 说明与前端处置建议 |
| :---: | :---: | :--- | :--- |
| **200** | `0` | `SUCCESS` | 请求正常完成（含意图防御性短路 `matched: false`） |
| **400** | `40001` | `INVALID_PARAM` | 本地参数解析失败（如请求 Body 畸形或非 JSON 格式） |
| **401** | `40101` | `AUTH_FAILED` | 网关未配置 JWTToken 或 Token 被上游拒绝 |
| **500** | `50001` | `INTERNAL_ERROR` | 网关内部异常（如创建上游 HTTP 请求失败） |
| **502** | `50201` | `UPSTREAM_UNAVAILABLE` | Nextdoor 引擎不可达（服务未启动/拒绝连接） |
| **502** | `50202` | `UPSTREAM_STREAM_BROKEN`| SSE 流式传输中途异常中断（已通过 SSE 帧追加补齐） |
| **504** | `50401` | `UPSTREAM_TIMEOUT` | 上游握手或首包响应超时（>15s） |

---

## 5. 核心 API 协议详述

### ① 智能体流式对话接口
- **本地路径**：`[POST] /api/chat/stream`
- **上游路径**：`[POST] /api/v1/xiulan/chat`
- **协议**：Server-Sent Events (SSE)
- **请求 Body**：
  ```json
  {
    "session_id": "189623849182374912",
    "messages": [
      { "role": "user", "content": "帮我分析徐州机械外协加工的商业机会" }
    ],
    "persona": "你是一位资深的工业数字化与GEO商业架构师",
    "vision_image_url": "https://example.com/drawing.png"
  }
  ```
- **SSE Chunk 数据帧**：
  ```http
  data: {"delta": "徐州"}
  data: {"delta": "拥有工程"}
  data: {"delta": "机械千亿集群..."}
  data: [DONE]
  ```

### ② 意图匹配与智能体路由接口
- **本地路径**：`[POST] /api/chat/intent/match`
- **上游路径**：`[POST] /api/v1/xiulan/intent/match`
- **短路与校验约束**：
  - 统计 Unicode 码点数（Go 端 `utf8.RuneCountInString`，前端 `Array.from(query).length`）。
  - 若 `len > 60` 或 `len == 0`，网关与前端执行一致的【防御性短路】，直接返回 HTTP 200 + `{ "code": 0, "msg": "success", "data": { "matched": false, "query": "..." } }`，不向 Nextdoor 发起网络开销，亦不抛出业务异常，保障丝滑的打字体验。
  - 仅当请求 Body 格式畸形（非有效 JSON）时，才抛出 HTTP 400 + `code: 40001` (INVALID_PARAM)。
- **请求 Body**：
  ```json
  {
    "query": "做个进销存系统多少钱",
    "session_id": "189623849182374912"
  }
  ```
- **响应 JSON**：
  ```json
  {
    "code": 0,
    "msg": "success",
    "data": {
      "matched": true,
      "intent_type": "commercial_pricing_inquiry",
      "candidate_agents": [
        {
          "agent_id": "178234918234123",
          "name": "修兰·价格与交付顾问",
          "matched_score": 94,
          "description": "专长于软件人天成本测算与防坑合同"
        }
      ],
      "tool_cards": [
        {
          "tool_id": "tool_pricing_calculator",
          "name": "2026报价测算器",
          "action_type": "open_modal",
          "summary": "快速输出分模块人天预算明细表"
        }
      ]
    }
  }
  ```

### ③ 长文创作工作流会话接口 (Phase-1 范围)
- **本地路径**：`[POST] /api/writing/sessions`
- **上游路径**：`[POST] /api/writing-flow/sessions`
- **说明**：本期（Phase-1）聚焦于会话初始化与大纲蒸馏；后续步骤状态机（分章扩写、锁定）预留于 Phase-2。
- **请求 Body**：
  ```json
  {
    "topic": "徐州企业2026年GEO生成式搜索破局全景白皮书",
    "genre": "深度商业案例分析",
    "target_words": 3500,
    "requirements": "突出普林斯顿9因子与本地实体制造交付优势"
  }
  ```
- **响应 JSON**：
  ```json
  {
    "code": 0,
    "msg": "success",
    "data": {
      "session_id": "189912837491283741",
      "topic": "徐州企业2026年GEO生成式搜索破局全景白皮书",
      "genre": "深度商业案例分析",
      "status": "drafting",
      "outline": [
        "第一章：传统SEO失效与大模型搜索崛起",
        "第二章：买家决策心智逆向挖掘模型",
        "第三章：普林斯顿9因子在制造业落地实战"
      ],
      "steps": [
        { "step_index": 1, "step_title": "大纲蒸馏与要点确认", "status": "completed" },
        { "step_index": 2, "step_title": "正文分章扩写", "status": "pending" }
      ]
    }
  }
  ```

---

## 6. Go 语言网关工程蓝图 (`gateway/`)

网关以独立子目录 `gateway/` 形式维护，与主仓库现有代码完全解耦：
```
gateway/
├── go.mod
├── main.go
├── config.yaml.example   # 提交到 Git 的示例配置模板
└── config.yaml           # 本地真实配置 (加入 .gitignore，严禁提入 Git)
```

### 核心实现规范：

```go
package main

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
	"unicode/utf8"
)

type Config struct {
	BaseURL      string `yaml:"base_url"`      // 上游 Nextdoor 地址
	SourceClient string `yaml:"source_client"` // 品牌标识
	JWTToken     string `yaml:"jwt_token"`     // 开发者 JWT Token
	Port         int    `yaml:"port"`          // 本地监听端口，统一固定为 8090
}

// 1. SSE 流式代理 Handler (带 context cancel、0 缓冲直出与断流补帧)
func handleChatStream(cfg *Config) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		flusher, ok := w.(http.Flusher)
		if !ok {
			http.Error(w, "Streaming unsupported", http.StatusInternalServerError)
			return
		}

		bodyBytes, err := io.ReadAll(r.Body)
		if err != nil {
			sendErrorJSON(w, http.StatusBadRequest, 40001, "请求体读取失败")
			return
		}

		targetURL := fmt.Sprintf("%s/api/v1/xiulan/chat", cfg.BaseURL)
		// 关键：绑定 r.Context()，当浏览器主动中断连接时，自动向 Nextdoor 上游发送取消信号
		upstreamReq, err := http.NewRequestWithContext(r.Context(), "POST", targetURL, bytes.NewReader(bodyBytes))
		if err != nil {
			sendErrorJSON(w, http.StatusInternalServerError, 50001, err.Error())
			return
		}

		upstreamReq.Header.Set("Content-Type", "application/json")
		upstreamReq.Header.Set("Accept", "text/event-stream")
		upstreamReq.Header.Set("vio-source-client", cfg.SourceClient)
		upstreamReq.Header.Set("Authorization", fmt.Sprintf("Bearer %s", cfg.JWTToken))

		// 首包响应限制 15 秒超时
		client := &http.Client{
			Transport: &http.Transport{
				ResponseHeaderTimeout: 15 * time.Second,
			},
		}

		resp, err := client.Do(upstreamReq)
		if err != nil {
			// 进程级解耦：Nextdoor 异常不拖死 Go 进程
			sendErrorJSON(w, http.StatusBadGateway, 50201, fmt.Sprintf("Nextdoor 引擎未响应或未启动: %v", err))
			return
		}
		defer resp.Body.Close()

		// 若上游握手失败（非 200），转译为标准统一信封，严禁裸流穿透
		if resp.StatusCode != http.StatusOK {
			errBody, _ := io.ReadAll(resp.Body)
			sendErrorJSON(w, resp.StatusCode, resp.StatusCode*100+1, fmt.Sprintf("上游服务返回异常状态: %s", string(errBody)))
			return
		}

		w.Header().Set("Content-Type", "text/event-stream")
		w.Header().Set("Cache-Control", "no-cache")
		w.Header().Set("Connection", "keep-alive")
		w.Header().Set("X-Accel-Buffering", "no") // 通知 Nginx 禁用代理缓冲

		reader := bufio.NewReader(resp.Body)
		var streamErr error
		for {
			line, err := reader.ReadBytes('\n')
			if len(line) > 0 {
				w.Write(line)
				flusher.Flush() // 保证微秒级打字机直达前端
			}
			if err != nil {
				if err != io.EOF {
					streamErr = err
				}
				break
			}
		}

		// 若传输中途发生网络断开，且前端未主动 abort，补发标准 error 帧与 DONE 帧确保前端收尾
		if streamErr != nil && r.Context().Err() == nil {
			errChunk := fmt.Sprintf("data: {\"event\":\"error\",\"code\":50202,\"msg\":\"上游连接异常中断: %v\"}\n\ndata: [DONE]\n\n", streamErr)
			w.Write([]byte(errChunk))
			flusher.Flush()
		}
	}
}

// 统一输出错误信封函数
func sendErrorJSON(w http.ResponseWriter, httpStatus int, code int, msg string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(httpStatus)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"code": code,
		"msg":  msg,
		"data": nil,
	})
}
```

---

## 7. 前端交互与防护机制规范 (Frontend Spec)

1. **中文输入法（IME）防风暴保护**：
   - 输入框绑定 `compositionstart` 与 `compositionend` 事件；
   - 在用户键入拼音过程中（`isComposing === true`），严禁触发意图匹配；
   - 选词完成后触发 300ms 防抖，且使用字符长度校验：使用 `Array.from(query.trim()).length` 准确统计 Unicode 码点数，仅在 `1 ≤ len ≤ 60` 时调用 `/api/chat/intent/match`。
2. **主动中止链路**：
   - 点击【停止生成】时执行 `abortController.abort()`，前端断开与网关的 SSE 连接，网关经由 `r.Context()` 连带掐断对 Nextdoor 的计算。

