<template>
  <div>
    <p>Home page</p>
    <p>Random number from backend: {{ randomNumber }}</p>
    <button @click="getRandom">New random number</button>
    <router-link to="/about"><a>about</a></router-link>
    <router-link to="/tryaccess/login/user"><a>login</a></router-link>
    <router-link to="/tryaccess/signup/user"><a>signup</a></router-link>
    <router-link to="/musiclist"><a>musiclist</a></router-link>
    <router-link to="/sing/2"><a>sing</a></router-link>
  </div>
</template>

<script>
import axios from 'axios'
export default {
  data () {
    return {
      randomNumber: 0
    }
  },
  methods: {
    getRandom () {
      const path = 'http://localhost:5042/api/random'
      axios.get(path)
        .then(response => {
          this.randomNumber = response.data.randomNumber
        })
        .catch(error => {
          console.log(error)
        })
    }
  },
  created () {
    this.getRandom()
  }
}
</script>
