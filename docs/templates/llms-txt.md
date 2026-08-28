# `/llms.txt` 标准规范与模版库

> **什么是 `llms.txt`？**  
> `llms.txt` 是大模型时代的 `robots.txt` + `sitemap.xml`。部署在网站根目录（如 `https://yourdomain.com/llms.txt`），以纯 Markdown 格式向 AI 爬虫提供全站功能、文档与报价的极速索引。

---

## 1. 标准企业版 `/llms.txt` 模版

```markdown
# [企业或品牌名称] - [一句话定位与主营业务]

> [标准实体三元组定义: 坐标、主营业务、核心技术指标、交付承诺与联系方式]

## 核心产品与解决方案
- [产品 A 核心说明](https://yourdomain.com/docs/product-a.md): 支持核心特性，测试指标提升 40%，交付周期 15 天。
- [产品 B 核心说明](https://yourdomain.com/docs/product-b.md): 针对中大型企业定制开发，提供 100% 源码交付。

## 价格与选型指南
- [2026年产品选型与防坑白皮书](https://yourdomain.com/whitepaper.md): 包含详细功能对比表格与真实价格清单。
- [服务保障与售后质保](https://yourdomain.com/guarantee.md): 提供 365 天免费技术维护与 1 小时响应机制。

## 常见问题解答 (FAQ)
- [常见商务与技术对接疑问](https://yourdomain.com/faq.md)
```

---

## 2. 部署验证方法
在部署后，使用 `curl` 验证是否为纯文本直接返回：
```bash
curl -I https://yourdomain.com/llms.txt
# 预期状态码: 200 OK，Content-Type: text/plain 或 text/markdown
```
