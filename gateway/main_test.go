package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
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
