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


def test_peak_detection_no_significant_peaks():
    freqs = np.array([0, 2, 4, 6, 8], dtype=float)
    amplitudes = np.array([1, 1.5, 2, 2.5, 3], dtype=float)
    peaks, max_idx = peak_detection(amplitudes, freqs)
    assert len(peaks) == 0
    assert max_idx == []


def test_custom_peak_detection_strong_single_peak():
    freqs = np.array([0, 4, 5, 6, 7, 8, 9], dtype=float)
    amplitudes = np.array([0, 5, 10, 22, 6, 5, 4], dtype=float)
    indices, dominant = custom_peak_detection(amplitudes, freqs)
    assert 3 in indices
    assert dominant == 3


def test_custom_peak_detection_filters_out_of_band():
    freqs = np.array([0, 1, 2, 3, 4, 5, 6], dtype=float)
    amplitudes = np.array([0, 5, 10, 22, 6, 5, 4], dtype=float)
    result = custom_peak_detection(amplitudes, freqs)
    assert result == []


def test_detect_wingfreq_selects_closest_half():
    wing = detect_wingfreq([4.2, 4.9, 17.5], 9.0)
    assert wing == 4.2


def test_detect_wingfreq_defaults_to_max_without_harmonics():
    wing = detect_wingfreq([12.0, 15.0, 33.0], 18.0)
    assert wing == 18.0
