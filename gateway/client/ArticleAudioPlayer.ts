/**
 * 官网文章「AI 智能朗读」伴听播放控制器 (ArticleAudioPlayer)
 * 
 * 核心技术实现:
 * 1. 框架无关: 纯原生 TypeScript 编写，可直接注入任何静态 HTML 博客页面，也可被 Vue 3 / React 封装。
 * 2. 双模智能驱动:
 *    - 语义文本智能切片 (≤ 300 字符/分片，按句子自然停顿切分)
 *    - 首段秒开播放: 第 1 段极速返回二进制流并即刻发声
 *    - 静默管道预加载: 播放当前分片的同时，后台静默请求下一分片音频
 * 3. 浏览器多级缓存 (CacheStorage): 相同文本与音色直接命中本地离线缓存，零网络开销、零算力浪费。
 * 4. 完整播放控制: 暂停/播放、倍速切换 (1.0x ~ 2.0x)、分段进度跳跃、实时段落高亮回调。
 */

import { NextdoorVoiceClient } from './voiceClient';
import { PlayerState, SemanticVoiceItem, TextChunk } from './voiceTypes';

export interface ArticlePlayerOptions {
  /** Voice 客户端实例 */
  client: NextdoorVoiceClient;
  /** 默认音色别名 (默认: standard_female_warm) */
  defaultVoiceAlias?: string;
  /** 默认语速 (0.5 ~ 2.0，默认 1.0) */
  defaultSpeed?: number;
  /** 是否开启 CacheStorage 本地多级缓存 (默认 true) */
  enableCache?: boolean;
  /** 分片最大字符数 (默认 280 字符，安全保留在 300 字符同步阈值内) */
  maxChunkSize?: number;
  /** 状态变更监听 */
  onStateChange?: (state: PlayerState) => void;
  /** 播放进度监听 (当前秒数, 估算总秒数, 百分比 0~100) */
  onProgress?: (currentSec: number, totalSec: number, percent: number) => void;
  /** 开始播放某个分片时的回调 (用于文章 DOM 段落高亮联动) */
  onChunkStart?: (chunkIndex: number, totalChunks: number, chunkText: string) => void;
  /** 异常回调 */
  onError?: (err: Error) => void;
}

export class ArticleAudioPlayer {
  private client: NextdoorVoiceClient;
  private currentVoiceAlias: string;
  private speed: number;
  private enableCache: boolean;
  private maxChunkSize: number;

  private state: PlayerState = 'idle';
  private chunks: TextChunk[] = [];
  private currentChunkIndex: number = 0;
  private audioCache = new Map<string, string>(); // 内存二级缓存 key -> objectURL
  private audioElement: HTMLAudioElement;
  private activeAbortController: AbortController | null = null;

  private onStateChange?: (state: PlayerState) => void;
  private onProgress?: (currentSec: number, totalSec: number, percent: number) => void;
  private onChunkStart?: (chunkIndex: number, totalChunks: number, chunkText: string) => void;
  private onError?: (err: Error) => void;

  private isDestroyed = false;
  private cacheStorageName = 'geo-article-voice-cache-v1';

  constructor(options: ArticlePlayerOptions) {
    this.client = options.client;
    this.currentVoiceAlias = options.defaultVoiceAlias || 'standard_female_warm';
    this.speed = options.defaultSpeed || 1.0;
    this.enableCache = options.enableCache !== false;
    this.maxChunkSize = options.maxChunkSize || 280;

    this.onStateChange = options.onStateChange;
    this.onProgress = options.onProgress;
    this.onChunkStart = options.onChunkStart;
    this.onError = options.onError;

    // 初始化底层 HTML5 Audio 实例
    this.audioElement = new Audio();
    this.audioElement.playbackRate = this.speed;
    this.setupAudioListeners();
  }

  /**
   * 绑定原生音频事件
   */
  private setupAudioListeners(): void {
    this.audioElement.addEventListener('ended', () => {
      this.handleChunkEnded();
    });

    this.audioElement.addEventListener('timeupdate', () => {
      this.handleTimeUpdate();
    });

    this.audioElement.addEventListener('error', (e) => {
      const err = new Error(`音频播放异常: ${this.audioElement.error?.message || '未知错误'}`);
      this.setState('error');
      this.onError?.(err);
    });
  }

  /**
   * 状态流转管理器
   */
  private setState(newState: PlayerState): void {
    if (this.state === newState) return;
    this.state = newState;
    this.onStateChange?.(newState);
  }

