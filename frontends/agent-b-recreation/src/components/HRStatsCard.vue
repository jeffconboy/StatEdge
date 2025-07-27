<template>
  <div class="hr-stats-card">
    <div class="hr-stats-card__header">
      <h3 class="hr-stats-card__title">HR Betting Analysis</h3>
      <div class="hr-stats-card__confidence" :class="confidenceClass">
        <span class="confidence-label">Confidence:</span>
        <span class="confidence-value">{{ confidence }}%</span>
      </div>
    </div>

    <div class="hr-stats-grid">
      <!-- Statcast Power Metrics -->
      <div class="stat-section">
        <h4 class="section-title">Power Metrics</h4>
        <div class="stat-row">
          <span class="stat-label">Avg Exit Velocity</span>
          <span class="stat-value">{{ stats.avgExitVelo || 'N/A' }} mph</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Max Exit Velocity</span>
          <span class="stat-value">{{ stats.maxExitVelo || 'N/A' }} mph</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Hard Hit %</span>
          <span class="stat-value">{{ stats.hardHitPercent || 'N/A' }}%</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Barrel %</span>
          <span class="stat-value">{{ stats.barrelPercent || 'N/A' }}%</span>
        </div>
      </div>

      <!-- Home Run Trends -->
      <div class="stat-section">
        <h4 class="section-title">HR Trends</h4>
        <div class="stat-row">
          <span class="stat-label">HRs Last 15 Games</span>
          <span class="stat-value trend-value">{{ stats.hrLast15 || 0 }}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">HRs vs Pitcher Type</span>
          <span class="stat-value">{{ stats.hrVsPitcherType || 'N/A' }}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Home/Away Splits</span>
          <span class="stat-value">{{ stats.homeAwayHR || 'N/A' }}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Day/Night HRs</span>
          <span class="stat-value">{{ stats.dayNightHR || 'N/A' }}</span>
        </div>
      </div>

      <!-- Ballpark & Matchup -->
      <div class="stat-section">
        <h4 class="section-title">Matchup Analysis</h4>
        <div class="stat-row">
          <span class="stat-label">Ballpark HR Factor</span>
          <span class="stat-value">{{ ballpark.hrFactor || 'N/A' }}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Wind Conditions</span>
          <span class="stat-value">{{ ballpark.wind || 'N/A' }}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">vs Today's Pitcher</span>
          <span class="stat-value">{{ matchup.vsPitcher || 'N/A' }}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Pitcher HR/9</span>
          <span class="stat-value">{{ matchup.pitcherHR9 || 'N/A' }}</span>
        </div>
      </div>

      <!-- AI Prediction -->
      <div class="stat-section prediction-section">
        <h4 class="section-title">AI Prediction</h4>
        <div class="prediction-content">
          <div class="prediction-result" :class="predictionClass">
            {{ prediction.outcome || 'Analyzing...' }}
          </div>
          <div class="prediction-reasoning">
            {{ prediction.reasoning || 'Calculating probability based on advanced metrics...' }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface HRStatsProps {
  stats: {
    avgExitVelo?: number
    maxExitVelo?: number
    hardHitPercent?: number
    barrelPercent?: number
    hrLast15?: number
    hrVsPitcherType?: string
    homeAwayHR?: string
    dayNightHR?: string
  }
  ballpark: {
    hrFactor?: number
    wind?: string
  }
  matchup: {
    vsPitcher?: string
    pitcherHR9?: number
  }
  prediction: {
    outcome?: string
    reasoning?: string
  }
  confidence: number
}

const props = defineProps<HRStatsProps>()

const confidenceClass = computed(() => {
  if (props.confidence >= 80) return 'confidence--high'
  if (props.confidence >= 60) return 'confidence--medium'
  return 'confidence--low'
})

const predictionClass = computed(() => {
  if (props.prediction.outcome?.toLowerCase().includes('likely')) return 'prediction--positive'
  if (props.prediction.outcome?.toLowerCase().includes('unlikely')) return 'prediction--negative'
  return 'prediction--neutral'
})
</script>

<style lang="scss" scoped>
.hr-stats-card {
  background: linear-gradient(135deg, #1a1d29 0%, #2d3748 100%);
  border-radius: 16px;
  padding: 24px;
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);

  &__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 16px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }

  &__title {
    font-size: 1.5rem;
    font-weight: 700;
    margin: 0;
    color: #f7fafc;
  }

  &__confidence {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    border-radius: 20px;
    font-weight: 600;
    font-size: 0.875rem;

    &.confidence--high {
      background: rgba(72, 187, 120, 0.2);
      color: #48bb78;
      border: 1px solid rgba(72, 187, 120, 0.3);
    }

    &.confidence--medium {
      background: rgba(237, 137, 54, 0.2);
      color: #ed8936;
      border: 1px solid rgba(237, 137, 54, 0.3);
    }

    &.confidence--low {
      background: rgba(245, 101, 101, 0.2);
      color: #f56565;
      border: 1px solid rgba(245, 101, 101, 0.3);
    }
  }
}

.hr-stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
}

.stat-section {
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  padding: 16px;
  border: 1px solid rgba(255, 255, 255, 0.08);

  &.prediction-section {
    grid-column: span 2;
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(99, 102, 241, 0.1) 100%);
    border: 1px solid rgba(59, 130, 246, 0.2);
  }
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 12px 0;
  color: #a0aec0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);

  &:last-child {
    border-bottom: none;
  }
}

.stat-label {
  font-size: 0.875rem;
  color: #cbd5e0;
  font-weight: 500;
}

.stat-value {
  font-size: 0.875rem;
  font-weight: 600;
  color: #f7fafc;

  &.trend-value {
    background: linear-gradient(135deg, #48bb78, #38a169);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-weight: 700;
  }
}

.prediction-content {
  text-align: center;
}

.prediction-result {
  font-size: 1.25rem;
  font-weight: 700;
  margin-bottom: 12px;
  padding: 12px 20px;
  border-radius: 8px;
  display: inline-block;

  &.prediction--positive {
    background: rgba(72, 187, 120, 0.2);
    color: #48bb78;
    border: 1px solid rgba(72, 187, 120, 0.3);
  }

  &.prediction--negative {
    background: rgba(245, 101, 101, 0.2);
    color: #f56565;
    border: 1px solid rgba(245, 101, 101, 0.3);
  }

  &.prediction--neutral {
    background: rgba(237, 137, 54, 0.2);
    color: #ed8936;
    border: 1px solid rgba(237, 137, 54, 0.3);
  }
}

.prediction-reasoning {
  font-size: 0.875rem;
  color: #a0aec0;
  line-height: 1.5;
  font-style: italic;
}

.confidence-label {
  color: rgba(255, 255, 255, 0.7);
}

.confidence-value {
  font-weight: 700;
}

@media (max-width: 768px) {
  .hr-stats-grid {
    grid-template-columns: 1fr;
  }

  .stat-section.prediction-section {
    grid-column: span 1;
  }

  .hr-stats-card__header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
}
</style>