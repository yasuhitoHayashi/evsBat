import numpy as np

# Set constants
FS = 1000  # Sampling frequency (Hz)
WINDOW_LENGTH = 4096  # FFT window length


def preprocess_time_series(time_series):
    """Preprocess the time series: remove DC component and apply Hanning window"""
    time_series = time_series - np.mean(time_series)  # Remove trend
    windowed_series = time_series * np.hanning(
        len(time_series)
    )  # Apply Hanning window
    return windowed_series


def pad_time_series(time_series, target_length=WINDOW_LENGTH):
    """If the data length is shorter than the window length, pad with zeros at the end"""
    if len(time_series) < target_length:
        return np.pad(
            time_series, (0, target_length - len(time_series)), "constant"
        )
    else:
        return time_series[:target_length]


def compute_fft(time_series, win_len=WINDOW_LENGTH, fs=FS):
    """Perform FFT and obtain frequency and its amplitude"""
    fft_result = np.fft.fft(time_series)
    freqs = np.fft.fftfreq(win_len, d=1 / fs)
    return freqs[: win_len // 2], 20 * np.log(
        np.abs(fft_result)[: win_len // 2]
    )
