def resample(data, orig_sr, target_sr):
    if orig_sr == target_sr:
        return data

    axis = -1
    ratio = float(target_sr) / orig_sr
    size = int(np.ceil(y.shape[-1] * ratio))

    data = resampy.resample(data, orig_sr, target_sr, filter='kaiser_best', axis=axis)

    n = data.shape[axis]
    if n > size:
        slices = [slice(None)] * data.ndim
        slices[axis] = slice(0, size)
        data = data[tuple(slices)]
    elif n < size:
        lengths = [(0, 0)] * data.ndim
        lengths[axis] = (0, size - n)
        data = np.pad(data, lengths, 'constant')

    return np.ascontiguousarray(y_hat, dtype=y.dtype)
