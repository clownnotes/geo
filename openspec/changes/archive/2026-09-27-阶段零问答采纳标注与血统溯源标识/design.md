# Design: 阶段零问答采纳标注与血统溯源标识

## 1. 面向对象模型设计 (OOP)

### 1.1 文件对象 (FileItem) 属性扩展
在前端 `files` 字典中，每个文件对象结构如下：
```ts
interface StudioFileItem {
  name: string;               // 文件名，如 "01_豆包提问清单_推荐版.txt"
  category: 'questions' | 'answers' | 'materials' | 'drafts' | 'reports';
  dir: string;                // 目录中文名，如 "豆包出的题目"
  content: string;            // 文件内容
  savedContent: string;       // 上次保存内容
  isDirty: boolean;           // 是否有未保存变动
  isActive?: boolean;         // 【新增】是否为当前客户采纳的生效底牌
  versionTag?: string;        // 【新增】血统版本号（如 "QA-V1", "QA-V2"）
  pairFile?: string;          // 【新增】绑定的对应问/答文件名
}
```

### 1.2 项目聚合底牌与文件持久化 (LocalStorage 本地持久化)
遵循 AGENTS.md 纯前端打样铁律，**严禁修改后端 server.py 与 data/projects.json**。
1. **生效底牌记录**：统一持久化于浏览器 `localStorage`（键名格式：`geo_step0_active_qa_${clientId}`）：
```json
{
  "clientId": "geo",
  "activeQaVersion": "QA-V1",
  "activeQuestionFile": "01_豆包提问清单_推荐版.txt",
  "activeAnswerFile": "02_豆包实测回答记录_初测.txt",
  "updatedAt": "2026-09-27T15:20:00.000Z"
}
```
2. **阶段零文件字典持久化**（与阶段一 `geo_step1_state_*` 机制对齐）：
持久化于 `localStorage`（键名：`geo_step0_files_${clientId}`），保证打磨保存的新版题目（如 `01_豆包题目_第2版.txt`）在刷新后不丢失。

### 1.3 血统溯源码 (Lineage Stamp) 规范
- 格式模板：`QA-V${N}`（如 `QA-V1`, `QA-V2`）
- 文件内容首行规范头（人机共读，严禁 Emoji）：
  ```markdown
  === 阶段零生效底牌 (基线标识: QA-V1) ===
  客户品牌：邻里GEO (geo)
  当前状态: 客户采纳生效中
  配对文件: 02_豆包实测回答记录_初测.txt
  ------------------------------------------------
  ```
- 下游消费端（阶段一素材与报告）显式印制规范：
  ```markdown
  > [溯源血统]：本报告基于阶段零生效底牌【QA-V1】（01_豆包提问清单_推荐版.txt + 02_豆包实测回答记录_初测.txt）直出
  ```

---

## 2. 状态机与交互时序流程

### 2.1 初始加载与双向一致性校验兜底
```
[1. 从 localStorage: geo_step0_files_${clientId} 恢复文件列表]
       │
[2. 从 localStorage: geo_step0_active_qa_${clientId} 获取采纳记录]
       │
       ├─► activeQuestionFile 且该文件真实存在于 files 字典中？
       │     ├─ 是 ─► 将对应题目和回答标记为 isActive = true, versionTag = activeQaVersion
       │     └─ 否 ─► 执行【校验纠偏】：
       │               ① 兜底将第 1 个推荐版设为 isActive = true, versionTag = 'QA-V1'；
       │               ② 立即同步修正回写 localStorage，防止下游溯源章引用不存在的文件名！
```

### 2.2 0.1 出题阶段：设为当前采纳
1. 专家查看/打磨某份题目文件（如 `01_豆包题目_第2版.txt`）；
2. 点击编辑器顶栏【设为客户采纳】：
   - 互斥逻辑：遍历所有 `category === 'questions'` 的文件，将其 `isActive` 设为 `false`；
   - 当前文件 `isActive = true`；
   - 提取最大版本号或自动递增（`QA-V1` 递增为 `QA-V2`）；
   - 更新文件头部的版本说明文字；
   - 更新本地存储 `localStorage.setItem('geo_step0_active_qa_' + pId, ...)`；
   - 左侧文件树高亮徽章瞬间切换至新文件。

### 2.3 0.2 网页提问拿答案：继承与固化
1. 进入 0.2 子步骤，当前激活的回答文件自动读取 `activeQaVersion`（如 `QA-V2`）；
2. 专家将豆包真实问答贴回编辑器；
3. 点击【完成阶段零并存入底牌】：
   - 固化当前回答文件为 `activeAnswerFile`；
   - 将全量文件内容与底牌元数据保存至本地存储；
   - 触发阶段流转，安全进入阶段一。

### 2.4 阶段一（商业诊断）：消费与溯源盖章
1. 阶段一加载时，调用 `stage1Config.resolveContext(projectData)`，同时读取阶段零本地底牌；
2. 提取 `activeQaVersion`、`activeQuestionFile`、`activeAnswerFile`；
3. 构建 `01_阶段零豆包实测问答素材.md` 与 `01_商业诊断与转化初稿.md` 时，顶部注入溯源血统章；
4. 交付专家与老板查看报告时，能清晰看见该诊断基于阶段零的哪一套问答。

---

## 3. 组件视觉与细节规范 (纯 Lucide 图标，严禁 Emoji)

### 3.1 左侧资源管理器 (StudioFileTree.vue)
- 在文件行条目右侧添加徽章：
  ```html
  <span
    v-if="files[fn]?.isActive"
    class="text-[10px] px-1.5 py-0.5 rounded font-mono font-medium bg-[#7c5bf5]/15 text-[#7c5bf5] border border-[#7c5bf5]/30 flex items-center gap-1 shrink-0"
  >
    <i data-lucide="check" class="w-3 h-3 text-[#7c5bf5]"></i>
    <span>已采纳</span>
    <span class="opacity-80">[{{ files[fn]?.versionTag || 'QA-V1' }}]</span>
  </span>
  ```

### 3.2 中间多 Tab 编辑器 (StudioEditor.vue)
- 在编辑器顶栏（操作按钮区域）：
  ```html
  <!-- 采纳状态与切换按钮 (使用 Lucide 专业图标) -->
  <div class="flex items-center gap-2">
    <span
      v-if="currentFile?.isActive"
      class="text-[11px] px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-medium flex items-center gap-1"
    >
      <i data-lucide="check-circle" class="w-3.5 h-3.5 text-emerald-600"></i>
      客户生效底牌 [{{ currentFile?.versionTag || 'QA-V1' }}]
    </span>
    <button
      v-else-if="canAdoptCurrentFile"
      type="button"
      @click="$emit('adoptFile', activeFileName)"
      class="text-[12px] px-2.5 py-1 bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-300 rounded font-medium transition cursor-pointer flex items-center gap-1"
    >
      <i data-lucide="star" class="w-3.5 h-3.5 text-amber-600"></i>
      设为客户采纳
    </button>
  </div>
  ```
