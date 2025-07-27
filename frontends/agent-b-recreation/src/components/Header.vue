<template>
  <header class="header">
    <div class="header__content">
      <!-- Mobile menu toggle -->
      <button
        class="header__mobile-toggle"
        @click="toggleMobileMenu"
        aria-label="Toggle navigation"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      <!-- Search Bar -->
      <div class="header__search">
        <div class="search-container">
          <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"></circle>
            <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-4.35-4.35"></path>
          </svg>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search baseball players, stats, teams..."
            class="search-input"
            @input="handleSearch"
            @focus="showSuggestions = true"
            @blur="hideSuggestions"
          />
        </div>

        <!-- Search Suggestions -->
        <div v-if="showSuggestions && (searchLoading || searchSuggestions.length)" class="search-suggestions">
          <!-- Loading State -->
          <div v-if="searchLoading" class="search-suggestion search-loading">
            <div class="suggestion-name">Searching players...</div>
          </div>
          
          <!-- Results -->
          <div
            v-for="suggestion in searchSuggestions"
            :key="suggestion.id"
            class="search-suggestion"
            @mousedown="selectSuggestion(suggestion)"
          >
            <div class="suggestion-type">{{ suggestion.type }}</div>
            <div class="suggestion-name">{{ suggestion.name }}</div>
            <div v-if="suggestion.team" class="suggestion-team">{{ suggestion.team }}</div>
          </div>
          
          <!-- No Results -->
          <div v-if="!searchLoading && !searchSuggestions.length && searchQuery.length >= 2" class="search-suggestion">
            <div class="suggestion-name">No players found for "{{ searchQuery }}"</div>
          </div>
        </div>
      </div>

      <!-- User Actions -->
      <div class="header__actions">
        <button class="btn btn-primary">
          <svg class="action-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
          </svg>
          Sign In
        </button>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { playerApi, useApiError } from '@/services/api'

const router = useRouter()
const emit = defineEmits(['toggle-mobile-menu'])
const { handleError } = useApiError()

const searchQuery = ref('')
const showSuggestions = ref(false)
const searchResults = ref([])
const searchLoading = ref(false)

let searchTimeout: NodeJS.Timeout

const searchSuggestions = computed(() => {
  return searchResults.value.map(player => ({
    id: player.id,
    type: 'Player',
    name: player.name,
    team: `${player.team} • ${player.position}`
  }))
})

const handleSearch = async () => {
  clearTimeout(searchTimeout)
  
  if (!searchQuery.value.trim() || searchQuery.value.length < 2) {
    searchResults.value = []
    showSuggestions.value = false
    return
  }

  searchTimeout = setTimeout(async () => {
    try {
      searchLoading.value = true
      const response = await playerApi.search({
        query: searchQuery.value,
        limit: 6
      })
      // StatEdge API returns array directly, not nested in players property
      searchResults.value = response.data || []
      showSuggestions.value = true
    } catch (error) {
      const errorInfo = handleError(error)
      console.error('Search failed:', errorInfo.message)
      searchResults.value = []
    } finally {
      searchLoading.value = false
    }
  }, 300)
}

const selectSuggestion = (suggestion: any) => {
  searchQuery.value = suggestion.name
  showSuggestions.value = false
  
  // Navigate based on suggestion type
  if (suggestion.type === 'Player') {
    router.push(`/players/${suggestion.id}`)
  } else if (suggestion.type === 'Team') {
    router.push(`/teams/${suggestion.id}`)
  }
}

const hideSuggestions = () => {
  setTimeout(() => {
    showSuggestions.value = false
  }, 200)
}

const toggleMobileMenu = () => {
  emit('toggle-mobile-menu')
}
</script>

<style lang="scss" scoped>
.header {
  height: $header-height;
  background-color: $white;
  border-bottom: 1px solid $background-gray;
  position: fixed;
  top: 0;
  left: $sidebar-width;
  right: 0;
  z-index: 999;

  &__content {
    height: 100%;
    display: flex;
    align-items: center;
    padding: 0 $spacing-lg;
    gap: $spacing-lg;
  }

  &__mobile-toggle {
    display: none;
    background: none;
    border: none;
    cursor: pointer;
    padding: $spacing-sm;
    color: $text-secondary;

    svg {
      width: 24px;
      height: 24px;
    }

    @media (max-width: $breakpoint-mobile) {
      display: block;
    }
  }

  &__search {
    flex: 1;
    max-width: 600px;
    position: relative;
  }

  &__actions {
    display: flex;
    align-items: center;
    gap: $spacing-md;
  }
}

.search-container {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: $spacing-md;
  width: 20px;
  height: 20px;
  color: $text-muted;
  z-index: 1;
}

.search-input {
  width: 100%;
  padding: $spacing-sm $spacing-md $spacing-sm 48px;
  border: 2px solid $background-gray;
  border-radius: 24px;
  font-size: 0.875rem;
  background-color: $background-light;
  transition: all 0.2s ease;

  &:focus {
    outline: none;
    border-color: $primary;
    background-color: $white;
  }

  &::placeholder {
    color: $text-muted;
  }
}

.search-suggestions {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background-color: $white;
  border: 1px solid $background-gray;
  border-radius: $border-radius-md;
  box-shadow: $shadow-lg;
  margin-top: $spacing-xs;
  max-height: 300px;
  overflow-y: auto;
  z-index: 1000;
}

.search-suggestion {
  padding: $spacing-md;
  cursor: pointer;
  border-bottom: 1px solid $background-light;
  transition: background-color 0.2s ease;

  &:hover {
    background-color: $background-light;
  }

  &:last-child {
    border-bottom: none;
  }
}

.suggestion-type {
  font-size: 0.75rem;
  font-weight: 600;
  color: $primary;
  text-transform: uppercase;
  margin-bottom: 2px;
}

.suggestion-name {
  font-weight: 600;
  color: $text-primary;
  margin-bottom: 2px;
}

.suggestion-team {
  font-size: 0.875rem;
  color: $text-secondary;
}

.search-loading {
  opacity: 0.7;
  font-style: italic;
  
  .suggestion-name {
    color: $text-muted;
  }
}

.action-icon {
  width: 16px;
  height: 16px;
  margin-right: $spacing-sm;
}

// Mobile responsive
@media (max-width: $breakpoint-mobile) {
  .header {
    left: 0;
    
    &__search {
      max-width: none;
    }
  }
}
</style>