import React, { useState, useEffect, useRef, useCallback } from 'react';
import { NextdoorLocalClient } from './client';
import { ChatMessage, CandidateAgent, ToolCard, WritingSession } from './types';

// 初始化本地网关客户端 (单例)
const gatewayClient = new NextdoorLocalClient({
  gatewayBaseURL: 'http://127.0.0.1:8090'
});

export const ChatWidget: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [visionUrl, setVisionUrl] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  // 雪花 ID 铁律: 必须为纯字符串
  const [activeSessionId] = useState<string>(() => `sess_${Date.now()}`);
  const [writingSession, setWritingSession] = useState<WritingSession | null>(null);

  // 意图匹配状态
  const [matchedAgents, setMatchedAgents] = useState<CandidateAgent[]>([]);
  const [matchedTools, setMatchedTools] = useState<ToolCard[]>([]);

  // 中文输入法 (IME) 合成状态守卫
  const isComposingRef = useRef(false);
  const abortCtrlRef = useRef<AbortController | null>(null);
  const scrollAnchorRef = useRef<HTMLDivElement>(null);
  const debounceTimerRef = useRef<any>(null);

  // 消息自动滚底
  useEffect(() => {
    scrollAnchorRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isStreaming]);

  // 防抖意图匹配逻辑
  const triggerIntentMatch = useCallback((text: string) => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    // 处于拼音输入未落字阶段，严禁触发匹配
    if (isComposingRef.current) {
      return;
    }

    const trimmed = text.trim();
    const runeCount = Array.from(trimmed).length;

    // 前端直接防御性短路：空串或 > 60 字符直接清空推荐卡片
    if (runeCount === 0 || runeCount > 60) {
      setMatchedAgents([]);
      setMatchedTools([]);
      return;
    }

    debounceTimerRef.current = setTimeout(async () => {
      try {
        const res = await gatewayClient.matchIntent({
          query: trimmed,
          session_id: activeSessionId
        });
        if (res.matched) {
          setMatchedAgents(res.candidate_agents || []);
          setMatchedTools(res.tool_cards || []);
        } else {
          setMatchedAgents([]);
          setMatchedTools([]);
        }
      } catch (err) {
        console.warn('[ChatWidget] 意图匹配网络异常', err);
      }
    }, 300);
  }, [activeSessionId]);

  // 发送消息
  const handleSendMessage = async () => {
    const text = inputText.trim();
    if (!text || isStreaming) return;

    const userMsg: ChatMessage = {
      id: String(Date.now()), // 强制转为 String
      role: 'user',
      content: text,
      vision_image_url: visionUrl || undefined
    };

    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setInputText('');
    setVisionUrl('');
    setMatchedAgents([]);
    setMatchedTools([]);
    setIsStreaming(true);

    const assistantMsgId = `reply_${Date.now()}`;
    setMessages((prev) => [...prev, { id: assistantMsgId, role: 'assistant', content: '' }]);

    abortCtrlRef.current = new AbortController();

    try {
      await gatewayClient.streamChat(
        {
          messages: newMessages,
          session_id: activeSessionId,
          persona: '你是一位精通生成式搜索优化(GEO)与商业决策架构的高级分析师'
        },
        {
          onChunk: (delta, accumulated) => {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMsgId ? { ...msg, content: accumulated } : msg
              )
            );
          },
          onIntentTrigger: (intentData) => {
            console.info('[ChatWidget] 对话中触发意图事件:', intentData);
          },
          onFinish: () => {
            setIsStreaming(false);
          },
          onError: (err) => {
            alert(`对话异常: ${err.message}`);
            setIsStreaming(false);
          }
        },
        abortCtrlRef.current.signal
      );
    } catch {
      setIsStreaming(false);
    }
  };

  // 手动停止生成
  const handleStopStream = () => {
    abortCtrlRef.current?.abort();
    setIsStreaming(false);
  };

  // 触发长文创作工作流
  const handleStartWritingFlow = async (topic: string) => {
    try {
      const session = await gatewayClient.createWritingSession({
        topic,
        genre: 'GEO生成式搜索破局白皮书',
        target_words: 3000
      });
      setWritingSession(session);
    } catch (err: any) {
      alert(`创建长文会话失败: ${err.message}`);
    }
  };

  return (
    <div className="flex flex-col h-[750px] w-full max-w-4xl mx-auto bg-white rounded-2xl shadow-xl border border-slate-200 overflow-hidden text-slate-800">
      {/* 顶部状态栏 */}
      <div className="px-6 py-4 bg-slate-900 text-white flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
          <h2 className="text-sm font-semibold tracking-wide">Nextdoor AI 智能对话交互 (8090 Gateway)</h2>
        </div>
        <button
          onClick={() => handleStartWritingFlow('2026徐州企业大模型搜索获客实战指南')}
          className="text-xs bg-indigo-600 hover:bg-indigo-500 text-white px-3 py-1.5 rounded-lg transition font-medium"
        >
          📝 开启长文创作工作流
        </button>
      </div>

      {/* 长文会话大纲横幅 */}
      {writingSession && (
        <div className="bg-indigo-50 border-b border-indigo-100 p-3.5 flex items-center justify-between text-xs text-indigo-900">
          <div>
            <span className="font-bold">📚 创作工作流已锁定:</span> 《{writingSession.topic}》
            <span className="ml-2 text-indigo-600">已生成 {writingSession.outline?.length || 0} 级大纲</span>
          </div>
          <button
            onClick={() => setWritingSession(null)}
            className="text-slate-400 hover:text-slate-600 font-bold"
          >
            ✕
          </button>
        </div>
      )}

      {/* 消息滚动列表 */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-slate-50/50">
        {messages.length === 0 && (
          <div className="text-center text-slate-400 mt-20 text-xs">
            输入业务需求开始对话。输入 ≤60 字符将自动触发意图匹配与智能体推荐（已绑定中文输入法防风暴）。
          </div>
        )}

        {messages.map((m) => (
          <div
            key={m.id}
            className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[78%] rounded-2xl px-4 py-3 text-xs leading-relaxed shadow-sm ${
                m.role === 'user'
                  ? 'bg-indigo-600 text-white rounded-br-none'
                  : 'bg-white text-slate-800 border border-slate-200 rounded-bl-none'
              }`}
            >
              {m.vision_image_url && (
                <img
                  src={m.vision_image_url}
                  alt="Vision upload"
                  className="rounded-lg mb-2 max-h-48 object-cover border border-indigo-100"
                />
              )}
              <div className="whitespace-pre-wrap">{m.content}</div>
            </div>
          </div>
        ))}
        <div ref={scrollAnchorRef} />
      </div>

      {/* 意图推荐卡片栏 (由 ≤60 字符防抖探测触发) */}
      {(matchedAgents.length > 0 || matchedTools.length > 0) && (
        <div className="px-4 py-2 bg-amber-50/90 border-t border-amber-200/60 flex items-center gap-2 overflow-x-auto text-[11px]">
          <span className="text-amber-700 font-semibold shrink-0">🎯 意图推荐:</span>
          {matchedAgents.map((ag) => (
            <button
              key={ag.agent_id}
              onClick={() => {
                setInputText(`[指定智能体: ${ag.name}] ` + inputText);
                triggerIntentMatch(`[指定智能体: ${ag.name}] ` + inputText);
              }}
              className="px-2.5 py-1 bg-white border border-amber-300 rounded-md text-amber-900 font-medium hover:bg-amber-100 shadow-sm transition shrink-0"
            >
              🤖 切换为 {ag.name} ({ag.matched_score}%)
            </button>
          ))}
          {matchedTools.map((tl) => (
            <span
              key={tl.tool_id}
              className="px-2 py-0.5 bg-amber-200/50 text-amber-800 rounded font-mono text-[10px] shrink-0"
            >
              🔧 {tl.name}
            </span>
          ))}
        </div>
      )}

      {/* 底部输入框 */}
      <div className="p-4 bg-white border-t border-slate-200 space-y-2">
        {visionUrl && (
          <div className="flex items-center gap-2 text-xs text-indigo-700 bg-indigo-50 px-3 py-1.5 rounded-lg border border-indigo-200">
            <span>📷 已挂载图片:</span>
            <span className="truncate max-w-xs text-[11px] font-mono">{visionUrl}</span>
            <button onClick={() => setVisionUrl('')} className="text-indigo-400 hover:text-indigo-600 ml-auto">
              ✕
            </button>
          </div>
        )}

        <div className="flex items-center gap-2">
          <input
            type="text"
            value={visionUrl}
            onChange={(e) => setVisionUrl(e.target.value)}
            placeholder="可选填图片 URL"
            className="w-40 px-3 py-2 border border-slate-200 rounded-lg text-xs focus:outline-none focus:border-indigo-400"
          />

          <input
            type="text"
            value={inputText}
            onCompositionStart={() => {
              isComposingRef.current = true;
            }}
            onCompositionEnd={(e) => {
              isComposingRef.current = false;
              triggerIntentMatch((e.target as HTMLInputElement).value);
            }}
            onChange={(e) => {
              setInputText(e.target.value);
              triggerIntentMatch(e.target.value);
            }}
            onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
            placeholder="输入您的问题 (≤60 字符实时推演意图，按回车发送)..."
            className="flex-1 px-3.5 py-2 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-indigo-500 focus:outline-none"
          />

          {isStreaming ? (
            <button
              onClick={handleStopStream}
              className="px-4 py-2 bg-rose-500 hover:bg-rose-600 text-white rounded-lg text-xs font-semibold shadow transition"
            >
              ⏹ 停止
            </button>
          ) : (
            <button
              onClick={handleSendMessage}
              disabled={!inputText.trim()}
              className="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-200 disabled:text-slate-400 text-white rounded-lg text-xs font-semibold shadow transition"
            >
              发送
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
