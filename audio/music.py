import numpy as np
import scipy as sp
import wave
import os
from time import sleep
from glob import glob
import sox

from audio import analyze

def load_music(song_id):
    if song_id in [s[12:-4] for s in glob('./audio/wav/*.wav')]:
        with open('./audio/wav/{0}.wav'.format(song_id), 'rb') as f:
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
    with open('./audio/vocal/{0}.wav'.format(song_id), 'rb') as f:
        vocal = np.frombuffer(f.read()[44:], dtype='int16')
    # TODO: get silent part from vocal data -> noise_time
    noise_time = 1
    with open('./audio/wav/{0}.wav'.format(song_id), 'rb') as f:
        data = np.frombuffer(f.read()[44:], dtype='int16')[:1024*250]
    return create_hash(data.astype(np.float32) / 32676) + (noise_time,)

def create_hash(data):
    f, t = analyze.find_peaks(data)
    return analyze.peaks_to_landmarks(f, t)
    # => list_hsh, list_ptime (both in str)

class WebSocketApp:
    def __init__(self, tpl):
        self.data = []
        self.counter = [0, 0]
        self.lag = False
        self.hsh_data = [int(i) for i in tpl[0].split()]
        self.ptime = [int(i) for i in tpl[1].split()]
        self.noise = tpl[2]

    def upload(self, stream):
        self.data.extend(np.frombuffer(stream, dtype='float32'))
        self.counter[0] += 1

    def lag_estimate(self):
        hsh, ptime = tuple(list(map(int, l.split())) for l in create_hash(np.array(self.data[:1024*250])))
        lag_dict = {0:0}
        for i in range(len(hsh)):
            if hsh[i] in self.hsh_data:
                lag = ptime[i] - self.ptime[self.hsh_data.index(hsh[i])]
                if lag in lag_dict.keys():
                    lag_dict[lag] += 1
                else:
                    lag_dict[lag] = 1
        self.lag = True
        if len(lag_dict) >= 3:
            poss_lag = sorted(lag_dict.values(), reverse=True)[:3]
            for i in range(2, 1, -1):
                if poss_lag[i] * 3 < poss_lag[i-1] or poss_lag[i] == 1:
                    poss_lag = poss_lag[:i]
            lag_data = [(k, v) for k, v in lag_dict.items() if v in poss_lag]
            if np.array([l[0] for l in lag_data]).std() < 2:
                # let error of max 4 diffs
                self.lag = round(128 * sum([l[0] * l[1] for l in lag_data]) / sum(poss_lag))
        # TODO: erase below before publication
        with open('lag.txt', 'w') as f:
            f.write('final lag = {0} ({1}), std = {2}\n'.format(self.lag, self.lag / 128, np.array([l[0] for l in lag_data]).std()))
            f.write('rank : lag (possibility) ... @{0}\n'.format(self.counter))
            poss_lag = 2
            i = 1
            while poss_lag != 1 and i < 10:
                poss_lag = max(lag_dict.values())
                usual_lag = [k for k, v in lag_dict.items() if v == poss_lag][0]
                f.write('   {0} : {1} ({2})\n'.format(i, usual_lag, poss_lag))
                lag_dict.pop(usual_lag)
                i += 1

    def noise_reduction(self):
        # get noise spectrum
        while self.counter[0] != -self.counter[1]:
            if self.counter[0] == self.counter[1]:
                sleep(1)
                continue
            start = 1024 * self.counter[1] + self.lag
            end = start + 1024
            if start < 0:
                l = [0 for i in range(-self.lag)] + self.data[0:end]
            else:
                l = self.data[start:end]
            # make list of len 1024 to nr
            # self._sub(list) <- analyze? func for reduce noise ([audio data, 1024] -> [audio data, 1024])
            self.counter[1] += 1

    def return_counter(self):
        return abs(self.counter[0])

    def close(self, info):
        if self.lag > 0:
            self.data.extend([0 for i in range(self.lag)])
        self.counter[0] *= -1
        v = (np.array(self.data) * 32767).astype(np.int16)
        with wave.Wave_write('hoge.wav') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(info['framerate'])
            wf.writeframes(v.tobytes('C'))
        print(self.lag)
