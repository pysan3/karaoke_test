<template>
  <div>
    <h2>Select an music</h2>
      <input @change="onFileChange" type="file" name="file" accept="audio/*" capture="microphone">
      <audio id="player" controls></audio>
    <div id="byte_content"></div>
    <h2>data of music</h2>
    <h3>music name</h3>
    <input type="text" placeholder="music name" v-model="song_title">
    <h4>{{ song_title.length }}</h4>
    <br>
    <button @click="getRandom">New random number</button>
    <h3>singer name</h3>
    <input type="text" placeholder="name of singer" v-model="singer">
    <h4>{{ singer.length }}</h4>
    <h3>upload data type</h3>
    <input type="text" placeholder="file type" v-model="file_type">
    <button id="btn" @click="upload">upload music</button>
    <br>
    <h2>result</h2>
    <br>
    <div v-if="uploading === 1">
      <h3>uploading ...</h3>
    </div>
    <div v-else-if="uploading === 2">
      <button @click="sing">already exists</button>
    </div>
    <div v-else-if="uploading === 3">
      <button @click="sing">finished upload</button>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { mapState } from 'vuex'
export default {
  data () {
    return {
      song_title: '',
      singer: 'default',
      file_type: '',
      uploadFile: null,
      songID: 0,
      uploading: 0 // 0:none, 1:uploading, 2:samename, 3:finished
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
        this.song_title = fname.slice(0, -1).join('.')
        this.file_type = fname[fname.length - 1]
      }
      this.uploadFile = file
    },
    upload () {
      if (this.song_title.length * this.singer.length === 0) {
        alert('name should be longer than one letter')
        return
      }
      // functions
      const vm = this
      const checkExistence = async () => {
        await axios
          .post('http://localhost:5042/api/alreadyExists', {
            song_title: vm.song_title,
            singer: vm.singer
          })
          .then(response => {
            vm.songID = response.data.song_id - 0
          })
      }
      const uploadMusicData = () => {
        const formData = new FormData()
        formData.append('user_id', vm.user_id)
        formData.append('song_title', vm.song_title)
        formData.append('singer', vm.singer)
        formData.append('file_type', vm.file_type)
        formData.append('music', vm.uploadFile)
        const config = {
          headers: {
            'context-type': 'multipart/form-data'
          }
        }
        axios
          .post('http://localhost:5042/api/upload', formData, config)
          .then(response => {
            vm.songID = response.data.song_id
          })
      }
      const checkUpload = songID => {
        axios
          .get('http://localhost:5042/api/isUploaded/' + songID)
          .then(response => {
            if (response.data.isUploaded === 1) {
              clearInterval(interval)
              vm.uploading = 3
            }
          })
      }
      // program here
      let interval
      checkExistence().then(() => {
        if (this.songID) {
          this.uploading = 2
        } else {
          this.uploading = 1
          uploadMusicData()
          interval = setInterval(function () {
            checkUpload(vm.songID)
          }, 1000)
        }
      })
    },
    sing () {
      this.$router.push('/sing/' + this.songID)
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
