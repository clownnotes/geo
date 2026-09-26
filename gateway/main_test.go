package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"strings"
	"sync/atomic"
	"testing"
	"time"
)

// 1. 测试 CORS 白名单安全机制
func TestCORSWhitelist(t *testing.T) {
	cfg := defaultConfig()
	cfg.AllowedOrigin = "http://127.0.0.1:8088,http://localhost:8088"
	mux := setupMux(cfg)

	// 测试用例 A: 白名单内 Origin 放行
	reqValid := httptest.NewRequest("OPTIONS", "/healthz", nil)
	reqValid.Header.Set("Origin", "http://127.0.0.1:8088")
	recValid := httptest.NewRecorder()
	mux.ServeHTTP(recValid, reqValid)

	if recValid.Code != http.StatusNoContent {
		t.Fatalf("预检请求预期状态码 204, 实际得到: %d", recValid.Code)
	}
	if recValid.Header().Get("Access-Control-Allow-Origin") != "http://127.0.0.1:8088" {
		t.Fatalf("预期 ACAO 为 http://127.0.0.1:8088, 实际得到: %s", recValid.Header().Get("Access-Control-Allow-Origin"))
	}

	// 测试用例 B: 恶意 Origin 严厉拒绝 (禁止反射)
	reqEvil := httptest.NewRequest("OPTIONS", "/healthz", nil)
	reqEvil.Header.Set("Origin", "http://evil.example")
	recEvil := httptest.NewRecorder()
	mux.ServeHTTP(recEvil, reqEvil)

	if recEvil.Code != http.StatusForbidden {
		t.Fatalf("恶意 Origin 预检请求预期被拒绝为 403 Forbidden, 实际得到: %d", recEvil.Code)
	}
	if recEvil.Header().Get("Access-Control-Allow-Origin") != "" {
		t.Fatalf("恶意 Origin 严禁回写 ACAO, 实际回写: %s", recEvil.Header().Get("Access-Control-Allow-Origin"))
	}
}

// 2. 测试未配置 JWT 凭证时按 401 / 40101 严密拦截
func TestJWTMissingRejection(t *testing.T) {
	cfg := defaultConfig()
	cfg.JWTToken = "" // 未配置 Token
	cfg.AllowMissingJWT = false
	mux := setupMux(cfg)

	body := bytes.NewBufferString(`{"messages":[{"role":"user","content":"测试"}]}`)
	req := httptest.NewRequest("POST", "/api/chat/stream", body)
	rec := httptest.NewRecorder()
	mux.ServeHTTP(rec, req)

	if rec.Code != http.StatusUnauthorized {
		t.Fatalf("未配置 JWT 预期状态码 401, 实际得到: %d", rec.Code)
	}

	var res map[string]interface{}
	json.Unmarshal(rec.Body.Bytes(), &res)
	if int(res["code"].(float64)) != 40101 {
		t.Fatalf("预期业务错误码 40101, 实际得到: %v", res["code"])
	}
}

// 3. 测试意图匹配防御性短路 (空串 & 超长短路返回 matched: false)
func TestIntentDefensiveShortCircuit(t *testing.T) {
	cfg := defaultConfig()
	cfg.JWTToken = "" // 即使没有 Token，短路请求在网关层直接响应，不报 401
	mux := setupMux(cfg)

	// 测试用例 A: 空串短路
	bodyEmpty := bytes.NewBufferString(`{"query":""}`)
	reqEmpty := httptest.NewRequest("POST", "/api/chat/intent/match", bodyEmpty)
	recEmpty := httptest.NewRecorder()
	mux.ServeHTTP(recEmpty, reqEmpty)

	if recEmpty.Code != http.StatusOK {
		t.Fatalf("空串短路预期状态码 200, 实际得到: %d", recEmpty.Code)
	}
	var resEmpty map[string]interface{}
	json.Unmarshal(recEmpty.Body.Bytes(), &resEmpty)
	dataEmpty := resEmpty["data"].(map[string]interface{})
	if dataEmpty["matched"].(bool) != false {
		t.Fatalf("空串预期 matched: false")
	}

	// 测试用例 B: 超过 60 字符短路
	longQuery := strings.Repeat("中", 61)
	bodyLong := bytes.NewBufferString(fmt.Sprintf(`{"query":"%s"}`, longQuery))
	reqLong := httptest.NewRequest("POST", "/api/chat/intent/match", bodyLong)
	recLong := httptest.NewRecorder()
	mux.ServeHTTP(recLong, reqLong)

	if recLong.Code != http.StatusOK {
		t.Fatalf("超长短路预期状态码 200, 实际得到: %d", recLong.Code)
	}
	var resLong map[string]interface{}
	json.Unmarshal(recLong.Body.Bytes(), &resLong)
	dataLong := resLong["data"].(map[string]interface{})
	if dataLong["matched"].(bool) != false {
		t.Fatalf("超长输入预期 matched: false")
	}
}

