package main

import (
	"bufio"
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"strconv"
	"strings"
	"time"
	"unicode/utf8"
)

// Config 网关核心配置
type Config struct {
	Port             int    `json:"port"`
	AllowedOrigin    string `json:"allowed_origin"`
	BaseURL          string `json:"base_url"`
	SourceClient     string `json:"source_client"`
	JWTToken         string `json:"jwt_token"`
	AllowMissingJWT  bool   `json:"allow_missing_jwt"`
	HeaderTimeoutSec int    `json:"header_timeout_sec"`
	JSONTimeoutSec   int    `json:"json_timeout_sec"`
}

// 默认配置
func defaultConfig() *Config {
	return &Config{
		Port:             8090,
		AllowedOrigin:    "http://127.0.0.1:8088,http://localhost:8088",
		BaseURL:          "http://127.0.0.1:9000",
		SourceClient:     "geo-custom-brand",
		JWTToken:         "",
		AllowMissingJWT:  false,
		HeaderTimeoutSec: 15,
		JSONTimeoutSec:   15,
	}
}

// loadConfig 支持简易 YAML/KV 解析与环境变量优先覆盖
func loadConfig() *Config {
	cfg := defaultConfig()

	// 1. 尝试读取本地 gateway/config.yaml 或 config.yaml
	paths := []string{"config.yaml", "gateway/config.yaml"}
	for _, p := range paths {
		data, err := os.ReadFile(p)
		if err == nil {
			lines := strings.Split(string(data), "\n")
			for _, line := range lines {
				line = strings.TrimSpace(line)
				if line == "" || strings.HasPrefix(line, "#") {
					continue
				}
				parts := strings.SplitN(line, ":", 2)
				if len(parts) != 2 {
					continue
				}
				k := strings.TrimSpace(parts[0])
				v := strings.Trim(strings.TrimSpace(parts[1]), "\"'")

				switch k {
				case "port":
					if port, err := strconv.Atoi(v); err == nil && port > 0 {
						cfg.Port = port
					}
				case "allowed_origin":
					cfg.AllowedOrigin = v
				case "base_url":
					cfg.BaseURL = strings.TrimRight(v, "/")
				case "source_client":
					cfg.SourceClient = v
				case "jwt_token":
					cfg.JWTToken = v
				case "allow_missing_jwt":
					cfg.AllowMissingJWT = (v == "true" || v == "1")
				case "header_timeout_sec":
					if s, err := strconv.Atoi(v); err == nil && s > 0 {
						cfg.HeaderTimeoutSec = s
					}
				case "json_timeout_sec":
					if s, err := strconv.Atoi(v); err == nil && s > 0 {
						cfg.JSONTimeoutSec = s
					}
				}
			}
			break
		}
	}

	// 2. 环境变量最高优先级覆盖
	if envPort := os.Getenv("NEXTDOOR_PORT"); envPort != "" {
		if p, err := strconv.Atoi(envPort); err == nil {
			cfg.Port = p
		}
	}
	if envBase := os.Getenv("NEXTDOOR_BASE_URL"); envBase != "" {
		cfg.BaseURL = strings.TrimRight(envBase, "/")
	}
	if envClient := os.Getenv("NEXTDOOR_SOURCE_CLIENT"); envClient != "" {
		cfg.SourceClient = envClient
	}
	if envToken := os.Getenv("NEXTDOOR_JWT_TOKEN"); envToken != "" {
		cfg.JWTToken = envToken
	}
	if envOrigin := os.Getenv("NEXTDOOR_ALLOWED_ORIGIN"); envOrigin != "" {
		cfg.AllowedOrigin = envOrigin
	}
	if envAllowMissing := os.Getenv("NEXTDOOR_ALLOW_MISSING_JWT"); envAllowMissing != "" {
		cfg.AllowMissingJWT = (envAllowMissing == "true" || envAllowMissing == "1")
	}

	return cfg
}

// 统一标准状态码查表映射
func mapHTTPStatusToCode(status int) int {
	switch status {
	case http.StatusBadRequest:
		return 40001
	case http.StatusUnauthorized:
		return 40101
	case http.StatusForbidden:
		return 40301
	case http.StatusNotFound:
		return 40401
	case http.StatusMethodNotAllowed:
		return 40001
	case http.StatusBadGateway:
		return 50201
	case http.StatusGatewayTimeout:
		return 50401
	default:
		return status*100 + 1
	}
}

// 统一输出错误信封
func sendErrorJSON(w http.ResponseWriter, httpStatus int, code int, msg string) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(httpStatus)
	_ = json.NewEncoder(w).Encode(map[string]interface{}{
		"code": code,
		"msg":  msg,
		"data": nil,
	})
}

