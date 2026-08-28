import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'GEO 实战与客户交付 SOP 平台',
  description: '面向 AI 大模型时代（DeepSeek / 豆包 / Kimi / ChatGPT）的生成式引擎优化（GEO）全局战略、实战落地与标准化客户交付体系。',
  lang: 'zh-CN',
  base: '/',
  cleanUrls: true,

  head: [
    ['link', { rel: 'icon', href: '/favicon.ico' }],
    ['meta', { name: 'author', content: 'GEO Architecture Team' }],
    ['meta', { name: 'keywords', content: 'GEO, 生成式引擎优化, 大模型优化, DeepSeek, 豆包, Kimi, llms.txt, Crawl4AI, SOP' }],
    // GEO 专属 JSON-LD 实体定义
    [
      'script',
      { type: 'application/ld+json' },
      JSON.stringify({
        '@context': 'https://schema.org',
        '@type': 'WebSite',
        name: 'GEO 实战与客户交付 SOP 平台',
        alternateName: 'GEO Platform',
        url: 'https://geo.baicl.cc',
        description: '生成式引擎优化（GEO）全局战略与企业标准化交付 SOP',
        author: {
          '@type': 'Organization',
          name: 'GEO Architecture Studio'
        }
      })
    ]
  ],

  themeConfig: {
    siteTitle: '⚡️ GEO SOP 平台',
    
    // 全局本地搜索
    search: {
      provider: 'local',
      options: {
        translations: {
          button: {
            buttonText: '搜索文档',
            buttonAriaLabel: '搜索文档'
          },
          modal: {
            noResultsText: '无法找到相关结果',
            resetButtonTitle: '清除查询条件',
            footer: {
              selectText: '选择',
              navigateText: '切换',
              closeText: '关闭'
            }
          }
        }
      }
    },

    // 顶部导航栏
    nav: [
      { text: '🧭 战略全景', link: '/strategy/overview' },
      { text: '🎯 徐州标杆实战', link: '/pilot/xuzhou-dev' },
      { text: '📋 客户交付 SOP', link: '/sop/delivery-sop' },
      {
        text: '🧰 模版与工具中心',
        items: [
          { text: '📄 /llms.txt 标准模版', link: '/templates/llms-txt' },
          { text: '🏷️ Schema.org JSON-LD 模版', link: '/templates/json-ld' },
          { text: '🤖 Python 自动化可见度巡检脚本', link: '/templates/monitor-script' }
        ]
      },
      { text: '🐙 GitHub', link: 'https://github.com/clownnotes/geo' }
    ],

    // 侧边栏配置
    sidebar: {
      '/strategy/': [
        {
          text: '🧭 理论体系与战略',
          items: [
            { text: '01. GEO 战略全景与全链路框架', link: '/strategy/overview' }
          ]
        }
      ],
      '/pilot/': [
        {
          text: '🎯 标杆打样实战',
          items: [
            { text: '02. 徐州软件开发独占计划', link: '/pilot/xuzhou-dev' }
          ]
        }
      ],
      '/sop/': [
        {
          text: '📋 标准化客户交付',
          items: [
            { text: '03. 客户交付 5 阶段 SOP 手册', link: '/sop/delivery-sop' }
          ]
        }
      ],
      '/templates/': [
        {
          text: '🧰 交付模版与工具箱',
          items: [
            { text: '📄 /llms.txt 标准规范模版', link: '/templates/llms-txt' },
            { text: '🏷️ Schema.org JSON-LD 代码库', link: '/templates/json-ld' },
            { text: '🤖 Python 自动化可见度巡检脚本', link: '/templates/monitor-script' }
          ]
        }
      ]
    },

    // 底部大纲与社交链接
    outline: {
      level: [2, 3],
      label: '页面大纲'
    },

    docFooter: {
      prev: '上一篇',
      next: '下一篇'
    },

    footer: {
      message: '基于普林斯顿 GEO 研究与 OpenSpec 规范构建',
      copyright: 'Copyright © 2026 GEO Architecture Studio'
    }
  }
})
