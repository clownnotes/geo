/**
 * Nextdoor 开放平台本地网关客户端 SDK
 * 运行环境: 浏览器 / Node.js
 * 核心特性: 前端零 Token 鉴权负担、SSE 流式打字机透传、Unicode 码点短路、雪花 ID 安全保证
 */

import {
  ApiResponse,
  LocalGatewayOptions,
  StreamChatRequest,
  StreamChatHandlers,
  IntentMatchRequest,
  IntentMatchResult,
  CreateWritingSessionRequest,
  WritingSession,
  GatewayApiError
} from './types';

export class NextdoorLocalClient {
  private baseURL: string;
  private onError?: (error: GatewayApiError) => void;

  constructor(options: LocalGatewayOptions = {}) {
    this.baseURL = (options.gatewayBaseURL || 'http://127.0.0.1:8090').replace(/\/+$/, '');
    this.onError = options.onError;
  }

  /**
   * 基础统一 JSON 请求封装
   */
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseURL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      ...(options.headers as Record<string, string> || {})
    };

    let response: Response;
    try {
      response = await fetch(url, { ...options, headers });
    } catch (err: any) {
      const error = new GatewayApiError(50201, `本地网关不可达 (${url}): ${err.message}`);
      this.onError?.(error);
      throw error;
    }

    if (!response.ok) {
      let errData: any = null;
      try {
        errData = await response.json();
      } catch {
        // ignore
      }
      const code = errData?.code || response.status * 100 + 1;
      const msg = errData?.msg || `HTTP 请求异常: ${response.statusText}`;
      const error = new GatewayApiError(code, msg, errData);
      this.onError?.(error);
      throw error;
    }

    const resJson: ApiResponse<T> = await response.json();

    // 严格以 code === 0 判定成功
    if (resJson.code !== 0) {
      const error = new GatewayApiError(resJson.code, resJson.msg || '未知网关业务错误', resJson.data);
      this.onError?.(error);
      throw error;
    }

    return resJson.data;
  }

  // =========================================================================
  // 1. [SSE] 智能体流式对话 (POST /api/chat/stream)
  // =========================================================================
  public async streamChat(
    payload: StreamChatRequest,
    handlers: StreamChatHandlers,
    signal?: AbortSignal
  ): Promise<string> {
    const url = `${this.baseURL}/api/chat/stream`;

    handlers.onStart?.();

    let response: Response;
    try {
      response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream'
        },
        body: JSON.stringify(payload),
        signal
      });
    } catch (err: any) {
      if (err.name === 'AbortError') {
        handlers.onFinish?.('');
        return '';
      }
      const error = new GatewayApiError(50201, `无法连接本地网关 (${url}): ${err.message}`);
      handlers.onError?.(error);
      throw error;
    }

    // 握手阶段失败 (返回的是标准错误信封)
    if (!response.ok) {
      let errData: any = null;
      try {
        errData = await response.json();
      } catch {
        // ignore
      }
      const code = errData?.code || response.status * 100 + 1;
      const msg = errData?.msg || `流式对话连接失败: ${response.statusText}`;
      const error = new GatewayApiError(code, msg, errData);
      handlers.onError?.(error);
      throw error;
    }

    if (!response.body) {
      const error = new Error('当前环境不支持 ReadableStream');
      handlers.onError?.(error);
      throw error;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';
    let fullText = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // 保持分行断句完整

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed || trimmed.startsWith(':')) continue;

          if (trimmed.startsWith('data:')) {
            const rawData = trimmed.slice(5).trim();
            if (rawData === '[DONE]') {
              break;
            }

            try {
              if (rawData.startsWith('{') && rawData.endsWith('}')) {
                const parsed = JSON.parse(rawData);

                // 检查中途中断的 error 补发帧
                if (parsed.event === 'error') {
                  const error = new GatewayApiError(parsed.code || 50202, parsed.msg || '上游连接异常中断');
                  handlers.onError?.(error);
                  continue;
                }

                // 检查意图触发事件
                if (parsed.event === 'intent_trigger') {
                  handlers.onIntentTrigger?.(parsed.data);
                  continue;
                }

                const chunk = parsed.delta || parsed.content || '';
                fullText += chunk;
                handlers.onChunk?.(chunk, fullText);
              } else {
                fullText += rawData;
                handlers.onChunk?.(rawData, fullText);
              }
            } catch {
              fullText += rawData;
              handlers.onChunk?.(rawData, fullText);
            }
          }
        }
      }

      handlers.onFinish?.(fullText);
      return fullText;
    } catch (err: any) {
      if (err.name === 'AbortError') {
        handlers.onFinish?.(fullText);
        return fullText;
      }
      handlers.onError?.(err);
      throw err;
    }
  }

  // =========================================================================
  // 2. [POST] 意图匹配与智能体路由 (POST /api/chat/intent/match)
  // =========================================================================
  public async matchIntent(params: IntentMatchRequest): Promise<IntentMatchResult> {
    const rawQuery = (params.query || '').trim();
    // 使用 Array.from 准确统计 Unicode 码点数 (对齐 Go 端 utf8.RuneCountInString)
    const runeCount = Array.from(rawQuery).length;

    // 前端防短路守卫：空串或超长直接在客户端短路返回，零网络消耗
    if (runeCount === 0 || runeCount > 60) {
      return {
        matched: false,
        query: rawQuery
      };
    }

    return this.request<IntentMatchResult>('/api/chat/intent/match', {
      method: 'POST',
      body: JSON.stringify({
        query: rawQuery,
        ...(params.session_id ? { session_id: String(params.session_id) } : {})
      })
    });
  }

  // =========================================================================
  // 3. [POST] 长文与剧本创作工作流会话 (POST /api/writing/sessions)
  // =========================================================================
  public async createWritingSession(
    payload: CreateWritingSessionRequest
  ): Promise<WritingSession> {
    if (!payload.topic?.trim()) {
      throw new GatewayApiError(40001, '创作主题 topic 不能为空');
    }

    return this.request<WritingSession>('/api/writing/sessions', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }
}
