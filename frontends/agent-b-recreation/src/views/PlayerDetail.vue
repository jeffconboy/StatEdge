<template>
  <div class="player-detail">
    <div v-if="loading" class="loading-container">
      <div class="loading-spinner">Loading player data...</div>
    </div>

    <div v-else-if="error" class="error-container">
      <div class="error-message">{{ error }}</div>
      <button @click="$router.go(-1)" class="btn btn-secondary">Go Back</button>
    </div>

    <div v-else-if="playerData" class="player-content">
      <!-- Header -->
      <div class="player-header">
        <button @click="$router.go(-1)" class="back-button">
          ← Back to Dashboard
        </button>
        
        <div class="player-info">
          <!-- AI Portrait -->
          <div class="player-portrait">
            <img 
              v-if="playerData.player_info.ai_portrait_url" 
              :src="playerData.player_info.ai_portrait_url" 
              :alt="playerData.player_info.name"
              class="ai-portrait"
            />
            <div v-else class="portrait-placeholder">
              <span class="placeholder-text">{{ playerData.player_info.name.charAt(0) }}</span>
            </div>
          </div>
          
          <div class="player-details">
            <h1 class="player-name">{{ playerData.player_info.name }}</h1>
            <div class="player-meta">
              <span class="team">{{ playerData.player_info.team }}</span>
              <span class="position">{{ playerData.player_info.position }}</span>
            </div>
          </div>
          
          <!-- AI Betting Analysis Section -->
          <div class="ai-section">
            <button 
              @click="showAIChat = !showAIChat"
              class="btn btn-primary ai-toggle-btn"
              :class="{ active: showAIChat }"
            >
              🤖 AI Betting Analysis
            </button>
            
            <div v-if="showAIChat" class="ai-chat-container">
              <!-- Quick Betting Questions -->
              <div class="quick-questions">
                <h5>Popular Betting Questions:</h5>
                <div class="question-buttons">
                  <button 
                    @click="aiQuestion = 'Should I bet on his home run prop tonight?'"
                    class="quick-question-btn"
                  >
                    Home Run Prop
                  </button>
                  <button 
                    @click="aiQuestion = 'Analyze his total bases prop for tonight'"
                    class="quick-question-btn"
                  >
                    Total Bases
                  </button>
                  <button 
                    @click="aiQuestion = 'Should I bet over or under on his RBI prop?'"
                    class="quick-question-btn"
                  >
                    RBI Prop
                  </button>
                  <button 
                    @click="aiQuestion = 'Analyze his recent hitting trends for betting'"
                    class="quick-question-btn"
                  >
                    Hitting Trends
                  </button>
                </div>
              </div>
              
              <div class="ai-input-section">
                <textarea
                  v-model="aiQuestion"
                  placeholder="Ask about betting props... e.g., 'Should I bet on his home run prop tonight?' or 'Analyze his recent hitting trends'"
                  class="ai-input"
                  rows="3"
                ></textarea>
                <button 
                  @click="getAIAnalysis"
                  :disabled="!aiQuestion.trim() || aiLoading"
                  class="btn btn-secondary ai-ask-btn"
                >
                  {{ aiLoading ? 'Analyzing...' : 'Get AI Analysis' }}
                </button>
              </div>
              
              <div v-if="aiResponse" class="ai-response">
                <div class="analysis-header">
                  <h4>🎯 Professional Betting Analysis</h4>
                  <div class="data-badge" :class="{ loading: leagueLoading, error: leagueError }">
                    <span v-if="leagueLoading">🔄 Loading League Data...</span>
                    <span v-else-if="leagueError" :title="leagueError">⚠️ Using Fallback Data</span>
                    <span v-else-if="leagueAverages.data_source === 'cached'" :title="cacheTimeRemaining">📊 493k+ Records (Cached)</span>
                    <span v-else>📊 493k+ Real Statcast Records (Live)</span>
                    <button 
                      v-if="leagueAverages.data_source === 'cached'" 
                      @click="refreshLeagueData"
                      class="refresh-btn"
                      title="Refresh league data"
                    >
                      🔄
                    </button>
                  </div>
                </div>
                
                <div class="ai-content">
                  <!-- Main Recommendation -->
                  <div v-if="extractRecommendation(aiResponse.explanation)" class="recommendation-box">
                    <div class="rec-header">
                      <span class="rec-label">Recommendation:</span>
                      <span class="rec-value" :class="getRecommendationClass(aiResponse.explanation)">
                        {{ extractRecommendation(aiResponse.explanation) }}
                      </span>
                    </div>
                  </div>
                  
                  <!-- Confidence Level -->
                  <div v-if="extractConfidence(aiResponse.explanation)" class="confidence-section">
                    <div class="confidence-header">
                      <span class="conf-label">Confidence Level:</span>
                      <span class="conf-value" :class="getConfidenceClass(aiResponse.explanation)">
                        {{ extractConfidence(aiResponse.explanation) }}
                      </span>
                    </div>
                    <div class="confidence-bar">
                      <div class="conf-fill" :style="{ width: getConfidenceWidth(aiResponse.explanation) }"></div>
                    </div>
                  </div>
                  
                  <!-- Enhanced Analysis Content -->
                  <div class="analysis-content-enhanced">
                    <div v-for="section in formatAnalysisIntoSections(aiResponse.explanation)" 
                         :key="section.title" 
                         class="analysis-section">
                      <div class="section-header">
                        <span class="section-icon">{{ section.icon }}</span>
                        <h4 class="section-title">{{ section.title }}</h4>
                      </div>
                      <div class="section-content">
                        <p v-if="section.type === 'text'" class="section-text">{{ section.content }}</p>
                        <ul v-else-if="section.type === 'list'" class="section-list">
                          <li v-for="item in section.items" :key="item" class="list-item">
                            <span class="bullet">•</span>
                            <span class="item-text">{{ item }}</span>
                          </li>
                        </ul>
                      </div>
                    </div>
                  </div>
                  
                  <!-- Player Context Summary -->
                  <div class="context-summary">
                    <h5>📊 Key Metrics Summary</h5>
                    <div class="metrics-grid">
                      <div class="metric-item">
                        <span class="metric-label">Exit Velocity</span>
                        <span class="metric-value">{{ avgExitVelo.toFixed(1) }} mph</span>
                        <span class="metric-rank" :class="{ elite: avgExitVelo > 90 }">
                          {{ avgExitVelo > 95 ? 'Elite' : avgExitVelo > 90 ? 'Above Avg' : 'Average' }}
                        </span>
                      </div>
                      <div class="metric-item">
                        <span class="metric-label">Hard Hit Rate</span>
                        <span class="metric-value">{{ hardHitRate.toFixed(1) }}%</span>
                        <span class="metric-rank" :class="{ elite: hardHitRate > 40 }">
                          {{ hardHitRate > 45 ? '90th+ %ile' : hardHitRate > 40 ? '75th+ %ile' : 'Below Avg' }}
                        </span>
                      </div>
                      <div class="metric-item">
                        <span class="metric-label">Sample Size</span>
                        <span class="metric-value">{{ validStatcastPitches.length }}</span>
                        <span class="metric-rank" :class="{ elite: validStatcastPitches.length > 50 }">
                          {{ validStatcastPitches.length > 50 ? 'Reliable' : validStatcastPitches.length > 30 ? 'Good' : 'Limited' }}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <!-- Disclaimer -->
                  <div class="betting-disclaimer">
                    ⚠️ <strong>Disclaimer:</strong> This analysis is for informational purposes only. Betting involves risk and should be done responsibly.
                  </div>
                </div>
              </div>
              
              <div v-if="aiError" class="ai-error">
                {{ aiError }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Stats Section -->
      <div class="stats-section">
        <div class="stats-grid">
          <!-- Batting Stats -->
          <div v-if="battingStats" class="stat-category">
            <h3>2025 Batting Stats</h3>
            <div class="stat-items">
              <div class="stat-item">
                <div class="stat-label">AVG</div>
                <div class="stat-value">{{ formatStat(battingStats.AVG) }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">HR</div>
                <div class="stat-value">{{ battingStats.HR || 0 }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">RBI</div>
                <div class="stat-value">{{ battingStats.RBI || 0 }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">OPS</div>
                <div class="stat-value">{{ formatStat(battingStats.OPS) }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">wRC+</div>
                <div class="stat-value">{{ Math.round(battingStats.wRC_plus) || 'N/A' }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">WAR</div>
                <div class="stat-value">{{ formatStat(battingStats.WAR) }}</div>
              </div>
            </div>
          </div>

          <!-- Statcast Data -->
          <div v-if="statcastData" class="stat-category">
            <h3>Statcast Metrics</h3>
            <div class="stat-items">
              <div class="stat-item">
                <div class="stat-label">Exit Velocity</div>
                <div class="stat-value">{{ avgExitVelo.toFixed(1) }} mph</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">Launch Angle</div>
                <div class="stat-value">{{ avgLaunchAngle.toFixed(1) }}°</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">Hard Hit %</div>
                <div class="stat-value">{{ hardHitRate.toFixed(1) }}%</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">Barrels</div>
                <div class="stat-value">{{ barrelCount }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Recent Activity -->
        <div v-if="recentGames.length" class="recent-activity">
          <h3>Recent Games</h3>
          <div class="games-list">
            <div v-for="game in recentGames" :key="game.date" class="game-item">
              <div class="game-date">{{ formatDate(game.date) }}</div>
              <div class="game-stats">{{ game.stats }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { playerApi, useApiError } from '@/services/api'

const route = useRoute()
const { handleError } = useApiError()

const playerData = ref(null)
const loading = ref(true)
const error = ref('')

// AI Analysis state
const showAIChat = ref(false)
const aiQuestion = ref('')
const aiResponse = ref(null)
const aiLoading = ref(false)
const aiError = ref('')

const playerId = computed(() => route.params.id as string)

// Computed stats
const battingStats = computed(() => {
  if (!playerData.value?.fangraphs_batting?.length) return null
  
  // Find 2025 season data, fallback to most recent
  const season2025 = playerData.value.fangraphs_batting.find(stat => stat.Season === 2025)
  return season2025 || playerData.value.fangraphs_batting[0]
})

const statcastData = computed(() => {
  return playerData.value?.statcast_summary || []
})

// Optimized Statcast filtering with memoization
const validStatcastPitches = computed(() => {
  if (!statcastData.value.length) return []
  
  // More efficient filtering - check multiple conditions at once
  return statcastData.value.filter(pitch => {
    const data = pitch.data || pitch
    return data.launch_speed && 
           typeof data.launch_speed === 'number' && 
           data.launch_speed > 0 &&
           data.launch_speed < 130 // Exclude outliers
  })
})

const avgExitVelo = computed(() => {
  if (!validStatcastPitches.value.length) return 0
  const total = validStatcastPitches.value.reduce((sum, pitch) => {
    const data = pitch.data || pitch
    return sum + (data.launch_speed || 0)
  }, 0)
  return total / validStatcastPitches.value.length
})

// League averages data with caching
const leagueAverages = ref({
  hard_hit_rate: 38.0,
  avg_exit_velocity: 88.5,
  barrel_rate: 6.8,
  data_source: 'loading'
})

const leagueLoading = ref(false)
const leagueError = ref('')

const CACHE_KEY = 'statEdge_leagueAverages'
const CACHE_DURATION = 60 * 60 * 1000 // 1 hour in milliseconds

const refreshLeagueData = async () => {
  localStorage.removeItem(CACHE_KEY)
  await fetchLeagueAverages()
}

const cacheTimeRemaining = computed(() => {
  try {
    const cached = localStorage.getItem(CACHE_KEY)
    if (!cached) return 'No cache'
    
    const { timestamp } = JSON.parse(cached)
    const remaining = Math.round((CACHE_DURATION - (Date.now() - timestamp)) / 60000)
    return `Cached ${remaining} min remaining`
  } catch (e) {
    return 'Cache invalid'
  }
})

const fetchLeagueAverages = async (retryCount = 0) => {
  // Check cache first
  const cached = localStorage.getItem(CACHE_KEY)
  if (cached) {
    try {
      const { data, timestamp } = JSON.parse(cached)
      const now = Date.now()
      
      // Use cached data if less than 1 hour old
      if (now - timestamp < CACHE_DURATION) {
        leagueAverages.value = { ...data, data_source: 'cached' }
        console.log('League averages loaded from cache:', data)
        return
      }
    } catch (e) {
      console.warn('Invalid cache data, fetching fresh:', e)
      localStorage.removeItem(CACHE_KEY) // Clear corrupt cache
    }
  }

  // Prevent concurrent requests
  if (leagueLoading.value) {
    console.log('League averages already loading, skipping request')
    return
  }

  // Fetch fresh data with retry logic
  leagueLoading.value = true
  leagueError.value = ''
  
  try {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 10000) // 10s timeout
    
    const response = await fetch('http://localhost:18000/api/league/hard-hit-average', {
      signal: controller.signal,
      headers: {
        'Cache-Control': 'no-cache'
      }
    })
    
    clearTimeout(timeoutId)
    
    if (response.ok) {
      const data = await response.json()
      
      // Validate response data
      if (data && typeof data.hard_hit_rate === 'number' && data.hard_hit_rate > 0) {
        leagueAverages.value = data
        
        // Cache the fresh data
        localStorage.setItem(CACHE_KEY, JSON.stringify({
          data,
          timestamp: Date.now()
        }))
        
        console.log('League averages loaded fresh:', data)
      } else {
        throw new Error('Invalid response data format')
      }
    } else if (response.status >= 500 && retryCount < 2) {
      // Retry on server errors
      console.warn(`Server error ${response.status}, retrying...`)
      setTimeout(() => fetchLeagueAverages(retryCount + 1), 1000 * (retryCount + 1))
      return
    } else {
      throw new Error(`API error: ${response.status}`)
    }
  } catch (error) {
    console.error('Failed to load league averages:', error)
    
    if (error.name === 'AbortError') {
      leagueError.value = 'Request timeout - using cached data'
    } else if (retryCount < 2) {
      console.warn('Retrying league averages request...')
      setTimeout(() => fetchLeagueAverages(retryCount + 1), 2000)
      return
    } else {
      leagueError.value = 'Failed to load league data - using estimates'
    }
    
    // Graceful degradation - keep using fallback values
  } finally {
    leagueLoading.value = false
  }
}

const avgLaunchAngle = computed(() => {
  if (!validStatcastPitches.value.length) return 0
  const total = validStatcastPitches.value.reduce((sum, pitch) => {
    const data = pitch.data || pitch
    return sum + (data.launch_angle || 0)
  }, 0)
  return total / validStatcastPitches.value.length
})

const hardHitRate = computed(() => {
  if (!validStatcastPitches.value.length) return 0
  const hardHits = validStatcastPitches.value.filter(pitch => {
    const data = pitch.data || pitch
    return data.launch_speed >= 95
  }).length
  return (hardHits / validStatcastPitches.value.length) * 100
})

const barrelCount = computed(() => {
  if (!validStatcastPitches.value.length) return 0
  return validStatcastPitches.value.filter(pitch => {
    const data = pitch.data || pitch
    return data.launch_speed >= 98 && 
           data.launch_angle >= 26 && 
           data.launch_angle <= 30
  }).length
})

// Barrel rate calculations
const barrelRate = computed(() => {
  if (!validStatcastPitches.value.length) return 0
  return Math.round((barrelCount.value / validStatcastPitches.value.length) * 1000) / 10
})

const barrelPerPA = computed(() => {
  const totalPA = battingStats.value?.PA || 1
  return Math.round((barrelCount.value / totalPA) * 1000) / 10
})

// FanGraphs barrel data for comparison
const fangraphsBarrels = computed(() => {
  if (!battingStats.value) return null
  return {
    barrel_count: battingStats.value.Barrels || 0,
    barrel_percentage: battingStats.value['Barrel%'] || 0,
    plate_appearances: battingStats.value.PA || 0
  }
})

const recentGames = computed(() => {
  if (!statcastData.value.length) return []
  
  // Group by game date and create summary
  const gameMap = new Map()
  statcastData.value.forEach(pitch => {
    if (!pitch.game_date) return
    
    const date = pitch.game_date.split('T')[0]
    if (!gameMap.has(date)) {
      gameMap.set(date, { date, pitches: [] })
    }
    gameMap.get(date).pitches.push(pitch)
  })
  
  return Array.from(gameMap.values())
    .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
    .slice(0, 5)
    .map(game => ({
      date: game.date,
      stats: `${game.pitches.length} tracked pitches`
    }))
})

const loadPlayerData = async (retryCount = 0) => {
  try {
    loading.value = true
    error.value = ''
    
    console.log(`Loading player data for ID: ${playerId.value}`)
    
    // Add timeout to player API call
    const timeoutPromise = new Promise((_, reject) =>
      setTimeout(() => reject(new Error('Request timeout')), 15000)
    )
    
    const response = await Promise.race([
      playerApi.getSummary(playerId.value),
      timeoutPromise
    ])
    
    // Validate response data
    if (!response || (!response.data && !response.player_info)) {
      throw new Error('Invalid player data received')
    }
    
    playerData.value = response.data || response
    console.log('Player data loaded successfully:', playerData.value.player_info?.name)
    
  } catch (err) {
    console.error('Failed to load player data:', err)
    
    if (err.message === 'Request timeout' && retryCount < 1) {
      console.warn('Player data request timed out, retrying...')
      setTimeout(() => loadPlayerData(retryCount + 1), 2000)
      return
    }
    
    const errorInfo = handleError(err)
    error.value = errorInfo.message || 'Failed to load player data. Please try again.'
  } finally {
    loading.value = false
  }
}

const getAIAnalysis = async () => {
  if (!aiQuestion.value.trim() || !playerData.value) return
  
  try {
    aiLoading.value = true
    aiError.value = ''
    aiResponse.value = null
    
    console.log('Starting AI analysis...')
    
    // Prepare comprehensive context with real Statcast data
    const playerContext = {
      player_name: playerData.value.player_info.name,
      team: playerData.value.player_info.team,
      position: playerData.value.player_info.position,
      season: '2025',
      
      // 2025 FanGraphs Stats
      batting_stats_2025: battingStats.value ? {
        games: battingStats.value.G,
        avg: battingStats.value.AVG,
        obp: battingStats.value.OBP,
        slg: battingStats.value.SLG,
        ops: battingStats.value.OPS,
        home_runs: battingStats.value.HR,
        rbi: battingStats.value.RBI,
        runs: battingStats.value.R,
        stolen_bases: battingStats.value.SB,
        wrc_plus: battingStats.value.wRC_plus,
        war: battingStats.value.WAR,
        babip: battingStats.value.BABIP,
        iso: battingStats.value.ISO
      } : null,
      
      // Live Statcast Metrics
      statcast_metrics: {
        avg_exit_velocity: Math.round(avgExitVelo.value * 10) / 10,
        avg_launch_angle: Math.round(avgLaunchAngle.value * 10) / 10,
        hard_hit_rate: Math.round(hardHitRate.value * 10) / 10,
        barrel_count: barrelCount.value,
        barrel_rate: barrelRate.value,
        barrel_per_pa: barrelPerPA.value,
        total_tracked_balls: validStatcastPitches.value.length,
        sample_size: validStatcastPitches.value.length,
        recent_games_tracked: recentGames.value.length,
        
        // League Comparisons
        hard_hit_above_average: hardHitRate.value > leagueAverages.value.hard_hit_rate,
        barrel_above_average: barrelRate.value > leagueAverages.value.barrel_rate,
        exit_velo_above_average: avgExitVelo.value > leagueAverages.value.avg_exit_velocity,
        exit_velo_elite: avgExitVelo.value > 90, // Elite threshold
        barrel_elite: barrelRate.value > 25, // Elite barrel rate threshold
        
        // Contact Quality Zones
        sweet_spot_contact: validStatcastPitches.value.filter(p => {
          const data = p.data || p
          return data.launch_angle >= 8 && data.launch_angle <= 32
        }).length,
        weak_contact: validStatcastPitches.value.filter(p => {
          const data = p.data || p
          return data.launch_speed < 85
        }).length,
        
        // Recent actual at-bats with outcomes (summarized for AI)
        recent_statcast_samples: validStatcastPitches.value.slice(-5).map(pitch => {
          const data = pitch.data || pitch
          return {
            date: data.game_date?.split('T')[0], // Just date, not full timestamp
            exit_velocity: Math.round(data.launch_speed * 10) / 10,
            launch_angle: Math.round(data.launch_angle * 10) / 10,
            outcome: data.description || data.type || 'contact',
            is_barrel: data.launch_speed > 98 && data.launch_angle >= 26 && data.launch_angle <= 30,
            is_hard_hit: data.launch_speed > 95
          }
        }),
        
        // Performance metadata
        data_freshness: {
          league_data_age: leagueAverages.value.data_source === 'cached' ? 'cached' : 'live',
          sample_reliability: validStatcastPitches.value.length > 50 ? 'high' : 
                             validStatcastPitches.value.length > 20 ? 'medium' : 'low',
          last_updated: new Date().toISOString()
        }
      },
      
      // Advanced performance analysis
      performance_analysis: {
        // Recent vs Season comparison
        contact_quality_trend: {
          current_hard_hit_rate: Math.round(hardHitRate.value * 10) / 10,
          league_average_hard_hit: calculateLeagueAverageHardHit(),
          league_sample_size: playerData.value?.statcast_summary?.length || 0,
          percentile_rank: hardHitRate.value > 45 ? '90th+' : hardHitRate.value > 40 ? '75th+' : hardHitRate.value > 35 ? '50th+' : 'Below avg',
          trending: hardHitRate.value > 40 ? 'hot' : hardHitRate.value < 30 ? 'cold' : 'average'
        },
        
        exit_velocity_analysis: {
          current_avg: Math.round(avgExitVelo.value * 10) / 10,
          elite_threshold: 95.0,
          above_average_threshold: 90.0,
          status: avgExitVelo.value >= 95 ? 'elite' : avgExitVelo.value >= 90 ? 'above_average' : 'average',
          contact_consistency: validStatcastPitches.value.length > 50 ? 'reliable_sample' : 'small_sample'
        },
        
        power_indicators: {
          barrel_rate: barrelRate.value,
          barrel_per_pa: barrelPerPA.value,
          sweet_spot_percentage: validStatcastPitches.value.length > 0 ?
            Math.round((validStatcastPitches.value.filter(p => p.launch_angle >= 8 && p.launch_angle <= 32).length / validStatcastPitches.value.length) * 1000) / 10 : 0,
          power_potential: avgExitVelo.value > 92 && avgLaunchAngle.value > 10 ? 'high' : 'moderate'
        },
        
        // Barrel Analysis with League Context  
        barrel_analysis: {
          statcast_barrels: barrelCount.value,
          statcast_barrel_rate: barrelRate.value,
          fangraphs_barrels: fangraphsBarrels.value?.barrel_count || 0,
          fangraphs_barrel_rate: fangraphsBarrels.value?.barrel_percentage * 100 || 0,
          league_barrel_rate: leagueAverages.value.barrel_rate,
          above_league_average: barrelRate.value > leagueAverages.value.barrel_rate,
          elite_barrel_tier: barrelRate.value > 25,
          barrel_context: barrelRate.value > 25 ? 'elite' : 
                          barrelRate.value > leagueAverages.value.barrel_rate ? 'above_average' : 'below_average'
        },
        
        recent_form: {
          last_5_games: recentGames.value.slice(0, 5).map(game => ({
            date: game.date,
            tracked_pitches: game.stats || 'No data',
            // Calculate actual stats from Statcast data for this date
            game_statcast_data: validStatcastPitches.value.filter(p => 
              p.game_date && p.game_date.startsWith(game.date)
            ),
          })).map(game => {
            const dayPitches = game.game_statcast_data
            return {
              date: game.date,
              tracked_pitches: game.tracked_pitches,
              contact_events: dayPitches.length,
              avg_exit_velo: dayPitches.length > 0 ? 
                Math.round((dayPitches.reduce((sum, p) => sum + (p.launch_speed || 0), 0) / dayPitches.length) * 10) / 10 : 0,
              hard_hit_balls: dayPitches.filter(p => p.launch_speed > 95).length,
              barrels: dayPitches.filter(p => p.launch_speed > 98 && p.launch_angle >= 26 && p.launch_angle <= 30).length,
              has_power_contact: dayPitches.some(p => p.launch_speed > 100)
            }
          }),
          sample_reliability: validStatcastPitches.value.length > 30 ? 'good' : validStatcastPitches.value.length > 15 ? 'fair' : 'limited',
          data_recency: recentGames.value.length > 0 ? 'current_season' : 'limited_data',
          recent_power_trend: validStatcastPitches.value.slice(-20).filter(p => p.launch_speed > 95).length / Math.min(20, validStatcastPitches.value.length)
        }
      },
      
      // Betting context and recommendations
      betting_context: {
        prop_analysis_factors: [
          'Contact quality trends (exit velocity, hard hit rate)',
          'Power indicators (barrel rate, sweet spot contact)',
          'Recent form vs season averages',
          'Sample size reliability',
          'League percentile rankings'
        ],
        
        confidence_factors: {
          sample_size_adequate: validStatcastPitches.value.length > 30,
          recent_data_available: recentGames.value.length > 3,
          performance_consistent: Math.abs(avgExitVelo.value - 88) < 10, // Not extreme outlier
          stats_reliable: battingStats.value?.G > 50
        },
        
        risk_assessment: {
          high_confidence_props: avgExitVelo.value > 90 && hardHitRate.value > 40 ? ['total_bases', 'hits'] : [],
          moderate_confidence_props: hardHitRate.value > 35 ? ['rbi', 'runs'] : [],
          avoid_props: validStatcastPitches.value.length < 15 ? ['specific_outcome_props'] : []
        }
      },
      
      // Database context
      data_source: {
        total_statcast_records: '493k+',
        season_coverage: '2025 full season',
        data_quality: 'official_mlb_statcast',
        last_updated: new Date().toISOString().split('T')[0]
      }
    }
    
    // Use intelligent mock response based on real Statcast data
    console.log('Generating AI analysis from real Statcast metrics...')
    console.log('Player data being analyzed:', playerData.value)
    console.log('Exit velocity:', avgExitVelo.value)
    console.log('Hard hit rate:', hardHitRate.value)
    console.log('Sample size:', validStatcastPitches.value.length)
    console.log('Player context for AI:', playerContext)
    console.log('Recent games data:', recentGames.value)
    console.log('First recent game structure:', recentGames.value[0])  
    console.log('Recent 5 games processed:', recentGames.value.slice(0, 5))
    console.log('First processed game:', recentGames.value.slice(0, 5)[0])
    console.log('Valid Statcast pitches count:', validStatcastPitches.value.length)
    console.log('Recent Statcast samples:', validStatcastPitches.value.slice(-10))
    console.log('First Statcast sample:', validStatcastPitches.value.slice(-10)[0])
    
    // Debug the actual Statcast data structure
    const samplePitch = validStatcastPitches.value[0]
    console.log('Statcast pitch fields:', Object.keys(samplePitch))
    console.log('Sample pitch launch_speed:', samplePitch?.launch_speed)
    console.log('Sample pitch launch_angle:', samplePitch?.launch_angle)
    console.log('Sample pitch game_date:', samplePitch?.game_date)
    
    // Test hard hit calculation
    const hardHits = validStatcastPitches.value.filter(p => p.launch_speed > 95)
    console.log('Hard hits (>95 mph):', hardHits.length)
    console.log('Sample hard hit:', hardHits[0])
    console.log('Making API call to:', 'http://localhost:3001/api/ai/chat')
    // Create a simplified context for AI (reduce payload size)
    const simplifiedContext = {
      player_name: playerContext.player_name,
      team: playerContext.team,
      position: playerContext.position,
      season: playerContext.season,
      
      // Key stats only
      statcast_metrics: {
        avg_exit_velocity: playerContext.statcast_metrics.avg_exit_velocity,
        hard_hit_rate: playerContext.statcast_metrics.hard_hit_rate,
        barrel_rate: playerContext.statcast_metrics.barrel_rate,
        barrel_per_pa: playerContext.statcast_metrics.barrel_per_pa,
        sample_size: playerContext.statcast_metrics.sample_size,
        hard_hit_above_average: playerContext.statcast_metrics.hard_hit_above_average,
        barrel_above_average: playerContext.statcast_metrics.barrel_above_average,
        exit_velo_above_average: playerContext.statcast_metrics.exit_velo_above_average
      },
      
      // League context
      league_averages: {
        hard_hit_rate: leagueAverages.value.hard_hit_rate,
        avg_exit_velocity: leagueAverages.value.avg_exit_velocity,
        barrel_rate: leagueAverages.value.barrel_rate
      },
      
      // Recent samples (just 3)
      recent_samples: playerContext.statcast_metrics.recent_statcast_samples?.slice(0, 3) || []
    }
    
    console.log('Request payload:', { query: aiQuestion.value, context: simplifiedContext })
    
    // Call real AI API through Node.js gateway with timeout
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 30000) // 30 second timeout
    
    const response = await fetch('http://localhost:3001/api/ai/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('statEdgeToken') || 'demo-token'}`
      },
      body: JSON.stringify({
        query: aiQuestion.value,
        context: simplifiedContext
      }),
      signal: controller.signal
    })
    
    clearTimeout(timeoutId)
    
    if (!response.ok) {
      throw new Error(`AI API error: ${response.status}`)
    }
    
    const aiData = await response.json()
    
    if (aiData.error) {
      throw new Error(aiData.error)
    }
    
    aiResponse.value = { 
      explanation: aiData.explanation || aiData.data?.explanation || 'Analysis completed successfully.',
      data: aiData.data,
      suggestions: aiData.suggestions
    }
    aiQuestion.value = '' // Clear input after successful analysis
    
  } catch (err) {
    console.error('AI analysis error:', err)
    console.log('Error details:', err.message)
    console.log('Error name:', err.name)
    
    if (err.name === 'AbortError') {
      aiError.value = 'AI analysis timed out. The request is too large. Please try a simpler question.'
    } else if (err.message?.includes('fetch')) {
      aiError.value = 'Unable to connect to AI service. Please check your connection and try again.'
    } else {
      aiError.value = `Unable to generate betting analysis: ${err.message}. Please try again.`
    }
  } finally {
    aiLoading.value = false
  }
}

const formatStat = (value: number | undefined): string => {
  if (value === null || value === undefined) return 'N/A'
  if (typeof value === 'number') {
    return value.toFixed(3)
  }
  return String(value)
}

const formatDate = (dateString: string): string => {
  try {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric'
    })
  } catch {
    return dateString
  }
}

// AI Response Parsing Functions
const extractRecommendation = (text: string): string => {
  const patterns = [
    /(?:Recommendation[:\s]*)(OVER|UNDER|PASS)/i,
    /(?:recommend[:\s]*)(OVER|UNDER|PASS)/i,
    /(OVER|UNDER|PASS)(?:\s+recommended?)/i
  ]
  
  for (const pattern of patterns) {
    const match = text.match(pattern)
    if (match) return match[1].toUpperCase()
  }
  return ''
}

const extractConfidence = (text: string): string => {
  const patterns = [
    /(?:CONFIDENCE[:\s]*)(High|Moderate|Low)/i,
    /(?:Confidence[:\s]*)(High|Moderate|Low)(?:\s*\([\d%+-]+\))?/i,
    /(High|Moderate|Low)(?:\s+confidence)/i,
    /(\d+\/10)\s*confidence/i,
    /(\d+%)\s*confidence/i
  ]
  
  for (const pattern of patterns) {
    const match = text.match(pattern)
    if (match) return match[1]
  }
  return ''
}

const getRecommendationClass = (text: string): string => {
  const rec = extractRecommendation(text)
  if (rec === 'OVER') return 'rec-over'
  if (rec === 'UNDER') return 'rec-under'
  if (rec === 'PASS') return 'rec-pass'
  return ''
}

const getConfidenceClass = (text: string): string => {
  const conf = extractConfidence(text).toLowerCase()
  if (conf.includes('high') || conf.includes('70')) return 'conf-high'
  if (conf.includes('moderate') || conf.includes('55')) return 'conf-moderate'
  if (conf.includes('low')) return 'conf-low'
  return ''
}

const getConfidenceWidth = (text: string): string => {
  const conf = extractConfidence(text).toLowerCase()
  if (conf.includes('high') || conf.includes('70')) return '85%'
  if (conf.includes('moderate') || conf.includes('55')) return '65%'
  if (conf.includes('low')) return '35%'
  return '50%'
}

const formatAnalysisIntoSections = (text: string) => {
  const sections = []
  
  // Parse sections from AI response
  const sectionMap = {
    'KEY METRICS': { icon: '📊', title: 'Key Metrics' },
    'RECENT FORM': { icon: '⚡', title: 'Recent Form' },
    'RISK FACTORS': { icon: '🚨', title: 'Risk Factors' },
    'VALUE ASSESSMENT': { icon: '💰', title: 'Value Assessment' }
  }
  
  Object.entries(sectionMap).forEach(([key, config]) => {
    const regex = new RegExp(`${key}:(.*?)(?=\\n[A-Z ]+:|$)`, 's')
    const match = text.match(regex)
    
    if (match) {
      const content = match[1].trim()
      
      // Check if content has bullet points
      if (content.includes('•')) {
        const items = content.split('•').filter(item => item.trim()).map(item => item.trim())
        sections.push({
          title: config.title,
          icon: config.icon,
          type: 'list',
          items: items
        })
      } else {
        sections.push({
          title: config.title,
          icon: config.icon,
          type: 'text',
          content: content
        })
      }
    }
  })
  
  return sections
}

// Calculate real league averages from database
const calculateLeagueAverageHardHit = (): number => {
  return leagueAverages.value.hard_hit_rate
}

// Mock AI Response Generator for Demo
const generateMockAIResponse = (question: string, context: any): string => {
  const player = context.player_name
  const exitVelo = context.statcast_metrics.avg_exit_velocity
  const hardHitRate = context.statcast_metrics.hard_hit_rate
  const barrelRate = context.statcast_metrics.barrel_rate
  const barrelPerPA = context.statcast_metrics.barrel_per_pa
  const sampleSize = context.statcast_metrics.sample_size
  const barrelAnalysis = context.performance_analysis.barrel_analysis
  
  // Determine recommendation based on real metrics
  let recommendation = 'PASS'
  let confidence = 'Low'
  
  if (sampleSize > 30 && exitVelo > 90 && hardHitRate > 40 && barrelRate > 20) {
    recommendation = 'OVER'
    confidence = 'High (80%)'
  } else if (sampleSize > 20 && (exitVelo > 88 || hardHitRate > 35 || barrelRate > 15)) {
    recommendation = 'OVER'
    confidence = 'Moderate (65%)'
  } else if (exitVelo < 85 && hardHitRate < 30 && barrelRate < 10) {
    recommendation = 'UNDER'
    confidence = 'Moderate (60%)'
  }
  
  return `**Recommendation: ${recommendation}**

**Confidence Level: ${confidence}**

Based on ${player}'s 2025 Statcast data from our 493k+ record database:

**Key Supporting Factors:**
• Exit velocity: ${exitVelo.toFixed(1)} mph (${exitVelo > leagueAverages.value.avg_exit_velocity ? 'above average' : 'league average'})
• Hard hit rate: ${hardHitRate.toFixed(1)}% (league avg: ${leagueAverages.value.hard_hit_rate.toFixed(1)}%)
• Barrel rate: ${barrelRate.toFixed(1)}% (league avg: ${leagueAverages.value.barrel_rate.toFixed(1)}%)
• Barrels per PA: ${(barrelPerPA / 10).toFixed(1)}% (${barrelAnalysis.barrel_context} tier)
• Contact quality: ${exitVelo > 92 ? 'Elite tier' : exitVelo > 88 ? 'Above average' : 'Average'}
• Sample reliability: ${sampleSize} tracked batted balls in 2025

**Risk Factors:**
${sampleSize < 30 ? '• Limited sample size for high confidence' : '• Strong sample size supports analysis'}
• Recent performance trends ${hardHitRate > 40 ? 'favor power metrics' : 'show moderate contact quality'}

**Alternative Props:** Consider total bases or hits props given the contact quality metrics.

*Analysis powered by real MLB Statcast data (${sampleSize} events tracked)*`
}

onMounted(() => {
  loadPlayerData()
  fetchLeagueAverages()
})
</script>

<style lang="scss" scoped>
.player-detail {
  max-width: 1200px;
  margin: 0 auto;
  padding: $spacing-lg;
}

.loading-container,
.error-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  text-align: center;
}

.loading-spinner {
  font-size: 1.125rem;
  color: $text-secondary;
}

.error-message {
  color: $danger;
  margin-bottom: $spacing-lg;
  font-size: 1.125rem;
}

.player-header {
  margin-bottom: $spacing-xl;
  
  .back-button {
    color: $primary;
    text-decoration: none;
    font-size: 0.875rem;
    margin-bottom: $spacing-md;
    background: none;
    border: none;
    cursor: pointer;
    
    &:hover {
      text-decoration: underline;
    }
  }
}

.player-info {
  display: flex;
  gap: $spacing-xl;
  align-items: flex-start;
  
  .player-portrait {
    flex-shrink: 0;
  }
  
  .ai-portrait {
    width: 120px;
    height: 120px;
    border-radius: 12px;
    object-fit: cover;
    border: 3px solid $primary;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }
  
  .portrait-placeholder {
    width: 120px;
    height: 120px;
    border-radius: 12px;
    background: linear-gradient(135deg, $primary, #4f46e5);
    display: flex;
    align-items: center;
    justify-content: center;
    
    .placeholder-text {
      font-size: 3rem;
      font-weight: bold;
      color: white;
    }
  }
  
  .player-details {
    flex: 1;
    
    .player-name {
      font-size: 2.5rem;
      font-weight: 700;
      color: $text-primary;
      margin: 0 0 $spacing-md 0;
    }
    
    .player-meta {
      display: flex;
      gap: $spacing-lg;
      font-size: 1.125rem;
      color: $text-secondary;
      margin-bottom: $spacing-lg;
      
      .team {
        font-weight: 600;
        color: $primary;
      }
    }
}

// AI Analysis Styles
.ai-section {
  margin-top: $spacing-lg;
  
  .ai-toggle-btn {
    background: linear-gradient(135deg, $primary 0%, darken($primary, 10%) 100%);
    border: none;
    padding: $spacing-md $spacing-lg;
    border-radius: $border-radius-lg;
    color: white;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    
    &:hover {
      background: linear-gradient(135deg, darken($primary, 5%) 0%, darken($primary, 15%) 100%);
      transform: translateY(-2px);
    }
    
    &.active {
      background: linear-gradient(135deg, darken($primary, 10%) 0%, darken($primary, 20%) 100%);
    }
  }
  
  .ai-chat-container {
    margin-top: $spacing-lg;
    background: $white;
    border: 2px solid $primary;
    border-radius: $border-radius-lg;
    padding: $spacing-lg;
    box-shadow: $shadow-lg;
  }
  
  .quick-questions {
    margin-bottom: $spacing-lg;
    padding-bottom: $spacing-lg;
    border-bottom: 1px solid $background-gray;
    
    h5 {
      margin: 0 0 $spacing-md 0;
      color: $text-primary;
      font-size: 0.875rem;
      font-weight: 600;
    }
    
    .question-buttons {
      display: flex;
      flex-wrap: wrap;
      gap: $spacing-sm;
      
      .quick-question-btn {
        background: rgba($primary, 0.1);
        color: $primary;
        border: 1px solid rgba($primary, 0.3);
        padding: $spacing-xs $spacing-md;
        border-radius: $border-radius-md;
        font-size: 0.75rem;
        cursor: pointer;
        transition: all 0.2s ease;
        
        &:hover {
          background: rgba($primary, 0.2);
          border-color: $primary;
        }
      }
    }
  }
  
  .ai-input-section {
    display: flex;
    flex-direction: column;
    gap: $spacing-md;
    
    .ai-input {
      width: 100%;
      padding: $spacing-md;
      border: 2px solid $background-gray;
      border-radius: $border-radius-md;
      font-size: 0.875rem;
      resize: vertical;
      min-height: 80px;
      
      &:focus {
        outline: none;
        border-color: $primary;
      }
    }
    
    .ai-ask-btn {
      align-self: flex-end;
      background: $primary;
      color: white;
      border: none;
      padding: $spacing-sm $spacing-lg;
      border-radius: $border-radius-md;
      font-weight: 600;
      cursor: pointer;
      
      &:disabled {
        opacity: 0.6;
        cursor: not-allowed;
      }
      
      &:hover:not(:disabled) {
        background: darken($primary, 10%);
      }
    }
  }
  
  .ai-response {
    margin-top: $spacing-lg;
    padding: $spacing-lg;
    background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
    border-radius: $border-radius-lg;
    border: 2px solid $primary;
    box-shadow: $shadow-lg;
    
    .analysis-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: $spacing-lg;
      padding-bottom: $spacing-md;
      border-bottom: 1px solid rgba($primary, 0.2);
      
      h4 {
        margin: 0;
        color: $primary;
        font-size: 1.25rem;
        font-weight: 700;
      }
      
      .data-badge {
        background: rgba($primary, 0.1);
        color: $primary;
        padding: $spacing-xs $spacing-md;
        border-radius: $border-radius-md;
        font-size: 0.75rem;
        font-weight: 600;
        border: 1px solid rgba($primary, 0.3);
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        gap: $spacing-xs;
        
        &.loading {
          background: rgba($warning, 0.1);
          color: $warning;
          border-color: rgba($warning, 0.3);
          
          span {
            animation: pulse 1.5s ease-in-out infinite;
          }
        }
        
        &.error {
          background: rgba($danger, 0.1);
          color: $danger;
          border-color: rgba($danger, 0.3);
        }
        
        .refresh-btn {
          background: none;
          border: none;
          font-size: 0.7rem;
          cursor: pointer;
          padding: 2px;
          border-radius: 3px;
          transition: background-color 0.2s ease;
          
          &:hover {
            background: rgba($primary, 0.1);
          }
        }
      }
    }
    
    .recommendation-box {
      background: $white;
      border-radius: $border-radius-md;
      padding: $spacing-lg;
      margin-bottom: $spacing-lg;
      border: 2px solid transparent;
      
      &.has-over { border-color: #22c55e; }
      &.has-under { border-color: #ef4444; }
      &.has-pass { border-color: #f59e0b; }
      
      .rec-header {
        display: flex;
        align-items: center;
        gap: $spacing-md;
        
        .rec-label {
          font-size: 1rem;
          font-weight: 600;
          color: $text-primary;
        }
        
        .rec-value {
          font-size: 1.25rem;
          font-weight: 700;
          padding: $spacing-sm $spacing-lg;
          border-radius: $border-radius-md;
          
          &.rec-over {
            background: #dcfce7;
            color: #16a34a;
            border: 1px solid #22c55e;
          }
          
          &.rec-under {
            background: #fef2f2;
            color: #dc2626;
            border: 1px solid #ef4444;
          }
          
          &.rec-pass {
            background: #fef3c7;
            color: #d97706;
            border: 1px solid #f59e0b;
          }
        }
      }
    }
    
    .confidence-section {
      background: $white;
      border-radius: $border-radius-md;
      padding: $spacing-lg;
      margin-bottom: $spacing-lg;
      
      .confidence-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: $spacing-md;
        
        .conf-label {
          font-weight: 600;
          color: $text-primary;
        }
        
        .conf-value {
          font-weight: 700;
          
          &.conf-high { color: #16a34a; }
          &.conf-moderate { color: #d97706; }
          &.conf-low { color: #dc2626; }
        }
      }
      
      .confidence-bar {
        height: 8px;
        background: #e5e7eb;
        border-radius: 4px;
        overflow: hidden;
        
        .conf-fill {
          height: 100%;
          background: linear-gradient(90deg, #16a34a 0%, #22c55e 50%, #4ade80 100%);
          transition: width 0.6s ease;
        }
      }
    }
    
    .analysis-text {
      background: $white;
      padding: $spacing-lg;
      border-radius: $border-radius-md;
      margin-bottom: $spacing-lg;
      
      p {
        margin: 0;
        line-height: 1.6;
        color: $text-primary;
      }
    }
    
    .context-summary {
      background: rgba($white, 0.8);
      padding: $spacing-lg;
      border-radius: $border-radius-md;
      margin-bottom: $spacing-lg;
      
      h5 {
        margin: 0 0 $spacing-md 0;
        color: $primary;
        font-size: 1rem;
        font-weight: 600;
      }
      
      .metrics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: $spacing-md;
        
        .metric-item {
          background: $white;
          padding: $spacing-md;
          border-radius: $border-radius-sm;
          text-align: center;
          border: 1px solid $background-gray;
          
          .metric-label {
            display: block;
            font-size: 0.75rem;
            color: $text-secondary;
            font-weight: 600;
            margin-bottom: $spacing-xs;
          }
          
          .metric-value {
            display: block;
            font-size: 1.125rem;
            font-weight: 700;
            color: $text-primary;
            margin-bottom: $spacing-xs;
          }
          
          .metric-rank {
            font-size: 0.75rem;
            font-weight: 600;
            color: $text-secondary;
            
            &.elite {
              color: #16a34a;
              background: rgba(#16a34a, 0.1);
              padding: 2px 6px;
              border-radius: 4px;
            }
          }
        }
      }
    }
    
    .betting-disclaimer {
      background: rgba(#f59e0b, 0.1);
      border: 1px solid rgba(#f59e0b, 0.3);
      color: #92400e;
      padding: $spacing-md;
      border-radius: $border-radius-sm;
      font-size: 0.875rem;
      text-align: center;
    }
    
    .ai-content {
      p {
        margin-bottom: $spacing-md;
        line-height: 1.6;
        color: $text-primary;
      }
      
      .confidence-indicator {
        margin-bottom: $spacing-md;
        padding: $spacing-sm $spacing-md;
        background: rgba($primary, 0.1);
        border-radius: $border-radius-sm;
        font-size: 0.875rem;
        
        strong {
          color: $primary;
        }
      }
      
      .key-factors {
        strong {
          color: $primary;
          display: block;
          margin-bottom: $spacing-sm;
        }
        
        ul {
          margin: 0;
          padding-left: $spacing-lg;
          
          li {
            margin-bottom: $spacing-xs;
            color: $text-secondary;
            line-height: 1.5;
          }
        }
      }
    }
    
    // Enhanced Analysis Content Styling
    .analysis-content-enhanced {
      margin-top: $spacing-lg;
      
      .analysis-section {
        margin-bottom: $spacing-xl;
        padding: $spacing-lg;
        background: rgba(255, 255, 255, 0.9);
        border-radius: $border-radius-lg;
        border-left: 4px solid $primary;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        transition: all 0.3s ease;
        backdrop-filter: blur(10px);
        
        &:hover {
          transform: translateY(-2px);
          box-shadow: 0 8px 24px rgba(59, 130, 246, 0.15);
        }
        
        .section-header {
          display: flex;
          align-items: center;
          margin-bottom: $spacing-md;
          
          .section-icon {
            font-size: 1.5rem;
            margin-right: $spacing-sm;
            filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
          }
          
          .section-title {
            margin: 0;
            font-size: 1.1rem;
            font-weight: 700;
            color: $primary;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
          }
        }
        
        .section-content {
          .section-text {
            margin: 0;
            line-height: 1.8;
            color: $text-primary;
            font-size: 1rem;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            font-weight: 400;
          }
          
          .section-list {
            list-style: none;
            padding: 0;
            margin: 0;
            
            .list-item {
              display: flex;
              align-items: flex-start;
              margin-bottom: $spacing-md;
              padding: $spacing-sm $spacing-md;
              background: rgba($primary, 0.03);
              border-radius: $border-radius-md;
              border: 1px solid rgba($primary, 0.1);
              transition: all 0.2s ease;
              
              &:hover {
                background: rgba($primary, 0.08);
                border-color: rgba($primary, 0.2);
              }
              
              .bullet {
                color: $primary;
                font-weight: 700;
                font-size: 1.2rem;
                margin-right: $spacing-sm;
                margin-top: 2px;
                flex-shrink: 0;
              }
              
              .item-text {
                flex: 1;
                line-height: 1.7;
                color: $text-primary;
                font-size: 0.95rem;
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                font-weight: 400;
              }
            }
          }
        }
      }
    }
  }
  
  .ai-error {
    margin-top: $spacing-lg;
    padding: $spacing-md;
    background: rgba($danger, 0.1);
    color: $danger;
    border-radius: $border-radius-md;
    border: 1px solid rgba($danger, 0.3);
  }
}

.stats-section {
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    gap: $spacing-xl;
    margin-bottom: $spacing-xl;
  }
}

.stat-category {
  background: $white;
  border-radius: $border-radius-lg;
  padding: $spacing-lg;
  box-shadow: $shadow-sm;
  border: 1px solid $background-gray;
  
  h3 {
    font-size: 1.25rem;
    font-weight: 700;
    color: $text-primary;
    margin: 0 0 $spacing-lg 0;
    padding-bottom: $spacing-md;
    border-bottom: 2px solid $primary;
  }
}

.stat-items {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: $spacing-lg;
}

.stat-item {
  text-align: center;
  padding: $spacing-md;
  background: $background-light;
  border-radius: $border-radius-md;
  
  .stat-label {
    font-size: 0.75rem;
    font-weight: 600;
    color: $text-secondary;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: $spacing-xs;
  }
  
  .stat-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: $primary;
    font-family: $font-mono;
  }
}

.recent-activity {
  background: $white;
  border-radius: $border-radius-lg;
  padding: $spacing-lg;
  box-shadow: $shadow-sm;
  border: 1px solid $background-gray;
  
  h3 {
    font-size: 1.25rem;
    font-weight: 700;
    color: $text-primary;
    margin: 0 0 $spacing-lg 0;
    padding-bottom: $spacing-md;
    border-bottom: 2px solid $primary;
  }
}

.games-list {
  display: flex;
  flex-direction: column;
  gap: $spacing-md;
}

.game-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: $spacing-md;
  background: $background-light;
  border-radius: $border-radius-md;
  
  .game-date {
    font-weight: 600;
    color: $text-primary;
  }
  
  .game-stats {
    color: $text-secondary;
    font-size: 0.875rem;
  }
}

// Responsive adjustments
@media (max-width: $breakpoint-tablet) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .stat-items {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .player-info .player-name {
    font-size: 2rem;
  }
}

@media (max-width: $breakpoint-mobile) {
  .player-detail {
    padding: $spacing-md;
  }
  
  .stat-items {
    grid-template-columns: 1fr;
  }
  
  .player-meta {
    flex-direction: column;
    gap: $spacing-sm;
  }
}

// Animations
@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}
</style>