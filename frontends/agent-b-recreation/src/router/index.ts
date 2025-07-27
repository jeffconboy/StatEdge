import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '@/views/Dashboard.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: Dashboard
    },
    {
      path: '/players',
      name: 'players',
      component: () => import('@/views/Players.vue')
    },
    {
      path: '/players/:id',
      name: 'player-detail',
      component: () => import('@/views/PlayerDetail.vue')
    },
    {
      path: '/teams',
      name: 'teams',
      component: () => import('@/views/Teams.vue')
    },
    {
      path: '/analytics',
      name: 'analytics',
      component: () => import('@/views/Analytics.vue')
    },
    {
      path: '/trending',
      name: 'trending',
      component: () => import('@/views/Trending.vue')
    },
    {
      path: '/standings',
      name: 'standings',
      component: () => import('@/views/Standings.vue')
    },
    {
      path: '/compare',
      name: 'compare',
      component: () => import('@/views/Compare.vue')
    },
    {
      path: '/hr-betting',
      name: 'hr-betting',
      component: () => import('@/views/HRBetting.vue')
    }
  ]
})

export default router