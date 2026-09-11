# 客户重资料仓（GEOZiLiao）与主仓分工

> **一句话**：代码与轻量项目真源走 **GEO 双推**；整站大图大 ZIP 只进 **GEOZiLiao（自建 Git）**，不进 GitHub。

## 1. 为什么拆仓

| 风险 | 说明 |
| :--- | :--- |
| GitHub 单文件 100MB 硬限 | 大图、结案 ZIP、整站镜像容易顶满或拖慢双推 |
| 主仓体积膨胀 | Agent / CI / clone 变慢，与「代码+SOP」无关 |
| 备份缺口 | 未 commit 的本地 `outputs/site` 在换机/坏盘时会丢 |

拆仓后：主仓保持可双推；重资料只推 `https://git.baicl.cc/admin/GEOZiLiao.git`。

## 2. 双仓对照

| | **GEO（主工程）** | **GEOZiLiao（资料仓）** |
| :--- | :--- | :--- |
| 本机路径 | `/Users/a1/代码/GEO` | `/Users/a1/代码/GEOZiLiao`（与主仓**并列**） |
| Remote | `origin` 自建 + `github` 双推 | **仅** `origin` → `https://git.baicl.cc/admin/GEOZiLiao.git` |
| 放什么 | 代码、OpenSpec、SOP、`project.yaml`、词库、报告 Markdown/JSON、侦察记录 | `site/`、`assets/`、大体积 `archives/*.zip` |
| Agent 运行时 | 管理台仍读写本仓 `projects/{id}/outputs/` | **不是**运行入口，只做备份镜像 |

资料仓目录约定：

```text
GEOZiLiao/projects/{client_id}/
  site/       ← 对应 GEO/projects/{id}/outputs/site/
  assets/     ← 对应 GEO/projects/{id}/outputs/assets/
  archives/   ← 可选：结案大 ZIP
```

## 3. 日常备份（主仓 → 资料仓）

```bash
# 在主仓根目录
./scripts/sync_delivery_to_ziliao.sh          # 全部有 site/assets 的客户
./scripts/sync_delivery_to_ziliao.sh nextgeo  # 单个客户

cd ../GEOZiLiao
git add -A && git status
git commit -m "chore(sites): sync nextgeo delivery"
git push origin main
```

**未 `git push` = 只在本机有一份拷贝，不算备份成功。**

自建 HTTPS 若遇超时（如 HTTP 524），按目录/文件分批 commit 再 push，勿一次推几十 MB。

## 4. 换机 / 生产恢复（资料仓 → 主仓）

```bash
# 在主仓根目录（把资料仓镜像拉回运行目录）
./scripts/restore_delivery_from_ziliao.sh nextgeo
# 或不带参数：恢复全部已在资料仓存在的客户
```

生产机（Mac mini）建议并列克隆两仓；推生产前若主仓已不再跟踪 `outputs/site|assets`，必须先 restore 或单独 pull GEOZiLiao 再同步，否则 `git pull` 后线上站点会空。

## 5. 主仓 gitignore 约定

以下路径**本地仍可存在**（预览/编译照常），但**不得再双推进 GitHub**：

- `projects/*/outputs/site/`
- `projects/*/outputs/assets/`
- `projects/*/outputs/*_geo_delivery_archive.zip`
- `projects/*/outputs/*delivery*.zip`

轻量交付物（报告 md/json、`llms.txt` 草稿、探测脚本等）仍可留在主仓 `outputs/` 下非上述目录。

## 6. Agent 红线

1. **禁止**给 GEOZiLiao 配置或推送 GitHub remote。  
2. 改交付站内容：在主仓 `projects/{id}/outputs/` 改 → sync → 资料仓 commit/push。  
3. 不要把 `tools/`、`web/`、OpenSpec 拷进 GEOZiLiao。  
4. 禁止把 `.env`、密钥、cookie 写入任一仓。  
5. 新客户建站后：有 `site`/`assets` 就应纳入资料仓备份节奏。

## 7. 与 OpenSpec / 文档索引

- 资料仓协议副本：`GEOZiLiao/AGENTS.md`、`GEOZiLiao/README.md`  
- 主仓总协议：`AGENTS.md` §4 / §5 交叉引用本文  
- 同步脚本：`scripts/sync_delivery_to_ziliao.sh`、`scripts/restore_delivery_from_ziliao.sh`
