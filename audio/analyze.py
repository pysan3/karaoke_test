import numpy as np
import scipy as sp
from librosa.core import load, stft, istft
from librosa.output import write_wav
from chainer import Chain, serializers, config
import chainer.links as L
import chainer.functions as F

class UNet(Chain):
    def __init__(self):
        super(UNet, self).__init__()
        with self.init_scope():
            self.conv1 = L.Convolution2D(1, 16, 4, 2, 1)
            self.norm1 = L.BatchNormalization(16)
            self.conv2 = L.Convolution2D(16, 32, 4, 2, 1)
            self.norm2 = L.BatchNormalization(32)
            self.conv3 = L.Convolution2D(32, 64, 4, 2, 1)
            self.norm3 = L.BatchNormalization(64)
            self.conv4 = L.Convolution2D(64, 128, 4, 2, 1)
            self.norm4 = L.BatchNormalization(128)
            self.conv5 = L.Convolution2D(128, 256, 4, 2, 1)
            self.norm5 = L.BatchNormalization(256)
            self.conv6 = L.Convolution2D(256, 512, 4, 2, 1)
            self.norm6 = L.BatchNormalization(512)
            self.deconv1 = L.Deconvolution2D(512, 256, 4, 2, 1)
            self.denorm1 = L.BatchNormalization(256)
            self.deconv2 = L.Deconvolution2D(512, 128, 4, 2, 1)
            self.denorm2 = L.BatchNormalization(128)
            self.deconv3 = L.Deconvolution2D(256, 64, 4, 2, 1)
            self.denorm3 = L.BatchNormalization(64)
            self.deconv4 = L.Deconvolution2D(128, 32, 4, 2, 1)
            self.denorm4 = L.BatchNormalization(32)
            self.deconv5 = L.Deconvolution2D(64, 16, 4, 2, 1)
            self.denorm5 = L.BatchNormalization(16)
            self.deconv6 = L.Deconvolution2D(32, 1, 4, 2, 1)
        serializers.load_npz('./audio/unet.model', self)

    def __call__(self, X):
        h1 = F.leaky_relu(self.norm1(self.conv1(X)))
        h2 = F.leaky_relu(self.norm2(self.conv2(h1)))
        h3 = F.leaky_relu(self.norm3(self.conv3(h2)))
        h4 = F.leaky_relu(self.norm4(self.conv4(h3)))
        h5 = F.leaky_relu(self.norm5(self.conv5(h4)))
        h6 = F.leaky_relu(self.norm6(self.conv6(h5)))
        dh = F.relu(F.dropout(self.denorm1(self.deconv1(h6))))
        dh = F.relu(F.dropout(self.denorm2(self.deconv2(F.concat((dh, h5))))))
        dh = F.relu(F.dropout(self.denorm3(self.deconv3(F.concat((dh, h4))))))
        dh = F.relu(self.denorm4(self.deconv4(F.concat((dh, h3)))))
        dh = F.relu(self.denorm5(self.deconv5(F.concat((dh, h2)))))
        dh = F.sigmoid(self.deconv6(F.concat((dh, h1))))
        return dh

def load_audio(fname):
    y = load(fname, sr=16000)[0]
    spec = stft(y, n_fft=1024, hop_length=512, win_length=1024)
    spec = np.pad(spec, [(0, 0), (0, 1024 - spec.shape[1] % 1024)], 'constant')
    mag = np.abs(spec)
    mag /= np.max(mag)
    phase = np.exp(1.j*np.angle(spec))
    return mag, phase, y.shape[0]

def compute_mask(unet, input_mag):
    config.train = False
    config.enable_backprop = False
    mask = unet(input_mag[np.newaxis, np.newaxis, 1:, :]).data[0, 0, :, :]
    mask = np.vstack((np.zeros(mask.shape[1], dtype='float32'), mask))
    return mask

def save_audio(mag, phase):
    return istft(mag * phase, hop_length=512, win_length=1024)

def find_peaks(data):
    sgram = np.abs(stft(data, n_fft=512, window='hamming'))
    neighborhood = sp.ndimage.morphology.iterate_structure(sp.ndimage.morphology.generate_binary_structure(2, 1), 8)
    sgram_max = sp.ndimage.maximum_filter(sgram, footprint=neighborhood, mode='constant')
    # => (peaks_freq, peaks_time)
    return np.asarray((sgram==sgram_max) & (sgram > 0.2)).nonzero()

def peaks_to_landmarks(peaks_freq, peaks_time):
    peak_mat = np.zeros((np.max(peaks_freq)+30, np.max(peaks_time)+260), dtype=np.bool)
    peak_mat[peaks_freq, peaks_time] = True
    list_hsh = []
    list_ptime = []
    for pfreq, ptime in zip(peaks_freq, peaks_time):
        target_mask = np.zeros(peak_mat.shape, dtype=np.bool)
        target_mask[(pfreq-30 if pfreq >= 30 else 0) : pfreq+30, ptime+20 : ptime+260] = True
        targets_freq, targets_time = np.asarray(peak_mat & target_mask).nonzero()
        for pfreq_target, ptime_target in zip(targets_freq, targets_time):
            dtime = ptime_target - ptime
            hsh = (((pfreq & 511)<<12) | ((pfreq_target&63)<<6) | (dtime&63))
            list_hsh.append(hsh)
            list_ptime.append(ptime)
    return ' '.join(map(str, list_hsh)), ' '.join(map(str, list_ptime))

def lag_guess(hsh, ptime, hsh_data, ptime_data):
    lag_dict = {0:0}
    for i in range(len(hsh)):
        if hsh[i] in hsh_data:
            lag = ptime[i] - ptime_data[hsh_data.index(hsh[i])]
            if lag in lag_dict.keys():
                lag_dict[lag] += 1
            else:
                lag_dict[lag] = 1
    if len(lag_dict) >= 3:
        poss_lag = sorted(lag_dict.values(), reverse=True)[:3]
        for i in range(2, 1, -1):
            if poss_lag[i] * 2 < poss_lag[i-1] or poss_lag[i] == 1:
                poss_lag = poss_lag[:i]
        lag_data = [(k, v) for k, v in lag_dict.items() if v in poss_lag]
        if np.array([l[0] for l in lag_data]).std() < 2:
            # let error of max 4 diffs
            return round(128 * sum([l[0] * l[1] for l in lag_data]) / sum(poss_lag))
    return False
    with open('lag.txt', 'w') as f:
        f.write('final lag = {0} ({1}), std = {2}\n'.format(lag, lag / 128, np.array([l[0] for l in lag_data]).std()))
        f.write('rank : lag (possibility) ... @{0}\n'.format(0))
        poss_lag = 2
        i = 1
        while poss_lag != 1 and i < 10:
            poss_lag = max(lag_dict.values())
            usual_lag = [k for k, v in lag_dict.items() if v == poss_lag][0]
            f.write('   {0} : {1} ({2})\n'.format(i, usual_lag, poss_lag))
            lag_dict.pop(usual_lag)
            i += 1

def downsampling(data, y):
    data = sp.signal.lfilter(y, 1, data)
    return data[0::3]

# TODO: find places with no vocal
# TODO: check whether user sing voice contains howling sounds
#       (subtracted data is smaller than sent data <=> sound will become bigger if only contains raw env noise)
# TODO: if yes: subtract original sound with suitable aspect
# TODO: noise reduction using stft and spectral subtraction

# TODO: get audio data without noise
# TODO: evaluate users song