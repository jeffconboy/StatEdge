<template>
  <div class="live-scores">
    <div class="live-scores__header">
      <h2 class="live-scores__title">Live Scores</h2>
      <div class="live-scores__date">{{ currentDate }}</div>
      <div v-if="lastUpdated" class="live-scores__updated">
        Updated: {{ lastUpdated.toLocaleTimeString() }}
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="live-scores__loading">
      <div class="loading-spinner">Loading games...</div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="live-scores__error">
      <div class="error-message">{{ error }}</div>
      <button @click="loadGames" class="retry-button">Retry</button>
    </div>

    <!-- No Games State -->
    <div v-else-if="games.length === 0" class="live-scores__empty">
      <div class="empty-message">No games scheduled for today</div>
    </div>

    <!-- Games List -->
    <div v-else class="live-scores__container">
      <div class="live-scores__scroll">
        <div
          v-for="game in games"
          :key="game.id"
          class="game-card"
        >
          <div class="game-card__teams">
            <div class="team team--away">
              <div class="team__logo">
                <img 
                  :src="getTeamLogoUrl(game.awayTeam.abbreviation)" 
                  :alt="`${game.awayTeam.name} logo`"
                  class="team__logo-img"
                  @error="handleLogoError($event)"
                  @load="handleLogoLoad($event)"
                />
                <span class="team__logo-fallback">{{ game.awayTeam.abbreviation }}</span>
              </div>
              <div class="team__name">{{ game.awayTeam.name }}</div>
              <div class="team__score">{{ game.awayScore }}</div>
            </div>

            <div class="game-card__vs">
              <div class="vs-divider">@</div>
              <div class="game-status" :class="`game-status--${game.status}`">
                {{ getGameStatusText(game) }}
              </div>
            </div>

            <div class="team team--home">
              <div class="team__logo">
                <img 
                  :src="getTeamLogoUrl(game.homeTeam.abbreviation)" 
                  :alt="`${game.homeTeam.name} logo`"
                  class="team__logo-img"
                  @error="handleLogoError($event)"
                  @load="handleLogoLoad($event)"
                />
                <span class="team__logo-fallback">{{ game.homeTeam.abbreviation }}</span>
              </div>
              <div class="team__name">{{ game.homeTeam.name }}</div>
              <div class="team__score">{{ game.homeScore }}</div>
            </div>
          </div>

          <div v-if="game.inning" class="game-card__inning">
            {{ game.inning }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import type { Game } from '@/types'
import { gamesApi, useApiError } from '@/services/api'

const { handleError } = useApiError()

const games = ref<Game[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const lastUpdated = ref<Date | null>(null)
const refreshInterval = ref<NodeJS.Timeout | null>(null)

const currentDate = computed(() => {
  return new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
})

const loadGames = async () => {
  try {
    loading.value = true
    error.value = null
    
    console.log('Loading today\'s games...')
    const response = await gamesApi.getTodaysGames()
    console.log('Games API response:', response)
    
    if (response && response.games) {
      // Transform the API response to match our Game interface
      games.value = response.games.map((game: any) => ({
        id: game.id,
        homeTeam: {
          id: game.homeTeam.id,
          name: game.homeTeam.name,
          abbreviation: game.homeTeam.abbreviation
        },
        awayTeam: {
          id: game.awayTeam.id,
          name: game.awayTeam.name,
          abbreviation: game.awayTeam.abbreviation
        },
        homeScore: game.homeScore,
        awayScore: game.awayScore,
        status: game.status,
        time: game.time,
        inning: game.inning
      }))
      
      lastUpdated.value = new Date()
      console.log(`Loaded ${games.value.length} games`)
    } else {
      console.warn('No games data received, response:', response)
      games.value = []
    }
    
  } catch (err) {
    console.error('Failed to load games:', err)
    const errorInfo = handleError(err)
    error.value = errorInfo.message
    
    // Fallback to mock data if API fails
    try {
      console.log('Using fallback games data')
      const fallbackGames = await gamesApi.getLiveGames() // This includes fallback logic
      games.value = fallbackGames
    } catch (fallbackErr) {
      console.error('Fallback also failed:', fallbackErr)
      games.value = []
    }
    
  } finally {
    loading.value = false
  }
}

const startAutoRefresh = () => {
  // Refresh every 30 seconds for live games
  refreshInterval.value = setInterval(async () => {
    if (!loading.value) {
      console.log('Auto-refreshing games...')
      await loadGames()
    }
  }, 30000) // 30 seconds
}

const stopAutoRefresh = () => {
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value)
    refreshInterval.value = null
  }
}

