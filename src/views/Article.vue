<template>
  <div class="article-page" v-if="article">
    <article class="article">
      <div class="article-header">
        <router-link to="/" class="back-link">
          ← 返回首页
        </router-link>
        <h1 class="article-title">{{ article.title }}</h1>
        <div class="article-meta">
          <time class="article-date">{{ formatDate(article.date) }}</time>
        </div>
      </div>

      <div
        class="article-content markdown-body"
        v-html="renderedContent"
      ></div>
    </article>
  </div>
  <div class="article-page" v-else>
    <div class="container">
      <div class="loading">加载中...</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import MarkdownIt from 'markdown-it'
import markdownItAnchor from 'markdown-it-anchor'
import hljs from 'highlight.js'
import dayjs from 'dayjs'
import 'highlight.js/styles/github-dark.css'

const route = useRoute()
const article = ref(null)
const markdownContent = ref('')

// 配置 Markdown 渲染器
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  highlight: (str, lang) => {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return `<pre class="hljs"><code>${hljs.highlight(str, { language: lang }).value}</code></pre>`
      } catch (__) {}
    }
    return `<pre class="hljs"><code>${md.utils.escapeHtml(str)}</code></pre>`
  }
})

// 添加锚点插件
md.use(markdownItAnchor, {
  permalink: markdownItAnchor.permalink.linkInsideHeader({
    symbol: '#',
    placement: 'before'
  })
})

const renderedContent = computed(() => {
  if (!markdownContent.value) return ''
  return md.render(markdownContent.value)
})

const formatDate = (date) => {
  return dayjs(date).format('YYYY年MM月DD日')
}

const loadArticle = async (slug) => {
  try {
    // 获取文章索引
    const indexRes = await fetch('/articles/index.json')
    const articles = await indexRes.json()
    const found = articles.find(a => a.slug === slug)

    if (found) {
      article.value = found
      // 获取文章内容
      const contentRes = await fetch(`/articles/${slug}.md`)
      markdownContent.value = await contentRes.text()
    }
  } catch (error) {
    console.error('Failed to load article:', error)
  }
}

onMounted(() => {
  loadArticle(route.params.slug || route.path.slice(1))
})

watch(() => route.params.slug, (newSlug) => {
  if (newSlug) {
    loadArticle(newSlug)
    window.scrollTo(0, 0)
  }
})
</script>

<style scoped lang="scss">
.article-page {
  min-height: calc(100vh - var(--header-height));
}

.article {
  max-width: var(--content-max-width);
  margin: 0 auto;
  padding: var(--spacing-2xl) var(--spacing-lg);
}

.article-header {
  margin-bottom: var(--spacing-2xl);
}

.back-link {
  display: inline-flex;
  align-items: center;
  padding: var(--spacing-sm) var(--spacing-md);
  margin-bottom: var(--spacing-lg);
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  background: var(--color-bg-secondary);
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);

  &:hover {
    color: var(--color-primary);
    background: var(--color-primary-light);
  }
}

.article-title {
  font-size: clamp(1.75rem, 4vw, 2.5rem);
  font-weight: 700;
  line-height: 1.3;
  letter-spacing: -0.02em;
  margin-bottom: var(--spacing-md);
}

.article-meta {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.article-date {
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
}

.loading {
  text-align: center;
  padding: var(--spacing-3xl);
  color: var(--color-text-secondary);
}
</style>

<style lang="scss">
// Markdown 内容样式
.markdown-body {
  font-size: 1.0625rem;
  line-height: 1.8;
  color: var(--color-text);

  // 标题
  h2, h3, h4, h5, h6 {
    margin-top: var(--spacing-2xl);
    margin-bottom: var(--spacing-md);
    font-weight: 600;
    line-height: 1.4;
    letter-spacing: -0.01em;
  }

  h2 {
    font-size: 1.75rem;
    padding-bottom: var(--spacing-sm);
    border-bottom: 1px solid var(--color-border);
  }

  h3 {
    font-size: 1.375rem;
  }

  h4 {
    font-size: 1.125rem;
  }

  // 段落
  p {
    margin-bottom: var(--spacing-lg);
  }

  // 链接
  a {
    color: var(--color-primary);
    text-decoration: none;
    border-bottom: 1px solid transparent;
    transition: border-color var(--transition-fast);

    &:hover {
      border-bottom-color: var(--color-primary);
    }
  }

  // 图片
  img {
    border-radius: var(--radius-md);
    margin: var(--spacing-lg) 0;
    box-shadow: var(--shadow-md);
  }

  // 代码块
  pre {
    margin: var(--spacing-lg) 0;
    padding: var(--spacing-lg);
    background: var(--color-code-bg);
    border-radius: var(--radius-md);
    overflow-x: auto;

    code {
      color: #e6e6e6;
      font-family: var(--font-mono);
      font-size: 0.875rem;
      line-height: 1.6;
    }
  }

  // 行内代码
  code:not(pre code) {
    padding: 0.2em 0.4em;
    margin: 0 0.2em;
    font-family: var(--font-mono);
    font-size: 0.875em;
    background: var(--color-code-inline);
    border-radius: var(--radius-sm);
  }

  // 引用
  blockquote {
    margin: var(--spacing-lg) 0;
    padding: var(--spacing-md) var(--spacing-lg);
    border-left: 4px solid var(--color-primary);
    background: var(--color-bg-secondary);
    border-radius: 0 var(--radius-md) var(--radius-md) 0;
    color: var(--color-text-secondary);

    p {
      margin-bottom: 0;
    }
  }

  // 列表
  ul, ol {
    margin-bottom: var(--spacing-lg);
    padding-left: var(--spacing-xl);
  }

  li {
    margin-bottom: var(--spacing-sm);

    > ul, > ol {
      margin-bottom: 0;
    }
  }

  ul {
    list-style-type: disc;
  }

  ol {
    list-style-type: decimal;
  }

  // 表格
  table {
    width: 100%;
    margin: var(--spacing-lg) 0;
    border-collapse: collapse;
    overflow: hidden;
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-sm);
  }

  th, td {
    padding: var(--spacing-md) var(--spacing-lg);
    text-align: left;
    border-bottom: 1px solid var(--color-border);
  }

  th {
    font-weight: 600;
    background: var(--color-bg-secondary);
  }

  tr:last-child td {
    border-bottom: none;
  }

  // 分隔线
  hr {
    margin: var(--spacing-2xl) 0;
    border: none;
    border-top: 1px solid var(--color-border);
  }

  // 锚点链接
  .header-anchor {
    float: left;
    margin-left: -1.2em;
    padding-right: 0.4em;
    opacity: 0;
    transition: opacity var(--transition-fast);
    font-weight: normal;
  }

  h2:hover .header-anchor,
  h3:hover .header-anchor,
  h4:hover .header-anchor {
    opacity: 1;
  }
}
</style>
