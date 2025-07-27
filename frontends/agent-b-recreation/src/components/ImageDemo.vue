<template>
  <div class="image-demo">
    <h2>🎯 Sprint Demo: Player & Team Images</h2>
    
    <div class="demo-section">
      <h3>Player Headshots</h3>
      <div class="player-grid">
        <div 
          v-for="player in demoPlayers" 
          :key="player.id"
          class="player-card"
        >
          <div class="player-image-container">
            <img 
              :src="player.headshot_url" 
              :alt="`${player.name} headshot`"
              class="player-headshot"
              @error="handleImageError"
            />
            <div class="team-logo-overlay">
              <img 
                :src="player.team_logo_url" 
                :alt="`${player.team} logo`"
                class="team-logo"
              />
            </div>
          </div>
          <div class="player-info">
            <h4>{{ player.name }}</h4>
            <div class="team-info">{{ player.team }} • {{ player.position }}</div>
          </div>
        </div>
      </div>
    </div>

    <div class="demo-section">
      <h3>Team Logos</h3>
      <div class="team-grid">
        <div 
          v-for="team in demoTeams" 
          :key="team.code"
          class="team-card"
          :style="{ borderColor: team.primary_color }"
        >
          <img 
            :src="team.logo_url" 
            :alt="`${team.name} logo`"
            class="team-logo-large"
          />
          <div class="team-name">{{ team.name }}</div>
          <div class="team-city">{{ team.city }}</div>
        </div>
      </div>
    </div>

    <div class="demo-section">
      <h3>Integration Status</h3>
      <div class="status-grid">
        <div class="status-item completed">
          ✅ Database Schema - Player headshots & team logos
        </div>
        <div class="status-item completed">
          ✅ API Endpoints - Image serving with fallbacks
        </div>
        <div class="status-item completed">
          ✅ PlayerSpotlightCard - Real headshots with team overlays
        </div>
        <div class="status-item completed">
          ✅ TrendingPerformanceWidget - Aaron Judge with Yankees logo
        </div>
        <div class="status-item completed">
          ✅ Dashboard Integration - Hot players with images
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const demoPlayers = ref([
  {
    id: 1,
    name: "Aaron Judge",
    team: "NYY",
    position: "RF",
    headshot_url: "https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/592450/headshot/67/current",
    team_logo_url: "https://a.espncdn.com/i/teamlogos/mlb/500/nyy.png"
  },
  {
    id: 2,
    name: "Mike Trout",
    team: "LAA",
    position: "CF",
    headshot_url: "https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/545361/headshot/67/current",
    team_logo_url: "https://a.espncdn.com/i/teamlogos/mlb/500/laa.png"
  },
  {
    id: 3,
    name: "Ronald Acuña Jr.",
    team: "ATL",
    position: "OF",
    headshot_url: "https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/665742/headshot/67/current",
    team_logo_url: "https://a.espncdn.com/i/teamlogos/mlb/500/atl.png"
  },
  {
    id: 4,
    name: "Manny Machado",
    team: "SD",
    position: "3B",
    headshot_url: "https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/592518/headshot/67/current",
    team_logo_url: "https://a.espncdn.com/i/teamlogos/mlb/500/sd.png"
  }
])

const demoTeams = ref([
  {
    code: "NYY",
    name: "New York Yankees",
    city: "New York",
    logo_url: "https://a.espncdn.com/i/teamlogos/mlb/500/nyy.png",
    primary_color: "#0C2340"
  },
  {
    code: "LAA",
    name: "Los Angeles Angels", 
    city: "Los Angeles",
    logo_url: "https://a.espncdn.com/i/teamlogos/mlb/500/laa.png",
    primary_color: "#BA0021"
  },
  {
    code: "ATL",
    name: "Atlanta Braves",
    city: "Atlanta", 
    logo_url: "https://a.espncdn.com/i/teamlogos/mlb/500/atl.png",
    primary_color: "#CE1141"
  },
  {
    code: "SD",
    name: "San Diego Padres",
    city: "San Diego",
    logo_url: "https://a.espncdn.com/i/teamlogos/mlb/500/sd.png",
    primary_color: "#2F241D"
  }
])

const handleImageError = (event: Event) => {
  console.warn('Image failed to load:', event.target)
}
</script>

<style lang="scss" scoped>
.image-demo {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.demo-section {
  margin-bottom: 3rem;
  
  h3 {
    color: #333;
    margin-bottom: 1.5rem;
    font-size: 1.5rem;
  }
}

.player-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
}

.player-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  text-align: center;
  transition: transform 0.3s ease, box-shadow 0.3s ease;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
  }
}

.player-image-container {
  position: relative;
  width: 80px;
  height: 80px;
  margin: 0 auto 1rem;
  border-radius: 50%;
  overflow: hidden;
}

.player-headshot {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
  border: 3px solid #f0f0f0;
}

.team-logo-overlay {
  position: absolute;
  bottom: -4px;
  right: -4px;
  width: 28px;
  height: 28px;
  background: white;
  border-radius: 50%;
  padding: 3px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.team-logo {
  width: 100%;
  height: 100%;
  object-fit: contain;
  border-radius: 50%;
}

.player-info h4 {
  margin: 0 0 0.5rem 0;
  color: #333;
  font-size: 1.1rem;
}

.team-info {
  color: #666;
  font-size: 0.9rem;
  font-weight: 500;
}

.team-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
}

.team-card {
  background: white;
  border-radius: 8px;
  padding: 1rem;
  text-align: center;
  border: 2px solid #f0f0f0;
  transition: all 0.3s ease;

  &:hover {
    transform: scale(1.05);
  }
}

.team-logo-large {
  width: 60px;
  height: 60px;
  object-fit: contain;
  margin-bottom: 0.5rem;
}

.team-name {
  font-weight: 600;
  color: #333;
  margin-bottom: 0.25rem;
  font-size: 0.9rem;
}

.team-city {
  color: #666;
  font-size: 0.8rem;
}

.status-grid {
  display: grid;
  gap: 0.5rem;
}

.status-item {
  padding: 0.75rem 1rem;
  border-radius: 6px;
  font-weight: 500;
  
  &.completed {
    background: #d4edda;
    color: #155724;
    border: 1px solid #c3e6cb;
  }
}

h2 {
  text-align: center;
  color: #333;
  margin-bottom: 2rem;
  font-size: 2rem;
}
</style>