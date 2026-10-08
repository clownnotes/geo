// [NON-PROD] 本文件仅供本地网关单元测试与开发实验旁路使用。
// NE1 生产环境唯一真相源 (SSOT) 锁定为 8088 端口 Python Web 服务 (src/tools/geo/server.py)。
// 任何业务契约（article-chunk、磁盘缓存、上游请求字段）必须与 Python 8088 服务保持严格对齐。
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
	"path/filepath"
	"strconv"
	"strings"
	"sync"
	"time"
	"unicode/utf8"
)

// 确定项目根目录 (优先级: NEXTDOOR_PROJECT_ROOT 环境变量 > 向上查找包含 projects 或 .git 的目录 > 当前工作目录)
func findProjectRoot() string {
	if root := strings.TrimSpace(os.Getenv("NEXTDOOR_PROJECT_ROOT")); root != "" {
		if fi, err := os.Stat(root); err == nil && fi.IsDir() {
			return root
		}
	}
	dir, err := os.Getwd()
	if err != nil {
		return "."
	}
	for {
		if fi, err := os.Stat(filepath.Join(dir, "projects")); err == nil && fi.IsDir() {
			return dir
		}
		if _, err := os.Stat(filepath.Join(dir, ".git")); err == nil {
			return dir
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			break
		}
		dir = parent
	}
	return "."
}

// Config 网关核心配置
type Config struct {
	Host             string `json:"host"`
	Port             int    `json:"port"`
	AllowedOrigin    string `json:"allowed_origin"`
	BaseURL          string `json:"base_url"`
	SourceClient     string `json:"source_client"`
	JWTToken         string `json:"jwt_token"`
	VoiceKey         string `json:"voice_key"`
	AllowMissingJWT  bool   `json:"allow_missing_jwt"`
	HeaderTimeoutSec int    `json:"header_timeout_sec"`
	JSONTimeoutSec   int    `json:"json_timeout_sec"`
	ProjectRoot      string `json:"project_root"`
	BindAll          bool   `json:"bind_all"`
}

// 默认配置 (默认严格绑定 127.0.0.1 本地回环，杜绝全网暴露)
func defaultConfig() *Config {
	return &Config{
		Host:             "127.0.0.1",
		Port:             8090,
		AllowedOrigin:    "http://127.0.0.1:8088,http://localhost:8088",
		BaseURL:          "http://127.0.0.1:9000",
		SourceClient:     "geo",
		JWTToken:         "",
		VoiceKey:         "",
		AllowMissingJWT:  false,
		HeaderTimeoutSec: 15,
		JSONTimeoutSec:   15,
		ProjectRoot:      findProjectRoot(),
		BindAll:          false,
	}
}

