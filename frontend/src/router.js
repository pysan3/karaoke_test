import Vue from 'vue'
import Router from 'vue-router'

const routerOptions = [
  { path: '/', component: 'Home' },
  { path: '/user', component: 'User' },
  { path: '/about', component: 'About' },
  { path: '/helloworld', component: 'HelloWorld' },
  { path: '/tryaccess/:accessType/:url', component: 'TryAccess' },
  { path: '/musiclist', component: 'MusicList' },
  { path: '/musicupload', component: 'MusicUpload' },
  { path: '/sing/:song_id', component: 'Sing' },
  { path: '*', component: 'NotFound' }
]

const routes = routerOptions.map(route => {
  return {
    ...route,
    name: `${route.component}`.toLowerCase(),
    component: () => import(`@/components/${route.component}.vue`)
  }
})

Vue.use(Router)

export default new Router({
  mode: 'history',
  base: process.env.BASE_URL,
  routes
})
