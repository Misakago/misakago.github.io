<template>
  <div class="home-page">
    <div class="container">
      <!-- Hero Section -->
      <section class="hero">
        <h1 class="hero-title">
          你好，我是 <span class="highlight">Misaka</span>
        </h1>
        <p class="hero-description">
          欢迎来到我的技术博客，这里记录了我在编程旅程中的思考与实践
        </p>
      </section>

      <!-- Articles Grid -->
      <section class="articles-section">
        <h2 class="section-title">
          <span class="section-title-icon">📝</span>
          最新文章
          <span class="article-count">{{ articles.length }}</span>
        </h2>

        <div class="articles-grid">
          <article
            v-for="article in articles"
            :key="article.slug"
            class="article-card"
            @click="goToArticle(article.slug)"
          >
            <div class="article-card-content">
              <h3 class="article-title">{{ article.title }}</h3>
              <p class="article-description">{{ article.description }}</p>
              <div class="article-meta">
                <time class="article-date">{{ formatDate(article.date) }}</time>
              </div>
            </div>
            <div class="article-card-arrow">→</div>
          </article>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import dayjs from 'dayjs'

const router = useRouter()
const articles = ref([])

onMounted(async () => {
  // 动态导入文章数据
  const response = await fetch('/articles/index.json')
  const data = await response.json()
  articles.value = data.sort((a, b) => new Date(b.date) - new Date(a.date))
})

const goToArticle = (slug) => {
  router.push(`/${slug}`)
}

const formatDate = (date) => {
  return dayjs(date).format('YYYY年MM月DD日')
}
</script>

<style scoped lang="scss">
.home-page {
  min-height: calc(100vh - var(--header-height));
}

.container {
  max-width: var(--max-width);
  margin: 0 auto;
  padding: var(--spacing-2xl) var(--spacing-lg);
}

// Hero Section
.hero {
  text-align: center;
  padding: var(--spacing-3xl) 0;
  animation: fadeIn 0.6s ease-out;
}

.hero-title {
  font-size: clamp(2rem, 5vw, 3rem);
  font-weight: 700;
  margin-bottom: var(--spacing-lg);
  letter-spacing: -0.02em;

  .highlight {
    background: linear-gradient(135deg, var(--color-primary) 0%, #8b5cf6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
}

.hero-description {
  font-size: 1.125rem;
  color: var(--color-text-secondary);
  max-width: 500px;
  margin: 0 auto;
  line-height: 1.8;
}

// Articles Section
.articles-section {
  margin-top: var(--spacing-3xl);
}

.section-title {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: var(--spacing-xl);
}

.section-title-icon {
  font-size: 1.25rem;
}

.article-count {
  display: inline-flex;
  align-items: center;
  padding: 0.125rem 0.5rem;
  background: var(--color-primary-light);
  color: var(--color-primary);
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: var(--radius-full);
}

.articles-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--spacing-md);
}

.article-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-lg);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--transition-normal);

  &:hover {
    border-color: var(--color-primary);
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);

    .article-card-arrow {
      transform: translateX(4px);
      color: var(--color-primary);
    }
  }
}

.article-card-content {
  flex: 1;
}

.article-title {
  font-size: 1.125rem;
  font-weight: 600;
  margin-bottom: var(--spacing-sm);
  color: var(--color-text);
}

.article-description {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: var(--spacing-sm);
}

.article-meta {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.article-date {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}

.article-card-arrow {
  flex-shrink: 0;
  margin-left: var(--spacing-md);
  font-size: 1.25rem;
  color: var(--color-border);
  transition: all var(--transition-fast);
}

@media (min-width: 768px) {
  .articles-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