const getGameStatusText = (game: Game): string => {
  switch (game.status) {
    case 'live':
      return game.inning || 'Live'
    case 'final':
      return 'Final'
    case 'scheduled':
      return game.time || 'Scheduled'
    default:
      return ''
  }
}

const hasLiveGames = computed(() => {
  return games.value.some(game => game.status === 'live')
})

const getTeamLogoUrl = (abbreviation: string): string => {
  // ESPN team logos - mapping MLB abbreviations to ESPN codes
  const teamMapping: Record<string, string> = {
    // American League East
    'NYY': 'nyy',
    'BOS': 'bos', 
    'TB': 'tb',
    'TOR': 'tor',
    'BAL': 'bal',
    
    // American League Central
    'CWS': 'cws',
    'MIN': 'min',
    'DET': 'det',
    'CLE': 'cle',
    'KC': 'kc',
    
    // American League West
    'HOU': 'hou',
    'TEX': 'tex',
    'SEA': 'sea',
    'LAA': 'laa',
    'OAK': 'oak',
    'ATH': 'oak', // Athletics (now Sacramento) still use Oakland logos
    
    // National League East
    'ATL': 'atl',
    'NYM': 'nym',
    'PHI': 'phi',
    'WSH': 'wsh',
    'MIA': 'mia',
    
    // National League Central
    'CHC': 'chc',
    'MIL': 'mil',
    'CIN': 'cin',
    'STL': 'stl',
    'PIT': 'pit',
    
    // National League West
    'LAD': 'lad',
    'SF': 'sf',
    'SD': 'sd',
    'COL': 'col',
    'AZ': 'ari',  // Arizona Diamondbacks - MLB uses 'AZ', ESPN uses 'ari'
    'ARI': 'ari'   // Also handle if API returns 'ARI'
  }
  
  const espnCode = teamMapping[abbreviation] || abbreviation.toLowerCase()
  return `https://a.espncdn.com/i/teamlogos/mlb/500/${espnCode}.png`
}

const handleLogoError = (event: Event) => {
  const img = event.target as HTMLImageElement
  if (img) {
    img.style.display = 'none'
    console.warn(`Failed to load logo: ${img.src}`)
  }
}

const handleLogoLoad = (event: Event) => {
  const img = event.target as HTMLImageElement
  if (img && img.nextElementSibling) {
    // Hide fallback text when logo loads successfully
    (img.nextElementSibling as HTMLElement).style.display = 'none'
  }
}