// loadConfig 支持简易 YAML/KV 解析与环境变量优先覆盖
func loadConfig() *Config {
	cfg := defaultConfig()
	root := cfg.ProjectRoot

	// 1. 尝试读取配置文件 (支持根目录与基于 ProjectRoot 检索)
	paths := []string{
		"config.yaml",
		"src/gateway/config.yaml",
		"gateway/config.yaml",
		filepath.Join(root, "src", "gateway", "config.yaml"),
		filepath.Join(root, "gateway", "config.yaml"),
		filepath.Join(root, "config.yaml"),
	}
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
				case "bind_all":
					cfg.BindAll = (v == "true" || v == "1")
				case "project_root":
					if v != "" {
						cfg.ProjectRoot = v
					}
				case "allowed_origin":
					cfg.AllowedOrigin = v
				case "base_url":
					cfg.BaseURL = strings.TrimRight(v, "/")
				case "source_client":
					cfg.SourceClient = v
				case "jwt_token":
					cfg.JWTToken = v
				case "voice_key":
					cfg.VoiceKey = v
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
	if envVoice := os.Getenv("NEXTDOOR_VOICE_KEY"); envVoice != "" {
		cfg.VoiceKey = envVoice
	} else if envAPI := os.Getenv("NEXTDOOR_API_KEY"); envAPI != "" {
		cfg.VoiceKey = envAPI
	}
	if envOrigin := os.Getenv("NEXTDOOR_ALLOWED_ORIGIN"); envOrigin != "" {
		cfg.AllowedOrigin = envOrigin
	}
	if envAllowMissing := os.Getenv("NEXTDOOR_ALLOW_MISSING_JWT"); envAllowMissing != "" {
		cfg.AllowMissingJWT = (envAllowMissing == "true" || envAllowMissing == "1")
	}
	if envBind := os.Getenv("NEXTDOOR_BIND_ALL"); envBind != "" {
		cfg.BindAll = (envBind == "true" || envBind == "1")
	}
	if cfg.BindAll {
		cfg.Host = "0.0.0.0"
	}
	if envRoot := os.Getenv("NEXTDOOR_PROJECT_ROOT"); envRoot != "" {
		cfg.ProjectRoot = envRoot
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

		// [R-4 防护] 流式长连接单独清除写超时，允许打字机无限长输出；非流式端点享受全局 30s 写超时保护
		rc := http.NewResponseController(w)
		_ = rc.SetWriteDeadline(time.Time{})

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
			errPayload, _ := json.Marshal(map[string]interface{}{
				"event": "error",
				"code":  50202,
				"msg":   fmt.Sprintf("上游连接异常中断: %v", streamErr),
			})
			errChunk := fmt.Sprintf("data: %s\n\ndata: [DONE]\n\n", errPayload)
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
// 4. [2026-09-18] [统一API接入] 小毛驴统一账号与鉴权代理 Handler
// =========================================================================
func handleLoginProxy(cfg *Config) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			sendErrorJSON(w, http.StatusMethodNotAllowed, 40001, "仅支持 POST 请求")
			return
		}
		bodyBytes, err := io.ReadAll(r.Body)
		if err != nil {
			sendErrorJSON(w, http.StatusBadRequest, 40001, "请求体读取失败")
			return
		}
		targetURL := fmt.Sprintf("%s/api/v1/xiulan/login", cfg.BaseURL)
		upstreamReq, err := http.NewRequestWithContext(r.Context(), "POST", targetURL, bytes.NewReader(bodyBytes))
		if err != nil {
			sendErrorJSON(w, http.StatusInternalServerError, 50001, err.Error())
			return
		}
		upstreamReq.Header.Set("Content-Type", "application/json")
		upstreamReq.Header.Set("vio-source-client", cfg.SourceClient)

		client := &http.Client{Timeout: time.Duration(cfg.JSONTimeoutSec) * time.Second}
		resp, err := client.Do(upstreamReq)
		if err != nil {
			sendErrorJSON(w, http.StatusBadGateway, 50201, fmt.Sprintf("Nextdoor 统一认证服务不可达: %v", err))
			return
		}
		defer resp.Body.Close()

		w.Header().Set("Content-Type", "application/json; charset=utf-8")
		w.WriteHeader(resp.StatusCode)
		_, _ = io.Copy(w, resp.Body)
	}
}

func handleMeProxy(cfg *Config) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			sendErrorJSON(w, http.StatusMethodNotAllowed, 40001, "仅支持 GET 请求")
			return
		}
		authHeader := r.Header.Get("Authorization")
		if authHeader == "" {
			sendErrorJSON(w, http.StatusUnauthorized, 40101, "缺少 Authorization 令牌头")
			return
		}
		targetURL := fmt.Sprintf("%s/api/v1/xiulan/me", cfg.BaseURL)
		upstreamReq, err := http.NewRequestWithContext(r.Context(), "GET", targetURL, nil)
		if err != nil {
			sendErrorJSON(w, http.StatusInternalServerError, 50001, err.Error())
			return
		}
		upstreamReq.Header.Set("Content-Type", "application/json")
		upstreamReq.Header.Set("vio-source-client", cfg.SourceClient)
		upstreamReq.Header.Set("Authorization", authHeader)

		client := &http.Client{Timeout: time.Duration(cfg.JSONTimeoutSec) * time.Second}
		resp, err := client.Do(upstreamReq)
		if err != nil {
			sendErrorJSON(w, http.StatusBadGateway, 50201, fmt.Sprintf("Nextdoor 统一认证服务不可达: %v", err))
			return
		}
		defer resp.Body.Close()

		w.Header().Set("Content-Type", "application/json; charset=utf-8")
		w.WriteHeader(resp.StatusCode)
		_, _ = io.Copy(w, resp.Body)
	}
}

