import numpy as np
from process_fft import preprocess_time_series, pad_time_series, compute_fft, WINDOW_LENGTH, FS


def test_preprocess_time_series():
    arr = np.array([1, 2, 3, 4, 5], dtype=float)
    result = preprocess_time_series(arr)
    expected = (arr - np.mean(arr)) * np.hanning(len(arr))
    assert np.allclose(result, expected)


def test_pad_time_series_short_and_long():
    arr_short = np.array([1, 2, 3], dtype=float)
    padded = pad_time_series(arr_short, target_length=5)
    assert len(padded) == 5
    assert np.allclose(padded[:3], arr_short)
    assert np.all(padded[3:] == 0)

    arr_long = np.arange(10, dtype=float)
    trimmed = pad_time_series(arr_long, target_length=5)
    assert len(trimmed) == 5
    assert np.allclose(trimmed, arr_long[:5])


def test_compute_fft_peak():
    t = np.arange(WINDOW_LENGTH) / FS
    freq = 5.0
    signal = np.sin(2 * np.pi * freq * t)
    freqs, magnitude = compute_fft(signal)
    dominant = freqs[np.argmax(magnitude)]
    assert abs(dominant - freq) < 0.5
