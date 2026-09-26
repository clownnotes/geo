/**
 * Nextdoor 开放平台 - 数字人与语音合成 (voice) 模块
 * TypeScript 完整接口规范与数据模型
 * 
 * 架构规范约束:
 * 1. 雪花 ID 铁律: 所有 ID (task_id, voice_id, agent_id 等) 必须以 string 处理，严禁转为 Number。
 * 2. 统一信封: 遵循 { code: number, msg: string, data: T }，以 code === 0 判定业务成功。
 * 3. 前端零凭证: 浏览器前端严禁硬编码 ndsk_ 机器密钥，所有请求统一经由网关转发，凭证在服务端注入。
 */

// =========================================================================
// 1. 通用响应与网关信封
// =========================================================================

export interface ApiResponse<T = any> {
  code: number;
  msg: string;
  data: T;
}

export class VoiceApiError extends Error {
  public code: number;
  public details?: any;

  constructor(code: number, message: string, details?: any) {
    super(message);
    this.name = 'VoiceApiError';
    this.code = code;
    this.details = details;
  }
}

// =========================================================================
// 2. 核心枚举定义
// =========================================================================

/** 异步语音合成任务状态枚举 */
export type VoiceTaskStatus = 'queued' | 'processing' | 'done' | 'failed';

/** 标准语义音色别名 */
export type StandardVoiceAlias =
  | 'standard_female_warm'       // 温柔亲切女声
  | 'standard_male_magnetic'     // 磁性沉稳男声
  | 'standard_female_news'       // 专业播报女声
  | 'standard_male_narrator'     // 深度解说男声
  | 'standard_female_assistant'  // 智能助手女声
  | string;                      // 允许自定义或扩展别名

/** 音频格式 */
export type AudioFormat = 'mp3' | 'wav' | 'pcm' | 'opus';

// =========================================================================
// 3. API 1: [POST] /api/open/v1/voice/tts — 文本转语音 (同步直出/异步双模)
// =========================================================================

export interface OpenTTSRequest {
  /** 待合成文本内容 (必填，单次上限 2000 字符) */
  text: string;
  /** 语义音色别名或URI (如 standard_female_warm)，留空则使用系统默认 */
  voice?: StandardVoiceAlias;
  /** 语速比例，范围 0.5 ~ 2.0，默认 1.0 */
  rate?: number;
  /** 音调比例，范围 0.5 ~ 2.0，默认 1.0 */
  pitch?: number;
  /** 是否强制异步排队模式 */
  async?: boolean;
  /** 兼容别名字段 */
  voice_alias?: StandardVoiceAlias;
  speed?: number;
  /** 音频格式，默认 mp3 */
  format?: AudioFormat;
  /** 外部业务关联标识 (仅用于追踪，非必填) */
  trace_id?: string;
}

/** 文章伴读段落请求模型 (方案 A 前端零文本) */
export interface ArticleChunkRequest {
  /** 文章唯一标识 slug */
  article_id: string;
  /** 段落切片序号 (从 0 开始) */
  chunk_index: number;
  /** 音色代号 (缺省默认 standard_female_warm) */
  voice?: StandardVoiceAlias;
}

/** 长文本或超时降级时的异步任务创建结果 */
export interface OpenTTSAsyncTaskData {
  /** 任务雪花 ID (严格 string) */
  task_id: string;
  /** 当前任务状态 */
  status: VoiceTaskStatus;
  /** 预估扣除算力点数 */
  deducted_points?: number;
  /** 任务创建时间 (ISO 8601) */
  created_at?: string;
}

/** TTS 调用的综合返回结果（同步二进制或异步任务） */
export type OpenTTSResult =
  | {
      mode: 'sync';
      audioBlob: Blob;
      audioUrl: string;
      contentType: string;
    }
  | {
      mode: 'async';
      task: OpenTTSAsyncTaskData;
    };

// =========================================================================
// 4. API 2: [GET] /api/open/v1/voice/tasks/:task_id — 查询异步任务状态
// =========================================================================

export interface VoiceTaskResultData {
  /** 任务雪花 ID (严格 string) */
  task_id: string;
  /** 任务当前状态 */
  status: VoiceTaskStatus;
  /** 合成进度 (0 ~ 100) */
  progress: number;
  /** 完成时的音频公网下载/播放 URL */
  audio_url?: string;
  /** 音频时长 (秒) */
  duration_seconds?: number;
  /** 实际字数统计 */
  character_count?: number;
  /** 失败原因 */
  error_message?: string;
  /** 创建时间 */
  created_at?: string;
  /** 完成时间 */
  finished_at?: string;
}

