## 1. 布局约束与类名修复（P0，唯一必改代码缺口）
- [x] 1.1 将 `StudioSop.vue` 根节点 `lg:w-84` 改为标准 `lg:w-80`（`w-full lg:w-80 shrink-0`），杜绝无效类名回退撑满全屏。
- [x] 1.2 给 `StudioEditor.vue` 根节点补上 `min-w-0`（与已有 `flex-1` 并用）；核对 `Step0App.vue` 外层已是 `flex … lg:flex-row`，无需改结构。

## 2. 字体栈与侧栏字号（核对项，主工程已基本落地）
- [x] 2.1 核对 `geo-admin.css` / `index.html` 已注入苹方栈、等宽栈与 `-webkit-font-smoothing`；缺项才补，禁止重复堆叠冲突规则。
- [x] 2.2 核对侧栏三级小步（0.1 / 0.2）已为 `text-[13px]`；若仍有旧岛或缓存产物带 11px，以源码为准重编。

## 3. 三组件字号对齐（核对项，与 design 矩阵一致即可）
- [x] 3.1 核对 `StudioEditor.vue`：正文 14px、行号 12px、Tab 13px（当前源码已达标则勾选，勿无意义改类）。
- [x] 3.2 核对 `StudioFileTree.vue`：文件名与分类 13px。
- [x] 3.3 核对 `StudioSop.vue`：指引正文 13px、卡片标题 15px、主按钮 14px。

## 4. 构建与回归验证
- [x] 4.1 在 `web/step0-src` 执行 `npm run build` 重新编译阶段零岛（外挂盘沙盒若本机不可用，直接走主工程，禁止另开第二套字号真源）。
- [x] 4.2 确认产物落入主工程 `web/assets/step0/`（或既定输出路径），源码与产物一致。
- [x] 4.3 用本机 **Safari** 打开管理台 `http://127.0.0.1:8088` 或当前测试端口 `http://127.0.0.1:5188`。验证：三栏并列、中间编辑器可见、右侧约 320px、字号对齐 design 矩阵。
