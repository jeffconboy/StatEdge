<template>
  <Layout>
    <div class="dashboard">
      <!-- Live Scores Section -->
      <section class="dashboard__section">
        <LiveScoresTicker />
      </section>

      <!-- Featured Content Grid -->
      <section class="dashboard__section">
        <div class="featured-grid">
          <PlayerSpotlightCard
            v-for="(featured, index) in featuredPlayers"
            :key="index"
            :player="featured.player"
            :matchup="featured.matchup"
            :stats="featured.stats"
            :highlight="featured.highlight"
            :bg-color="featured.bgColor"
          />
        </div>
      </section>

      <!-- Main Content Grid -->
      <section class="dashboard__section">
        <div class="main-grid">
          <!-- Trending Performance Widget -->
          <div class="main-grid__item">
            <TrendingPerformanceWidget />
          </div>

          <!-- MLB Standings -->
          <div class="main-grid__item">
            <StandingsTable />
          </div>
        </div>
      </section>

      <!-- Database Stats -->
      <section v-if="databaseStats" class="dashboard__section">
        <div class="stats-overview card">
          <h3 class="stats-overview__title">StatEdge Database</h3>
          <div class="stats-overview__grid">
            <div class="stat-item">
              <div class="stat-value">{{ databaseStats.total_players?.toLocaleString() || 'N/A' }}</div>
              <div class="stat-label">Total Players</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ databaseStats.total_statcast_pitches?.toLocaleString() || 'N/A' }}</div>
              <div class="stat-label">Statcast Pitches</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ databaseStats.statcast_2025_records?.toLocaleString() || 'N/A' }}</div>
              <div class="stat-label">2025 Records</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ databaseStats.fangraphs_2025_batting_players?.toLocaleString() || 'N/A' }}</div>
              <div class="stat-label">2025 FanGraphs</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ formatDate(databaseStats.timestamp) }}</div>
              <div class="stat-label">Last Updated</div>
            </div>
          </div>
        </div>
      </section>
    </div>
  </Layout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import Layout from '@/components/Layout.vue'
import LiveScoresTicker from '@/components/LiveScoresTicker.vue'
import PlayerSpotlightCard from '@/components/PlayerSpotlightCard.vue'
import TrendingPerformanceWidget from '@/components/TrendingPerformanceWidget.vue'
import StandingsTable from '@/components/StandingsTable.vue'
import { systemApi, mockApi, playerApi, imageApi, useApiError } from '@/services/api'
import type { DatabaseStatsResponse } from '@/services/api'
import { getPlayerImages } from '@/services/playerImages'

const { handleError } = useApiError()

const featuredPlayers = ref<any[]>([])
const databaseStats = ref<DatabaseStatsResponse | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)

const loadDashboardData = async () => {
  try {
    loading.value = true
    error.value = null

    // Load featured players - use regular trending API with hardcoded images for demo
    try {
      console.log('Loading trending players...')
      const trending = await playerApi.getTrending()
      console.log('Trending response:', trending)
      
      // Use local images from database first, then fallbacks
      featuredPlayers.value = trending.data?.map((player, index) => {
        const images = getPlayerImages(
          player.name, 
          player.team, 
          player.mlb_id?.toString(), 
          player.local_image_path
        )
        return {
          player: { 
            name: player.name, 
            team: player.team,
            headshot_url: images.headshot_url,
            team_logo_url: images.team_logo_url,
            team_primary_color: '#000000'
          },
          matchup: `${player.team} • ${player.position}`,
          stats: [
            { label: 'AVG', value: player.stats?.batting_average?.toFixed(3) || '.000' },
            { label: 'HR', value: player.stats?.home_runs || 0 },
            { label: 'AB', value: player.stats?.at_bats || 0 },
            { label: 'H', value: player.stats?.hits || 0 }
          ],
          highlight: `${player.stats?.batting_average?.toFixed(3) || '.000'} AVG • ${player.stats?.hits || 0}/${player.stats?.at_bats || 0} in last 30 days`,
          bgColor: ['blue', 'green', 'purple', 'red'][index % 4]
        }
      }).slice(0, 4) || [] // Show up to 4 featured players
      
      console.log('Featured players with Mike Trout cartoon:', featuredPlayers.value)
    } catch (apiError) {
      console.error('Failed to load trending players:', apiError)
      const featured = await mockApi.getFeaturedPlayers()
      featuredPlayers.value = featured
    }

    // Load database stats from real API
    try {
      console.log('Attempting to load database stats...')
      const dbStats = await systemApi.getDatabaseStats()
      console.log('Database stats response:', dbStats)
      databaseStats.value = dbStats
    } catch (apiError) {
      console.error('Database stats API error:', apiError)
      console.warn('Failed to load database stats, using fallback')
      // Fallback data if API fails
      databaseStats.value = {
        total_players: 1693,
        total_statcast_pitches: 493231,
        statcast_2025_records: 493097,
        fangraphs_2025_batting_players: 1322,
        timestamp: new Date().toISOString()
      }
    }

  } catch (err) {
    const errorInfo = handleError(err)
    error.value = errorInfo.message
    console.error('Failed to load dashboard data:', err)
  } finally {
    loading.value = false
  }
}

