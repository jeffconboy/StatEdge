<template>
  <Layout>
    <div class="analytics-page">
      <div class="page-header">
        <h1 class="page-title">Analytics</h1>
        <p class="page-subtitle">Advanced baseball statistics and insights</p>
      </div>

      <div class="coming-soon">
        <div class="coming-soon-content">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
          </svg>
          <h2>Advanced Analytics</h2>
          <p>Sabermetrics and advanced baseball analytics coming soon!</p>
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

.analytics-page {
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