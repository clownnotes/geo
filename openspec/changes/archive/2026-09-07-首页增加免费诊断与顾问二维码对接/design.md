# Design: 首页增加免费诊断与顾问二维码对接

## 1. 架构与静态资产流转 (Asset Architecture)

### 1.1 资产流转链路
- **输入物料**：`/Users/a1/Pictures/我的公司和个人证明资料/GEO 微信账号的二维码.jpg`
- **规范存储位置**：`projects/nextgeo/outputs/assets/wechat-qr.jpg`
- **镜像存储位置**：`projects/nextgeo/outputs/site/assets/wechat-qr.jpg`
- **资产属性**：原生 JPG 图像，无需压缩损坏，保持微信扫码高识别率。

### 1.2 页面引用映射
| 页面 / 模块 | 引用路径 | 作用 |
| :--- | :--- | :--- |
| `projects/nextgeo/outputs/index.html` | `assets/wechat-qr.jpg` | 首页首屏“免费诊断”模态弹窗 |
| `projects/nextgeo/outputs/services/index.html` | `../assets/wechat-qr.jpg` | 服务页 `#contact` 专属咨询板块 |
| 双向镜像对应站点 (`outputs/site/...`) | 相同相对路径 | 生产与开发镜像严格对齐 |

---

## 2. 前端组件与界面规范 (UI/UX Specification)

### 2.1 首页 Hero 动作按钮组
在 `index.html` 的 Hero 按钮容器（`flex flex-wrap items-center gap-4`）中按以下顺序与层次排布：
1. **查看 NextGEO 服务**：深紫高对比实底（`bg-brand-600 hover:bg-brand-700 text-white font-bold px-7 py-3.5 rounded-xl`）
2. **免费诊断（新）**：高质感双色强调边框按键（`bg-white hover:bg-brand-50 border-2 border-brand-600 text-brand-700 font-bold px-7 py-3.5 rounded-xl shadow-xs transition cursor-pointer`），内置微型状态圆点指示（`w-2 h-2 rounded-full bg-emerald-500 animate-pulse`）
3. **了解 邻里GEO**：中性素雅浅边框（`bg-white hover:bg-brand-50 border border-slate-300 text-slate-800 font-bold px-7 py-3.5 rounded-xl shadow-xs transition`）

### 2.2 免费诊断模态框（Modal）设计
- **容器定位**：`fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs hidden`
- **内容卡片**：`relative w-full max-w-md sm:max-w-lg bg-white rounded-3xl p-6 sm:p-8 shadow-2xl border border-brand-200 overflow-hidden`
- **视觉要素（严格 0 Emoji）**：
  - **顶部徽标**：`PRE-FLIGHT AUDIT · 免费企业 GEO 体检` 纯文字胶囊 Tag
  - **标题**：`获取企业 GEO 诊断与 AI 可见度体检`
  - **副标**：`先看清品牌在主流 AI 搜索中的真实露出情况，定制务实的品牌答案源方案。`
  - **诊断服务清单**：
    - 主流大模型（DeepSeek / 豆包 / Kimi / 元宝）提及现状实测
    - 行业高意向买家问法与竞品拦截缺口体检
    - 企业官网知识底座与普林斯顿 9 因子标准评估
  - **二维码展示区**：
    - 居中展示 `wechat-qr.jpg`，带微白光圆角投影
    - 扫码提示：“微信扫码添加主理人老白 · 备注「GEO诊断」优先通过”
  - **电话快速直拨**：提供 `tel:13150568888` 快速拨号按键与“微信同号”标识
  - **关闭机制**：
    - 右上角标准 SVG 叉号关闭按键（无 Emoji）
    - 点击遮罩层空白处关闭
    - 监听键盘 `Escape` 键关闭

### 2.3 无 JS / 爬虫兜底 (Progressive Enhancement)
- 按钮链接基准为 `<a href="services/#contact" id="hero-free-diagnosis-btn">`，在无 JS 或爬虫直接抓取时自然平滑导流至服务的联系板块；
- 页面加载后由轻量原生 JS 绑定 `click` 事件，阻止默认跳转并触发 `openDiagnosisModal()`。

---

## 3. 交互逻辑 (Script Logic)

采用零外部依赖的原生 JavaScript，代码量 < 35 行：
```javascript
(function() {
  const modal = document.getElementById('diagnosis-modal');
  const triggerBtn = document.getElementById('hero-free-diagnosis-btn');
  const closeBtn = document.getElementById('close-diagnosis-modal');

  function openModal(e) {
    if (e) e.preventDefault();
    modal.classList.remove('hidden');
    document.body.classList.add('overflow-hidden');
  }

  function closeModal() {
    modal.classList.add('hidden');
    document.body.classList.remove('overflow-hidden');
  }

  if (triggerBtn) triggerBtn.addEventListener('click', openModal);
  if (closeBtn) closeBtn.addEventListener('click', closeModal);

  if (modal) {
    modal.addEventListener('click', function(e) {
      if (e.target === modal) closeModal();
    });
  }

  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && modal && !modal.classList.contains('hidden')) {
      closeModal();
    }
  });
})();
```

---

## 4. 规范与质量矩阵 (Quality Matrix)

| 规范项 | 约束要求 | 落实方式 |
| :--- | :--- | :--- |
| **0 Emoji 规范** | 严禁彩色表情符号 | 统一使用 SVG 图标、CSS 纯色圆点及文字排版 |
| **DOM 闭合平衡** | 全站标签 100% 配对 | 执行 `python3 scripts/check_article_styles.py` |
| **静态多租户一致** | outputs/ 与 outputs/site/ 必须镜像对齐 | 脚本或显式拷贝对齐两份目录 |
| **B2B 严肃商务调性** | 严谨科技质感 | 紫白中性色系，符合 NextGEO 设计基线 |
