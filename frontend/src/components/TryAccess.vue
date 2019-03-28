<template>
  <div>
    <h2>{{ accessTypes[accessID] }}</h2>
    <input type="text" placeholder="Username" v-model="user_name">
    <input type="password" placeholder="Password" v-model="user_password">
    <button @click="tryAccess">{{ accessTypes[accessID] }}!!</button>
    <p>
      {{ msg[-1 * (accessID - 1)] }}
      <button @click="accessOpposite">{{ accessTypes[-1 * (accessID - 1)] }}</button>
    </p>
    <p>user_name {{ user_name }}</p>
    <p>password {{ user_password }}</p>
  </div>
</template>

<script>
import axios from 'axios'
import * as types from '@/mutation-types'
import { mapState } from 'vuex'
export default {
  data () {
    return {
      accessTypes: ['signup', 'login'],
      accessID: (this.$route.params.accessType === 'login') + 0,
      url: '/' + this.$route.params.url.replace(/-/g, '/'),
      user_name: '',
      user_password: '',
      msg: ['make a new account', 'already have an account']
    }
  },
  computed: mapState([
    'user_id'
  ]),
  watch: {
    '$route' (to, _) { // eslint-disable-line no-unused-vars
      this.accessID = (to.params.accessType === 'login') + 0
    }
  },
  methods: {
    tryAccess () {
      if (this.user_name.length * this.user_password.length === 0) {
        alert('should not be zero charactors')
        return
      }
      axios.post('http://localhost:5042/api/' + this.accessTypes[this.accessID], {
        user_name: this.user_name,
        user_password: this.user_password
      })
        .then(response => {
          const responseID = response.data.user_id - 0
          if (responseID !== -1) {
            this.$store.commit(types.USER_ID, responseID)
            this.$router.push(this.url)
          } else {
            alert(response.data.msg)
          }
        })
        .catch(error => {
          console.log(error)
        })
    },
    accessOpposite () {
      this.$router.push({
        name: 'tryaccess',
        params: {
          accessType: this.accessTypes[-1 * (this.accessID - 1)]
        }
      })
    }
  },
  created () {
    if (this.accessID === 0 && this.$route.params.accessType !== 'signup') {
      alert('url broken')
      this.$router.push('/')
    }
  }
}
</script>

<style lang="stylus" scoped>
h1, h2 {
  font-weight: normal;
}
ul {
  list-style-type: none;
  padding: 0;
}
li {
  display: inline-block;
  margin: 0 10px;
}
a {
  color: #42b983;
}
.signup {
  margin-top: 20px;

  display: flex;
  flex-flow: column nowrap;
  justify-content: center;
  align-items: center
}
input {
  margin: 10px 0;
  padding: 10px;
}
</style>