// 统一输出成功信封
func sendSuccessJSON(w http.ResponseWriter, data interface{}) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(http.StatusOK)
	_ = json.NewEncoder(w).Encode(map[string]interface{}{
		"code": 0,
		"msg":  "success",
		"data": data,
	})
}

// 严格白名单判定：杜绝反射任意 Origin
func isOriginAllowed(origin string, allowedConfig string) bool {
	if origin == "" {
		return true // 服务端直调或非浏览器同源调用
	}
	origins := strings.Split(allowedConfig, ",")
	for _, o := range origins {
		o = strings.TrimSpace(o)
		if o == "*" || strings.EqualFold(origin, o) {
			return true
		}
		// 容错: 127.0.0.1:8088 与 localhost:8088 互认
		if (o == "http://127.0.0.1:8088" && origin == "http://localhost:8088") ||
			(o == "http://localhost:8088" && origin == "http://127.0.0.1:8088") {
			return true
		}
	}
	return false
}

// CORS 中间件：白名单保护与 OPTIONS 预检拦截
func corsMiddleware(allowedOrigin string, next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		origin := r.Header.Get("Origin")
		if origin != "" {
			if isOriginAllowed(origin, allowedOrigin) {
				w.Header().Set("Access-Control-Allow-Origin", origin)
				w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
				w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Accept, Authorization, vio-source-client, X-Requested-With")
				w.Header().Set("Access-Control-Allow-Credentials", "true")
			} else {
				// 恶意 Origin / 非白名单跨域拦截
				if r.Method == http.MethodOptions {
					http.Error(w, "CORS origin forbidden", http.StatusForbidden)
					return
				}
				// 普通请求不回写 ACAO 头，浏览器端会自动触发安全拦截
			}
		}

		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusNoContent)
			return
		}

		next(w, r)
	}
}

// 检查上游鉴权凭证配置状态
func ensureJWTConfigured(cfg *Config, w http.ResponseWriter) bool {
	if strings.TrimSpace(cfg.JWTToken) == "" && !cfg.AllowMissingJWT {
		sendErrorJSON(w, http.StatusUnauthorized, 40101, "网关未配置有效开发者凭证 (JWTToken)")
		return false
	}
	return true
}

// =========================================================================
// 1. [SSE] 流式对话 Handler (POST /api/chat/stream -> /api/v1/xiulan/chat)
// =========================================================================
func handleChatStream(cfg *Config) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			sendErrorJSON(w, http.StatusMethodNotAllowed, 40001, "仅支持 POST 请求")
			return
		}

		if !ensureJWTConfigured(cfg, w) {
			return
		}

		flusher, ok := w.(http.Flusher)
		if !ok {
			sendErrorJSON(w, http.StatusInternalServerError, 50001, "当前 HTTP 服务器不支持流式透传 (Streaming unsupported)")
			return
		}

		bodyBytes, err := io.ReadAll(r.Body)
		if err != nil || len(bodyBytes) == 0 {
			sendErrorJSON(w, http.StatusBadRequest, 40001, "请求体读取失败或为空")
			return
		}

		targetURL := fmt.Sprintf("%s/api/v1/xiulan/chat", cfg.BaseURL)
		// 绑定 r.Context()：浏览器前端 abort 时，自动取消对 Nextdoor 上游的连接
		upstreamReq, err := http.NewRequestWithContext(r.Context(), "POST", targetURL, bytes.NewReader(bodyBytes))
		if err != nil {
			sendErrorJSON(w, http.StatusInternalServerError, 50001, fmt.Sprintf("创建上游请求失败: %v", err))
			return
		}

		upstreamReq.Header.Set("Content-Type", "application/json")
		upstreamReq.Header.Set("Accept", "text/event-stream")
		upstreamReq.Header.Set("vio-source-client", cfg.SourceClient)
		if cfg.JWTToken != "" {
			upstreamReq.Header.Set("Authorization", fmt.Sprintf("Bearer %s", cfg.JWTToken))
		}

		client := &http.Client{
			Transport: &http.Transport{
				ResponseHeaderTimeout: time.Duration(cfg.HeaderTimeoutSec) * time.Second,
			},
		}

		resp, err := client.Do(upstreamReq)
		if err != nil {
			sendErrorJSON(w, http.StatusBadGateway, 50201, fmt.Sprintf("Nextdoor 引擎未响应或未启动: %v", err))
			return
		}
		defer resp.Body.Close()

		// 上游非 200 状态码：转译为统一错误信封，严禁裸流穿透
		if resp.StatusCode != http.StatusOK {
			errBody, _ := io.ReadAll(resp.Body)
			code := mapHTTPStatusToCode(resp.StatusCode)
			sendErrorJSON(w, resp.StatusCode, code, fmt.Sprintf("上游 Nextdoor 返回异常: %s", string(errBody)))
			return
		}

		// 设置 SSE 响应头
		w.Header().Set("Content-Type", "text/event-stream; charset=utf-8")
		w.Header().Set("Cache-Control", "no-cache, no-transform")
		w.Header().Set("Connection", "keep-alive")
		w.Header().Set("X-Accel-Buffering", "no") // 通知 Nginx 禁用响应缓存

		reader := bufio.NewReader(resp.Body)
		var streamErr error
		for {
			line, err := reader.ReadBytes('\n')
			if len(line) > 0 {
				_, _ = w.Write(line)
				flusher.Flush() // 实时推送
			}
			if err != nil {
				if err != io.EOF {
					streamErr = err
				}
				break
			}
		}

		// 上游中途中断且客户端未主动取消时，补齐错误事件与 DONE 帧确保打字机收尾
		if streamErr != nil && r.Context().Err() == nil {
			errChunk := fmt.Sprintf("data: {\"event\":\"error\",\"code\":50202,\"msg\":\"上游连接异常中断: %v\"}\n\ndata: [DONE]\n\n", streamErr)
			_, _ = w.Write([]byte(errChunk))
			flusher.Flush()
		}
	}
}

