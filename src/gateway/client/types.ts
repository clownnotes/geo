/**
 * Nextdoor 开放平台 AI 智能对话交互能力包 - TypeScript 类型定义
 * 
 * 铁律约束:
 * 1. 雪花 ID 铁律: 所有 ID (session_id, agent_id, tool_id 等) 必须声明为 string 类型，严禁转为 Number。
 * 2. 统一信封: 非流式接口必须遵循 { code, msg, data }，严格以 code === 0 判定业务成功。
 * 3. 前端零凭证: 前端无需携带 JWT Token 与 vio-source-client，直接调用本地网关 (http://127.0.0.1:8090)。
 */

// 1. 统一响应信封
export interface ApiResponse<T = any> {
  code: number;
  msg: string;
  data: T;
}

// 2. 本地网关客户端初始化配置
export interface LocalGatewayOptions {
  gatewayBaseURL?: string; // 默认: http://127.0.0.1:8090
  onError?: (error: GatewayApiError) => void;
}

// 3. 对话消息模型
export type MessageRole = 'user' | 'assistant' | 'system';

export interface ChatMessage {
  id?: string;               // 消息雪花 ID (必须为 string)
  role: MessageRole;
  content: string;
  created_at?: string;
  vision_image_url?: string; // 多模态图片链接
}

// 4. SSE 流式对话请求与回调
export interface StreamChatRequest {
  messages: ChatMessage[];
  session_id?: string;       // 会话雪花 ID (必须为 string)
  persona?: string;          // 智能体人设设定
  vision_image_url?: string; // 多模态图片
}

export interface StreamChatHandlers {
  onStart?: () => void;
  onChunk?: (delta: string, accumulatedText: string) => void;
  onIntentTrigger?: (intentData: any) => void;
  onFinish?: (fullResponse: string) => void;
  onError?: (error: Error) => void;
}

// 5. 意图匹配与智能体候选卡片
export interface IntentMatchRequest {
  query: string;             // 用户输入的短句 (1 <= Unicode码点 <= 60)
  session_id?: string;
}

export interface CandidateAgent {
  agent_id: string;          // 智能体雪花 ID (string)
  name: string;
  avatar_url?: string;
  description: string;
  matched_score: number;
}

export interface ToolCard {
  tool_id: string;           // 工具雪花 ID (string)
  name: string;
  action_type: string;
  summary: string;
  icon?: string;
}

export interface IntentMatchResult {
  matched: boolean;
  query: string;
  intent_type?: string;
  candidate_agents?: CandidateAgent[];
  tool_cards?: ToolCard[];
}

// 6. 长文与剧本创作工作流会话 (Phase-1 范围)
export interface CreateWritingSessionRequest {
  topic: string;             // 创作主题 (必填)
  genre?: string;            // 题材，如 "深度行业商业白皮书"
  target_words?: number;     // 目标字数
  requirements?: string;     // 创作要求或大纲指导
  options?: Record<string, unknown>;
}

export interface WritingStep {
  step_index: number;
  step_title: string;
  status: 'pending' | 'generating' | 'locked' | 'completed';
  content?: string;
}

export interface WritingSession {
  session_id: string;        // 会话雪花 ID (string)
  topic: string;
  genre: string;
  outline: string[];         // 自动生成的多级大纲
  steps: WritingStep[];      // 工作流步骤
  status: 'drafting' | 'distilling' | 'finalized';
  created_at?: string;
}

/**
 * 统一网关业务异常
 */
export class GatewayApiError extends Error {
  public code: number;
  public details?: any;

  constructor(code: number, msg: string, details?: any) {
    super(`[Gateway Error ${code}]: ${msg}`);
    this.name = 'GatewayApiError';
    this.code = code;
    this.details = details;
  }
}
