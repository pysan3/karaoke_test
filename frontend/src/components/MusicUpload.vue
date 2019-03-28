<template>
  <div>
    <h2>Select an music</h2>
      <input @change="onFileChange" type="file" name="file" accept="audio/*" capture="microphone">
      <audio id="player" controls></audio>
    <div id="byte_content"></div>
    <h2>data of music</h2>
    <h3>music name</h3>
    <button @click="getRandom">New random number</button>
    <br>
    <input type="text" placeholder="music name" v-model="song_title">
    <h3>singer name</h3>
    <input type="text" placeholder="name of singer" v-model="singer">
    <h3>upload data type</h3>
    <input type="text" placeholder="file type" v-model="file_type">
    <button id="btn" @click="upload">upload music</button>
    <br>
    <h1 v-if="uploading === 1">uploading ...</h1>
  </div>
</template>

<script>
import axios from 'axios'
import { mapState } from 'vuex'
export default {
  data () {
    return {
      song_title: 'hoge',
      singer: 'fhana',
      file_type: '',
      uploadFile: null,
      uploading: 0
    }
  },
  computed: mapState([
    'user_id'
  ]),
  methods: {
    onFileChange (e) {
      e.preventDefault()
      const file = e.target.files[0]
      const player = document.getElementById('player')
      player.src = URL.createObjectURL(file)
      let fname = file.name.split('.')
      if (fname.length !== 0) {
        let ftype = fname[fname.length - 1]
        fname = fname.slice(0, -1 - ftype.length)
        this.song_title = fname
        this.file_type = ftype
      }
      this.uploadFile = file
    },
    upload () {
      const vm = this
      if (this.song_title.length && this.singer.length) {
        alert('name should be longer than one letter')
        return
      }
      this.uploading = 1
      const formData = new FormData()
      formData.append('user_id', this.user_id)
      formData.append('song_title', this.song_title)
      formData.append('singer', this.singer)
      formData.append('file_type', this.file_type)
      formData.append('music', this.uploadFile)
      const config = {
        headers: {
          'context-type': 'multipart/form-data'
        }
      }
      axios.post('http://localhost:5042/api/upload', formData, config)
        .then(response => {
          const songID = response.data.song_id
          const checkUpload = songID => {
            axios.get('http://localhost:5042/api/isUploaded/' + songID)
              .then(response => {
                if (response.data.isUploaded === 1) {
                  clearInterval(interval)
                  vm.$router.push('/sing/' + songID)
                }
              })
              .catch(error => {
                console.log(error)
              })
          }
          const interval = setInterval(function () {
            checkUpload(songID)
          }, 1000)
        })
        .catch(error => {
          console.log(error)
        })
    },
    getRandom () {
      const path = 'http://localhost:5042/api/random'
      axios.get(path)
        .then(response => {
          this.song_title = response.data.randomNumber
        })
        .catch(error => {
          console.log(error)
        })
    }
  },
  created () {
    this.$store.dispatch('loggedin', 'musicupload')
  }
}
</script>
