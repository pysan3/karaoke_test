import numpy as np
import scipy as sp
from librosa.output import write_wav
import wave
import matplotlib.pyplot as plt
from time import time

import audio.music as backmusic
from audio import analyze

import cProfile

def detect_lag_length():
    with open('lag.txt', 'r') as f:
        lags = [(int(l.strip().split()[2]), int(l.strip().split()[3][1:-1])) for l in f.readlines()[2:]]
    lag = lags[0][0] * lags[0][1]
    count = lags[0][1]
    i = 1
    while abs(lags[i-1][0] - lags[i][0]) < 5:
        lag += lags[i][0] * lags[i][1]
        count += lags[i][1]
        i += 1
    lag /= count
    print(lag, i)
    x = np.arange(0, 256000 / 48000, 1.0 / 48000)
    with open('hoge.wav', 'rb') as f:
        data = f.read()
        hoge = np.frombuffer(data[44:], dtype='int16').astype(np.float32) / 32676
        hoge = hoge[:256000]
        plt.subplot(3, 1, 1)
        plt.plot(x, hoge)
    with open('audio/wav/8.wav', 'rb') as f:
        data = np.frombuffer(f.read()[44:], dtype='int16').astype(np.float32) / 32676
        data = data[:256000]
        plt.subplot(3, 1, 2)
        plt.plot(x, data)
    test = hoge[round(lag*512/4):]
    zero = []
    # check params
    y = sp.signal.firwin(511, 0.9)
    for i in range(0, len(test), 1024):
        zero.append(data[i:i+1024:3])
    zero = np.array(zero).flatten()
    # zero = np.zeros(256000)
    # delta = max(test) / max(data)
    # for i in range(len(test)):
    #     zero[i] = test[i] - data[i] * delta
    plt.subplot(3, 1, 3)
    plt.plot(zero)
    with wave.Wave_write('lag_correction.wav') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes((zero * 32676).astype(np.int16).tobytes('C'))
    plt.show()

def separate_whole_audio_data():
    unet = analyze.UNet()
    mag, phase, length = analyze.load_audio('audio/wav/fhana.wav')
    data = [[], []]
    start = time()
    for i in range(0, mag.shape[1], 1024):
        mask = analyze.compute_mask(unet, mag[:, i:i+1024])
        data[0].extend(analyze.save_audio(mag[:, i:i+1024]*mask, phase[:, i:i+1024]))
        data[1].extend(analyze.save_audio(mag[:, i:i+1024]*(1-mask), phase[:, i:i+1024]))
    for i in range(2):
        write_wav('data{0}.wav'.format(i), np.array(data[i][:length]), 16000, norm=True)
    print(time() - start)

def backmusic_upload():
    song_id = 100
    ftype = 'wav'
    with open('./audio/wav/fhana.wav', 'rb') as f:
        data = f.read()
    backmusic.upload(song_id, data, ftype)

def lag_estimation():
    with open('hoge.wav', 'rb') as f:
        data = np.frombuffer(f.read()[44:], dtype='int16').astype(np.float32) / 32676
    hsh, ptime = tuple(list(map(int, l.split())) for l in backmusic.create_hash(np.array(data[:1024*250])))
    with open('audio/wav/2.wav', 'rb') as f:
        data = np.frombuffer(f.read()[44:], dtype='int16').astype(np.float32) / 32676
    hsh_data, ptime_data = tuple(list(map(int, l.split())) for l in backmusic.create_hash(np.array(data[:1024*250])))
    print('here')
    print(analyze.lag_guess(hsh, ptime, hsh_data, ptime_data))

def downsampling_test():
    with wave.open('audio/wav/2.wav', 'r') as wf:
        print(wf.getframerate())
    with open('audio/wav/2.wav', 'rb') as f:
        data = np.frombuffer(f.read()[44:], dtype='int16').astype(np.float32) / 32676
    data = analyze.resampling(data, 48000, 16000)
    sp.io.wavfile.write('data.wav', 16000, data)
    with wave.open('data.wav', 'r') as wf:
        print(wf.getframerate())

def noise_detection(ntime):
    with open('hoge.wav', 'rb') as f:
        data = np.frombuffer(f.read()[44:], dtype='int16').astype(np.float32) / 32767
    start = int(ntime * 48000 / 1024)
    end = start + 1024 * 3
    noise_data = data[start:end]
    noise_data = analyze.resampling(noise_data, 48000, 16000)
    n_spec = sp.fft(noise_data * sp.hamming(1024))
    n_pow = sp.absolute(n_spec) ** 2
    start = 0
    result = []
    while True:
        end = start + 1024 * 3
        if end > len(data):
            break
        ndata = analyze.resampling(data[start:end], 48000, 16000)
        ndata = analyze.spectrum_subtraction(ndata, n_pow)
        result.extend(ndata)
        start = end
    v = (np.array(result) * 32767).astype(np.int16)
    with wave.Wave_write('result.wav') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(v.tobytes('C'))

def print_wav(filename):
    with open(filename + '.wav', 'rb') as f:
        data = np.frombuffer(f.read()[44:], dtype='int16').astype(np.float32) / 32767
    x = np.arange(0, len(data) / 48000, 1.0 / 48000)
    plt.plot(x, data)
    plt.show()

# separate_whole_audio_data()
# backmusic_upload()
# noise_reduction()
# lag_estimation()
# downsampling_test()
# noise_detection(3)
print_wav('result')

# main()
# pr = cProfile.Profile()
# pr.runcall(main)
# pr.print_stats()