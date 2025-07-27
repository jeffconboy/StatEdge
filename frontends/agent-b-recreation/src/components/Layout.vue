<template>
  <div class="layout">
    <Sidebar :class="{ 'sidebar--mobile-open': mobileMenuOpen }" />
    <div class="layout__main">
      <Header @toggle-mobile-menu="toggleMobileMenu" />
      <main class="layout__content">
        <slot />
      </main>
    </div>
    
    <!-- Mobile overlay -->
    <div
      v-if="mobileMenuOpen"
      class="layout__overlay"
      @click="closeMobileMenu"
    ></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import Sidebar from './Sidebar.vue'
import Header from './Header.vue'

const mobileMenuOpen = ref(false)

const toggleMobileMenu = () => {
  mobileMenuOpen.value = !mobileMenuOpen.value
}

const closeMobileMenu = () => {
  mobileMenuOpen.value = false
}

const handleResize = () => {
  if (window.innerWidth > 768) {
    mobileMenuOpen.value = false
  }
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style lang="scss" scoped>
.layout {
  display: flex;
  min-height: 100vh;

  &__main {
    flex: 1;
    margin-left: $sidebar-width;
    display: flex;
    flex-direction: column;
  }

  &__content {
    flex: 1;
    margin-top: $header-height;
    padding: $spacing-lg;
    background-color: $background-light;
    min-height: calc(100vh - #{$header-height});
  }

  &__overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.5);
    z-index: 999;
    display: none;
  }
}

// Mobile responsive
@media (max-width: $breakpoint-mobile) {
  .layout {
    &__main {
      margin-left: 0;
    }

    &__overlay {
      display: block;
    }
  }
}
</style>