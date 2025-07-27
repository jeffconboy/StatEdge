<template>
  <div class="standings-table card">
    <div class="standings-table__header">
      <h3 class="standings-table__title">MLB Standings</h3>
      <div class="standings-table__tabs">
        <button
          v-for="league in leagues"
          :key="league.key"
          class="tab-button"
          :class="{ 'tab-button--active': activeLeague === league.key }"
          @click="setActiveLeague(league.key)"
        >
          {{ league.label }}
        </button>
      </div>
    </div>

    <div class="standings-table__content">
      <div class="table-container">
        <table class="standings-table__table">
          <thead>
            <tr>
              <th class="team-column">Team</th>
              <th 
                v-for="column in columns"
                :key="column.key"
                class="stat-column"
                :class="{ 'sortable': column.sortable }"
                @click="column.sortable && sortBy(column.key)"
              >
                {{ column.label }}
                <svg
                  v-if="column.sortable && sortColumn === column.key"
                  class="sort-icon"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                  :class="{ 'sort-icon--desc': sortDirection === 'desc' }"
                >
                  <path d="M7 14l5-5 5 5H7z"/>
                </svg>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(team, index) in sortedStandings"
              :key="team.id"
              class="standings-row"
              :class="{ 'standings-row--playoff': index < 6 }"
            >
              <td class="team-cell">
                <div class="team-info">
                  <div class="team-logo">{{ team.abbreviation }}</div>
                  <div class="team-details">
                    <div class="team-name">{{ team.name }}</div>
                    <div class="team-record">({{ team.wins }}-{{ team.losses }})</div>
                  </div>
                </div>
              </td>
              <td class="stat-cell">{{ team.wins }}</td>
              <td class="stat-cell">{{ team.losses }}</td>
              <td class="stat-cell">{{ team.percentage.toFixed(3) }}</td>
              <td class="stat-cell">{{ team.gamesBehind === 0 ? '-' : team.gamesBehind.toFixed(1) }}</td>
              <td class="stat-cell">
                <span v-if="team.streak" class="streak" :class="`streak--${team.streak.charAt(0).toLowerCase()}`">
                  {{ team.streak }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="standings-table__legend">
      <div class="legend-item">
        <div class="legend-color legend-color--playoff"></div>
        <span>Playoff Position</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

interface StandingsTeam {
  id: string
  name: string
  abbreviation: string
  wins: number
  losses: number
  percentage: number
  gamesBehind: number
  streak?: string
}

const leagues = [
  { key: 'al', label: 'AL' },
  { key: 'nl', label: 'NL' }
]

const columns = [
  { key: 'wins', label: 'W', sortable: true },
  { key: 'losses', label: 'L', sortable: true },
  { key: 'percentage', label: 'PCT', sortable: true },
  { key: 'gamesBehind', label: 'GB', sortable: true },
  { key: 'streak', label: 'STRK', sortable: false }
]

const activeLeague = ref('al')
const sortColumn = ref('percentage')
const sortDirection = ref<'asc' | 'desc'>('desc')

// Mock standings data
const standingsData = ref({
  al: [
    { id: '1', name: 'Baltimore Orioles', abbreviation: 'BAL', wins: 65, losses: 42, percentage: 0.607, gamesBehind: 0, streak: 'W3' },
    { id: '2', name: 'Tampa Bay Rays', abbreviation: 'TB', wins: 63, losses: 45, percentage: 0.583, gamesBehind: 2.5, streak: 'L1' },
    { id: '3', name: 'New York Yankees', abbreviation: 'NYY', wins: 60, losses: 47, percentage: 0.561, gamesBehind: 5.0, streak: 'W2' },
    { id: '4', name: 'Toronto Blue Jays', abbreviation: 'TOR', wins: 58, losses: 49, percentage: 0.542, gamesBehind: 7.0, streak: 'W1' },
    { id: '5', name: 'Boston Red Sox', abbreviation: 'BOS', wins: 54, losses: 53, percentage: 0.505, gamesBehind: 11.0, streak: 'L2' },
    { id: '6', name: 'Houston Astros', abbreviation: 'HOU', wins: 62, losses: 44, percentage: 0.585, gamesBehind: 0, streak: 'W4' },
    { id: '7', name: 'Texas Rangers', abbreviation: 'TEX', wins: 58, losses: 49, percentage: 0.542, gamesBehind: 4.5, streak: 'W1' },
    { id: '8', name: 'Seattle Mariners', abbreviation: 'SEA', wins: 56, losses: 51, percentage: 0.523, gamesBehind: 6.5, streak: 'L1' },
    { id: '9', name: 'Los Angeles Angels', abbreviation: 'LAA', wins: 54, losses: 53, percentage: 0.505, gamesBehind: 8.5, streak: 'W2' },
    { id: '10', name: 'Oakland Athletics', abbreviation: 'OAK', wins: 35, losses: 72, percentage: 0.327, gamesBehind: 27.5, streak: 'L5' }
  ],
  nl: [
    { id: '11', name: 'Atlanta Braves', abbreviation: 'ATL', wins: 68, losses: 39, percentage: 0.636, gamesBehind: 0, streak: 'W2' },
    { id: '12', name: 'Los Angeles Dodgers', abbreviation: 'LAD', wins: 66, losses: 41, percentage: 0.617, gamesBehind: 0, streak: 'W3' },
    { id: '13', name: 'Milwaukee Brewers', abbreviation: 'MIL', wins: 60, losses: 47, percentage: 0.561, gamesBehind: 6.0, streak: 'W1' },
    { id: '14', name: 'Philadelphia Phillies', abbreviation: 'PHI', wins: 59, losses: 48, percentage: 0.551, gamesBehind: 7.0, streak: 'L1' },
    { id: '15', name: 'San Francisco Giants', abbreviation: 'SF', wins: 57, losses: 50, percentage: 0.533, gamesBehind: 9.0, streak: 'W2' },
    { id: '16', name: 'Miami Marlins', abbreviation: 'MIA', wins: 54, losses: 53, percentage: 0.505, gamesBehind: 12.0, streak: 'L3' },
    { id: '17', name: 'Arizona Diamondbacks', abbreviation: 'ARI', wins: 53, losses: 54, percentage: 0.495, gamesBehind: 13.0, streak: 'W1' },
    { id: '18', name: 'New York Mets', abbreviation: 'NYM', wins: 52, losses: 55, percentage: 0.486, gamesBehind: 14.0, streak: 'L2' },
    { id: '19', name: 'Cincinnati Reds', abbreviation: 'CIN', wins: 51, losses: 56, percentage: 0.477, gamesBehind: 15.0, streak: 'W1' },
    { id: '20', name: 'Colorado Rockies', abbreviation: 'COL', wins: 44, losses: 63, percentage: 0.411, gamesBehind: 22.0, streak: 'L4' }
  ]
})

const currentStandings = computed(() => standingsData.value[activeLeague.value])

const sortedStandings = computed(() => {
  const standings = [...currentStandings.value]
  
  if (!sortColumn.value) return standings

  return standings.sort((a, b) => {
    const aVal = a[sortColumn.value as keyof StandingsTeam]
    const bVal = b[sortColumn.value as keyof StandingsTeam]

    if (typeof aVal === 'number' && typeof bVal === 'number') {
      return sortDirection.value === 'asc' ? aVal - bVal : bVal - aVal
    }

    return 0
  })
})

const setActiveLeague = (league: string) => {
  activeLeague.value = league
}

const sortBy = (column: string) => {
  if (sortColumn.value === column) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortColumn.value = column
    sortDirection.value = column === 'losses' || column === 'gamesBehind' ? 'asc' : 'desc'
  }
}
</script>

