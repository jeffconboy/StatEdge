<template>
  <div id="app" class="app">
    <RouterView />
  </div>
</template>

<script setup lang="ts">
import { RouterView } from 'vue-router'
</script>

<style lang="scss">
.app {
  min-height: 100vh;
  background-color: $background-light;
  font-family: $font-primary;
}
</style>