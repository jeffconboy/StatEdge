<template>
  <Layout>
    <div class="compare-page">
      <div class="page-header">
        <h1 class="page-title">Compare</h1>
        <p class="page-subtitle">Compare player statistics side by side</p>
      </div>

      <div class="coming-soon">
        <div class="coming-soon-content">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"/>
          </svg>
          <h2>Player Comparison</h2>
          <p>Side-by-side player statistics comparison coming soon!</p>
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

.compare-page {
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