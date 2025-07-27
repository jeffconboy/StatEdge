<template>
  <aside class="sidebar">
    <!-- Logo Header -->
    <div class="sidebar__header">
      <div class="sidebar__logo">
        <div class="sidebar__logo-icon">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z"/>
          </svg>
        </div>
        <h1 class="sidebar__logo-text">StatEdge</h1>
      </div>
    </div>

    <!-- Primary Navigation -->
    <nav class="sidebar__nav">
      <div class="sidebar__nav-section">
        <router-link
          v-for="item in primaryNavigation"
          :key="item.name"
          :to="item.path"
          class="sidebar__nav-item"
          :class="{ 'sidebar__nav-item--active': $route.path === item.path }"
        >
          <component :is="getIconComponent(item.icon)" class="sidebar__nav-icon" />
          <span class="sidebar__nav-text">{{ item.name }}</span>
          <span v-if="item.badge" class="sidebar__nav-badge">{{ item.badge }}</span>
        </router-link>
      </div>

      <!-- Secondary Navigation -->
      <div class="sidebar__nav-section">
        <div class="sidebar__nav-section-title">More</div>
        <a
          v-for="item in secondaryNavigation"
          :key="item.name"
          :href="item.path"
          class="sidebar__nav-item sidebar__nav-item--secondary"
        >
          <component :is="getIconComponent(item.icon)" class="sidebar__nav-icon" />
          <span class="sidebar__nav-text">{{ item.name }}</span>
        </a>
      </div>

      <!-- Promotional Section -->
      <div class="sidebar__promo">
        <div class="sidebar__promo-icon">⭐</div>
        <div class="sidebar__promo-content">
          <div class="sidebar__promo-title">Premium Features</div>
          <div class="sidebar__promo-subtitle">Advanced baseball analytics</div>
        </div>
      </div>
    </nav>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import type { NavigationItem } from '@/types'

const route = useRoute()

const primaryNavigation: NavigationItem[] = [
  { name: 'Home', path: '/', icon: 'home' },
  { name: 'HR Betting', path: '/hr-betting', icon: 'target' },
  { name: 'Players', path: '/players', icon: 'users' },
  { name: 'Teams', path: '/teams', icon: 'shield' },
  { name: 'Analytics', path: '/analytics', icon: 'chart' },
  { name: 'Trending', path: '/trending', icon: 'trending' },
  { name: 'Standings', path: '/standings', icon: 'trophy' },
  { name: 'Compare', path: '/compare', icon: 'compare' }
]

const secondaryNavigation: NavigationItem[] = [
  { name: 'Scores', path: '#', icon: 'clock' },
  { name: 'Trending', path: '#', icon: 'trending' },
  { name: 'Examples', path: '#', icon: 'star' },
  { name: 'Data & Glossary', path: '#', icon: 'book' },
  { name: 'About', path: '#', icon: 'info' },
  { name: 'Blog', path: '#', icon: 'news' },
  { name: 'Shop', path: '#', icon: 'shop' }
]

// Simple icon components as strings for SVG paths
const icons: Record<string, string> = {
  home: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6',
  target: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm0-14c-3.31 0-6 2.69-6 6s2.69 6 6 6 6-2.69 6-6-2.69-6-6-6zm0 10c-2.21 0-4-1.79-4-4s1.79-4 4-4 4 1.79 4 4-1.79 4-4 4z',
  users: 'M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a4 4 0 11-8 0 4 4 0 018 0z',
  shield: 'M20.618 5.984A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z',
  chart: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z',
  trending: 'M13 7h8m0 0v8m0-8l-8 8-4-4-6 6',
  trophy: 'M12 15l-2 5h4l-2-5zm0 0l-2-7h4l-2 7z',
  compare: 'M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4',
  clock: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z',
  star: 'M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z',
  book: 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253',
  info: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
  news: 'M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z',
  shop: 'M16 11V7a4 4 0 00-8 0v4M5 9h14l-1 7a2 2 0 01-2 2H8a2 2 0 01-2-2L5 9z'
}

const getIconComponent = (iconName: string) => {
  return {
    template: `
      <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" :d="iconPath" />
      </svg>
    `,
    computed: {
      iconPath() {
        return icons[iconName] || icons.home
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.sidebar {
  width: $sidebar-width;
  height: 100vh;
  background-color: $white;
  box-shadow: $shadow-sidebar;
  display: flex;
  flex-direction: column;
  position: fixed;
  left: 0;
  top: 0;
  z-index: 1000;

  &__header {
    padding: $spacing-lg;
    border-bottom: 1px solid $background-gray;
  }

  &__logo {
    display: flex;
    align-items: center;
    gap: $spacing-md;
  }

  &__logo-icon {
    width: 32px;
    height: 32px;
    background-color: $primary;
    border-radius: $border-radius-md;
    display: flex;
    align-items: center;
    justify-content: center;
    color: $white;

    svg {
      width: 20px;
      height: 20px;
    }
  }

  &__logo-text {
    font-size: 1.25rem;
    font-weight: 700;
    color: $text-primary;
    margin: 0;
  }

  &__nav {
    flex: 1;
    padding: $spacing-lg $spacing-md;
    overflow-y: auto;
  }

  &__nav-section {
    margin-bottom: $spacing-xl;

    &:last-child {
      margin-bottom: 0;
    }
  }

  &__nav-section-title {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    color: $text-muted;
    letter-spacing: 0.05em;
    margin-bottom: $spacing-md;
  }

  &__nav-item {
    display: flex;
    align-items: center;
    padding: $spacing-sm $spacing-md;
    color: $text-secondary;
    text-decoration: none;
    border-radius: $border-radius-md;
    margin-bottom: $spacing-xs;
    transition: all 0.2s ease;
    font-weight: 500;

    &:hover {
      background-color: $background-light;
      color: $text-primary;
    }

    &--active {
      background-color: rgba($primary, 0.1);
      color: $primary;
    }

    &--secondary {
      .sidebar__nav-icon {
        width: 16px;
        height: 16px;
      }
    }
  }

  &__nav-icon {
    width: 20px;
    height: 20px;
    margin-right: $spacing-md;
    flex-shrink: 0;
  }

  &__nav-text {
    flex: 1;
  }

  &__nav-badge {
    background-color: $success;
    color: $white;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 12px;
    margin-left: auto;
  }

  &__promo {
    margin-top: $spacing-xl;
    padding: $spacing-md;
    background-color: #fef3c7;
    border: 1px solid #fbbf24;
    border-radius: $border-radius-md;
    display: flex;
    align-items: flex-start;
    gap: $spacing-sm;
  }

  &__promo-icon {
    font-size: 1.25rem;
    flex-shrink: 0;
  }

  &__promo-content {
    flex: 1;
  }

  &__promo-title {
    font-weight: 600;
    color: #92400e;
    font-size: 0.875rem;
    margin-bottom: 2px;
  }

  &__promo-subtitle {
    font-size: 0.75rem;
    color: #b45309;
  }
}

.icon {
  width: 100%;
  height: 100%;
}

// Mobile responsive
@media (max-width: $breakpoint-mobile) {
  .sidebar {
    transform: translateX(-100%);
    transition: transform 0.3s ease;

    &--mobile-open {
      transform: translateX(0);
    }
  }
}
</style>