func handleWechatQRProxy(cfg *Config) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			sendErrorJSON(w, http.StatusMethodNotAllowed, 40001, "仅支持 GET 请求")
			return
		}
		targetURL := fmt.Sprintf("%s/api/auth/wechat-qr", cfg.BaseURL)
		upstreamReq, err := http.NewRequestWithContext(r.Context(), "GET", targetURL, nil)
		if err != nil {
			sendErrorJSON(w, http.StatusInternalServerError, 50001, err.Error())
			return
		}
		upstreamReq.Header.Set("Content-Type", "application/json")
		upstreamReq.Header.Set("vio-source-client", cfg.SourceClient)

		client := &http.Client{Timeout: time.Duration(cfg.JSONTimeoutSec) * time.Second}
		resp, err := client.Do(upstreamReq)
		if err != nil {
			sendErrorJSON(w, http.StatusBadGateway, 50201, fmt.Sprintf("Nextdoor 统一认证服务不可达: %v", err))
			return
		}
		defer resp.Body.Close()

		w.Header().Set("Content-Type", "application/json; charset=utf-8")
		w.WriteHeader(resp.StatusCode)
		_, _ = io.Copy(w, resp.Body)
	}
}

// [2026-09-18] [接入小毛驴统一API] 通用上游透传代理 (支持 POST 透传 uploads, kb 等)
func handleGenericPostProxy(cfg *Config, targetSubPath string) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			sendErrorJSON(w, http.StatusMethodNotAllowed, 40001, "仅支持 POST 请求")
			return
		}
		targetURL := fmt.Sprintf("%s%s", cfg.BaseURL, targetSubPath)
		upstreamReq, err := http.NewRequestWithContext(r.Context(), "POST", targetURL, r.Body)
		if err != nil {
			sendErrorJSON(w, http.StatusInternalServerError, 50001, err.Error())
			return
		}
		if ctype := r.Header.Get("Content-Type"); ctype != "" {
			upstreamReq.Header.Set("Content-Type", ctype)
		}
		upstreamReq.Header.Set("vio-source-client", cfg.SourceClient)
		if auth := r.Header.Get("Authorization"); auth != "" {
			upstreamReq.Header.Set("Authorization", auth)
		} else if cfg.JWTToken != "" {
			upstreamReq.Header.Set("Authorization", fmt.Sprintf("Bearer %s", cfg.JWTToken))
		}

		client := &http.Client{Timeout: time.Duration(cfg.JSONTimeoutSec) * time.Second}
		resp, err := client.Do(upstreamReq)
		if err != nil {
			sendErrorJSON(w, http.StatusBadGateway, 50201, fmt.Sprintf("上游服务不可达: %v", err))
			return
		}
		defer resp.Body.Close()

		if respCtype := resp.Header.Get("Content-Type"); respCtype != "" {
			w.Header().Set("Content-Type", respCtype)
		}
		w.WriteHeader(resp.StatusCode)
		_, _ = io.Copy(w, resp.Body)
	}
}

// IPRateLimiter 基于滑动窗口的轻量级单 IP 限流器
type IPRateLimiter struct {
	sync.Mutex
	ips    map[string][]time.Time
	limit  int
	window time.Duration
}

func newIPRateLimiter(limit int, window time.Duration) *IPRateLimiter {
	return &IPRateLimiter{
		ips:    make(map[string][]time.Time),
		limit:  limit,
		window: window,
	}
}

