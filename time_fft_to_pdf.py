import os
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages
from scipy.signal import spectrogram

from process_fft import *
from detect_peaks import *


sns.set(
    "paper",
    "whitegrid",
    "bright",
    font_scale=1.5,
    rc={"lines.linewidth": 3, "grid.linestyle": "--"},
)


def plot_and_save_time_series_fft_to_pdf(
    folder_name, data_list, folder_file_names, output_pdf_path
):
    """選択したCSVファイルの時系列データとFFT結果をPDFに保存する"""
    with PdfPages(output_pdf_path) as pdf:
        for i in range(0, len(data_list), 5):
            fig, axes = plt.subplots(5, 2, figsize=(15, 20))

            for j in range(5):
                if i + j >= len(data_list):
                    break

                time_series = data_list[i + j]
                data_name = os.path.basename(folder_file_names[i + j])

                # 時系列データのプロット
                axes[j, 0].plot(time_series)
                axes[j, 0].set_title(f"{data_name}")
                axes[j, 0].set_xlabel("Time [ms]")
                axes[j, 0].set_ylabel("Number of pixel")

                # FFTの計算とプロット
                preprocessed_series = preprocess_time_series(time_series)
                padded_series = pad_time_series(preprocessed_series)
                freqs, fft_magnitude = compute_fft(padded_series)

                # カスタムピーク検知
                peak_indices, _ = peak_detection(fft_magnitude, freqs)
                peak_freqs = freqs[peak_indices]
                peak_values = fft_magnitude[peak_indices]

                # FFT結果のプロット
                axes[j, 1].plot(freqs, fft_magnitude)
                axes[j, 1].set_xlim((0, 30))
                axes[j, 1].set_xlabel("Frequency [Hz]")
                axes[j, 1].set_ylabel("Amplitude")

                # 検出されたピークをプロット
                if len(peak_freqs) > 0:
                    axes[j, 1].plot(peak_freqs, peak_values, "rx")
                    axes[j, 1].set_title(
                        f"a peak is {round(peak_freqs[0], 1)} [Hz]"
                    )

            plt.tight_layout()
            pdf.savefig(fig)
            plt.close(fig)


def plot_and_save_time_series_stft_to_pdf(
    folder_name, data_list, output_pdf_path
):
    """
    folder_name: ファイル名のリスト
    data_list: 時系列データのリスト
    output_pdf_path: 出力PDFのパス

    folder_nameごとのdata_listをstft処理をしてプロットしてPDFに保存
    """
    target_data_len = 300  # fftする対象データの長さ [ms]
    shift_length = 128  # スライドする長さ [ms]
    window_length = 256  # 窓長（0づめしたあとの長さ）
    with PdfPages(output_pdf_path) as pdf:
        for i in range(0, len(data_list), 5):
            fig, axes = plt.subplots(5, 2, figsize=(15, 20))

            for j in range(5):
                if i + j >= len(data_list):
                    break

                time_series = data_list[i + j]

                # 時系列データのプロット
                axes[j, 0].plot(time_series)
                axes[j, 0].set_title(f"{folder_name} - Time Series {i + j + 1}")
                axes[j, 0].set_xlabel("Time [ms]")
                axes[j, 0].set_ylabel("Number of pixel")

                event_num_arr = preprocess_time_series(time_series)
                f, t, Sxx = spectrogram(
                    event_num_arr,
                    fs=1000,
                    nperseg=window_length,
                    noverlap=window_length - shift_length,
                )
                axes[j, 1].pcolormesh(
                    t, f, 10 * np.log10(Sxx), shading="gouraud"
                )
                # fig.colorbar(label="Power (dB)")
                axes[j, 1].set_title("Spectrogram")
                axes[j, 1].set_ylabel("Frequency [Hz]")
                axes[j, 1].set_xlabel("Time [s]")
                axes[j, 1].set_ylim(0, 25)
                axes[j, 1].legend()
                # windows_num = (
                #     len(event_num_arr) - target_data_len
                # ) // shift_len + 1
                # stft_peaks = []
                # for i in range(windows_num):
                #     if len(event_num_arr) < i * shift_len + windows_len:
                #         target_arr = event_num_arr[
                #             i * shift_len + windows_len :
                #         ]
                #         padded_series = pad_time_series(target_arr)
                #     else:
                #         target_arr = event_num_arr[
                #             i * shift_len
                #             + windows_len : (i + 1) * shift_len
                #             + windows_len
                #         ]
                #         padded_series = pad_time_series(target_arr)
                #     freqs, fft_magnitude = compute_fft(padded_series)

                #     # カスタムピーク検知
                #     peak_indices, _ = peak_detection(fft_magnitude, freqs)

                #     print(f"STFT peaks: {peak_indices}")
                #     peak_freqs = freqs[peak_indices]
                #     peak_values = fft_magnitude[peak_indices]
                #     stft_peaks.append([peak_freqs, peak_values])

                # for peak in stft_peaks:
                #     if peak is None:
                #         continue
            #             axes[j, 1].plot(stft_peaks)

            #             axes[j, 1].set_title(f"{folder_name} - peaks {i + j + 1}")
            #             axes[j, 1].set_xlabel("frame")
            #             axes[j, 1].set_ylabel("Frequency [Hz]")
            #             axes[j, 1].set_xlim((0, 30))
            #             axes[j, 1].legend()
            plt.tight_layout()
            pdf.savefig(fig)
            plt.close(fig)


def plot_and_save_violin_to_pdf(all_peak_freqs, output_pdf_path, data_labels):
    """バイオリンプロットを作成して1つのPDFに保存"""
    with PdfPages(output_pdf_path) as pdf:
        fig, ax = plt.subplots(figsize=(4, 6))
        # sns.violinplot(
        #     data=all_peak_freqs, palette="muted", inner=None, ax=ax, alpha=0.6
        # )
        # all_peak_freqs = [
        #     9.13,
        #     453.26,
        #     8.59,
        #     403.12,
        #     8.97,
        #     19.14,
        #     12.04,
        #     10.89,
        #     None,
        #     19.28,
        #     None,
        #     20.74,
        #     388.84,
        #     11.82,
        #     19.74,
        #     19.35,
        #     19.70,
        #     283.62,
        #     7.27,
        #     None,
        #     None,
        #     None,
        #     None,
        #     None,
        # ]
        sns.stripplot(
            data=all_peak_freqs,
            color="k",
            size=8,
            jitter=True,
            alpha=1,
            marker="^",
            ax=ax,
        )
        ax.set_xticks(range(len(data_labels)))
        ax.set_xticklabels(data_labels)
        ax.set_xlabel("evsCluster")
        ax.set_ylabel("Estimated wingbeat frequency [Hz]")
        ax.set_ylim((0, 25))
        # ax.set_title("Peak Frequency Comparison (0 - 30 Hz)")
        plt.tight_layout()
        pdf.savefig(fig)
        plt.savefig("fw_evsCluster_1.png")
        plt.close(fig)
