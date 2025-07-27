<template>
  <div class="player-spotlight" :class="`player-spotlight--${bgColor}`">
    <div class="player-spotlight__content">
      <div class="player-spotlight__header">
        <h3 class="player-spotlight__name">{{ player.name }}</h3>
        <div class="player-spotlight__matchup">{{ matchup }}</div>
      </div>

      <div class="player-spotlight__stats">
        <div
          v-for="stat in stats"
          :key="stat.label"
          class="player-spotlight__stat"
        >
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
        </div>
      </div>

      <div v-if="highlight" class="player-spotlight__highlight">
        {{ highlight }}
      </div>
    </div>

    <div class="player-spotlight__avatar">
      <div class="modern-player-container">
        <!-- Team logo background -->
        <div v-if="player.team_logo_url" class="team-logo-background">
          <img 
            :src="player.team_logo_url" 
            :alt="`${player.team} logo`"
            class="team-logo-bg"
            @error="teamLogoError = true"
          />
        </div>
        
        <!-- Player headshot -->
        <div class="player-image-wrapper">
          <img 
            v-if="player.headshot_url"
            :src="player.headshot_url" 
            :alt="`${player.name} headshot`"
            class="modern-player-headshot"
            @error="handleImageError"
            @load="imageLoaded = true"
          />
          <div 
            v-else 
            class="modern-avatar-placeholder"
            :class="{ 'loading': imageLoading }"
          >
            {{ getPlayerInitials(player.name) }}
          </div>
        </div>
        
        <!-- Team badge -->
        <div v-if="player.team_logo_url" class="team-badge">
          <img 
            :src="player.team_logo_url" 
            :alt="`${player.team} logo`"
            class="team-badge-logo"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface PlayerSpotlightProps {
  player: {
    name: string
    team: string
    headshot_url?: string
    team_logo_url?: string
    team_primary_color?: string
  }
  matchup: string
  stats: Array<{
    label: string
    value: string | number
  }>
  highlight?: string
  bgColor: 'red' | 'green' | 'blue' | 'purple'
}

const props = defineProps<PlayerSpotlightProps>()

// Image loading states
const imageLoaded = ref(false)
const imageLoading = ref(false)
const imageError = ref(false)
const teamLogoError = ref(false)

// Handle image load errors
const handleImageError = () => {
  imageError.value = true
  imageLoaded.value = false
}

// Get player initials for fallback
const getPlayerInitials = (name: string): string => {
  return name.split(' ').map(n => n[0]).join('').toUpperCase()
}
</script>

