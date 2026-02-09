import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import './styles/main.scss'

// 路由配置
const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('./views/Home.vue'),
    meta: { title: '首页' }
  },
  {
    path: '/:slug',
    name: 'article',
    component: () => import('./views/Article.vue'),
    meta: { title: '文章' }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    return savedPosition || { top: 0, behavior: 'smooth' }
  }
})

// 设置页面标题
router.beforeEach((to, from, next) => {
  const baseTitle = "Misaka's Tech Blog"
  document.title = to.meta.title ? `${to.meta.title} - ${baseTitle}` : baseTitle
  next()
})

const app = createApp(App)
app.use(router)
app.mount('#app')