// 4. 测试客户端 Abort 触发 Context Cancel 连带取消上游请求 (验证 tasks 4.1)
func TestClientAbortUpstreamCancellation(t *testing.T) {
	var upstreamCanceled int32

	// 构造假上游 Nextdoor 服务
	upstream := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/event-stream")
		flusher, _ := w.(http.Flusher)
		fmt.Fprintf(w, "data: {\"delta\":\"第一字\"}\n\n")
		flusher.Flush()

		// 监听请求 context 是否被取消
		select {
		case <-r.Context().Done():
			atomic.StoreInt32(&upstreamCanceled, 1)
			return
		case <-time.After(2 * time.Second):
			// 若超时未感知到取消则失败
			return
		}
	}))
	defer upstream.Close()

	cfg := defaultConfig()
	cfg.BaseURL = upstream.URL
	cfg.JWTToken = "mock-jwt"
	mux := setupMux(cfg)

	// 模拟带 Cancel 的客户端上下文
	ctx, cancel := context.WithCancel(context.Background())
	body := bytes.NewBufferString(`{"messages":[{"role":"user","content":"测试中断"}]}`)
	req := httptest.NewRequest("POST", "/api/chat/stream", body).WithContext(ctx)

	// 使用管道模拟流式响应读取
	pr, pw := io.Pipe()
	rec := &pipeResponseWriter{header: make(http.Header), pw: pw}

	done := make(chan struct{})
	go func() {
		defer close(done)
		mux.ServeHTTP(rec, req)
	}()

	// 读取首包之后立即 cancel
	buf := make([]byte, 128)
	_, _ = pr.Read(buf)
	cancel() // 模拟浏览器主动 abort
	pw.Close()

	<-done

	// 等待并断言上游 context 是否连带感知到取消
	time.Sleep(100 * time.Millisecond)
	if atomic.LoadInt32(&upstreamCanceled) != 1 {
		t.Fatalf("客户端 abort 后，上游未成功感知到 context cancellation！")
	}
}

// 管道 ResponseWriter 用于测试流式输出与取消
type pipeResponseWriter struct {
	header http.Header
	pw     *io.PipeWriter
	code   int
}

func (p *pipeResponseWriter) Header() http.Header { return p.header }
func (p *pipeResponseWriter) Write(b []byte) (int, error) {
	return p.pw.Write(b)
}
func (p *pipeResponseWriter) WriteHeader(statusCode int) { p.code = statusCode }
func (p *pipeResponseWriter) Flush()                     {}

// =========================================================================
// 5. 语音模块 (Voice) 安全代理测试套件
// =========================================================================

