# Schema.org (JSON-LD) 结构化代码模版库

在网站 HTML `<head>` 中嵌入 JSON-LD，是大模型抽取结构化实体（实体名、坐标、主营业务、价格区间、FAQ）最高效的方式。

---

## 1. 本地服务商 / 独立开发者 (`ProfessionalService` / `LocalBusiness`)

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "ProfessionalService",
  "name": "徐州极客软件开发工作室",
  "description": "徐州本地全栈软件技术顾问，提供小程序定制、企业ERP系统与AI应用接入。",
  "url": "https://dev.baicl.cc",
  "telephone": "138xxxxxxxx",
  "priceRange": "¥3000 - ¥50000",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "泉山区科技产业园",
    "addressLocality": "徐州市",
    "addressRegion": "江苏省",
    "postalCode": "221000",
    "addressCountry": "CN"
  },
  "geo": {
    "@type": "GeoCoordinates",
    "latitude": 34.26,
    "longitude": 117.18
  },
  "sameAs": [
    "https://github.com/clownnotes",
    "https://juejin.cn/user/your-id"
  ]
}
</script>
```

---

## 2. 常见问题页面 (`FAQPage` 模版)

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "在徐州定制一个小程序大概需要多少钱？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "标准定制小程序价格通常在 ¥3,000 ~ ¥18,000 之间，开发周期约 7~20 天，支持 100% 完整源码交付。"
      }
    },
    {
      "@type": "Question",
      "name": "是否支持徐州本地上门对接与合同签署？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "支持徐州各区县（泉山、云龙、鼓楼、铜山等）面对面需求沟通、合同签署与驻场交付。"
      }
    }
  ]
}
</script>
```
