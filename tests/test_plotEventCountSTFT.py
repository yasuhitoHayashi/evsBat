from plotEventCountSTFT import read_pickles, process_pickle_file, calc_fft, calc_peak


def test_calc_fft_and_peak():
    pkl = "sampleData/particle_tracking_results_recording_2023-09-14_20-42-19_39.pkl"
    data = process_pickle_file(pkl)
    freqs, values = calc_fft(data)
    peaks, max_idx = calc_peak(freqs, values)
    assert len(freqs) == len(values)
    assert max_idx >= 0