<style lang="scss" scoped>
.standings-table {
  padding: $spacing-lg;

  &__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: $spacing-lg;
  }

  &__title {
    font-size: 1.25rem;
    font-weight: 700;
    color: $text-primary;
    margin: 0;
  }

  &__tabs {
    display: flex;
    gap: $spacing-xs;
  }

  &__content {
    margin-bottom: $spacing-md;
  }

  &__table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.875rem;
  }

  &__legend {
    display: flex;
    align-items: center;
    gap: $spacing-md;
    padding-top: $spacing-md;
    border-top: 1px solid $background-gray;
  }
}

.tab-button {
  padding: $spacing-sm $spacing-md;
  border: 1px solid $background-gray;
  background-color: $white;
  color: $text-secondary;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.875rem;
  transition: all 0.2s ease;

  &:first-child {
    border-radius: $border-radius-md 0 0 $border-radius-md;
  }

  &:last-child {
    border-radius: 0 $border-radius-md $border-radius-md 0;
  }

  &:not(:last-child) {
    border-right: none;
  }

  &:hover:not(&--active) {
    background-color: $background-light;
  }

  &--active {
    background-color: $primary;
    color: $white;
    border-color: $primary;
  }
}

.table-container {
  overflow-x: auto;
}

th, td {
  padding: $spacing-md $spacing-sm;
  text-align: left;
  border-bottom: 1px solid $background-light;
}