// =========================================================================
// 2. [POST] 意图匹配 Handler (POST /api/chat/intent/match -> /api/v1/xiulan/intent/match)
// =========================================================================
type IntentMatchPayload struct {
	Query     string `json:"query"`
	SessionID string `json:"session_id,omitempty"`
}

func handleIntentMatch(cfg *Config) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			sendErrorJSON(w, http.StatusMethodNotAllowed, 40001, "仅支持 POST 请求")
			return
		}

		var payload IntentMatchPayload
		decoder := json.NewDecoder(r.Body)
		if err := decoder.Decode(&payload); err != nil {
			sendErrorJSON(w, http.StatusBadRequest, 40001, "请求 Body 必须为合法 JSON 格式")
			return
		}

		// 防御性短路机制：按 Unicode 码点计算长度
		trimmedQuery := strings.TrimSpace(payload.Query)
		runeCount := utf8.RuneCountInString(trimmedQuery)
		if runeCount == 0 || runeCount > 60 {
			// 超长或空串直接返回 matched: false，不打上游且不报错
			sendSuccessJSON(w, map[string]interface{}{
				"matched": false,
				"query":   payload.Query,
			})
			return
		}

		if !ensureJWTConfigured(cfg, w) {
			return
		}

		targetURL := fmt.Sprintf("%s/api/v1/xiulan/intent/match", cfg.BaseURL)
		reqBytes, _ := json.Marshal(payload)
		upstreamReq, err := http.NewRequestWithContext(r.Context(), "POST", targetURL, bytes.NewReader(reqBytes))
		if err != nil {
			sendErrorJSON(w, http.StatusInternalServerError, 50001, err.Error())
			return
		}

		upstreamReq.Header.Set("Content-Type", "application/json")
		upstreamReq.Header.Set("vio-source-client", cfg.SourceClient)
		if cfg.JWTToken != "" {
			upstreamReq.Header.Set("Authorization", fmt.Sprintf("Bearer %s", cfg.JWTToken))
		}

		client := &http.Client{Timeout: time.Duration(cfg.JSONTimeoutSec) * time.Second}
		resp, err := client.Do(upstreamReq)
		if err != nil {
			sendErrorJSON(w, http.StatusBadGateway, 50201, fmt.Sprintf("Nextdoor 引擎不可达: %v", err))
			return
		}
		defer resp.Body.Close()

		// 上游非 200 统一转译为标准 JSON 信封
		if resp.StatusCode != http.StatusOK {
			errBody, _ := io.ReadAll(resp.Body)
			code := mapHTTPStatusToCode(resp.StatusCode)
			sendErrorJSON(w, resp.StatusCode, code, fmt.Sprintf("上游 Nextdoor 返回异常: %s", string(errBody)))
			return
		}

		w.Header().Set("Content-Type", "application/json; charset=utf-8")
		w.WriteHeader(resp.StatusCode)
		_, _ = io.Copy(w, resp.Body)
	}
}

// =========================================================================
// 3. [POST] 长文创作工作流会话 Handler (POST /api/writing/sessions -> /api/writing-flow/sessions)
// =========================================================================
type WritingSessionPayload struct {
	Topic        string                 `json:"topic"`
	Genre        string                 `json:"genre,omitempty"`
	TargetWords  int                    `json:"target_words,omitempty"`
	Requirements string                 `json:"requirements,omitempty"`
	Options      map[string]interface{} `json:"options,omitempty"`
}