func (l *IPRateLimiter) Allow(ip string) bool {
	l.Lock()
	defer l.Unlock()
	now := time.Now()
	cutoff := now.Add(-l.window)

	timestamps, exists := l.ips[ip]
	if !exists {
		l.ips[ip] = []time.Time{now}
		return true
	}

	valid := make([]time.Time, 0, len(timestamps))
	for _, t := range timestamps {
		if t.After(cutoff) {
			valid = append(valid, t)
		}
	}
	if len(valid) >= l.limit {
		l.ips[ip] = valid
		return false
	}
	l.ips[ip] = append(valid, now)
	return true
}

func getClientIP(r *http.Request) string {
	if xff := r.Header.Get("X-Forwarded-For"); xff != "" {
		parts := strings.Split(xff, ",")
		return strings.TrimSpace(parts[0])
	}
	if xri := r.Header.Get("X-Real-IP"); xri != "" {
		return strings.TrimSpace(xri)
	}
	ip := r.RemoteAddr
	if colon := strings.LastIndex(ip, ":"); colon != -1 {
		ip = ip[:colon]
	}
	return ip
}

// 路径与标识合法性白名单校验 (防止路径穿越与 SSRF)
func isValidTaskSuffix(s string) bool {
	if len(s) == 0 || len(s) > 64 {
		return false
	}
	for _, c := range s {
		if !((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
			(c >= '0' && c <= '9') || c == '_' || c == '-') {
			return false
		}
	}
	return true
}

func isValidVoiceName(s string) bool {
	if len(s) == 0 || len(s) > 64 {
		return false
	}
	for _, c := range s {
		if !((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
			(c >= '0' && c <= '9') || c == '_' || c == '-' || c == '.') {
			return false
		}
	}
	return true
}

// 全局语音 TTS 限流器: 单 IP 每分钟最多 60 次请求 (防刷保护)
var voiceTTSLimiter = newIPRateLimiter(60, 1*time.Minute)

// [2026-09-26] [数字人与语音合成] 开放平台机器密钥 (ndsk_) 鉴权代理
func handleVoiceOpenProxy(cfg *Config, targetSubPath string) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		// 1. 严格检查网关是否配置了开放平台机器密钥 (VoiceKey)
		// 注意：不得复用 AllowMissingJWT——语音开放路由与聊天 JWT 开关解耦
		if strings.TrimSpace(cfg.VoiceKey) == "" {
			sendErrorJSON(w, http.StatusUnauthorized, 40101, "网关未配置开放平台机器密钥 (VoiceKey)")
			return
		}

		targetURL := fmt.Sprintf("%s%s", cfg.BaseURL, targetSubPath)
		// 支持类似 /api/open/v1/voice/tasks/:task_id 的动态路径透传
		if strings.HasSuffix(targetSubPath, "/") && strings.HasPrefix(r.URL.Path, targetSubPath) {
			suffix := strings.TrimPrefix(r.URL.Path, targetSubPath)
			if !isValidTaskSuffix(suffix) {
				sendErrorJSON(w, http.StatusBadRequest, 40001, "任务路径标识不合法")
				return
			}
			targetURL = fmt.Sprintf("%s%s%s", cfg.BaseURL, targetSubPath, suffix)
		}

		// 2. 针对 TTS 接口执行防刷与文本长度硬截断安全防御 (<= 2000 字符)
		var bodyReader io.Reader = r.Body
		if targetSubPath == "/api/open/v1/voice/tts" && r.Method == http.MethodPost {
			// 生产安全拦截：公网禁止直接调用任意文本 TTS 代理，除非显式开启 ALLOW_OPEN_TTS_PROXY=1
			if os.Getenv("ALLOW_OPEN_TTS_PROXY") != "1" {
				sendErrorJSON(w, http.StatusForbidden, 40301, "生产安全拦截：公网禁止直接调用任意文本 TTS 代理，文章伴读请访问 /api/voice/article-chunk")
				return
			}

			// A. IP 令牌桶限流防刷
			clientIP := getClientIP(r)
			if !voiceTTSLimiter.Allow(clientIP) {
				sendErrorJSON(w, http.StatusTooManyRequests, 42901, "请求过于频繁，触发防刷限流保护")
				return
			}

			// B. 文本长度硬顶校验 (对齐上游 2000 字符硬顶)
			bodyBytes, err := io.ReadAll(r.Body)
			if err != nil || len(bodyBytes) == 0 {
				sendErrorJSON(w, http.StatusBadRequest, 40001, "请求体读取失败或为空")
				return
			}

			var payload struct {
				Text string `json:"text"`
			}
			if err := json.Unmarshal(bodyBytes, &payload); err != nil {
				sendErrorJSON(w, http.StatusBadRequest, 40001, "请求体 JSON 格式不合法")
				return
			}
			if utf8.RuneCountInString(payload.Text) > 2000 {
				sendErrorJSON(w, http.StatusBadRequest, 40001, "文本长度超过单次上限 (最大支持 2000 字符)")
				return
			}

			bodyReader = bytes.NewReader(bodyBytes)
		}

		upstreamReq, err := http.NewRequestWithContext(r.Context(), r.Method, targetURL, bodyReader)
		if err != nil {
			sendErrorJSON(w, http.StatusInternalServerError, 50001, err.Error())
			return
		}

		if ctype := r.Header.Get("Content-Type"); ctype != "" {
			upstreamReq.Header.Set("Content-Type", ctype)
		}
		if accept := r.Header.Get("Accept"); accept != "" {
			upstreamReq.Header.Set("Accept", accept)
		}
		upstreamReq.Header.Set("vio-source-client", cfg.SourceClient)

		// 3. 严格只注入服务端 VoiceKey！彻底忽略并剥离客户端传入的 Authorization (保障前端零凭证)
		if cfg.VoiceKey != "" {
			upstreamReq.Header.Set("Authorization", fmt.Sprintf("Bearer %s", cfg.VoiceKey))
			upstreamReq.Header.Set("X-Api-Key", cfg.VoiceKey)
		}

		client := &http.Client{Timeout: 60 * time.Second}
		resp, err := client.Do(upstreamReq)
		if err != nil {
			sendErrorJSON(w, http.StatusBadGateway, 50201, fmt.Sprintf("语音服务上游不可达: %v", err))
			return
		}
		defer resp.Body.Close()

		if respCtype := resp.Header.Get("Content-Type"); respCtype != "" {
			w.Header().Set("Content-Type", respCtype)
		}
		w.WriteHeader(resp.StatusCode)
		_, _ = io.Copy(w, resp.Body)
	}
}

