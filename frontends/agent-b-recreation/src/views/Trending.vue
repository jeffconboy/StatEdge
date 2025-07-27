<template>
  <Layout>
    <div class="trending-page">
      <div class="page-header">
        <h1 class="page-title">Trending</h1>
        <p class="page-subtitle">Hot players and trending statistics</p>
      </div>

      <div class="coming-soon">
        <div class="coming-soon-content">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>
          </svg>
          <h2>Trending Performance</h2>
          <p>Player trending analysis and hot streaks coming soon!</p>
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup lang="ts">
import Layout from '@/components/Layout.vue'
</script>

<style lang="scss" scoped>
// Variables are automatically imported via Vite config

.trending-page {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: $spacing-xl;
  text-align: center;
}

.page-title {
  font-size: 2.5rem;
  font-weight: 800;
  color: $text-primary;
  margin: 0 0 $spacing-sm 0;
}

.page-subtitle {
  font-size: 1.125rem;
  color: $text-secondary;
  margin: 0;
}

.coming-soon {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.coming-soon-content {
  text-align: center;
  color: $text-muted;

  svg {
    width: 64px;
    height: 64px;
    margin-bottom: $spacing-lg;
    opacity: 0.5;
  }

  h2 {
    color: $text-secondary;
    margin-bottom: $spacing-sm;
  }

  p {
    margin: 0;
    font-size: 1.125rem;
  }
}
</style>