// 5.0 测试公网默认严密阻断任意文本 TTS 代理 (未显式开启 ALLOW_OPEN_TTS_PROXY=1 时返回 403 / 40301)
func TestVoiceTTSForbiddenByDefault(t *testing.T) {
	t.Setenv("ALLOW_OPEN_TTS_PROXY", "")
	cfg := defaultConfig()
	cfg.VoiceKey = "ndsk_test_key"
	mux := setupMux(cfg)

	body := bytes.NewBufferString(`{"text":"测试公网未授权代理拦截"}`)
	req := httptest.NewRequest("POST", "/api/open/v1/voice/tts", body)
	rec := httptest.NewRecorder()
	mux.ServeHTTP(rec, req)

	if rec.Code != http.StatusForbidden {
		t.Fatalf("未开启代理标志时预期 403 Forbidden, 实际得到: %d", rec.Code)
	}
	var res map[string]interface{}
	_ = json.Unmarshal(rec.Body.Bytes(), &res)
	if int(res["code"].(float64)) != 40301 {
		t.Fatalf("预期安全拦截错误码 40301, 实际得到: %v", res["code"])
	}
}

// 5.1 测试未配置 VoiceKey 时严密拒绝 401 / 40101
func TestVoiceTTSMissingKeyRejection(t *testing.T) {
	t.Setenv("ALLOW_OPEN_TTS_PROXY", "1")
	cfg := defaultConfig()
	cfg.VoiceKey = ""
	cfg.AllowMissingJWT = false
	mux := setupMux(cfg)

	body := bytes.NewBufferString(`{"text":"测试未配置密钥"}`)
	req := httptest.NewRequest("POST", "/api/open/v1/voice/tts", body)
	rec := httptest.NewRecorder()
	mux.ServeHTTP(rec, req)

	if rec.Code != http.StatusUnauthorized {
		t.Fatalf("未配置 VoiceKey 预期状态码 401, 实际得到: %d", rec.Code)
	}

	var res map[string]interface{}
	_ = json.Unmarshal(rec.Body.Bytes(), &res)
	if int(res["code"].(float64)) != 40101 {
		t.Fatalf("预期业务错误码 40101, 实际得到: %v", res["code"])
	}
}

// 5.2 测试文本超过 2000 字符硬顶拦截 400 / 40001
func TestVoiceTTSTextTruncation(t *testing.T) {
	t.Setenv("ALLOW_OPEN_TTS_PROXY", "1")
	cfg := defaultConfig()
	cfg.VoiceKey = "ndsk_test_key"
	mux := setupMux(cfg)

	// 构造 2001 字符超长文本 (对齐上游 2000 字符限制)
	overLimitText := strings.Repeat("字", 2001)
	payload, _ := json.Marshal(map[string]string{"text": overLimitText})
	req := httptest.NewRequest("POST", "/api/open/v1/voice/tts", bytes.NewReader(payload))
	rec := httptest.NewRecorder()
	mux.ServeHTTP(rec, req)

	if rec.Code != http.StatusBadRequest {
		t.Fatalf("超过 2000 字符预期被拒绝为 400 Bad Request, 实际得到: %d", rec.Code)
	}

	var res map[string]interface{}
	_ = json.Unmarshal(rec.Body.Bytes(), &res)
	if int(res["code"].(float64)) != 40001 {
		t.Fatalf("预期业务错误码 40001, 实际得到: %v", res["code"])
	}
}

// 5.3 测试彻底剥离客户端 Authorization，强制使用服务端 VoiceKey
func TestVoiceOpenProxyAuthorizationStripping(t *testing.T) {
	t.Setenv("ALLOW_OPEN_TTS_PROXY", "1")
	var capturedAuth string
	var capturedSourceClient string

	// 构造模拟上游
	upstream := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		capturedAuth = r.Header.Get("Authorization")
		capturedSourceClient = r.Header.Get("vio-source-client")
		w.Header().Set("Content-Type", "audio/mpeg")
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("fake-mp3-bytes"))
	}))
	defer upstream.Close()

	cfg := defaultConfig()
	cfg.BaseURL = upstream.URL
	cfg.SourceClient = "geo-test"
	cfg.VoiceKey = "ndsk_server_secret_voice_key"
	mux := setupMux(cfg)

	body := bytes.NewBufferString(`{"text":"正常短文本"}`)
	req := httptest.NewRequest("POST", "/api/open/v1/voice/tts", body)
	// 客户端恶意或误传 Authorization
	req.Header.Set("Authorization", "Bearer evil_client_jwt_or_key")

	rec := httptest.NewRecorder()
	mux.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("预期成功 200, 实际得到: %d", rec.Code)
	}
	// 断言上游收到的是服务端 VoiceKey，而不是客户端的 evil token
	expectedAuth := "Bearer ndsk_server_secret_voice_key"
	if capturedAuth != expectedAuth {
		t.Fatalf("客户端 Authorization 未被彻底剥离！预期上游收到 %s, 实际收到: %s", expectedAuth, capturedAuth)
	}
	if capturedSourceClient != "geo-test" {
		t.Fatalf("上游未收到正确的 source_client: %s", capturedSourceClient)
	}
}