// =========================================================================
// 5. [POST] 官网文章伴读切片音频 Handler (/api/voice/article-chunk)
// =========================================================================
type ArticleChunkPayload struct {
	ArticleID  string `json:"article_id"`
	ChunkIndex int    `json:"chunk_index"`
	Voice      string `json:"voice"`
}

type AudioMetaFile struct {
	Slug        string `json:"slug"`
	Title       string `json:"title"`
	TotalChunks int    `json:"total_chunks"`
	Chunks      []struct {
		Index     int    `json:"index"`
		Text      string `json:"text"`
		CharCount int    `json:"char_count"`
	} `json:"chunks"`
}

func handleArticleChunk(cfg *Config) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			sendErrorJSON(w, http.StatusMethodNotAllowed, 40001, "仅支持 POST 请求")
			return
		}

		var payload ArticleChunkPayload
		if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
			sendErrorJSON(w, http.StatusBadRequest, 40001, "请求体 JSON 格式不合法")
			return
		}

		articleID := strings.TrimSpace(payload.ArticleID)
		if articleID == "" || strings.Contains(articleID, "..") || strings.Contains(articleID, "/") || strings.Contains(articleID, "\\") {
			sendErrorJSON(w, http.StatusBadRequest, 40001, "文章 ID 格式不合法")
			return
		}

		if payload.ChunkIndex < 0 {
			sendErrorJSON(w, http.StatusBadRequest, 40001, "段落序号必须 >= 0")
			return
		}

		voice := strings.TrimSpace(payload.Voice)
		if voice == "" {
			voice = "standard_female_warm"
		}
		if !isValidVoiceName(voice) {
			sendErrorJSON(w, http.StatusBadRequest, 40001, "音色标识格式不合法")
			return
		}

		// 1. 检查 30 天 LRU 本地磁盘缓存 (统一基于 ProjectRoot 检索)
		cacheDir := filepath.Join(cfg.ProjectRoot, "storage", "audio_cache")
		_ = os.MkdirAll(cacheDir, 0755)
		cacheFile := filepath.Join(cacheDir, fmt.Sprintf("%s_%d_%s.mp3", articleID, payload.ChunkIndex, voice))

		if fi, err := os.Stat(cacheFile); err == nil && fi.Size() > 0 {
			if time.Since(fi.ModTime()) < 30*24*time.Hour {
				data, err := os.ReadFile(cacheFile)
				if err == nil {
					w.Header().Set("Content-Type", "audio/mpeg")
					w.Header().Set("Cache-Control", "public, max-age=2592000")
					w.Header().Set("X-GEO-Cache", "HIT")
					w.WriteHeader(http.StatusOK)
					_, _ = w.Write(data)
					return
				}
			}
		}

		// 2. 读取本地切片元数据 (统一基于 ProjectRoot 检索)
		metaPaths := []string{
			filepath.Join(cfg.ProjectRoot, "projects", "nextgeo", "outputs", "site", "assets", "audio_meta", articleID+".json"),
			filepath.Join(cfg.ProjectRoot, "projects", "nextgeo", "outputs", "assets", "audio_meta", articleID+".json"),
			filepath.Join(cfg.ProjectRoot, "assets", "audio_meta", articleID+".json"),
		}
		var metaData []byte
		var readErr error = fmt.Errorf("not found")
		for _, p := range metaPaths {
			metaData, readErr = os.ReadFile(p)
			if readErr == nil {
				break
			}
		}
		if readErr != nil {
			sendErrorJSON(w, http.StatusNotFound, 40401, fmt.Sprintf("未找到文章【%s】的切片索引", articleID))
			return
		}

		var meta AudioMetaFile
		if err := json.Unmarshal(metaData, &meta); err != nil {
			sendErrorJSON(w, http.StatusInternalServerError, 50001, "切片索引解析失败")
			return
		}

		if payload.ChunkIndex >= len(meta.Chunks) {
			sendErrorJSON(w, http.StatusNotFound, 40401, fmt.Sprintf("段落序号 [%d] 超出文章总段落数 [%d]", payload.ChunkIndex, len(meta.Chunks)))
			return
		}

		chunkText := strings.TrimSpace(meta.Chunks[payload.ChunkIndex].Text)
		if chunkText == "" {
			sendErrorJSON(w, http.StatusBadRequest, 40001, "该段落文本为空")
			return
		}

		// 3. 服务端向小毛驴发起 TTS 请求（代持 VoiceKey）
		ttsReqBody := map[string]interface{}{
			"text":  chunkText,
			"voice": voice,
			"rate":  1.0,
			"pitch": 1.0,
			"async": false,
		}
		reqBytes, _ := json.Marshal(ttsReqBody)

		targetURL := fmt.Sprintf("%s/api/open/v1/voice/tts", cfg.BaseURL)
		upstreamReq, err := http.NewRequestWithContext(r.Context(), http.MethodPost, targetURL, bytes.NewReader(reqBytes))
		if err != nil {
			sendErrorJSON(w, http.StatusInternalServerError, 50001, err.Error())
			return
		}

		upstreamReq.Header.Set("Content-Type", "application/json")
		upstreamReq.Header.Set("vio-source-client", cfg.SourceClient)
		if cfg.VoiceKey != "" {
			upstreamReq.Header.Set("Authorization", fmt.Sprintf("Bearer %s", cfg.VoiceKey))
			upstreamReq.Header.Set("X-Api-Key", cfg.VoiceKey)
		}

		client := &http.Client{Timeout: 30 * time.Second}
		resp, err := client.Do(upstreamReq)
		if err != nil {
			sendErrorJSON(w, http.StatusBadGateway, 50201, fmt.Sprintf("上游语音服务不可达: %v", err))
			return
		}
		defer resp.Body.Close()

		respBytes, err := io.ReadAll(resp.Body)
		if err != nil {
			sendErrorJSON(w, http.StatusInternalServerError, 50001, "上游音频读取失败")
			return
		}

		if resp.StatusCode != http.StatusOK {
			w.Header().Set("Content-Type", resp.Header.Get("Content-Type"))
			w.WriteHeader(resp.StatusCode)
			_, _ = w.Write(respBytes)
			return
		}

		// 4. 成功获取音频流，写入本地磁盘缓存
		_ = os.WriteFile(cacheFile, respBytes, 0644)

		w.Header().Set("Content-Type", "audio/mpeg")
		w.Header().Set("Cache-Control", "public, max-age=2592000")
		w.Header().Set("X-GEO-Cache", "MISS")
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write(respBytes)
	}
}