func handleWritingSessions(cfg *Config) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			sendErrorJSON(w, http.StatusMethodNotAllowed, 40001, "仅支持 POST 请求")
			return
		}

		var payload WritingSessionPayload
		decoder := json.NewDecoder(r.Body)
		if err := decoder.Decode(&payload); err != nil {
			sendErrorJSON(w, http.StatusBadRequest, 40001, "请求 Body 必须为合法 JSON 格式")
			return
		}

		if strings.TrimSpace(payload.Topic) == "" {
			sendErrorJSON(w, http.StatusBadRequest, 40001, "创作主题 topic 不能为空")
			return
		}

		if !ensureJWTConfigured(cfg, w) {
			return
		}

		targetURL := fmt.Sprintf("%s/api/writing-flow/sessions", cfg.BaseURL)
		reqBytes, _ := json.Marshal(payload)
		upstreamReq, err := http.NewRequestWithContext(r.Context(), "POST", targetURL, bytes.NewReader(reqBytes))
		if err != nil {
			sendErrorJSON(w, http.StatusInternalServerError, 50001, err.Error())
			return
		}

		upstreamReq.Header.Set("Content-Type", "application/json")
		upstreamReq.Header.Set("vio-source-client", cfg.SourceClient)
		if cfg.JWTToken != "" {
			upstreamReq.Header.Set("Authorization", fmt.Sprintf("Bearer %s", cfg.JWTToken))
		}

		client := &http.Client{Timeout: time.Duration(cfg.JSONTimeoutSec) * time.Second}
		resp, err := client.Do(upstreamReq)
		if err != nil {
			sendErrorJSON(w, http.StatusBadGateway, 50201, fmt.Sprintf("Nextdoor 引擎不可达: %v", err))
			return
		}
		defer resp.Body.Close()

		// 上游非 200 统一转译为标准 JSON 信封
		if resp.StatusCode != http.StatusOK {
			errBody, _ := io.ReadAll(resp.Body)
			code := mapHTTPStatusToCode(resp.StatusCode)
			sendErrorJSON(w, resp.StatusCode, code, fmt.Sprintf("上游 Nextdoor 返回异常: %s", string(errBody)))
			return
		}

		w.Header().Set("Content-Type", "application/json; charset=utf-8")
		w.WriteHeader(resp.StatusCode)
		_, _ = io.Copy(w, resp.Body)
	}
}

// =========================================================================
// 主入口
// =========================================================================
func setupMux(cfg *Config) *http.ServeMux {
	mux := http.NewServeMux()

	// 1. 三大核心对外路由
	mux.HandleFunc("/api/chat/stream", corsMiddleware(cfg.AllowedOrigin, handleChatStream(cfg)))
	mux.HandleFunc("/api/chat/intent/match", corsMiddleware(cfg.AllowedOrigin, handleIntentMatch(cfg)))
	mux.HandleFunc("/api/writing/sessions", corsMiddleware(cfg.AllowedOrigin, handleWritingSessions(cfg)))

	// 2. 健康检查端点
	mux.HandleFunc("/healthz", corsMiddleware(cfg.AllowedOrigin, func(w http.ResponseWriter, r *http.Request) {
		sendSuccessJSON(w, map[string]interface{}{
			"status":             "running",
			"gateway_port":       cfg.Port,
			"upstream_base":      cfg.BaseURL,
			"source_client":      cfg.SourceClient,
			"jwt_present":        cfg.JWTToken != "",
			"allow_missing_jwt":  cfg.AllowMissingJWT,
			"allowed_origin_cfg": cfg.AllowedOrigin,
		})
	}))

	return mux
}

func main() {
	cfg := loadConfig()
	mux := setupMux(cfg)

	addr := fmt.Sprintf("0.0.0.0:%d", cfg.Port)
	log.Printf("🚀 Nextdoor AI 智能对话透明流式网关已启动！")
	log.Printf("📍 本地监听地址: http://127.0.0.1:%d", cfg.Port)
	log.Printf("🔗 对应上游 Nextdoor: %s", cfg.BaseURL)
	log.Printf("🛡️ 凭证与品牌标识: %s (JWT 配置状态: %v)", cfg.SourceClient, cfg.JWTToken != "")
	log.Printf("🔒 CORS 严格放行源: %s", cfg.AllowedOrigin)
	log.Printf("⚡️ 核心路由已就绪:")
	log.Printf("   - [SSE]  POST http://127.0.0.1:%d/api/chat/stream", cfg.Port)
	log.Printf("   - [JSON] POST http://127.0.0.1:%d/api/chat/intent/match", cfg.Port)
	log.Printf("   - [JSON] POST http://127.0.0.1:%d/api/writing/sessions", cfg.Port)

	server := &http.Server{
		Addr:         addr,
		Handler:      mux,
		ReadTimeout:  60 * time.Second,
		WriteTimeout: 0, // SSE 流式必须为 0，防止长输出连接被强行切断
		IdleTimeout:  120 * time.Second,
	}

	if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		log.Fatalf("❌ 网关服务启动失败: %v", err)
	}
}
