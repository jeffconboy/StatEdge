<template>
  <Layout>
    <div class="hr-betting">
      <!-- Page Header -->
      <div class="hr-betting__header">
        <h1 class="page-title">Home Run Betting Research</h1>
        <p class="page-subtitle">Advanced analytics to help you make informed HR betting decisions</p>
      </div>

      <!-- Player Search Section -->
      <div class="search-section">
        <div class="search-container">
          <div class="search-input-wrapper">
            <input
              v-model="searchQuery"
              @input="handleSearch"
              type="text"
              placeholder="Search for a player (e.g., Kyle Stowers, Aaron Judge)"
              class="search-input"
            />
            <div v-if="searching" class="search-spinner">
              <div class="spinner"></div>
            </div>
          </div>
          
          <!-- Search Results -->
          <div v-if="searchResults.length > 0" class="search-results">
            <div
              v-for="player in searchResults"
              :key="player.id"
              @click="selectPlayer(player)"
              class="search-result-item"
            >
              <div class="player-info">
                <div class="player-name">{{ player.name }}</div>
                <div class="player-details">{{ player.team }} • {{ player.position }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Selected Player Analysis -->
      <div v-if="selectedPlayer" class="player-analysis">
        <!-- Player Header -->
        <div class="player-header">
          <div class="player-basic-info">
            <h2 class="player-name">{{ selectedPlayer.name }}</h2>
            <div class="player-meta">
              <span class="team">{{ selectedPlayer.team }}</span>
              <span class="position">{{ selectedPlayer.position }}</span>
            </div>
          </div>
          <div class="today-matchup" v-if="todaysGame">
            <div class="matchup-label">Today's Game</div>
            <div class="matchup-details">{{ todaysGame }}</div>
          </div>
        </div>

        <!-- HR Stats Analysis -->
        <HRStatsCard
          :stats="hrStats"
          :ballpark="ballparkFactors"
          :matchup="matchupData"
          :prediction="aiPrediction"
          :confidence="predictionConfidence"
        />

        <!-- Recent Performance Chart -->
        <div class="performance-section">
          <h3 class="section-title">Recent HR Performance</h3>
          <div class="performance-chart">
            <div v-if="recentGames.length === 0" class="no-data">
              Loading recent performance data...
            </div>
            <div v-else class="games-list">
              <div
                v-for="game in recentGames"
                :key="game.date"
                class="game-item"
              >
                <div class="game-date">{{ formatDate(game.date) }}</div>
                <div class="game-opponent">vs {{ game.opponent }}</div>
                <div class="game-result" :class="{ 'has-hr': game.homeRuns > 0 }">
                  {{ game.homeRuns }} HR
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Quick Access Players -->
      <div v-if="!selectedPlayer" class="quick-access">
        <h3 class="section-title">Popular HR Bets Today</h3>
        <div class="popular-players">
          <div
            v-for="player in popularPlayers"
            :key="player.id"
            @click="quickSelectPlayer(player)"
            class="popular-player-card"
          >
            <div class="player-name">{{ player.name }}</div>
            <div class="player-team">{{ player.team }}</div>
            <div class="hr-probability">{{ player.hrProbability }}% HR chance</div>
          </div>
        </div>
      </div>
    </div>
  </Layout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import Layout from '@/components/Layout.vue'
import HRStatsCard from '@/components/HRStatsCard.vue'
import { playerApi } from '@/services/api'

// Reactive data
const searchQuery = ref('')
const searching = ref(false)
const searchResults = ref<any[]>([])
const selectedPlayer = ref<any>(null)
const todaysGame = ref<string>('')
const recentGames = ref<any[]>([])

// Mock data for HR analysis
const hrStats = ref({
  avgExitVelo: 94.2,
  maxExitVelo: 112.8,
  hardHitPercent: 42.3,
  barrelPercent: 12.8,
  hrLast15: 4,
  hrVsPitcherType: '2 vs RHP, 2 vs LHP',
  homeAwayHR: '3 Home, 1 Away',
  dayNightHR: '2 Day, 2 Night'
})

const ballparkFactors = ref({
  hrFactor: 1.15,
  wind: '8 mph out to RF'
})

const matchupData = ref({
  vsPitcher: '2-7, 1 HR in 9 AB',
  pitcherHR9: 1.8
})

const aiPrediction = ref({
  outcome: 'HR Likely (68% chance)',
  reasoning: 'Strong exit velocity metrics, favorable ballpark conditions, and positive matchup history suggest above-average HR probability tonight.'
})

const predictionConfidence = ref(68)

const popularPlayers = ref([
  { id: 1, name: 'Aaron Judge', team: 'NYY', hrProbability: 25 },
  { id: 2, name: 'Kyle Stowers', team: 'BAL', hrProbability: 18 },
  { id: 3, name: 'Ronald Acuña Jr.', team: 'ATL', hrProbability: 22 },
  { id: 4, name: 'Mike Trout', team: 'LAA', hrProbability: 20 }
])

// Search functionality
let searchTimeout: NodeJS.Timeout

const handleSearch = () => {
  if (searchTimeout) clearTimeout(searchTimeout)
  
  if (searchQuery.value.length < 2) {
    searchResults.value = []
    return
  }

  searching.value = true
  
  searchTimeout = setTimeout(async () => {
    try {
      const response = await playerApi.search({
        query: searchQuery.value,
        limit: 10
      })
      
      searchResults.value = response.players || []
    } catch (error) {
      console.error('Search error:', error)
      searchResults.value = []
    } finally {
      searching.value = false
    }
  }, 300)
}

const selectPlayer = async (player: any) => {
  selectedPlayer.value = player
  searchResults.value = []
  searchQuery.value = player.name
  
  // Load player stats and generate mock data
  await loadPlayerAnalysis(player)
}

const quickSelectPlayer = async (player: any) => {
  // Convert popular player to full player object
  const fullPlayer = {
    id: player.id,
    name: player.name,
    team: player.team,
    position: 'OF'
  }
  await selectPlayer(fullPlayer)
}

const loadPlayerAnalysis = async (player: any) => {
  try {
    // Generate mock today's matchup
    const opponents = ['BOS', 'NYY', 'LAA', 'HOU', 'LAD', 'SF', 'ATL', 'PHI']
    const randomOpponent = opponents[Math.floor(Math.random() * opponents.length)]
    todaysGame.value = `vs ${randomOpponent} - 7:05 PM`
    
    // Generate mock recent games
    recentGames.value = Array.from({ length: 15 }, (_, i) => ({
      date: new Date(Date.now() - (i + 1) * 24 * 60 * 60 * 1000).toISOString(),
      opponent: opponents[Math.floor(Math.random() * opponents.length)],
      homeRuns: Math.random() > 0.75 ? 1 : Math.random() > 0.95 ? 2 : 0
    }))
    
    // Randomize stats slightly for different players
    const baseStats = {
      avgExitVelo: 90 + Math.random() * 10,
      maxExitVelo: 105 + Math.random() * 15,
      hardHitPercent: 30 + Math.random() * 25,
      barrelPercent: 8 + Math.random() * 12,
      hrLast15: Math.floor(Math.random() * 8),
      hrVsPitcherType: '1 vs RHP, 2 vs LHP',
      homeAwayHR: '2 Home, 1 Away', 
      dayNightHR: '1 Day, 2 Night'
    }
    
    hrStats.value = baseStats
    predictionConfidence.value = Math.floor(50 + Math.random() * 40)
    
    const outcomes = [
      'HR Likely (75% chance)',
      'HR Possible (55% chance)', 
      'HR Unlikely (35% chance)',
      'HR Very Likely (85% chance)'
    ]
    
    aiPrediction.value = {
      outcome: outcomes[Math.floor(Math.random() * outcomes.length)],
      reasoning: 'Analysis based on exit velocity trends, ballpark factors, pitcher matchup history, and weather conditions.'
    }
    
  } catch (error) {
    console.error('Error loading player analysis:', error)
  }
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { 
    month: 'short', 
    day: 'numeric' 
  })
}

