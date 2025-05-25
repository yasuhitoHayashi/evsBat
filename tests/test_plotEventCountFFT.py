import os
from plotEventCountFFT import read_pickles, process_pickle_file


def test_read_pickles():
    files = read_pickles("sampleData", "windowed_fft_results")
    assert any(f.endswith("_peaks.txt") for f in files) or files == []


def test_process_pickle_file_output():
    pkl = "sampleData/particle_tracking_results_recording_2023-09-14_20-42-19_39.pkl"
    result = process_pickle_file(pkl)
    assert result is not None
    assert len(result) > 0
