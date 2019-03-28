<template>
  <div>
    <button id='btn'>press here</button>
    <h2 v-if="isReady === 1">ready</h2>
  </div>
</template>

<script>
import { mapState } from 'vuex'
export default {
  data () {
    return {
      song_id: this.$route.params.song_id,
      isReady: 0
    }
  },
  computed: mapState([
    'user_id'
  ]),
  methods: {
    getMusic () {
      window.AudioContext = window.AudioContext || window.webkitAudioContext
      const vm = this
      let context = null
      let connection = null
      let request = new XMLHttpRequest()
      request.responseType = 'arraybuffer'
      request.onreadystatechange = () => {
        if (request.readyState === 4) {
          if (request.status === 0 || request.status === 200) {
            const responseData = request.response
            const btn = document.getElementById('btn')
            btn.onclick = () => {
              context = new AudioContext()
              const p = context.decodeAudioData(responseData)
              connection = new WebSocket('ws://localhost:5042/ws/sing')
              connection.onopen = event => {
                console.log(event)
                connection.send(JSON.stringify({
                  user_id: vm.user_id,
                  song_id: vm.song_id,
                  framerate: context.sampleRate
                }))
                p.then(buffer => {
                  playSound(buffer)
                })
              }
            }
            vm.isReady = 1
          } else if (request.status === 500) {
            request = null
            alert('error occured')
            vm.$router.push({ name: 'musiclist' })
          }
        }
      }
      const playSound = buffer => {
        const vm = this
        const p = navigator.mediaDevices.getUserMedia({ audio: true, video: false })
        const src = context.createBufferSource()
        src.buffer = buffer
        src.connect(context.destination)
        p.then(stream => {
          src.onended = () => {
            stream.getTracks().forEach(track => {
              track.stop()
            })
            const isDone = () => {
              if (connection.bufferedAmount === 0) {
                clearInterval(interval)
                connection.close()
                connection = null
                vm.$router.push('/user')
              }
            }
            stream = null
            const interval = setInterval(isDone, 1000)
          }
          handleSuccess(stream)
          src.start(0)
        })
      }
      const handleSuccess = stream => {
        const wsContext = new AudioContext()
        const input = wsContext.createMediaStreamSource(stream)
        const processor = wsContext.createScriptProcessor(1024, 1, 1)
        input.connect(processor)
        processor.connect(wsContext.destination)
        processor.onaudioprocess = e => {
          const voice = e.inputBuffer.getChannelData(0)
          if (connection !== null) {
            connection.send(voice.buffer)
          }
        }
      }
      request.open('GET', 'http://localhost:5042/audio/load_music/' + this.user_id + '_' + this.song_id, true)
      request.send()
    }
  },
  created () {
    this.$store.dispatch('loggedin', 'sing-' + this.song_id)
    this.getMusic()
  }
}
</script>
