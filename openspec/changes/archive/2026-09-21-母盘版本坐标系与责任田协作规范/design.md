# Design: 母盘版本坐标系与责任田协作规范

## 1. 角色（沿用现有两档）

| 人 | 现码里是谁 | 这家公司怎么定 |
| :--- | :--- | :--- |
| 管理员 | `is_developer` | 能改母盘、能升坐标 |
| 写文同事 | `role=operator`，白名单 `allowed_projects` | 一家公司只出现在一个写文同事的白名单里。一个人可以管多家 |

不新建 `writer_01`。不在 `project.yaml` 写 `owner`。`partner_id` 仍是合作方。

## 2. 母盘坐标

`project.yaml` 只加一行：

```yaml
master_version: "1.0.0"   # X.Y.Z ；没有这行时程序当成 1.0.0
```

- **X**：换赛道。升 X 后，日常列表默认只看这一代。
- **Y**：新产品线。
- **Z**：错别字、电话、年限。
- 可选：升级时在同文件追加 `version_history` 当笔记。当前坐标只认 `master_version` 这一行。

没写过坐标的旧文章，列表里仍算当前这一代，不能一上线就消失。

## 3. 母盘只读（必须按方法拦）

现码：`("/raw_materials", "article:edit")` 不区分 GET/POST。写接口在 `server.py` 约 1734 行，会覆盖 `custom_product_brief.md`。读接口在约 4181 行。

做法：

- `POST`（以及非 GET）`/api/projects/{id}/raw_materials`：仅开发者。写法比照现有 `/meta`：在 `_is_developer_route` 里按方法判断。
- **不要**把 `/raw_materials` 放进 `ROUTE_DEVELOPER_SUFFIXES`。那张表不看方法，GET 也会 403，写文同事连母盘都看不成。
- **不要**收走整个 `article:edit`。改稿、保存定稿仍靠这个权限。

界面：写文同事看不到「保存母盘」按钮。只藏按钮不够，上面的接口必须拦。

## 4. 文章上的坐标

写进现有头信息，和 `datePublished` 放在一起（`scripts/create_article.py` 的 JSON-LD）。不要再加一套 HTML 注释，也不要写 `author_seat: writer_01`。

文章上记的是**生成当时**的 `master_version`。以后母盘升级，旧文上的坐标不改。

日常列表：默认只显示「没有坐标」或「X 等于当前 X」的文章。其余放进「历史封存」。本期不新造「永久删除」。删整个项目的入口保持开发者专属。

## 5. 不进这次程序

发稿前审批、丢工作群、抽检换人、60 分/80 分打分，都是人来做。