const formatDate = (dateString: string | undefined): string => {
  if (!dateString) return 'N/A'
  
  try {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    })
  } catch {
    return 'N/A'
  }
}

onMounted(() => {
  loadDashboardData()
})
</script>

<style lang="scss" scoped>
.dashboard {
  max-width: 1400px;
  margin: 0 auto;
  padding: $spacing-lg;
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.1) 0%, 
    rgba(255, 255, 255, 0.05) 100%);
  backdrop-filter: blur(20px);
  border-radius: $border-radius-xl;
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.1);

  &__section {
    margin-bottom: $spacing-2xl;
    position: relative;

    &:last-child {
      margin-bottom: 0;
    }

    // Add subtle section separators
    &:not(:last-child)::after {
      content: '';
      position: absolute;
      bottom: -#{$spacing-xl};
      left: 50%;
      transform: translateX(-50%);
      width: 60%;
      height: 1px;
      background: linear-gradient(90deg, 
        transparent 0%, 
        rgba(255, 255, 255, 0.1) 50%, 
        transparent 100%);
    }
  }
}

.featured-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: $spacing-xl;
  margin-bottom: $spacing-2xl;
  perspective: 1000px;

  // Removed staggered animation - too distracting
  > * {
    // No animation - static cards
  }

  @media (max-width: $breakpoint-tablet) {
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: $spacing-lg;
  }

  @media (max-width: $breakpoint-mobile) {
    grid-template-columns: 1fr;
    gap: $spacing-lg;
  }
}

.main-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: $spacing-xl;

  &__item {
    min-height: 450px;
    background: linear-gradient(145deg, 
      rgba(255, 255, 255, 0.1) 0%, 
      rgba(255, 255, 255, 0.05) 100%);
    backdrop-filter: blur(15px);
    border-radius: $border-radius-xl;
    border: 1px solid rgba(255, 255, 255, 0.15);
    box-shadow: 
      0 12px 40px rgba(0, 0, 0, 0.08),
      inset 0 1px 0 rgba(255, 255, 255, 0.2);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;

    // Subtle hover effect
    &:hover {
      transform: translateY(-4px);
      box-shadow: 
        0 20px 60px rgba(0, 0, 0, 0.12),
        inset 0 1px 0 rgba(255, 255, 255, 0.3);
      border-color: rgba(255, 255, 255, 0.2);
    }

    // Animated background pattern
    &::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: radial-gradient(circle at 80% 20%, rgba(255, 255, 255, 0.05) 0%, transparent 60%);
      pointer-events: none;
      z-index: 0;
    }

    // Ensure content is above background
    > * {
      position: relative;
      z-index: 1;
    }
  }

  @media (max-width: $breakpoint-tablet) {
    grid-template-columns: 1fr;
    gap: $spacing-lg;
  }
}

