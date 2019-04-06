<template>
  <div id="musiclist">
    <h3>music list</h3>
    <ul>
      <li v-for="item in mList" v-bind:key="item.id">
        <router-link v-bind:to="{name: 'sing', params: { song_id: item.song_id }}">{{ item.name }} {{ item.singer }}</router-link>
      </li>
    </ul>
    <router-link to="/musicupload">music upload</router-link>
  </div>
</template>

<script>
import axios from 'axios'
export default {
  data () {
    return {
      mList: []
    }
  },
  methods: {
    updateTable () {
      axios.get('http://localhost:5042/api/musiclist')
        .then(response => {
          this.mList = []
          const list = JSON.parse(response.data)
          for (var i = 0, l = list.length; i < l; ++i) {
            const jsonData = {
              'song_id': list[i][0],
              'name': list[i][1],
              'singer': list[i][2],
              'count': list[i][3]
            }
            this.mList.push(jsonData)
          }
        })
        .catch(error => {
          console.log(error)
        })
    }
  },
  created () {
    this.updateTable()
  }
}
</script>

<style lang="stylus">
#musiclist {
  font-family: "Avenir", Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  /*text-align: center;*/
  color: #2c3e50;
  margin: 20px auto 0;
  /* width: 800px; */
}
</style>