<style lang="scss" scoped>
.player-spotlight {
  border-radius: $border-radius-xl;
  padding: $spacing-xl;
  color: $white;
  position: relative;
  overflow: hidden;
  min-height: 220px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
  
  // Enhanced shadows and borders
  box-shadow: 
    0 16px 40px rgba(0, 0, 0, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.3),
    inset 0 -1px 0 rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.2);

  // Animated background overlay
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: radial-gradient(circle at 30% 20%, rgba(255, 255, 255, 0.15) 0%, transparent 70%),
                radial-gradient(circle at 70% 80%, rgba(255, 255, 255, 0.1) 0%, transparent 60%);
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.3s ease;
    z-index: 1;
  }

  &:hover {
    transform: translateY(-8px) scale(1.02);
    box-shadow: 
      0 24px 60px rgba(0, 0, 0, 0.2),
      inset 0 1px 0 rgba(255, 255, 255, 0.4),
      inset 0 -1px 0 rgba(0, 0, 0, 0.3);

    &::before {
      opacity: 1;
    }

    .player-spotlight__content {
      transform: translateZ(0);
    }
  }

  &--red {
    background: linear-gradient(135deg, 
      #dc3545 0%, 
      #c82333 50%, 
      #a71e2a 100%);
    box-shadow: 
      0 16px 40px rgba(220, 53, 69, 0.25),
      inset 0 1px 0 rgba(255, 255, 255, 0.3),
      inset 0 -1px 0 rgba(0, 0, 0, 0.2);
  }

  &--green {
    background: linear-gradient(135deg, 
      #28a745 0%, 
      #1e7e34 50%, 
      #155724 100%);
    box-shadow: 
      0 16px 40px rgba(40, 167, 69, 0.25),
      inset 0 1px 0 rgba(255, 255, 255, 0.3),
      inset 0 -1px 0 rgba(0, 0, 0, 0.2);
  }

  &--blue {
    background: linear-gradient(135deg, 
      #3b82f6 0%, 
      #1e40af 50%, 
      #1e3a8a 100%);
    box-shadow: 
      0 16px 40px rgba(59, 130, 246, 0.25),
      inset 0 1px 0 rgba(255, 255, 255, 0.3),
      inset 0 -1px 0 rgba(0, 0, 0, 0.2);
  }

  &--purple {
    background: linear-gradient(135deg, 
      #6f42c1 0%, 
      #5a32a3 50%, 
      #4c2a85 100%);
    box-shadow: 
      0 16px 40px rgba(111, 66, 193, 0.25),
      inset 0 1px 0 rgba(255, 255, 255, 0.3),
      inset 0 -1px 0 rgba(0, 0, 0, 0.2);
  }

  &__content {
    flex: 1;
    z-index: 2;
    position: relative;
    margin-right: 120px; // Reserve space for larger image
    overflow: hidden; // Prevent text overflow
  }

  &__header {
    margin-bottom: $spacing-md;
  }

  &__name {
    font-size: 1.25rem;
    font-weight: 700;
    margin: 0 0 $spacing-xs 0;
    line-height: 1.2;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__matchup {
    font-size: 0.875rem;
    opacity: 0.9;
    font-weight: 500;
  }

  &__stats {
    display: flex;
    gap: $spacing-md;
    margin-bottom: $spacing-md;
    flex-wrap: wrap;
  }

  &__stat {
    text-align: center;
    min-width: 50px;
  }

  &__highlight {
    font-size: 0.875rem;
    font-weight: 500;
    opacity: 0.95;
    font-style: italic;
    line-height: 1.4;
  }

  &__avatar {
    position: absolute;
    right: $spacing-md;
    bottom: $spacing-md;
    width: 100px; // Increased from 80px
    height: 100px; // Increased from 80px
    z-index: 1;
  }
}

.stat-value {
  font-size: 1.125rem;
  font-weight: 700;
  line-height: 1;
  margin-bottom: 2px;
}

.stat-label {
  font-size: 0.75rem;
  opacity: 0.9;
  text-transform: uppercase;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.modern-player-container {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.team-logo-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  opacity: 0.1;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
}

.team-logo-bg {
  width: 120%;
  height: 120%;
  object-fit: contain;
  filter: blur(1px);
}

.player-image-wrapper {
  position: relative;
  width: 90%;
  height: 90%;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modern-player-headshot {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center 10%;
  border-radius: 16px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  background: linear-gradient(145deg, 
    rgba(255, 255, 255, 0.15), 
    rgba(255, 255, 255, 0.05));
  backdrop-filter: blur(15px);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 
    0 12px 40px rgba(0, 0, 0, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.4),
    inset 0 -1px 0 rgba(0, 0, 0, 0.1);
  transform: scale(0.9);
  position: relative;

  // Subtle glow effect
  &::before {
    content: '';
    position: absolute;
    top: -2px;
    left: -2px;
    right: -2px;
    bottom: -2px;
    background: linear-gradient(135deg, 
      rgba(255, 255, 255, 0.3) 0%, 
      rgba(255, 255, 255, 0.1) 100%);
    border-radius: 18px;
    z-index: -1;
    opacity: 0;
    transition: opacity 0.3s ease;
  }

  &:hover {
    transform: translateY(-3px) scale(0.95);
    border-color: rgba(255, 255, 255, 0.5);
    box-shadow: 
      0 20px 60px rgba(0, 0, 0, 0.2),
      inset 0 1px 0 rgba(255, 255, 255, 0.5),
      inset 0 -1px 0 rgba(0, 0, 0, 0.15);

    &::before {
      opacity: 1;
    }
  }
}

.modern-avatar-placeholder {
  width: 100%;
  height: 100%;
  background: linear-gradient(145deg, rgba(255,255,255,0.15), rgba(255,255,255,0.05));
  border-radius: 12px;
  border: 2px solid rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1.5rem;
  color: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;

  &.loading {
    opacity: 0.7; // Simple opacity change instead of pulsing
  }
}

.team-badge {
  position: absolute;
  bottom: -6px;
  right: -6px;
  width: 32px;
  height: 32px;
  background: linear-gradient(145deg, 
    rgba(255, 255, 255, 0.98) 0%, 
    rgba(255, 255, 255, 0.9) 100%);
  border-radius: 10px;
  padding: 5px;
  box-shadow: 
    0 8px 24px rgba(0, 0, 0, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.8),
    inset 0 -1px 0 rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(15px);
  border: 2px solid rgba(255, 255, 255, 0.4);
  z-index: 3;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;

  // Subtle pulse animation
  &::before {
    content: '';
    position: absolute;
    top: -2px;
    left: -2px;
    right: -2px;
    bottom: -2px;
    background: linear-gradient(135deg, 
      rgba(255, 255, 255, 0.6) 0%, 
      transparent 100%);
    border-radius: 12px;
    opacity: 0;
    transition: opacity 0.3s ease;
    z-index: -1;
  }

  &:hover {
    transform: scale(1.15) rotate(5deg);
    box-shadow: 
      0 12px 32px rgba(0, 0, 0, 0.25),
      inset 0 1px 0 rgba(255, 255, 255, 0.9),
      inset 0 -1px 0 rgba(0, 0, 0, 0.15);

    &::before {
      opacity: 1;
    }
  }
}

.team-badge-logo {
  width: 100%;
  height: 100%;
  object-fit: contain;
  border-radius: 4px;
}

// Removed pulsing animation - too distracting

// Responsive adjustments
@media (max-width: $breakpoint-tablet) {
  .player-spotlight {
    min-height: 160px;

    &__content {
      margin-right: 90px; // Reduced margin for smaller screens
    }

    &__name {
      font-size: 1.125rem;
    }

    &__stats {
      gap: $spacing-sm;
    }

    &__avatar {
      width: 80px; // Slightly reduced for tablet
      height: 80px;

      svg {
        width: 30px;
        height: 30px;
      }
    }
  }
}

@media (max-width: $breakpoint-mobile) {
  .player-spotlight {
    &__content {
      margin-right: 70px; // Further reduced for mobile
    }

    &__avatar {
      width: 60px; // Smaller for mobile
      height: 60px;
    }
  }
}
</style>