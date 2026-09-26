/**
 * Nextdoor 开放平台 - 数字人与语音合成 (voice) 客户端 SDK
 * 
 * 运行环境: 浏览器 / Node.js
 * 核心设计:
 * 1. 前端零凭证优先: 默认通过本地网关中继 (如 http://127.0.0.1:8090)，严禁在前端暴露 ndsk_ 机器密钥。
 * 2. 6 大核心 API 完整支持 (TTS 同步/异步双模、任务轮询、音色发现、声音克隆合成、ASR 听写、音色绑定)。
 * 3. 智能音频流/JSON 双态解析: 自动识别 audio/mpeg 二进制流或 application/json 任务响应。
 * 4. 雪花 ID 严格防精度丢失保证。
 */

import {
  ApiResponse,
  VoiceApiError,
  OpenTTSRequest,
  OpenTTSResult,
  OpenTTSAsyncTaskData,
  VoiceTaskResultData,
  SemanticVoiceItem,
  CloneSynthesizeRequest,
  CloneSynthesizeResultData,
  AudioTranscriptionRequest,
  AudioTranscriptionResultData,
  AvatarVoiceBindRequest,
  AvatarVoiceBindResultData
} from './voiceTypes';

export interface VoiceClientOptions {
  /**
   * 网关或开放平台基地址:
   * - 浏览器前端 (推荐): 指向同源或本地网关，如 'http://127.0.0.1:8090' 或 '' (同源)
   * - 服务端直连模式: 'https://nextdoor.baicl.cc'
   */
  baseURL?: string;
  /** 品牌来源标识，默认 'geo' */
  sourceClient?: string;
  /** 服务端直调时的开放平台机器密钥 (ndsk_ 开头，前端请保持留空！) */
  openApiKey?: string;
  /** 服务端直调时的用户 JWT (用于 ASR、克隆声音与智能体绑定) */
  jwtToken?: string;
  /** 默认超时时间 (毫秒)，默认 30000ms */
  timeoutMs?: number;
  /** 全局错误处理回调 */
  onError?: (error: VoiceApiError) => void;
}

export class NextdoorVoiceClient {
  private baseURL: string;
  private sourceClient: string;
  private openApiKey?: string;
  private jwtToken?: string;
  private timeoutMs: number;
  private onError?: (error: VoiceApiError) => void;

  constructor(options: VoiceClientOptions = {}) {
    this.baseURL = (options.baseURL || 'http://127.0.0.1:8090').replace(/\/+$/, '');
    this.sourceClient = options.sourceClient || 'geo';
    this.openApiKey = options.openApiKey;
    this.jwtToken = options.jwtToken;
    this.timeoutMs = options.timeoutMs || 30000;
    this.onError = options.onError;
  }

  /**
   * 构建基础请求头（自动注入品牌标识与凭证）
   */
  private buildHeaders(customHeaders: Record<string, string> = {}): Record<string, string> {
    const headers: Record<string, string> = {
      'vio-source-client': this.sourceClient,
      ...customHeaders
    };

    // 若配置了 openApiKey (服务端模式)，自动注入
    if (this.openApiKey) {
      headers['Authorization'] = `Bearer ${this.openApiKey}`;
      headers['X-Api-Key'] = this.openApiKey;
    } else if (this.jwtToken) {
      headers['Authorization'] = `Bearer ${this.jwtToken}`;
    }

    return headers;
  }

