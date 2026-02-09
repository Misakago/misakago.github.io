<template>
  <footer class="footer">
    <div class="footer-container">
      <div class="footer-content">
        <p class="footer-text">
          &copy; {{ currentYear }} Misaka. Built with
          <a href="https://vuejs.org/" target="_blank" rel="noopener">Vue 3</a> &
          <a href="https://vitejs.dev/" target="_blank" rel="noopener">Vite</a>
        </p>
        <p class="footer-links">
          <a href="https://github.com/Misakago" target="_blank" rel="noopener">GitHub</a>
          <span class="separator">·</span>
          <a href="https://github.com/Misakago/blog" target="_blank" rel="noopener">Source</a>
        </p>
      </div>
    </div>
  </footer>
</template>

<script setup>
import { computed } from 'vue'

const currentYear = computed(() => new Date().getFullYear())
</script>

<style scoped lang="scss">
.footer {
  margin-top: var(--spacing-3xl);
  padding: var(--spacing-2xl) 0;
  border-top: 1px solid var(--color-border);
  background: var(--color-bg-secondary);
}

.footer-container {
  max-width: var(--max-width);
  margin: 0 auto;
  padding: 0 var(--spacing-lg);
}

.footer-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-sm);
}

.footer-text {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

.footer-links {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: 0.875rem;
  color: var(--color-text-tertiary);

  a {
    color: var(--color-text-tertiary);

    &:hover {
      color: var(--color-primary);
    }
  }
}

.separator {
  color: var(--color-border);
}

@media (min-width: 640px) {
  .footer-content {
    flex-direction: row;
    justify-content: space-between;
  }
}
</style>
