import numpy as np
import wave
import os
from time import sleep
from glob import glob
import sox

from audio import analyze

def load_music(song_id, audio_type):
    if song_id in [s[9 + len(audio_type):-4] for s in glob('./audio/{0}/*.wav'.format(audio_type))]:
        with open('./audio/{0}/{1}.wav'.format(audio_type, song_id), 'rb') as f:
            return f.read()
    else:
        return False

def upload(song_id, data, ftype):
    with open('./audio/wav/tmp_{0}.{1}'.format(song_id, ftype), 'wb') as f:
        f.write(data)
    tfm = sox.Transformer()
    tfm.set_output_format(file_type='wav', rate=48000, bits=16, channels=1)
    if tfm.build('./audio/wav/tmp_{0}.{1}'.format(song_id, ftype), './audio/wav/{0}.wav'.format(song_id)):
        os.remove('./audio/wav/tmp_{0}.{1}'.format(song_id, ftype))
        separate_audio(song_id)
        return True
    else:
        return False

def separate_audio(song_id):
    unet = analyze.UNet()
    mag, phase, length = analyze.load_audio('./audio/wav/{0}.wav'.format(song_id))
    vocal = []
    inst = []
    for i in range(0, mag.shape[1], 1024):
        mask = analyze.compute_mask(unet, mag[:, i:i+1024])
        vocal.extend(analyze.save_audio(mag[:, i:i+1024]*mask, phase[:, i:i+1024]))
        inst.extend(analyze.save_audio(mag[:, i:i+1024]*(1-mask), phase[:, i:i+1024]))
    analyze.write_wav('./audio/vocal/{0}.wav'.format(song_id), np.array(vocal[:length]), 16000, norm=True)
    analyze.write_wav('./audio/inst/{0}.wav'.format(song_id), np.array(inst[:length]), 16000, norm=True)

def upload_hash(song_id):
    noise_t = analyze.noise_time(song_id)
    with open('./audio/wav/{0}.wav'.format(song_id), 'rb') as f:
        data = np.frombuffer(f.read()[44:], dtype='int16')[:1024*250]
    return create_hash(data.astype(np.float32) / 32676) + (noise_t,)

def create_hash(data):
    f, t = analyze.find_peaks(data)
    return analyze.peaks_to_landmarks(f, t)
    # => list_hsh, list_ptime (both in str)

class WebSocketApp:
    def __init__(self, tpl):
        self.data = []
        self.result = []
        self.counter = [0, 0]
        self.lag = False
        self.hsh_data = [int(i) for i in tpl[0].split()]
        self.ptime = [int(i) for i in tpl[1].split()]
        self.noise = tpl[2]

    def upload(self, stream):
        self.data.extend(np.frombuffer(stream, dtype='float32'))
        self.counter[0] += 1

    def lag_estimate(self, median):
        hsh, ptime = tuple(list(map(int, l.split())) for l in create_hash(np.array(self.data[:1024*250])))
        self.lag = analyze.lag_guess(hsh, ptime, self.hsh_data, self.ptime)
        lag = self.lag or median
        if lag < 0:
            self.data = [0]*lag + self.data
        elif lag > 0:
            self.data = self.data[lag:]
        return lag

    def noise_reduction(self):
        if self.counter[0] - 3 >= 48000 * self.noise / 1024:
            start = (self.counter[0] - 3) * 1024
            end = start + 1024 * 3
            noise_data = self.data[start:end]
            noise_data = analyze.resampling(noise_data, 48000, 16000)
            n_spec = sp.fft(noise_data * sp.hamming(1024))
            n_pow = sp.absolute(n_spec) ** 2.0
        # get noise spectrum
        while self.counter[0] != -self.counter[1]:
            if self.counter[0] == self.counter[1]:
                sleep(1)
                continue
            start = 1024 * self.counter[1]
            end = start + 1024 * 3
            data = analyze.resampling(self.data[start:end], 48000, 16000)
            data = analyze.spectrum_subtraction(data, n_pow)
            # self._sub(list) <- analyze? func for reduce noise ([audio data, 1024] -> [audio data, 1024])
            self.result.extend(data)
            self.counter[1] += 3

    def return_counter(self):
        return abs(self.counter[0])

    def close(self, info):
        self.counter[0] *= -1
        v = (np.array(self.data) * 32767).astype(np.int16)
        with wave.Wave_write('hoge.wav') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(info['framerate'])
            wf.writeframes(v.tobytes('C'))
        v = (np.array(self.result) * 32767).astype(np.int16)
        with wave.Wave_write('result.wav') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(v.tobytes('C'))
