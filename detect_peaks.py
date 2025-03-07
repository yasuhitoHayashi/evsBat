import numpy as np
from scipy.signal import find_peaks

# 定数の設定
FILTER_LOW = 4.0  # フィルタリングの下限周波数
FILTER_HIGH = 30.0  # フィルタリングの上限周波数


def peak_detection(fft_amplitude, fft_freq):
    # 周波数を制限
    freq_mask = (fft_freq >= FILTER_LOW) & (fft_freq <= FILTER_HIGH)
    # fft_freq = fft_freq[freq_mask]
    # fft_amplitude = fft_amplitude[freq_mask]
    filter_idx = np.where(freq_mask)
    fft_amplitude = fft_amplitude[filter_idx]
    min_area_idx = filter_idx[0][0]
    # ピークを見つける
    peaks, _ = find_peaks(
        fft_amplitude, height=np.max(fft_amplitude) * 0.95
    )  # 10% threshold for peaks

    peak_heights = fft_amplitude[peaks]
    # peaks = peaks + min_area_idx

    # peak_frequencies = fft_freq[peaks]
    # peak_amplitudes = fft_amplitude[peaks]
    # peak_heights = (
    #     properties["peak_heights"][peaks] / np.max(fft_amplitude) * 100
    # )
    if len(peaks) > 1:
        print(f"multiple peaks found in this file")
        # ピークの中で最大のものを特定
        max_height_index = peaks[np.argmax(peak_heights)] + min_area_idx
        top_2_indices = np.argsort(peak_heights)[-2:][::-1]
        peaks = peaks[top_2_indices] + min_area_idx
    elif len(peaks) == 1:
        print(f"A peak found in this file")
        max_height_index = peaks[np.argmax(peak_heights)] + min_area_idx
        peaks = peaks + min_area_idx
    else:
        # ピークがない場合は処理をスキップ
        print(f"No peaks found in this file")
        peaks = peaks + min_area_idx
        max_height_index = []

    return peaks, max_height_index


def custom_peak_detection(fft_amp, fft_fq):
    increase_cnter = 0
    last_amp_point = fft_amp[0]
    list_peak_idx = []

    for i, amp_point in enumerate(fft_amp):
        if amp_point > last_amp_point:
            increase_cnter += 1
        elif increase_cnter >= 1:
            fq = fft_fq[i - 1]
            top_fq = fq * 2
            bottom_fq = fq / 2
            peak_flg = 1

            avg_amp = 0.0
            tmp_cnter = 0
            for j, fq_point in enumerate(fft_fq):
                if fq_point <= bottom_fq:
                    continue
                elif top_fq < fq_point:
                    increase_cnter = 0
                    break
                elif i == j:
                    continue

                if fft_amp[j] > last_amp_point:
                    peak_flg = 0
                    if j < i:
                        increase_cnter = 0
                    break

                avg_amp += fft_amp[j]
                tmp_cnter += 1

            if peak_flg:
                avg_amp /= tmp_cnter
                amp_diff = last_amp_point - avg_amp
                if (amp_diff > 10.0) and (amp_diff != np.inf):
                    list_peak_idx.append(i - 1)
                    increase_cnter = 0

        last_amp_point = amp_point

    if list_peak_idx:
        # 4 - 30Hzの範囲で最も値が大きなピークのみを抽出
        valid_peak_indices = [
            idx
            for idx in list_peak_idx
            if FILTER_LOW <= fft_fq[idx] <= FILTER_HIGH
        ]
        if valid_peak_indices:

            max_peak_idx = max(valid_peak_indices, key=lambda idx: fft_amp[idx])
            # return [max_peak_idx]
            return valid_peak_indices, max_peak_idx
    return []


def detect_wingfreq(peak_freqs: list, max_peak_freq: float):
    double_freq = [
        peak_freq
        for peak_freq in peak_freqs
        if (max_peak_freq - 1) * 2 <= peak_freq <= (max_peak_freq + 1) * 2
    ]
    half_freq = [
        peak_freq
        for peak_freq in peak_freqs
        if (max_peak_freq - 1) / 2 <= peak_freq <= (max_peak_freq + 1) / 2
    ]
    if len(double_freq) >= 2:
        diff_f = 100
        idx = 0
        for i, f in enumerate(double_freq):
            diff_f_calc = f - max_peak_freq * 2
            if diff_f > diff_f_calc:
                diff_f = diff_f_calc
                idx = i
        double_freq = double_freq[idx]

    elif len(double_freq) == 1:
        double_freq = double_freq[0]

    if len(half_freq) >= 2:
        diff_f = 100
        idx = 0
        for i, f in enumerate(half_freq):
            diff_f_calc = f - max_peak_freq / 2
            if diff_f > diff_f_calc:
                diff_f = diff_f_calc
                idx = i
        half_freq = half_freq[idx]

    elif len(half_freq) == 1:
        half_freq = half_freq[0]

    if half_freq:
        wingfreq = half_freq
    elif double_freq:
        wingfreq = max_peak_freq
    else:
        wingfreq = max_peak_freq

    return wingfreq
