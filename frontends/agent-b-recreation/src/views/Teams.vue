<template>
  <Layout>
    <div class="teams-page">
      <div class="page-header">
        <h1 class="page-title">Teams</h1>
        <p class="page-subtitle">Explore MLB team statistics and rosters</p>
      </div>

      <div class="coming-soon">
        <div class="coming-soon-content">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M20.618 5.984A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
          </svg>
          <h2>Teams Section</h2>
          <p>Team statistics and roster information coming soon!</p>
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup lang="ts">
import Layout from '@/components/Layout.vue'
</script>

<style lang="scss" scoped>
.teams-page {
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