// =========================================================================
// 5. API 3: [GET] /api/open/v1/voice/voices — 获取标准语义音色列表
// =========================================================================

export interface SemanticVoiceItem {
  /** 语义音色唯一别名 (如 standard_female_warm) */
  voice_alias: string;
  /** 人性化音色名称 (如 "温婉知性 · 佳悦") */
  name: string;
  /** 性别标识: 'female' | 'male' | 'neutral' */
  gender: 'female' | 'male' | 'neutral';
  /** 适用语言标签 (如 'zh-CN', 'en-US') */
  locale: string;
  /** 场景推荐描述 (如 "适合知识讲解、官网博客伴读") */
  scenario: string;
  /** 试听样音 URL */
  sample_audio_url?: string;
  /** 试听推荐文本 */
  sample_text?: string;
}

// =========================================================================
// 6. API 4: [POST] /api/voices/synthesize — 专属克隆声音长任务合成 (F5-TTS)
// =========================================================================

export interface CloneSynthesizeRequest {
  /** 专属克隆音色 ID (雪花 ID，严格为 string，且值必须有效) */
  voice_id: string;
  /** 待合成文字内容 */
  text: string;
  /** 语速比例，默认 1.0 */
  speed?: number;
  /** 是否去除静音首尾 */
  remove_silence?: boolean;
}

export interface CloneSynthesizeResultData {
  /** 任务雪花 ID (严格 string) */
  task_id: string;
  /** 任务状态 */
  status: VoiceTaskStatus;
  /** 消耗算力点数 */
  consumed_credits: number;
}

// =========================================================================
// 7. API 5: [POST] /api/audios/transcriptions — 语音转文字 (ASR)
// =========================================================================

export interface AudioTranscriptionRequest {
  /** 音频文件二进制 (Blob 或 File) */
  file: Blob | File;
  /** 音频语种提示 (可选，如 'zh', 'en') */
  language?: string;
  /** 是否需要返回时间戳词级切片 */
  word_timestamps?: boolean;
}

export interface TranscriptionWordSlice {
  word: string;
  start_ms: number;
  end_ms: number;
}

export interface AudioTranscriptionResultData {
  /** 识别出的完整文本内容 */
  text: string;
  /** 音频总时长 (秒) */
  duration_seconds: number;
  /** 语种标识 */
  language: string;
  /** 词级切片详情 (若请求时开启) */
  words?: TranscriptionWordSlice[];
}

// =========================================================================
// 8. API 6: [POST] /api/v1/xiulan/me/avatar/voice — 用户专属音色克隆与绑定
// =========================================================================

export interface AvatarVoiceBindRequest {
  /** 10~30 秒的高清录音样本 (Blob 或 File) */
  sample_file: Blob | File;
  /** 专属音色名称 (如 "李总数字人原声") */
  voice_name: string;
  /** 录音对应的参考文本内容 (用于精准声学特征提取) */
  reference_text: string;
  /** 绑定的数字人/智能体 ID (可选，不填默认绑定到当前登录智能体) */
  agent_id?: string;
}

export interface AvatarVoiceBindResultData {
  /** 生成的克隆音色雪花 ID (严格 string) */
  voice_id: string;
  /** 音色名称 */
  voice_name: string;
  /** 绑定生效的智能体 ID */
  bound_agent_id: string;
  /** 试听音频地址 */
  preview_audio_url?: string;
  /** 状态 */
  status: 'active' | 'processing' | 'failed';
}

// =========================================================================
// 9. 智能分片与客户端播放状态
// =========================================================================

export interface TextChunk {
  index: number;
  text: string;
  charCount: number;
}

export type PlayerState = 'idle' | 'loading' | 'playing' | 'paused' | 'ended' | 'error';

export interface PlayerEventMap {
  stateChange: (state: PlayerState) => void;
  progress: (currentSec: number, totalSec: number, percent: number) => void;
  chunkStart: (chunkIndex: number, totalChunks: number, chunkText: string) => void;
  voiceChange: (voice: SemanticVoiceItem) => void;
  error: (error: Error) => void;
}