// 5.4 测试单 IP 触发防刷限流 429 / 42901
func TestVoiceTTSRateLimiting(t *testing.T) {
	t.Setenv("ALLOW_OPEN_TTS_PROXY", "1")
	cfg := defaultConfig()
	cfg.VoiceKey = "ndsk_test_key"
	mux := setupMux(cfg)

	// 临时创建一个极小限额限流器用于快速单测
	origLimiter := voiceTTSLimiter
	voiceTTSLimiter = newIPRateLimiter(2, 1*time.Minute)
	defer func() { voiceTTSLimiter = origLimiter }()

	payload := `{"text":"限流测试文本"}`
	testIP := "192.168.100.200:12345"

	// 第 1 次：允许
	req1 := httptest.NewRequest("POST", "/api/open/v1/voice/tts", bytes.NewBufferString(payload))
	req1.RemoteAddr = testIP
	rec1 := httptest.NewRecorder()
	mux.ServeHTTP(rec1, req1)
	if rec1.Code == http.StatusTooManyRequests {
		t.Fatalf("第 1 次请求不应被限流")
	}

	// 第 2 次：允许
	req2 := httptest.NewRequest("POST", "/api/open/v1/voice/tts", bytes.NewBufferString(payload))
	req2.RemoteAddr = testIP
	rec2 := httptest.NewRecorder()
	mux.ServeHTTP(rec2, req2)
	if rec2.Code == http.StatusTooManyRequests {
		t.Fatalf("第 2 次请求不应被限流")
	}

	// 第 3 次：触发限流 429
	req3 := httptest.NewRequest("POST", "/api/open/v1/voice/tts", bytes.NewBufferString(payload))
	req3.RemoteAddr = testIP
	rec3 := httptest.NewRecorder()
	mux.ServeHTTP(rec3, req3)
	if rec3.Code != http.StatusTooManyRequests {
		t.Fatalf("第 3 次请求预期被限流 429, 实际得到: %d", rec3.Code)
	}

	var res map[string]interface{}
	_ = json.Unmarshal(rec3.Body.Bytes(), &res)
	if int(res["code"].(float64)) != 42901 {
		t.Fatalf("预期限流业务码 42901, 实际得到: %v", res["code"])
	}
}

