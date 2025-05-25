import numpy as np
from detect_peaks import peak_detection, custom_peak_detection, detect_wingfreq


def test_peak_detection_multiple_peaks():
    freqs = np.array([0, 5, 10, 15, 20, 25, 30], dtype=float)
    amplitudes = np.array([1, 2, 10, 2, 9, 2, 1], dtype=float)
    peaks, max_idx = peak_detection(amplitudes, freqs)
    assert max_idx == 2
    assert set(peaks) == {2, 4}


def test_custom_peak_detection():
    freqs = np.array([0, 5, 10, 15, 20], dtype=float)
    amplitudes = np.array([0, 5, 20, 5, 0], dtype=float)
    result = custom_peak_detection(amplitudes, freqs)
    assert result and 2 in result[0]


def test_detect_wingfreq_prefer_half():
    wing = detect_wingfreq([4.5, 18], 9.0)
    assert wing == 4.5