// =========================================================================
// 主入口
// =========================================================================
func setupMux(cfg *Config) *http.ServeMux {
	mux := http.NewServeMux()

	// 1. 核心 AI 对外路由
	mux.HandleFunc("/api/chat/stream", corsMiddleware(cfg.AllowedOrigin, handleChatStream(cfg)))
	mux.HandleFunc("/api/chat/intent/match", corsMiddleware(cfg.AllowedOrigin, handleIntentMatch(cfg)))
	mux.HandleFunc("/api/writing/sessions", corsMiddleware(cfg.AllowedOrigin, handleWritingSessions(cfg)))

	// 2. [2026-09-18] [统一API接入] 账号认证与单点登录透传路由
	mux.HandleFunc("/api/v1/xiulan/login", corsMiddleware(cfg.AllowedOrigin, handleLoginProxy(cfg)))
	mux.HandleFunc("/api/auth/login", corsMiddleware(cfg.AllowedOrigin, handleLoginProxy(cfg)))
	mux.HandleFunc("/api/v1/sessions", corsMiddleware(cfg.AllowedOrigin, handleLoginProxy(cfg)))
	mux.HandleFunc("/api/v1/xiulan/me", corsMiddleware(cfg.AllowedOrigin, handleMeProxy(cfg)))
	mux.HandleFunc("/api/auth/me", corsMiddleware(cfg.AllowedOrigin, handleMeProxy(cfg)))
	mux.HandleFunc("/api/auth/wechat-qr", corsMiddleware(cfg.AllowedOrigin, handleWechatQRProxy(cfg)))
	mux.HandleFunc("/api/v1/auth/wechat-qr", corsMiddleware(cfg.AllowedOrigin, handleWechatQRProxy(cfg)))

	// 3. [2026-09-18] [统一API接入] 社区素材上传与知识库透传路由
	mux.HandleFunc("/api/v1/community/uploads", corsMiddleware(cfg.AllowedOrigin, handleGenericPostProxy(cfg, "/api/v1/community/uploads")))
	mux.HandleFunc("/api/kb/documents", corsMiddleware(cfg.AllowedOrigin, handleGenericPostProxy(cfg, "/api/kb/documents")))
	mux.HandleFunc("/api/v1/kb/documents", corsMiddleware(cfg.AllowedOrigin, handleGenericPostProxy(cfg, "/api/kb/documents")))
	mux.HandleFunc("/api/kb/chat", corsMiddleware(cfg.AllowedOrigin, handleGenericPostProxy(cfg, "/api/kb/chat")))
	mux.HandleFunc("/api/v1/kb/chat", corsMiddleware(cfg.AllowedOrigin, handleGenericPostProxy(cfg, "/api/kb/chat")))

	// 4. [2026-09-26] [数字人与语音合成能力包] 开放能力中继与安全代理
	mux.HandleFunc("/api/voice/article-chunk", corsMiddleware(cfg.AllowedOrigin, handleArticleChunk(cfg)))
	mux.HandleFunc("/api/open/v1/voice/tts", corsMiddleware(cfg.AllowedOrigin, handleVoiceOpenProxy(cfg, "/api/open/v1/voice/tts")))
	mux.HandleFunc("/api/open/v1/voice/tasks/", corsMiddleware(cfg.AllowedOrigin, handleVoiceOpenProxy(cfg, "/api/open/v1/voice/tasks/")))
	mux.HandleFunc("/api/open/v1/voice/voices", corsMiddleware(cfg.AllowedOrigin, handleVoiceOpenProxy(cfg, "/api/open/v1/voice/voices")))
	mux.HandleFunc("/api/voices/synthesize", corsMiddleware(cfg.AllowedOrigin, handleGenericPostProxy(cfg, "/api/voices/synthesize")))
	mux.HandleFunc("/api/audios/transcriptions", corsMiddleware(cfg.AllowedOrigin, handleGenericPostProxy(cfg, "/api/audios/transcriptions")))
	mux.HandleFunc("/api/v1/xiulan/me/avatar/voice", corsMiddleware(cfg.AllowedOrigin, handleGenericPostProxy(cfg, "/api/v1/xiulan/me/avatar/voice")))

	// 5. 健康检查端点
	mux.HandleFunc("/healthz", corsMiddleware(cfg.AllowedOrigin, func(w http.ResponseWriter, r *http.Request) {
		sendSuccessJSON(w, map[string]interface{}{
			"status":             "running",
			"gateway_port":       cfg.Port,
			"upstream_base":      cfg.BaseURL,
			"source_client":      cfg.SourceClient,
			"jwt_present":        cfg.JWTToken != "",
			"voice_key_present":  cfg.VoiceKey != "",
			"allow_missing_jwt":  cfg.AllowMissingJWT,
			"allowed_origin_cfg": cfg.AllowedOrigin,
		})
	}))

	return mux
}