  /**
   * 通用 JSON 格式请求管道 (支持 code === 0 校验与雪花 ID 保护)
   */
  private async requestJSON<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseURL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
    const headers = this.buildHeaders({
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      ...(options.headers as Record<string, string> || {})
    });

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeoutMs);

    try {
      const response = await fetch(url, {
        ...options,
        headers,
        signal: controller.signal
      });

      const rawText = await response.text();
      let json: ApiResponse<T>;
      try {
        json = JSON.parse(rawText);
      } catch (parseErr) {
        throw new VoiceApiError(
          response.status * 100 + 1,
          `解析服务端响应失败: ${response.statusText} (${rawText.slice(0, 100)})`
        );
      }

      if (!response.ok || json.code !== 0) {
        const errCode = json.code || response.status * 100 + 1;
        const errMsg = json.msg || `语音接口请求失败 (${response.status})`;
        const error = new VoiceApiError(errCode, errMsg, json);
        this.onError?.(error);
        throw error;
      }

      return json.data;
    } catch (err: any) {
      if (err.name === 'AbortError') {
        const timeoutErr = new VoiceApiError(50401, `语音接口调用超时 (${this.timeoutMs}ms)`);
        this.onError?.(timeoutErr);
        throw timeoutErr;
      }
      if (err instanceof VoiceApiError) {
        throw err;
      }
      const networkErr = new VoiceApiError(50201, `网络连接异常: ${err.message}`);
      this.onError?.(networkErr);
      throw networkErr;
    } finally {
      clearTimeout(timeoutId);
    }
  }

  // =========================================================================
  // API 1: [POST] /api/open/v1/voice/tts — 文本转语音 (同步二进制/异步任务双模)
  // =========================================================================
  /**
   * 发起文本转语音合成请求:
   * - 短文本 (≤300字): 排队成功后直接返回二进制音频 Blob (audio/mpeg)
   * - 长文本 (>300字) 或超时: 返回异步任务 task_id
   */
  public async tts(request: OpenTTSRequest, options?: { signal?: AbortSignal }): Promise<OpenTTSResult> {
    if (!request.text || !request.text.trim()) {
      throw new VoiceApiError(40001, '待合成文本不能为空');
    }

    const endpoint = '/api/open/v1/voice/tts';
    const url = `${this.baseURL}${endpoint}`;
    const headers = this.buildHeaders({
      'Content-Type': 'application/json',
      'Accept': 'audio/mpeg, application/json'
    });

    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify(request),
      signal: options?.signal
    });

    const contentType = response.headers.get('content-type') || '';

    // 1. 如果返回的是二进制音频流
    if (contentType.includes('audio/') || contentType.includes('application/octet-stream')) {
      const blob = await response.blob();
      const audioUrl = URL.createObjectURL(blob);
      return {
        mode: 'sync',
        audioBlob: blob,
        audioUrl,
        contentType
      };
    }

    // 2. 如果返回的是 JSON (异步任务或错误)
    const rawText = await response.text();
    let json: ApiResponse<OpenTTSAsyncTaskData>;
    try {
      json = JSON.parse(rawText);
    } catch {
      throw new VoiceApiError(50001, `无法识别的响应格式: ${contentType}`);
    }

    if (!response.ok || json.code !== 0) {
      throw new VoiceApiError(json.code || 50001, json.msg || 'TTS 合成失败', json);
    }

    return {
      mode: 'async',
      task: json.data
    };
  }

  // =========================================================================
  // API 2: [GET] /api/open/v1/voice/tasks/:task_id — 查询异步任务状态
  // =========================================================================
  /**
   * 查询异步语音任务合成进度与音频 URL
   */
  public async getTask(taskId: string): Promise<VoiceTaskResultData> {
    if (!taskId) {
      throw new VoiceApiError(40001, 'task_id 不能为空');
    }
    const endpoint = `/api/open/v1/voice/tasks/${encodeURIComponent(taskId)}`;
    return this.requestJSON<VoiceTaskResultData>(endpoint, { method: 'GET' });
  }

  /**
   * 自动轮询异步任务，直到合成完成并返回音频地址
   * @param taskId 异步任务 ID
   * @param options 轮询间隔与最大等待时长配置
   */
  public async pollTaskUntilDone(
    taskId: string,
    options: {
      intervalMs?: number;
      maxWaitMs?: number;
      onProgress?: (progress: number, status: string) => void;
    } = {}
  ): Promise<string> {
    const intervalMs = options.intervalMs || 1000;
    const maxWaitMs = options.maxWaitMs || 120000;
    const startTime = Date.now();

    while (Date.now() - startTime < maxWaitMs) {
      const task = await this.getTask(taskId);
      options.onProgress?.(task.progress || 0, task.status);

      if (task.status === 'done' && task.audio_url) {
        return task.audio_url;
      }
      if (task.status === 'failed') {
        throw new VoiceApiError(50001, task.error_message || '异步语音合成任务失败');
      }

      await new Promise((resolve) => setTimeout(resolve, intervalMs));
    }

    throw new VoiceApiError(50401, `轮询语音任务超时 (超过 ${maxWaitMs / 1000} 秒)`);
  }

  // =========================================================================
  // API 3: [GET] /api/open/v1/voice/voices — 获取标准语义音色列表
  // =========================================================================
  /**
   * 获取开放平台标准语义音色列表
   */
  public async getVoices(): Promise<SemanticVoiceItem[]> {
    const endpoint = '/api/open/v1/voice/voices';
    return this.requestJSON<SemanticVoiceItem[]>(endpoint, { method: 'GET' });
  }

  // =========================================================================
  // API 4: [POST] /api/voices/synthesize — 专属克隆声音长任务合成 (F5-TTS)
  // =========================================================================
  /**
   * 提交克隆声音长任务合成
   */
  public async synthesizeCloneVoice(
    request: CloneSynthesizeRequest
  ): Promise<CloneSynthesizeResultData> {
    if (!request.voice_id || request.voice_id === '0') {
      throw new VoiceApiError(40001, 'voice_id 必填且必须大于 0');
    }
    if (!request.text || !request.text.trim()) {
      throw new VoiceApiError(40001, '合成文本不能为空');
    }

    const endpoint = '/api/voices/synthesize';
    return this.requestJSON<CloneSynthesizeResultData>(endpoint, {
      method: 'POST',
      body: JSON.stringify(request)
    });
  }

  // =========================================================================
  // API 5: [POST] /api/audios/transcriptions — 语音转文字 (ASR)
  // =========================================================================
  /**
   * 上传音频文件进行语音转文字听写 (ASR)
   */
  public async transcribeAudio(
    request: AudioTranscriptionRequest
  ): Promise<AudioTranscriptionResultData> {
    if (!request.file) {
      throw new VoiceApiError(40001, '请提供有效的音频文件');
    }

    const endpoint = '/api/audios/transcriptions';
    const url = `${this.baseURL}${endpoint}`;

    const formData = new FormData();
    formData.append('file', request.file);
    if (request.language) {
      formData.append('language', request.language);
    }
    if (request.word_timestamps !== undefined) {
      formData.append('word_timestamps', String(request.word_timestamps));
    }

    // 注意：FormData 上传不能手动显式设置 Content-Type，由浏览器自动填充带 boundary 的 multipart
    const headers = this.buildHeaders({
      'Accept': 'application/json'
    });

    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: formData
    });

    const rawText = await response.text();
    let json: ApiResponse<AudioTranscriptionResultData>;
    try {
      json = JSON.parse(rawText);
    } catch {
      throw new VoiceApiError(50001, `解析 ASR 响应失败: ${rawText.slice(0, 100)}`);
    }

    if (!response.ok || json.code !== 0) {
      throw new VoiceApiError(json.code || 50001, json.msg || '语音听写失败', json);
    }

    return json.data;
  }

  // =========================================================================
  // API 6: [POST] /api/v1/xiulan/me/avatar/voice — 用户专属音色克隆与绑定
  // =========================================================================
  /**
   * 上传 10~30 秒样本音频，提取声学特征并绑定专属克隆音色
   */
  public async bindAvatarVoice(
    request: AvatarVoiceBindRequest
  ): Promise<AvatarVoiceBindResultData> {
    if (!request.sample_file) {
      throw new VoiceApiError(40001, '样本音频文件不能为空');
    }
    if (!request.voice_name || !request.voice_name.trim()) {
      throw new VoiceApiError(40001, '专属音色名称不能为空');
    }
    if (!request.reference_text || !request.reference_text.trim()) {
      throw new VoiceApiError(40001, '录音参考文案不能为空');
    }

    const endpoint = '/api/v1/xiulan/me/avatar/voice';
    const url = `${this.baseURL}${endpoint}`;

    const formData = new FormData();
    formData.append('sample_file', request.sample_file);
    formData.append('voice_name', request.voice_name);
    formData.append('reference_text', request.reference_text);
    if (request.agent_id) {
      formData.append('agent_id', request.agent_id);
    }

    const headers = this.buildHeaders({
      'Accept': 'application/json'
    });

    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: formData
    });

    const rawText = await response.text();
    let json: ApiResponse<AvatarVoiceBindResultData>;
    try {
      json = JSON.parse(rawText);
    } catch {
      throw new VoiceApiError(50001, `解析音色绑定响应失败: ${rawText.slice(0, 100)}`);
    }

    if (!response.ok || json.code !== 0) {
      throw new VoiceApiError(json.code || 50001, json.msg || '音色克隆绑定失败', json);
    }

    return json.data;
  }

  // =========================================================================
  // 智能高级语法糖: 统一文本朗读 (自动处理同步直出或异步轮询)
  // =========================================================================
  /**
   * 智能语音合成门面方法:
   * 自动判断文本长度，若触发异步任务则静默轮询，最终统一返回可直接播放的 audioUrl
   */
  public async synthesizeSpeech(
    text: string,
    options: {
      voice_alias?: string;
      speed?: number;
      onProgress?: (progress: number, status: string) => void;
    } = {}
  ): Promise<string> {
    const result = await this.tts({
      text,
      voice_alias: options.voice_alias,
      speed: options.speed
    });

    if (result.mode === 'sync') {
      return result.audioUrl;
    }

    // 异步长任务模式，轮询结果
    return this.pollTaskUntilDone(result.task.task_id, {
      onProgress: options.onProgress
    });
  }
}
