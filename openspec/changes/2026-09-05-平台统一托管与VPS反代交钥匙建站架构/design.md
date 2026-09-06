# Design: 平台统一托管与VPS反代交钥匙建站架构

## Architecture (架构设计与拓扑关系)

### 1. 物理机总控 + VPS 商用转发 + 腾讯云边缘 CDN 三层拓扑
```
[终端访客 / 大模型联网检索蜘蛛 (Bytespider / DeepSeek / Kimi / 百度)]
                                │
                                ▼
                   [第一层：腾讯云边缘 CDN]
      - 全球/全国节点秒级就近响应，降低大模型爬虫抓取延迟
      - 生产发布态静态强缓存 (HTML/CSS/JS/llms.txt)
      - 消化 99% 的公网访问流量，彻底抹平客户 VPS 3~5 Mbps 的带宽瓶颈
                                │ (回源商用 IP)
                                ▼
                   [第二层：公网商用 VPS (3~5 Mbps)]
      - 解决家用宽带不能商用绑定 80/443 端口的限制
      - 承接客户域名的直接解析 (A/CNAME)
      - Nginx 反向代理网关 (配置 SSL 证书与回源转发)
                                │ (穿透回源 / 数据转发)
                                ▼
                   [第三层：家用物理机 (Mac mini)]
      - 接入中国联通动态公网 IP (50 Mbps 上行)
      - GEO 5 步流水线控制台与语料提纯编译中枢
      - 零云端高带宽租用成本，100% 掌控客户数据与生成逻辑
```

### 2. 静态缓存时机原则（杜绝调试死锁）
- **痛点**：若一开始就给网站加死长效静态缓存，在第 1~5 步修改素材或重新编译时，浏览器和代理会一直返回旧缓存，导致“改了不生效”。
- **对策**：
  1. **开发预览态（Local / Preview）**：
     - 请求携带时间戳参数（`?t=时间戳`）；
     - 服务端返回响应头：`Cache-Control: no-cache, no-store, must-revalidate`；
     - 确保任何编译改动在管理台刷新即见。
  2. **生产发布态（Release / CDN）**：
     - 当且仅当在控制台点击【🚀 一键发布/更新上线】时，才将最新静态产物推至 VPS / CDN 节点；
     - 内容发生变更时，触发 CDN **Purge Cache（一键刷新 URL 缓存）** 指引，重载全网边缘快照。

---

## Interface (接口与组件设计)

### 1. 后端路由规范
- **生产级独立站点宿主路由**：
  - `GET /sites/{project_id}/` ➔ 直接返回 `projects/{project_id}/outputs/site/index.html`（`Content-Type: text/html; charset=utf-8`，带 `Cache-Control: no-cache` 预览头）。
  - `GET /sites/{project_id}/{asset_file}` ➔ 静态提供 `llms.txt`、`robots.txt`、`schema.jsonld` 等。
- **VPS 反向代理与 CDN 适配配置接口**：
  - `GET /api/projects/{id}/site/nginx-conf`
  - 返回 JSON:
    ```json
    {
      "success": true,
      "domain": "code.baicl.cc",
      "upstream": "http://127.0.0.1:8088",
      "nginx_conf": "server {\n    listen 80;\n    server_name code.baicl.cc;\n    # 腾讯云 CDN / VPS 代理规则\n    ...\n}"
    }
    ```

### 2. 前端阶段二交互升级
- **状态卡片**：从单纯的“静态生成就绪”，升级为**“🚀 网站在线运行中枢”**：
  - 呈现：🟢 集中托管状态正常；
  - 呈现：生产直访地址（新窗口打开立即体验纯净站，无调试外框）；
  - 按钮组：
    1. 【🌐 在线直达】（打开 `http://127.0.0.1:8088/sites/{id}/`）；
    2. 【⚡ 复制 VPS 反代配置】（弹窗展示带腾讯云 CDN 兼容的 Nginx 配置）；
    3. 【📦 离线源码包导出 (.zip)】（作为客户资产兜底）。
