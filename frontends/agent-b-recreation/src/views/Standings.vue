<template>
  <Layout>
    <div class="standings-page">
      <div class="page-header">
        <h1 class="page-title">Standings</h1>
        <p class="page-subtitle">Current MLB league standings</p>
      </div>

      <div class="standings-content">
        <StandingsTable />
      </div>
    </div>
  </Layout>
</template>

<script setup lang="ts">
import Layout from '@/components/Layout.vue'
import StandingsTable from '@/components/StandingsTable.vue'
</script>

<style lang="scss" scoped>
// Variables are automatically imported via Vite config

.standings-page {
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

.standings-content {
  max-width: 1000px;
  margin: 0 auto;
}
</style>