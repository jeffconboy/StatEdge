<template>
  <Layout>
    <div class="players-page">
      <div class="page-header">
        <h1 class="page-title">Players</h1>
        <p class="page-subtitle">Search and explore baseball player statistics</p>
      </div>

      <div class="search-section card">
        <div class="search-form">
          <div class="search-input-group">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Search for players..."
              class="search-input"
              @input="handleSearch"
              @keyup.enter="executeSearch"
            />
            <button class="search-button btn btn-primary" @click="executeSearch">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="11" cy="11" r="8"></circle>
                <path d="M21 21l-4.35-4.35"></path>
              </svg>
              Search
            </button>
          </div>

          <div class="search-filters">
            <select v-model="selectedPosition" class="filter-select">
              <option value="">All Positions</option>
              <option value="P">Pitcher</option>
              <option value="C">Catcher</option>
              <option value="1B">First Base</option>
              <option value="2B">Second Base</option>
              <option value="3B">Third Base</option>
              <option value="SS">Shortstop</option>
              <option value="LF">Left Field</option>
              <option value="CF">Center Field</option>
              <option value="RF">Right Field</option>
              <option value="DH">Designated Hitter</option>
            </select>

            <select v-model="selectedTeam" class="filter-select">
              <option value="">All Teams</option>
              <option value="NYY">New York Yankees</option>
              <option value="BOS">Boston Red Sox</option>
              <option value="LAD">Los Angeles Dodgers</option>
              <option value="SF">San Francisco Giants</option>
              <option value="HOU">Houston Astros</option>
              <option value="ATL">Atlanta Braves</option>
            </select>
          </div>
        </div>
      </div>

      <div v-if="loading" class="loading-state">
        <div class="loading-spinner">Loading players...</div>
      </div>

      <div v-else-if="error" class="error-state">
        <div class="error-message">{{ error }}</div>
      </div>

      <div v-else-if="searchResults.length === 0 && hasSearched" class="empty-state">
        <div class="empty-message">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"></circle>
            <path d="M16 16s-1.5-2-4-2-4 2-4 2"></path>
            <line x1="9" y1="9" x2="9.01" y2="9"></line>
            <line x1="15" y1="9" x2="15.01" y2="9"></line>
          </svg>
          <h3>No players found</h3>
          <p>Try adjusting your search terms or filters</p>
        </div>
      </div>

      <div v-else-if="searchResults.length > 0" class="results-section">
        <div class="results-header">
          <h2>Search Results</h2>
          <div class="results-count">{{ searchResults.length }} players found</div>
        </div>

        <div class="players-grid">
          <div
            v-for="player in searchResults"
            :key="player.id"
            class="player-card card"
          >
            <div class="player-card__header">
              <div class="player-avatar">
                {{ getPlayerInitials(player.name) }}
              </div>
              <div class="player-info">
                <h3 class="player-name">{{ player.name }}</h3>
                <div class="player-team">{{ player.team }}</div>
                <div class="player-position">{{ player.position }}</div>
              </div>
            </div>

            <div v-if="player.stats" class="player-card__stats">
              <div class="stat-row">
                <span class="stat-label">AVG</span>
                <span class="stat-value">{{ formatStat('avg', player.stats.avg) }}</span>
              </div>
              <div class="stat-row">
                <span class="stat-label">HR</span>
                <span class="stat-value">{{ player.stats.homeRuns || 0 }}</span>
              </div>
              <div class="stat-row">
                <span class="stat-label">RBI</span>
                <span class="stat-value">{{ player.stats.rbi || 0 }}</span>
              </div>
            </div>

            <div class="player-card__actions">
              <button class="btn btn-secondary" @click="viewPlayer(player.id)">
                View Profile
              </button>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="welcome-state">
        <div class="welcome-message">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"></circle>
            <path d="M21 21l-4.35-4.35"></path>
          </svg>
          <h2>Search for Players</h2>
          <p>Enter a player name, team, or position to get started</p>
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import Layout from '@/components/Layout.vue'
import { playerApi, useApiError } from '@/services/api'
import type { Player } from '@/types'

const router = useRouter()
const { handleError } = useApiError()

