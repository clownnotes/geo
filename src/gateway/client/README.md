# Nextdoor Gateway 客户端 SDK

本目录包含 Nextdoor 透明网关的前端客户端与交互组件 SDK，供前端业务宿主项目引用。

## 目录结构

- `client.ts`：网关主客户端（包含流式对话 `streamChat`、意图匹配 `matchIntent`、健康检查等）
- `voiceClient.ts`：语音开放能力客户端（伴读音频切片 `getArticleAudioChunk`、TTS 合成、任务轮询等）
- `ArticleAudioPlayer.ts`：纯 TypeScript 伴读音频播放核心驱动器
- `ArticleAudioPlayer.vue`：伴读音频播放器 Vue 3 组件
- `ChatWidget.tsx`：React 智能对话交互组件（支持拼音输入法防风暴、实时意图推荐）
- `types.ts` & `voiceTypes.ts`：全量 TypeScript 类型定义契约（雪花 ID 纯字符串）

## 引用方式

宿主项目（如 `src/web/step0-src` 或外部协作项目）可在 `vite.config.ts` 或 `tsconfig.json` 中配置 alias 指向本目录：

```typescript
// vite.config.ts
resolve: {
  alias: {
    '@gateway': path.resolve(__dirname, '../../gateway/client')
  }
}
```
