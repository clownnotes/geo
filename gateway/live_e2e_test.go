package main

import (
	"bytes"
	"net/http"
	"net/http/httptest"
	"os"
	"testing"
	"time"
)

// 针对真实开发服务器 (:3002) 的端到端全链路闭环测试 (Task 4.1 & 4.2)
func TestLiveArticleChunkE2E(t *testing.T) {
	if os.Getenv("RUN_LIVE_E2E") != "true" {
		t.Skip("跳过真实 E2E 联网测试: 需设置环境变量 RUN_LIVE_E2E=true 显式启用")
	}
	cfg := loadConfig()
	if cfg.BaseURL == "" || cfg.VoiceKey == "" {
		t.Skip("跳过真实 E2E 测试: 未配置有效 BaseURL 或 VoiceKey")
	}

	mux := setupMux(cfg)

	// 清空可能存在的旧缓存
	cacheFile := "storage/audio_cache/ai-agents-unbundle-search-direct-answers_0_standard_female_warm.mp3"
	_ = os.Remove(cacheFile)

	// 1. 发起首段直出请求 (Cache MISS -> 小毛驴开发库 :3002)
	payload := `{"article_id":"ai-agents-unbundle-search-direct-answers","chunk_index":0,"voice":"standard_female_warm"}`
	req1 := httptest.NewRequest("POST", "/api/voice/article-chunk", bytes.NewBufferString(payload))
	rec1 := httptest.NewRecorder()

	start1 := time.Now()
	mux.ServeHTTP(rec1, req1)
	elapsed1 := time.Since(start1)

	if rec1.Code != http.StatusOK {
		t.Fatalf("首段请求失败: HTTP %d, body: %s", rec1.Code, rec1.Body.String())
	}
	if rec1.Header().Get("X-GEO-Cache") != "MISS" {
		t.Fatalf("首次请求预期 X-GEO-Cache: MISS, 实际: %s", rec1.Header().Get("X-GEO-Cache"))
	}
	if rec1.Header().Get("Content-Type") != "audio/mpeg" {
		t.Fatalf("预期 Content-Type: audio/mpeg, 实际: %s", rec1.Header().Get("Content-Type"))
	}
	audioBytes := rec1.Body.Bytes()
	if len(audioBytes) < 1000 {
		t.Fatalf("返回音频过小: %d 字节", len(audioBytes))
	}
	t.Logf("✅ 首次请求成功 (Cache MISS): 耗时 %v, 音频大小 %d 字节", elapsed1, len(audioBytes))

	// 验证本地磁盘缓存文件已落盘
	fi, err := os.Stat(cacheFile)
	if err != nil || fi.Size() == 0 {
		t.Fatalf("磁盘缓存文件未正确生成: %v", err)
	}

	// 2. 发起同段落二次请求 (Cache HIT -> 0 延迟、0 上游调用、0 算力扣费)
	req2 := httptest.NewRequest("POST", "/api/voice/article-chunk", bytes.NewBufferString(payload))
	rec2 := httptest.NewRecorder()

	start2 := time.Now()
	mux.ServeHTTP(rec2, req2)
	elapsed2 := time.Since(start2)

	if rec2.Code != http.StatusOK {
		t.Fatalf("二次请求失败: HTTP %d", rec2.Code)
	}
	if rec2.Header().Get("X-GEO-Cache") != "HIT" {
		t.Fatalf("二次请求预期 X-GEO-Cache: HIT, 实际: %s", rec2.Header().Get("X-GEO-Cache"))
	}
	if elapsed2 > 50*time.Millisecond {
		t.Fatalf("本地缓存命中耗时过长: %v (预期 < 50ms)", elapsed2)
	}
	t.Logf("✅ 二次请求成功 (Cache HIT): 耗时 %v (极速本地命中), 音频大小 %d 字节", elapsed2, rec2.Body.Len())

	// 3. 验证公网无法利用旧代理传入自定义文本 (403 Forbidden 40301)
	reqEvil := httptest.NewRequest("POST", "/api/open/v1/voice/tts", bytes.NewBufferString(`{"text":"黑客试图盗刷语音算力"}`))
	recEvil := httptest.NewRecorder()
	mux.ServeHTTP(recEvil, reqEvil)

	if recEvil.Code != http.StatusForbidden {
		t.Fatalf("旧代理预期被 403 阻断, 实际得到: %d", recEvil.Code)
	}
	t.Logf("✅ 旧代理公网防护有效: 拦截状态码 %d", recEvil.Code)
}