// 5.5 测试官网文章伴读切片接口 (POST /api/voice/article-chunk)
func TestArticleChunkEndpoint(t *testing.T) {
	var upstreamCalled int32
	var capturedVoiceReq map[string]interface{}

	upstream := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		atomic.AddInt32(&upstreamCalled, 1)
		_ = json.NewDecoder(r.Body).Decode(&capturedVoiceReq)
		w.Header().Set("Content-Type", "audio/mpeg")
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("mock-mp3-stream-data"))
	}))
	defer upstream.Close()

	cfg := defaultConfig()
	cfg.BaseURL = upstream.URL
	cfg.VoiceKey = "ndsk_chunk_test_key"
	mux := setupMux(cfg)

	// 准备临时缓存目录并清空测试残留
	cacheFile := "storage/audio_cache/ai-agents-unbundle-search-direct-answers_0_standard_female_warm.mp3"
	_ = os.Remove(cacheFile)
	defer os.Remove(cacheFile)

	// Case A: 非法方法 GET
	reqGet := httptest.NewRequest("GET", "/api/voice/article-chunk", nil)
	recGet := httptest.NewRecorder()
	mux.ServeHTTP(recGet, reqGet)
	if recGet.Code != http.StatusMethodNotAllowed {
		t.Fatalf("GET 请求预期 405, 实际得到: %d", recGet.Code)
	}

	// Case B: 路径穿越非法 article_id
	badBody := bytes.NewBufferString(`{"article_id":"../../etc/passwd","chunk_index":0}`)
	reqBad := httptest.NewRequest("POST", "/api/voice/article-chunk", badBody)
	recBad := httptest.NewRecorder()
	mux.ServeHTTP(recBad, reqBad)
	if recBad.Code != http.StatusBadRequest {
		t.Fatalf("路径穿越预期 400, 实际得到: %d", recBad.Code)
	}

	// Case C: 文章未找到 404
	notFoundBody := bytes.NewBufferString(`{"article_id":"non-existent-article-xyz","chunk_index":0}`)
	reqNotFound := httptest.NewRequest("POST", "/api/voice/article-chunk", notFoundBody)
	recNotFound := httptest.NewRecorder()
	mux.ServeHTTP(recNotFound, reqNotFound)
	if recNotFound.Code != http.StatusNotFound {
		t.Fatalf("不存在文章预期 404, 实际得到: %d", recNotFound.Code)
	}

	// Case D: 首次正常请求 (MISS -> 请求上游小毛驴 -> 写入磁盘缓存)
	validBody := bytes.NewBufferString(`{"article_id":"ai-agents-unbundle-search-direct-answers","chunk_index":0,"voice":"standard_female_warm"}`)
	reqValid := httptest.NewRequest("POST", "/api/voice/article-chunk", validBody)
	recValid := httptest.NewRecorder()
	mux.ServeHTTP(recValid, reqValid)

	if recValid.Code != http.StatusOK {
		t.Fatalf("首次正常请求预期 200, 实际得到: %d, body: %s", recValid.Code, recValid.Body.String())
	}
	if recValid.Header().Get("X-GEO-Cache") != "MISS" {
		t.Fatalf("首次请求预期 X-GEO-Cache: MISS, 实际: %s", recValid.Header().Get("X-GEO-Cache"))
	}
	if recValid.Body.String() != "mock-mp3-stream-data" {
		t.Fatalf("返回音频内容与上游不一致: %s", recValid.Body.String())
	}
	if atomic.LoadInt32(&upstreamCalled) != 1 {
		t.Fatalf("预期上游被调用 1 次, 实际: %d", atomic.LoadInt32(&upstreamCalled))
	}
	// 断言向小毛驴发出的上游请求使用的是标准契约字段
	if capturedVoiceReq["voice"] != "standard_female_warm" || capturedVoiceReq["rate"] != 1.0 {
		t.Fatalf("上游请求字段与契约不符: %+v", capturedVoiceReq)
	}

	// Case E: 二次请求命中 30 天 LRU 本地磁盘缓存 (HIT -> 0 上游调用)
	reqHit := httptest.NewRequest("POST", "/api/voice/article-chunk", bytes.NewBufferString(`{"article_id":"ai-agents-unbundle-search-direct-answers","chunk_index":0,"voice":"standard_female_warm"}`))
	recHit := httptest.NewRecorder()
	mux.ServeHTTP(recHit, reqHit)

	if recHit.Code != http.StatusOK {
		t.Fatalf("二次缓存命中请求预期 200, 实际得到: %d", recHit.Code)
	}
	if recHit.Header().Get("X-GEO-Cache") != "HIT" {
		t.Fatalf("二次请求预期 X-GEO-Cache: HIT, 实际: %s", recHit.Header().Get("X-GEO-Cache"))
	}
	// 上游调用次数应该仍然为 1 (0 上游调用)
	if atomic.LoadInt32(&upstreamCalled) != 1 {
		t.Fatalf("二次缓存命中请求不应调用上游！实际调用次数: %d", atomic.LoadInt32(&upstreamCalled))
	}
}
