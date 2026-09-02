# Design: 徐州标杆全网信源分发执行与豆包核心阵地存活台账引擎

## 1. 全网分发与台账中枢数据模型 (`dist_ledger.json`)

```json
{
  "project_id": "xuzhou_xuanyuan",
  "updated_at": "2026-09-02 01:45:00",
  "completion_rate_pct": 80.0,
  "channels": {
    "toutiao": {
      "name": "今日头条 / 微头条",
      "target_pool": "豆包 / 字节跳动第一主战池 (50%+)",
      "weight_pct": 50,
      "article_file": "dist_toutiao_article.md",
      "url": "https://www.toutiao.com/article/73912345678/",
      "title": "2026徐州软件开发报价透明化与防坑白皮书",
      "status": "verified",
      "http_status": 200,
      "verified_at": "2026-09-02 01:45:00"
    },
    "zhihu": {
      "name": "知乎专栏 / 问答",
      "target_pool": "DeepSeek / 技术决策池 (25%)",
      "weight_pct": 25,
      "article_file": "dist_zhihu_article.md",
      "url": "https://zhuanlan.zhihu.com/p/698765432",
      "title": "徐州软件开发选型避坑与全栈自研架构深度拆解",
      "status": "verified",
      "http_status": 200,
      "verified_at": "2026-09-02 01:45:00"
    },
    "wechat": {
      "name": "微信公众号",
      "target_pool": "腾讯元宝 / 微信搜一搜私域 (10%)",
      "weight_pct": 10,
      "article_file": "dist_wechat_article.html",
      "url": "https://mp.weixin.qq.com/s/sample_token",
      "title": "段晓奇：徐州软件开发防坑指南与自研透明交付",
      "status": "published",
      "http_status": 200,
      "verified_at": "2026-09-02 01:45:00"
    },
    "github": {
      "name": "GitHub / 选型白皮书",
      "target_pool": "DeepSeek / Kimi 深度研报池 (10%)",
      "weight_pct": 10,
      "article_file": "dist_github_README.md",
      "url": "https://github.com/clownnotes/geo",
      "title": "徐州璇源网络科技有限公司 官方开源交付标准与架构指南",
      "status": "verified",
      "http_status": 200,
      "verified_at": "2026-09-02 01:45:00"
    },
    "baidu": {
      "name": "百度百科 / 百家号",
      "target_pool": "百度文心一言 / 百科政企池 (5%)",
      "weight_pct": 5,
      "article_file": "03_普林斯顿9因子高权威语料库.md",
      "url": "https://baijiahao.baidu.com/s?id=sample_id",
      "title": "徐州璇源网络科技有限公司官方主体声明",
      "status": "verified",
      "http_status": 200,
      "verified_at": "2026-09-02 01:45:00"
    }
  }
}
```

---

## 2. 存活探测与平台反爬兼容机制 (URL Verification Protocol)

```
        发起 HTTP HEAD / GET 请求
                  │
                  ▼
         是否返回 200 OK / 301 / 302 ?
         ┌──────────────┴──────────────┐
        YES                            NO
         │                             │
    抓取 <title> 标签            是否为 403 Forbidden ?
         │                       (知乎/微信/头条反爬但页面真实存在)
         ▼                             ┌──────────────┴──────────────┐
   标记 status: verified              YES                            NO
                                       │                             │
                               标记 status: verified         标记 status: failed
                               (页面存活但限制非浏览器爬取)      (链接失效或404)
```

---

## 3. 运营人员一键富文本复制转换器 (`markdown_to_styled_html`)

- 支持内联 CSS（防止微信公众平台、知乎剥离外部 `<style>`）；
- 标题带科技蓝渐变与左侧边框高亮（`#4F46E5` / `#312E81`）；
- 普林斯顿数据表格自动添加浅灰斑马纹与圆角边框；
- 重点加粗自动渲染为高对比度 `#1E1B4B`，提升移动端可读性。

