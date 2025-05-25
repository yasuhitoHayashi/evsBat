import pandas as pd
import numpy as np
import glob
import pickle
import matplotlib.pyplot as plt
from scipy.fft import fft, fftfreq
from scipy.signal import find_peaks
import argparse
import os

from time_fft_to_pdf import *
from process_fft import *
from detect_peaks import *


parser = argparse.ArgumentParser(description="Particle tracking script.")
parser.add_argument(
    "-i",
    "--input",
    required=True,
    help="Path to the input pickle file or directory.",
)
args = parser.parse_args()
input_path = args.input
# FOLDERS = ["momojiro"]
# DATA_LABELS = [
#     "$Myotis\\ macrodactylus$",
# ]

# FOLDERS = ["kiku", "yubi", "momojiro"]
# DATA_LABELS = [
#     "$Rhinolophus\\ nippon$",
#     "$Miniopterus\\ fuliginosus$",
#     "$Myotis\\ macrodactylus$",
# ]
FOLDERS = ["move_objects"]
DATA_LABELS = [
    "$moveing\\ objects$",
]


def read_pickles(input_path, folder_name):
    files = glob.glob(f"{input_path}/{folder_name}/*.pkl")

    return files


def process_pickle_file(particle_output_file):
    output_directory = os.path.dirname(particle_output_file)

    # 出力フォルダ (fft_results) を作成
    fft_results_dir = os.path.join(output_directory, "windowed_fft_results")
    os.makedirs(
        fft_results_dir, exist_ok=True
    )  # 既に存在していてもエラーを出さない

    # ファイル名の処理: 前から3つ目の "_" より後の部分を使い、".pkl"を除去
    base_filename = os.path.basename(particle_output_file)
    base_filename = "_".join(base_filename.split("_")[3:]).replace(".pkl", "")

    with open(particle_output_file, "rb") as f:
        particle_data = pickle.load(f)

    # イベント数が最大の粒子を抽出
    # max_particle_id = max(
    #     particle_data, key=lambda p: len(particle_data[p]["events"])
    # )
    # particle_info = particle_data[max_particle_id]
    particle_info = particle_data
    event_coords = np.array(particle_info)

    # ミリ秒に変換
    event_times = event_coords[:, 2] * 1e-3

    # 最小時間と最大時間を取得
    min_time, max_time = np.min(event_times), np.max(event_times)

    # 1ミリ秒単位の時間ビンを作成
    time_bin_size = 1  # ms
    time_bins = np.arange(min_time, max_time + time_bin_size, time_bin_size)

    # 各時間ビンでのイベント数を計算
    event_counts, _ = np.histogram(event_times, bins=time_bins)

if os.path.isdir(input_path):
    # ディレクトリ内のすべてのファイルを処理
    all_peak_freqs = []
    dict_peak_freqs = {}
    dict_file_names = {}
    for folder_name in FOLDERS:
        pickle_list = read_pickles(input_path, folder_name)
        event_num_list = []
        folder_peak_freqs = []
        folder_file_names = []
        for pkl_data in pickle_list:
            base_name = os.path.basename(pkl_data)
            print(f"Processing file: {base_name}")
            event_num_arr = process_pickle_file(pkl_data)
            freqs, fft_magnitude = calc_fft(event_num_arr)
            peak_indices, max_peak_idx = calc_peak(freqs, fft_magnitude)
            if len(peak_indices) == 0:
                event_num_list.append(event_num_arr)
                folder_peak_freqs.append(np.nan)
                folder_file_names.extend([base_name])
            else:
                peak_freqs = freqs[peak_indices]
                max_peak_freq = freqs[max_peak_idx]
                peak_freqs = detect_wingfreq(peak_freqs, max_peak_freq)
                folder_peak_freqs.append(round(peak_freqs, 1))
                folder_file_names.extend([base_name])
                event_num_list.append(event_num_arr)

        dict_peak_freqs[folder_name] = folder_peak_freqs
        dict_file_names[folder_name] = folder_file_names

        all_peak_freqs.append(folder_peak_freqs)

        output_pdf_path = os.path.join(
            input_path, f"{folder_name}_analysis.pdf"
        )
        plot_and_save_time_series_fft_to_pdf(
            folder_name, event_num_list, folder_file_names, output_pdf_path
        )

    # バイオリンプロットを1つのPDFに保存
    violin_pdf_path = os.path.join(input_path, "peak_frequency_comparison.pdf")
    plot_and_save_violin_to_pdf(all_peak_freqs, violin_pdf_path, DATA_LABELS)

    # データをcsvに保存 (ピーク周波数とファイル名を含める)
    df_peak_freqs = pd.DataFrame(
        dict([(k, pd.Series(v)) for k, v in dict_peak_freqs.items()])
    )
    print(df_peak_freqs)
    df_file_names = pd.DataFrame(
        dict([(k + "_file", pd.Series(v)) for k, v in dict_file_names.items()])
    )

    # ファイル名とピーク周波数を結合して1つのデータフレームに
    df_combined = pd.concat([df_peak_freqs, df_file_names], axis=1)

    # 結果を"peak_freqs.csv"に保存
    df_combined.to_csv(os.path.join(input_path, "peak_freqs.csv"))

elif os.path.isfile(input_path) and input_path.endswith(".pkl"):
    # 単一ファイルを処理
    print(f"Processing file: {input_path}")
    process_pickle_file(input_path)
else:
    print(f"Error: {input_path} is not a valid pickle file or directory.")
