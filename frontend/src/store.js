import Vue from 'vue'
import Vuex from 'vuex'
import * as types from './mutation-types'

Vue.use(Vuex)

const state = {
  user_id: 1
}

const mutations = {
  [types.USER_ID] (state, num) {
    state.user_id = num - 0
  }
}

const actions = {
  loggedin (context, url) {
    const request = new XMLHttpRequest()
    request.responseType = 'text'
    request.onload = () => {
      if (request.responseText === '0') {
        window.location.href = '/tryaccess/login/' + url
      }
    }
    request.open('GET', 'http://localhost:5042/api/loggedin/' + context.state.user_id, true)
    request.send()
  }
}

export default new Vuex.Store({
  state,
  mutations,
  actions
})