onMounted(() => {
  // Component initialization
})
</script>

<style lang="scss" scoped>
.hr-betting {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
  color: white;

  &__header {
    text-align: center;
    margin-bottom: 40px;
  }
}

.page-title {
  font-size: 2.5rem;
  font-weight: 700;
  margin: 0 0 12px 0;
  background: linear-gradient(135deg, #48bb78, #38a169);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.page-subtitle {
  font-size: 1.125rem;
  color: #a0aec0;
  margin: 0;
}

.search-section {
  margin-bottom: 40px;
}

.search-container {
  max-width: 600px;
  margin: 0 auto;
  position: relative;
}

.search-input-wrapper {
  position: relative;
}

.search-input {
  width: 100%;
  padding: 16px 20px;
  font-size: 1.125rem;
  background: rgba(255, 255, 255, 0.05);
  border: 2px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  color: white;
  transition: all 0.3s ease;

  &:focus {
    outline: none;
    border-color: #48bb78;
    box-shadow: 0 0 0 3px rgba(72, 187, 120, 0.1);
  }

  &::placeholder {
    color: #a0aec0;
  }
}

.search-spinner {
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid #48bb78;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.search-results {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: #2d3748;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  margin-top: 4px;
  max-height: 300px;
  overflow-y: auto;
  z-index: 1000;
}

.search-result-item {
  padding: 12px 16px;
  cursor: pointer;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  transition: background-color 0.2s ease;

  &:hover {
    background: rgba(255, 255, 255, 0.05);
  }

  &:last-child {
    border-bottom: none;
  }
}

.player-info {
  .player-name {
    font-weight: 600;
    margin-bottom: 4px;
  }

  .player-details {
    font-size: 0.875rem;
    color: #a0aec0;
  }
}

.player-analysis {
  margin-bottom: 40px;
}

.player-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.player-basic-info {
  .player-name {
    font-size: 2rem;
    font-weight: 700;
    margin: 0 0 8px 0;
  }

  .player-meta {
    display: flex;
    gap: 16px;
    font-size: 1rem;
    color: #a0aec0;

    .team, .position {
      font-weight: 600;
    }
  }
}

.today-matchup {
  text-align: right;

  .matchup-label {
    font-size: 0.875rem;
    color: #a0aec0;
    margin-bottom: 4px;
  }

  .matchup-details {
    font-size: 1.125rem;
    font-weight: 600;
    color: #48bb78;
  }
}

.performance-section {
  margin-top: 24px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.section-title {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0 0 16px 0;
  color: #f7fafc;
}

.performance-chart {
  .no-data {
    text-align: center;
    color: #a0aec0;
    padding: 40px;
    font-style: italic;
  }
}

.games-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 8px;
}

.game-item {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  padding: 12px;
  text-align: center;
  border: 1px solid rgba(255, 255, 255, 0.08);

  .game-date {
    font-size: 0.75rem;
    color: #a0aec0;
    margin-bottom: 4px;
  }

  .game-opponent {
    font-size: 0.875rem;
    font-weight: 600;
    margin-bottom: 4px;
  }

  .game-result {
    font-size: 0.875rem;
    font-weight: 600;
    color: #cbd5e0;

    &.has-hr {
      color: #48bb78;
    }
  }
}

.quick-access {
  .popular-players {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 16px;
  }
}

.popular-player-card {
  background: linear-gradient(135deg, rgba(72, 187, 120, 0.1) 0%, rgba(56, 161, 105, 0.1) 100%);
  border: 1px solid rgba(72, 187, 120, 0.2);
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 25px rgba(72, 187, 120, 0.15);
  }

  .player-name {
    font-size: 1.125rem;
    font-weight: 700;
    margin-bottom: 4px;
  }

  .player-team {
    font-size: 0.875rem;
    color: #a0aec0;
    margin-bottom: 8px;
  }

  .hr-probability {
    font-size: 1rem;
    font-weight: 600;
    color: #48bb78;
  }
}

@media (max-width: 768px) {
  .player-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .today-matchup {
    text-align: left;
  }

  .games-list {
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  }
}
</style>