func main() {
	cfg := loadConfig()
	mux := setupMux(cfg)

	addr := fmt.Sprintf("%s:%d", cfg.Host, cfg.Port)
	log.Printf("[INFO] Nextdoor AI 智能对话透明流式网关已启动")
	log.Printf("[INFO] 本地监听地址: http://%s", addr)
	log.Printf("[INFO] 对应上游 Nextdoor: %s", cfg.BaseURL)
	log.Printf("[INFO] 凭证与品牌标识: %s (JWT 配置状态: %v)", cfg.SourceClient, cfg.JWTToken != "")
	log.Printf("[INFO] CORS 严格放行源: %s", cfg.AllowedOrigin)
	log.Printf("[INFO] 项目根目录: %s", cfg.ProjectRoot)
	log.Printf("[INFO] 核心路由已就绪:")
	log.Printf("   - [SSE]  POST http://%s/api/chat/stream", addr)
	log.Printf("   - [JSON] POST http://%s/api/chat/intent/match", addr)
	log.Printf("   - [JSON] POST http://%s/api/writing/sessions", addr)

	server := &http.Server{
		Addr:         addr,
		Handler:      mux,
		ReadTimeout:  60 * time.Second,
		WriteTimeout: 30 * time.Second, // 默认 30s 写超时保护非流式端点，流式长连接端点由 ResponseController 单独放行
		IdleTimeout:  120 * time.Second,
	}

	if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		log.Fatalf("[ERROR] 网关服务启动失败: %v", err)
	}
}
