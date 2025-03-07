import numpy as np

# 定数の設定
FS = 1000  # サンプリング周波数 (Hz)
WINDOW_LENGTH = 4096  # FFTの窓長


def preprocess_time_series(time_series):
    """時系列データを前処理する: 直流成分を削除し、Hanning窓を適用する"""
    time_series = time_series - np.mean(time_series)  # トレンドの除去
    windowed_series = time_series * np.hanning(
        len(time_series)
    )  # Hanning窓の適用
    return windowed_series


def pad_time_series(time_series, target_length=WINDOW_LENGTH):
    """データの長さが窓長より短い場合、後ろに0詰めを行う"""
    if len(time_series) < target_length:
        return np.pad(
            time_series, (0, target_length - len(time_series)), "constant"
        )
    else:
        return time_series[:target_length]


def compute_fft(time_series, win_len=WINDOW_LENGTH, fs=FS):
    """FFTを実行し、周波数とその振幅を取得する"""
    fft_result = np.fft.fft(time_series)
    freqs = np.fft.fftfreq(win_len, d=1 / fs)
    return freqs[: win_len // 2], 20 * np.log(
        np.abs(fft_result)[: win_len // 2]
    )