const searchQuery = ref('')
const selectedPosition = ref('')
const selectedTeam = ref('')
const searchResults = ref<Player[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const hasSearched = ref(false)

const executeSearch = async () => {
  if (!searchQuery.value.trim()) return

  try {
    loading.value = true
    error.value = null
    hasSearched.value = true

    const response = await playerApi.search({
      query: searchQuery.value,
      position: selectedPosition.value || undefined,
      team: selectedTeam.value || undefined,
      limit: 50
    })

    searchResults.value = response.players
  } catch (err) {
    const errorInfo = handleError(err)
    error.value = errorInfo.message
    console.error('Player search failed:', err)
    
    // Mock data fallback
    searchResults.value = [
      {
        id: '1',
        name: 'Aaron Judge',
        team: 'New York Yankees',
        position: 'RF',
        stats: { avg: 0.312, homeRuns: 45, rbi: 108 }
      },
      {
        id: '2',
        name: 'Mike Trout',
        team: 'Los Angeles Angels',
        position: 'CF',
        stats: { avg: 0.295, homeRuns: 38, rbi: 95 }
      }
    ]
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  // Debounce logic could go here
}

const viewPlayer = (playerId: string) => {
  router.push(`/players/${playerId}`)
}

const getPlayerInitials = (name: string): string => {
  return name.split(' ').map(n => n[0]).join('').toUpperCase()
}

const formatStat = (type: string, value: any): string => {
  if (type === 'avg' && typeof value === 'number') {
    return value.toFixed(3)
  }
  return String(value || '0')
}
</script>

<style lang="scss" scoped>
.players-page {
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

.search-section {
  padding: $spacing-xl;
  margin-bottom: $spacing-xl;
}

.search-form {
  max-width: 800px;
  margin: 0 auto;
}

.search-input-group {
  display: flex;
  gap: $spacing-md;
  margin-bottom: $spacing-lg;
}

.search-input {
  flex: 1;
  padding: $spacing-md;
  border: 2px solid $background-gray;
  border-radius: $border-radius-md;
  font-size: 1rem;
  transition: border-color 0.2s ease;

  &:focus {
    outline: none;
    border-color: $primary;
  }
}

.search-button {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  padding: $spacing-md $spacing-lg;
  white-space: nowrap;

  svg {
    width: 16px;
    height: 16px;
  }
}

.search-filters {
  display: flex;
  gap: $spacing-md;
  justify-content: center;
}

.filter-select {
  padding: $spacing-sm $spacing-md;
  border: 1px solid $background-gray;
  border-radius: $border-radius-md;
  background-color: $white;
  font-size: 0.875rem;
  cursor: pointer;

  &:focus {
    outline: none;
    border-color: $primary;
  }
}

.loading-state, .error-state, .empty-state, .welcome-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.loading-spinner {
  color: $text-muted;
  font-size: 1.125rem;
}

.error-message {
  background-color: rgba($danger, 0.1);
  color: $danger;
  padding: $spacing-lg;
  border-radius: $border-radius-md;
  text-align: center;
}

.empty-message, .welcome-message {
  text-align: center;
  color: $text-muted;

  svg {
    width: 48px;
    height: 48px;
    margin-bottom: $spacing-md;
    opacity: 0.5;
  }

  h2, h3 {
    color: $text-secondary;
    margin-bottom: $spacing-sm;
  }

  p {
    margin: 0;
  }
}

.results-section {
  margin-bottom: $spacing-xl;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: $spacing-lg;

  h2 {
    font-size: 1.5rem;
    font-weight: 700;
    color: $text-primary;
    margin: 0;
  }
}

.results-count {
  color: $text-secondary;
  font-weight: 500;
}

.players-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: $spacing-lg;
}

.player-card {
  padding: $spacing-lg;
  transition: transform 0.2s ease, box-shadow 0.2s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: $shadow-lg;
  }

  &__header {
    display: flex;
    align-items: center;
    gap: $spacing-md;
    margin-bottom: $spacing-md;
  }

  &__stats {
    margin-bottom: $spacing-md;
  }

  &__actions {
    text-align: center;
  }
}

.player-avatar {
  width: 60px;
  height: 60px;
  background: linear-gradient(135deg, $primary 0%, $primary-dark 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: $white;
  font-weight: 700;
  font-size: 1.125rem;
  flex-shrink: 0;
}

.player-info {
  flex: 1;
}

.player-name {
  font-size: 1.125rem;
  font-weight: 700;
  color: $text-primary;
  margin: 0 0 4px 0;
}

.player-team {
  font-size: 0.875rem;
  color: $primary;
  font-weight: 600;
  margin-bottom: 2px;
}

.player-position {
  font-size: 0.75rem;
  color: $text-secondary;
  font-weight: 500;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: $spacing-xs 0;
  border-bottom: 1px solid $background-light;

  &:last-child {
    border-bottom: none;
  }
}

.stat-label {
  font-size: 0.875rem;
  color: $text-secondary;
  font-weight: 600;
}

.stat-value {
  font-size: 0.875rem;
  color: $text-primary;
  font-weight: 700;
  font-family: $font-mono;
}

// Mobile responsive
@media (max-width: $breakpoint-tablet) {
  .search-filters {
    flex-direction: column;
    align-items: center;
  }

  .filter-select {
    width: 200px;
  }

  .players-grid {
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: $spacing-md;
  }
}

@media (max-width: $breakpoint-mobile) {
  .page-title {
    font-size: 2rem;
  }

  .search-section {
    padding: $spacing-lg;
  }

  .search-input-group {
    flex-direction: column;
  }

  .search-button {
    justify-content: center;
  }

  .results-header {
    flex-direction: column;
    align-items: flex-start;
    gap: $spacing-sm;
  }

  .players-grid {
    grid-template-columns: 1fr;
  }

  .player-card {
    padding: $spacing-md;
  }
}
</style>