th {
  background-color: $background-light;
  font-weight: 700;
  color: $text-secondary;
  text-transform: uppercase;
  font-size: 0.75rem;
  letter-spacing: 0.5px;
  position: sticky;
  top: 0;
  z-index: 1;

  &.sortable {
    cursor: pointer;
    user-select: none;
    display: flex;
    align-items: center;
    gap: 4px;

    &:hover {
      color: $primary;
    }
  }

  &.team-column {
    min-width: 200px;
  }

  &.stat-column {
    text-align: center;
    min-width: 60px;
  }
}

.sort-icon {
  width: 12px;
  height: 12px;
  transition: transform 0.2s ease;

  &--desc {
    transform: rotate(180deg);
  }
}

.standings-row {
  transition: background-color 0.2s ease;

  &:hover {
    background-color: $background-light;
  }

  &--playoff {
    position: relative;

    &::before {
      content: '';
      position: absolute;
      left: 0;
      top: 0;
      bottom: 0;
      width: 4px;
      background-color: $success;
    }
  }
}

.team-cell {
  min-width: 200px;
}

.team-info {
  display: flex;
  align-items: center;
  gap: $spacing-md;
}

.team-logo {
  width: 32px;
  height: 32px;
  background-color: $primary;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: $white;
  font-weight: 700;
  font-size: 0.75rem;
  flex-shrink: 0;
}

.team-details {
  min-width: 0;
}

.team-name {
  font-weight: 600;
  color: $text-primary;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.team-record {
  font-size: 0.75rem;
  color: $text-secondary;
  font-weight: 500;
}

.stat-cell {
  text-align: center;
  font-weight: 500;
  color: $text-primary;
  font-family: $font-mono;
}

.streak {
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.75rem;

  &--w {
    background-color: rgba($success, 0.1);
    color: $success;
  }

  &--l {
    background-color: rgba($danger, 0.1);
    color: $danger;
  }
}

.legend-item {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  font-size: 0.75rem;
  color: $text-secondary;
  font-weight: 500;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 2px;

  &--playoff {
    background-color: $success;
  }
}

// Mobile responsive
@media (max-width: $breakpoint-tablet) {
  .standings-table {
    padding: $spacing-md;

    &__header {
      flex-direction: column;
      align-items: flex-start;
      gap: $spacing-md;
    }
  }

  .team-info {
    gap: $spacing-sm;
  }

  .team-logo {
    width: 24px;
    height: 24px;
    font-size: 0.625rem;
  }

  .team-name {
    font-size: 0.875rem;
  }

  th, td {
    padding: $spacing-sm;
  }
}

@media (max-width: $breakpoint-mobile) {
  .standings-table__table {
    font-size: 0.75rem;
  }

  .team-cell {
    min-width: 150px;
  }

  .team-name {
    font-size: 0.75rem;
  }

  .team-record {
    font-size: 0.625rem;
  }

  // Hide some columns on mobile
  th:nth-child(6), td:nth-child(6) {
    display: none;
  }
}
</style>