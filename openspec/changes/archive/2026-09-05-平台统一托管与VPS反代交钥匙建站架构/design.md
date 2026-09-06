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
      - Nginx 反向代理网关 (配置 SSL 证书与向物理机回源)
                                │ (穿透回源 / DDNS 动态公网)
                                ▼
                   [第三层：家用物理机 (Mac mini)]
      - 接入中国联通动态公网 IP (50 Mbps 上行)
      - GEO 5 步流水线控制台与语料提纯编译中枢
      - 零云端高带宽租用成本，100% 掌控客户数据与生成逻辑
```

### 2. 静态缓存时机与 Phase-1 交付边界
- **环境分离原则**：
  1. **开发预览态（Local / Preview）**：
     - 本地 Python 宿主通过 `/sites/{project_id}/` 对外提供服务；
     - 强制返回响应头：`Cache-Control: no-cache, no-store, must-revalidate`；
     - 确保任何编译改动在管理台刷新即见。
  2. **生产发布态（Release / CDN）**：
     - 生产环境由公网 VPS 与腾讯云 CDN 承担静态缓存；
     - **Phase-1 范围明确定位**：本期实现“安全本地纯净托管 + 带缓存策略的 Nginx 配置导出 + 腾讯云 CDN 刷新 (Purge Cache) 标准命令行脚本导出”；不引入外部云 SDK 强依赖，确保零外部凭证也能稳定闭环。

---

## Interface (接口与组件设计)

### 1. 安全与鉴权契约

#### (1) 纯净静态站点宿主路由：`GET /sites/{project_id}/` 与 `GET /sites/{project_id}/{asset_file}`
- **安全沙箱约束**：
  - `project_id` 必须严格通过正则校验：`^[a-zA-Z0-9_-]+$`；
  - 站点物理根路径限定为：`PROJECTS_DIR/{project_id}/outputs/site/`；
  - 使用 `os.path.commonpath` 与 `os.path.abspath` 进行路径遍历防御，若计算后路径超出 `outputs/site/` 范围或包含 `..`，立即拦截并返回 `403 Forbidden` 或 `404 Not Found`；
  - 严禁穿透读取 `project.yaml`、`raw_materials/` 或 `outputs/*.md` 等内部文件；
  - 若目标项目未执行阶段二编译（缺少 `outputs/site/index.html`）或是空模板（如 `_template`），直接返回 `404 Not Found`。
- **响应头规范**：
  - `Content-Type: text/html; charset=utf-8`（或相应静态文件 MIME 类型）；
  - `Cache-Control: no-cache, no-store, must-revalidate`（开发预览态防死锁）。

#### (2) VPS Nginx 配置生成接口：`GET /api/projects/{id}/site/nginx-conf`
- **强制鉴权**：
  - 必须携带有效 Bearer Token（使用 `require_auth` 鉴权闸门），未登录请求直接返回 `401 Unauthorized`。
- **动态 Upstream 回源规则**：
  - 支持通过 Query 参数 `?origin=http://your-mac-ddns:8088` 传入真实回源物理机公网地址；
  - 若未显式提供，默认使用占位符 `http://<YOUR_PHYSICAL_MAC_IP_OR_DDNS>:8088`，并在配置中以大段注释明确说明：**“严禁在独立 VPS 上直接使用 127.0.0.1:8088，必须替换为家用物理机公网 DDNS 或内网穿透域名”**。
- **返回 JSON 契约**：
  ```json
  {
    "success": true,
    "domain": "code.baicl.cc",
    "upstream": "http://<YOUR_PHYSICAL_MAC_IP_OR_DDNS>:8088",
    "nginx_conf": "server {\n    listen 80;\n    server_name code.baicl.cc;\n    ...\n}",
    "cdn_purge_guide": "tccli cdn PurgePathCache --Paths '[\"https://code.baicl.cc/\"]' --FlushType flush"
  }
  ```

---

## 前端阶段二交互升级

- **状态卡片**：
  - 呈现：🟢 集中托管状态正常；
  - 呈现：纯净直访地址（`http://127.0.0.1:8088/sites/{id}/`，新窗口打开查看无向导框架页面）；
  - 按钮组：
    1. 【🌐 在线直达】（打开独立纯净站点）；
    2. 【⚡ 复制 VPS 反代配置】（弹窗展示带腾讯云 CDN 兼容的 Nginx 配置与回源说明）；
    3. 【📦 离线源码包导出 (.zip)】（作为客户资产兜底）。
