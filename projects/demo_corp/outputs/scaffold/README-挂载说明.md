# 示例科技 GEO 底座补丁

1. `llms.txt`、`llms-full.txt`、`robots.txt` 放入网站**根目录**（Nginx / 静态托管 public 目录）；
2. `json-ld.html` 内容粘贴进全站 HTML `<head>`；
3. 上线后执行 `python3 -m tools.geo audit --project demo_corp` 复检，4/4 通过为验收线（见 SOP-02）。