.stats-overview {
  padding: $spacing-xl;
  background: linear-gradient(145deg, 
    rgba(255, 255, 255, 0.15) 0%, 
    rgba(255, 255, 255, 0.05) 100%);
  backdrop-filter: blur(15px);
  border-radius: $border-radius-xl;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 
    0 12px 40px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.3),
    inset 0 -1px 0 rgba(0, 0, 0, 0.1);
  position: relative;
  overflow: hidden;

  // Subtle animated background pattern
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: radial-gradient(circle at 20% 80%, rgba(255, 255, 255, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, rgba(255, 255, 255, 0.05) 0%, transparent 50%);
    pointer-events: none;
    z-index: 0;
  }

  &__title {
    font-size: 1.5rem;
    font-weight: 800;
    color: $text-primary;
    margin: 0 0 $spacing-xl 0;
    text-align: center;
    position: relative;
    z-index: 1;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    
    // Add subtle underline effect
    &::after {
      content: '';
      position: absolute;
      bottom: -8px;
      left: 50%;
      transform: translateX(-50%);
      width: 60px;
      height: 3px;
      background: linear-gradient(90deg, $primary, $primary-light);
      border-radius: 2px;
      box-shadow: 0 2px 8px rgba($primary, 0.3);
    }
  }

  &__grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: $spacing-lg;
    position: relative;
    z-index: 1;
  }
}

.stat-item {
  text-align: center;
  padding: $spacing-lg;
  border-radius: $border-radius-lg;
  background: linear-gradient(145deg, 
    rgba(255, 255, 255, 0.25) 0%, 
    rgba(255, 255, 255, 0.1) 100%);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 
    0 8px 24px rgba(0, 0, 0, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.4);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;

  // Subtle shine effect
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, 
      transparent 0%, 
      rgba(255, 255, 255, 0.1) 50%, 
      transparent 100%);
    transition: left 0.5s ease;
    pointer-events: none;
  }

  &:hover {
    transform: translateY(-2px); // Reduced movement
    background: linear-gradient(145deg, 
      rgba(255, 255, 255, 0.35) 0%, 
      rgba(255, 255, 255, 0.15) 100%);
    box-shadow: 
      0 8px 20px rgba(0, 0, 0, 0.08), // Reduced shadow
      inset 0 1px 0 rgba(255, 255, 255, 0.5);
    border-color: rgba(255, 255, 255, 0.3);

    &::before {
      left: 100%;
    }
  }

  &:active {
    transform: translateY(-1px); // Minimal active state
  }
}

.stat-value {
  font-size: 1.75rem;
  font-weight: 800;
  background: linear-gradient(135deg, $primary 0%, $primary-light 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: $spacing-sm;
  font-family: $font-mono;
  text-shadow: 0 2px 4px rgba($primary, 0.2);
  line-height: 1.2;
  position: relative;
  
  // Add subtle glow effect
  &::after {
    content: attr(data-value);
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    color: $primary;
    opacity: 0.3;
    filter: blur(8px);
    z-index: -1;
  }
}

.stat-label {
  font-size: 0.8rem;
  color: $text-secondary;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
  opacity: 0.8;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

// Loading and error states
.loading-spinner {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
  color: $text-muted;
}

.error-message {
  background-color: rgba($danger, 0.1);
  color: $danger;
  padding: $spacing-md;
  border-radius: $border-radius-md;
  text-align: center;
  margin-bottom: $spacing-lg;
}

// Removed slide-up and shimmer animations - too distracting

@keyframes shimmer {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}

// Removed float animation - too distracting

// Removed floating animation - too distracting
.dashboard__section {
  // No animation - static sections
}

// Hover effects for better interactivity
.card {
  transition: box-shadow 0.2s ease; // Only shadow transition
  
  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); // Subtle shadow only
  }
}

// Responsive adjustments with enhanced styling
@media (max-width: $breakpoint-mobile) {
  .dashboard {
    padding: $spacing-md;
    border-radius: $border-radius-lg;
    
    &__section {
      margin-bottom: $spacing-xl;
    }
  }

  .stats-overview {
    padding: $spacing-lg;

    &__title {
      font-size: 1.25rem;
    }

    &__grid {
      grid-template-columns: repeat(2, 1fr);
      gap: $spacing-md;
    }
  }

  .stat-item {
    padding: $spacing-md;
  }

  .stat-value {
    font-size: 1.4rem;
  }

  .stat-label {
    font-size: 0.75rem;
  }

  .main-grid__item {
    min-height: 350px;
  }
}
</style>