onMounted(async () => {
  console.log('LiveScoresTicker mounted - loading real game data')
  await loadGames()
  
  // Start auto-refresh if there are live games
  if (hasLiveGames.value) {
    startAutoRefresh()
  }
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style lang="scss" scoped>
.live-scores {
  margin-bottom: $spacing-xl;

  &__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: $spacing-md;
  }

  &__title {
    font-size: 1.5rem;
    font-weight: 700;
    color: $text-primary;
    margin: 0;
  }

  &__date {
    font-size: 0.875rem;
    color: $text-secondary;
    font-weight: 500;
  }

  &__updated {
    font-size: 0.75rem;
    color: $text-muted;
    font-style: italic;
  }

  &__loading, &__error, &__empty {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 120px;
    background-color: $white;
    border-radius: $border-radius-md;
    box-shadow: $shadow-sm;
  }

  &__loading {
    .loading-spinner {
      color: $text-secondary;
      font-size: 0.875rem;
    }
  }

  &__error {
    flex-direction: column;
    gap: $spacing-md;

    .error-message {
      color: $danger;
      font-size: 0.875rem;
      text-align: center;
    }

    .retry-button {
      background-color: $primary;
      color: $white;
      border: none;
      border-radius: $border-radius-sm;
      padding: $spacing-sm $spacing-md;
      font-size: 0.875rem;
      font-weight: 600;
      cursor: pointer;
      transition: background-color 0.2s ease;

      &:hover {
        background-color: $primary-dark;
      }
    }
  }

  &__empty {
    .empty-message {
      color: $text-muted;
      font-size: 0.875rem;
      text-align: center;
    }
  }

  &__container {
    position: relative;
    overflow: hidden;
  }

  &__scroll {
    display: flex;
    gap: $spacing-md;
    overflow-x: auto;
    padding-bottom: $spacing-sm;
    scroll-behavior: smooth;

    &::-webkit-scrollbar {
      height: 6px;
    }

    &::-webkit-scrollbar-track {
      background: $background-gray;
      border-radius: 3px;
    }

    &::-webkit-scrollbar-thumb {
      background: $text-muted;
      border-radius: 3px;

      &:hover {
        background: $text-secondary;
      }
    }
  }
}

.game-card {
  background-color: $white;
  border-radius: $border-radius-md;
  padding: $spacing-md;
  box-shadow: $shadow-sm;
  min-width: 280px;
  flex-shrink: 0;
  transition: box-shadow 0.2s ease;

  &:hover {
    box-shadow: $shadow-md;
  }

  &__teams {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: $spacing-sm;
  }

  &__vs {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin: 0 $spacing-md;
  }

  &__inning {
    text-align: center;
    font-size: 0.75rem;
    color: $text-secondary;
    font-weight: 600;
  }
}

.team {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  min-width: 80px;

  &__logo {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: $spacing-xs;
    position: relative;
    overflow: hidden;
    background-color: $background-light;
    border: 1px solid $background-gray;
  }

  &__logo-img {
    width: 100%;
    height: 100%;
    object-fit: contain;
    object-position: center;
    transition: opacity 0.3s ease;
    z-index: 2;
    position: relative;
  }

  &__logo-fallback {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-size: 0.75rem;
    font-weight: 700;
    color: $primary;
    background-color: $white;
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    z-index: 1;
    transition: opacity 0.3s ease;
  }

  &__name {
    font-size: 0.75rem;
    color: $text-secondary;
    margin-bottom: 2px;
    font-weight: 500;
  }

  &__score {
    font-size: 1.25rem;
    font-weight: 700;
    color: $text-primary;
  }
}

.vs-divider {
  font-size: 0.875rem;
  color: $text-muted;
  margin-bottom: $spacing-xs;
}

.game-status {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 12px;
  text-align: center;
  min-width: 60px;

  &--live {
    background-color: #dc3545;
    color: $white;
  }

  &--final {
    background-color: $background-gray;
    color: $text-secondary;
  }

  &--scheduled {
    background-color: $primary;
    color: $white;
  }
}

// Mobile responsive
@media (max-width: $breakpoint-mobile) {
  .live-scores {
    &__header {
      flex-direction: column;
      align-items: flex-start;
      gap: $spacing-xs;
    }
  }

  .game-card {
    min-width: 240px;
    padding: $spacing-sm;

    &__teams {
      margin-bottom: $spacing-xs;
    }
  }

  .team {
    min-width: 60px;

    &__logo {
      width: 28px;
      height: 28px;
      font-size: 0.625rem;
    }

    &__name {
      font-size: 0.6875rem;
    }

    &__score {
      font-size: 1.125rem;
    }
  }
}
</style>