  /**
   * 智能文本分片器:
   * 严格按照自然语言断句 (句号、感叹号、问号、换行) 拆解长文本为 ≤ maxChunkSize 的分片
   */
  public splitTextIntoChunks(text: string): TextChunk[] {
    if (!text || !text.trim()) return [];

    // 去除多余 Markdown 格式标记，保留可读正文
    const cleanText = text
      .replace(/```[\s\S]*?```/g, '') // 去除代码块
      .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1') // 提取超链接文字
      .replace(/[#*`>~_-]/g, ' ') // 移除 Markdown 特殊符号
      .replace(/\s+/g, ' ')
      .trim();

    // 正则拆分标点：保留标点符号
    const sentenceRegex = /([^。！？!?;；\n]+[。！？!?;；\n]+|[^。！？!?;；\n]+$)/g;
    const sentences = cleanText.match(sentenceRegex) || [cleanText];

    const chunks: TextChunk[] = [];
    let currentBuffer = '';

    for (const sentence of sentences) {
      if ((currentBuffer + sentence).length <= this.maxChunkSize) {
        currentBuffer += sentence;
      } else {
        if (currentBuffer.trim()) {
          chunks.push({
            index: chunks.length,
            text: currentBuffer.trim(),
            charCount: currentBuffer.trim().length
          });
        }
        // 如果单句本身就超长，进行硬切
        if (sentence.length > this.maxChunkSize) {
          let remaining = sentence;
          while (remaining.length > 0) {
            const slice = remaining.slice(0, this.maxChunkSize);
            chunks.push({
              index: chunks.length,
              text: slice.trim(),
              charCount: slice.trim().length
            });
            remaining = remaining.slice(this.maxChunkSize);
          }
          currentBuffer = '';
        } else {
          currentBuffer = sentence;
        }
      }
    }

    if (currentBuffer.trim()) {
      chunks.push({
        index: chunks.length,
        text: currentBuffer.trim(),
        charCount: currentBuffer.trim().length
      });
    }

    return chunks;
  }

  /**
   * 生成缓存哈希 Key
   */
  private generateCacheKey(text: string, voiceAlias: string): string {
    return `${voiceAlias}:${text.trim()}`;
  }

  /**
   * 从 CacheStorage 或内存中拉取已缓存的音频 Blob URL
   */
  private async getCachedAudioUrl(cacheKey: string): Promise<string | null> {
    // 1. 检查内存缓存
    if (this.audioCache.has(cacheKey)) {
      return this.audioCache.get(cacheKey)!;
    }

    // 2. 检查 CacheStorage
    if (this.enableCache && typeof caches !== 'undefined') {
      try {
        const cache = await caches.open(this.cacheStorageName);
        const match = await cache.match(new Request(`https://voice-cache.local/${encodeURIComponent(cacheKey)}`));
        if (match) {
          const blob = await match.blob();
          const url = URL.createObjectURL(blob);
          this.audioCache.set(cacheKey, url);
          return url;
        }
      } catch {
        // CacheStorage 降级
      }
    }

    return null;
  }

  /**
   * 将合成出的音频写入 CacheStorage 与内存缓存
   */
  private async setCachedAudio(cacheKey: string, blob: Blob): Promise<void> {
    const url = URL.createObjectURL(blob);
    this.audioCache.set(cacheKey, url);

    if (this.enableCache && typeof caches !== 'undefined') {
      try {
        const cache = await caches.open(this.cacheStorageName);
        const response = new Response(blob, {
          headers: { 'Content-Type': 'audio/mpeg' }
        });
        await cache.put(
          new Request(`https://voice-cache.local/${encodeURIComponent(cacheKey)}`),
          response
        );
      } catch {
        // 缓存失败忽略
      }
    }
  }

  /**
   * 获取或请求单个分片的音频 URL
   */
  private async resolveChunkAudioUrl(chunk: TextChunk, signal?: AbortSignal): Promise<string> {
    const cacheKey = this.generateCacheKey(chunk.text, this.currentVoiceAlias);
    const cachedUrl = await this.getCachedAudioUrl(cacheKey);
    if (cachedUrl) {
      return cachedUrl;
    }

    // 未命中缓存，发起 TTS 请求并绑定取消令牌
    const result = await this.client.tts(
      {
        text: chunk.text,
        voice_alias: this.currentVoiceAlias,
        speed: this.speed
      },
      { signal }
    );

    let finalUrl = '';
    if (result.mode === 'sync') {
      await this.setCachedAudio(cacheKey, result.audioBlob);
      finalUrl = this.audioCache.get(cacheKey) || result.audioUrl;
    } else {
      // 异步兜底轮询
      finalUrl = await this.client.pollTaskUntilDone(result.task.task_id);
    }

    return finalUrl;
  }

  /**
   * 静默预加载下一分片音频（与当前播放共享 AbortSignal，停止/切段时一并取消）
   */
  private preloadNextChunk(nextIndex: number, signal?: AbortSignal): void {
    if (nextIndex >= this.chunks.length) return;
    if (signal?.aborted) return;
    const nextChunk = this.chunks[nextIndex];
    const cacheKey = this.generateCacheKey(nextChunk.text, this.currentVoiceAlias);

    // 如果已经在缓存中则跳过
    if (this.audioCache.has(cacheKey)) return;

    // 后台非阻塞预加载；被 abort 时静默忽略
    this.resolveChunkAudioUrl(nextChunk, signal).catch((err: any) => {
      if (err?.name === 'AbortError' || signal?.aborted) return;
    });
  }

  /**
   * 载入待朗读的长文章文本
   */
  public loadArticle(text: string): void {
    this.stop();
    this.chunks = this.splitTextIntoChunks(text);
    this.currentChunkIndex = 0;
    this.setState('idle');
  }

  /**
   * 播放当前或指定分片
   */
  public async playChunk(index: number): Promise<void> {
    if (index < 0 || index >= this.chunks.length) return;

    // 级联取消上一次正在进行的请求，防止切段竞态与内存叠飞
    this.activeAbortController?.abort();
    this.activeAbortController = new AbortController();
    const currentSignal = this.activeAbortController.signal;

    this.currentChunkIndex = index;
    const chunk = this.chunks[index];

    this.setState('loading');
    this.onChunkStart?.(index, this.chunks.length, chunk.text);

    try {
      const audioUrl = await this.resolveChunkAudioUrl(chunk, currentSignal);
      if (this.isDestroyed || currentSignal.aborted || this.state === 'idle') return;

      this.audioElement.src = audioUrl;
      this.audioElement.playbackRate = this.speed;
      await this.audioElement.play();
      this.setState('playing');

      // 触发下一分片预加载（共用当前 AbortSignal）
      this.preloadNextChunk(index + 1, currentSignal);
    } catch (err: any) {
      if (err.name === 'AbortError' || currentSignal.aborted) {
        // 请求被主动中止 (切歌/切段/停止)，静默忽略
        return;
      }
      this.setState('error');
      this.onError?.(err);
    }
  }

  /**
   * 开始或继续朗读文章
   */
  public async play(): Promise<void> {
    if (this.chunks.length === 0) return;

    if (this.state === 'paused' && this.audioElement.src) {
      await this.audioElement.play();
      this.setState('playing');
      return;
    }

    await this.playChunk(this.currentChunkIndex);
  }

  /**
   * 暂停朗读
   */
  public pause(): void {
    if (this.state === 'playing') {
      this.audioElement.pause();
      this.setState('paused');
    }
  }

  /**
   * 切换播放/暂停状态
   */
  public togglePlay(): void {
    if (this.state === 'playing') {
      this.pause();
    } else {
      this.play();
    }
  }

  /**
   * 停止并重置到首句
   */
  public stop(): void {
    this.activeAbortController?.abort();
    this.activeAbortController = null;
    this.audioElement.pause();
    this.audioElement.currentTime = 0;
    this.currentChunkIndex = 0;
    this.setState('idle');
  }

  /**
   * 单分片播完后的流转逻辑
   */
  private handleChunkEnded(): void {
    if (this.currentChunkIndex + 1 < this.chunks.length) {
      // 自动播放下一分片
      this.playChunk(this.currentChunkIndex + 1);
    } else {
      // 全文朗读完毕
      this.setState('ended');
      this.currentChunkIndex = 0;
    }
  }

  /**
   * 时间进度更新计算
   */
  private handleTimeUpdate(): void {
    if (this.chunks.length === 0) return;

    const chunkDuration = this.audioElement.duration || 1;
    const chunkCurrent = this.audioElement.currentTime || 0;

    // 简单估算全文进度
    const chunkWeight = 100 / this.chunks.length;
    const progressPercent = Math.min(
      100,
      Math.round(
        this.currentChunkIndex * chunkWeight + (chunkCurrent / chunkDuration) * chunkWeight
      )
    );

    this.onProgress?.(
      Math.round(chunkCurrent),
      Math.round(chunkDuration * this.chunks.length),
      progressPercent
    );
  }

  /**
   * 调整播放倍速 (0.5x ~ 2.0x)
   */
  public setSpeed(speed: number): void {
    this.speed = Math.max(0.5, Math.min(2.0, speed));
    this.audioElement.playbackRate = this.speed;
  }

  /**
   * 切换当前朗读音色 (若正在播放则立即重启当前分片)
   */
  public async setVoice(voiceAlias: string): Promise<void> {
    if (this.currentVoiceAlias === voiceAlias) return;
    this.currentVoiceAlias = voiceAlias;
    this.activeAbortController?.abort();
    this.activeAbortController = null;

    if (this.state === 'playing' || this.state === 'loading') {
      await this.playChunk(this.currentChunkIndex);
    }
  }

  /**
   * 获取当前播放状态与分片信息
   */
  public getInfo() {
    return {
      state: this.state,
      currentChunkIndex: this.currentChunkIndex,
      totalChunks: this.chunks.length,
      currentVoiceAlias: this.currentVoiceAlias,
      speed: this.speed,
      currentChunkText: this.chunks[this.currentChunkIndex]?.text || ''
    };
  }

  /**
   * 销毁播放器，释放全部音频资源与 Object URL 内存
   */
  public destroy(): void {
    this.isDestroyed = true;
    this.activeAbortController?.abort();
    this.activeAbortController = null;
    this.audioElement.pause();
    this.audioElement.src = '';

    // 释放所有已创建的内存 Object URL，杜绝单页应用多文章切换时的内存泄漏
    for (const url of this.audioCache.values()) {
      try {
        if (url.startsWith('blob:')) {
          URL.revokeObjectURL(url);
        }
      } catch {
        // 忽略无效 URL 释放异常
      }
    }
    this.audioCache.clear();
  }
}
