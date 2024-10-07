import pandas as pd
import numpy as np
import pickle
import matplotlib.pyplot as plt
from scipy.fft import fft, fftfreq
from scipy.signal import find_peaks
import argparse
import os

parser = argparse.ArgumentParser(description='Particle tracking script.')
parser.add_argument('-i', '--input', required=True, help='Path to the input pickle file or directory.')
args = parser.parse_args()

def process_pickle_file(particle_output_file):
    output_directory = os.path.dirname(particle_output_file)
    
    # 出力フォルダ (fft_results) を作成
    fft_results_dir = os.path.join(output_directory, 'windowed_fft_results')
    os.makedirs(fft_results_dir, exist_ok=True)  # 既に存在していてもエラーを出さない
    
    # ファイル名の処理: 前から3つ目の "_" より後の部分を使い、".pkl"を除去
    base_filename = os.path.basename(particle_output_file)
    base_filename = '_'.join(base_filename.split('_')[3:]).replace('.pkl', '')

    with open(particle_output_file, 'rb') as f:
        particle_data = pickle.load(f)

    # イベント数が最大の粒子を抽出
    max_particle_id = max(particle_data, key=lambda p: len(particle_data[p]['events']))
    particle_info = particle_data[max_particle_id]
    event_coords = np.array(particle_info['events'])

    # ミリ秒に変換
    event_times = event_coords[:, 2] * 1e-3

    # 最小時間と最大時間を取得
    min_time, max_time = np.min(event_times), np.max(event_times)

    # 1ミリ秒単位の時間ビンを作成
    time_bin_size = 1  # ms
    time_bins = np.arange(min_time, max_time + time_bin_size, time_bin_size)

    # 各時間ビンでのイベント数を計算
    event_counts, _ = np.histogram(event_times, bins=time_bins)

    # ハミングウィンドウを適用
    window = np.hamming(len(event_counts))
    event_counts_windowed = event_counts * window

    # FFT計算
    N = len(event_counts)  # イベント数
    T = time_bin_size / 1000.0  # サンプリング間隔 (s)
    fft_result = fft(event_counts_windowed)  # FFT結果（ウィンドウ適用後）
    fft_amplitude = np.abs(fft_result)  # 振幅
    fft_freq = fftfreq(N, T)  # 周波数軸

    # ポジティブな周波数のみを取得
    fft_freq = fft_freq[:N//2]
    fft_amplitude = fft_amplitude[:N//2]

    # ピークを見つける
    peaks, properties = find_peaks(fft_amplitude, height=np.max(fft_amplitude) * 0.05)  # 10% threshold for peaks
    peak_frequencies = fft_freq[peaks]
    peak_amplitudes = fft_amplitude[peaks]
    peak_heights = properties['peak_heights'] / np.max(fft_amplitude) * 100  # 正規化して高さを％で計算

    # ピークが存在するか確認する
    if len(peaks) > 0:
        # ピークの中で最大のものを特定
        max_height_index = np.argmax(peak_heights)
    else:
        # ピークがない場合は処理をスキップ
        print(f"No peaks found in file: {particle_output_file}")
        return

    # ピーク情報をテキストファイルに保存
    output_txt_file = os.path.join(fft_results_dir, f'{base_filename}_fft_peaks.txt')
    with open(output_txt_file, 'w') as f:
        f.write("Frequency [Hz]\tAmplitude\tHeight [%]\n")
        for freq, amp, height in zip(peak_frequencies, peak_amplitudes, peak_heights):
            f.write(f"{freq:.2f}\t{amp:.2f}\t{height:.2f}\n")
    print(f"Peak data saved to {output_txt_file}")

    plt.figure(figsize=(20, 5))

    # 左側にイベント数のプロット
    plt.subplot(1, 2, 1)
    plt.plot(time_bins[:-1], event_counts, label='Event Count', linewidth=2)
    plt.xlabel('Time (milliseconds)')
    plt.ylabel('Number of Events')
    plt.title(f'Event Count over Time for Particle {max_particle_id} - {base_filename}')
    plt.grid(True)

    # 右側にFFTのプロット
    plt.subplot(1, 2, 2)
    plt.plot(fft_freq, 20 * np.log10(fft_amplitude), label='FFT Amplitude (dB)', linewidth=2)
    plt.scatter(fft_freq[peaks], 20 * np.log10(fft_amplitude[peaks]), color='red', marker='v', label='Peaks')
    # dBスケールを使わない場合
    #plt.plot(fft_freq, fft_amplitude, label='FFT Amplitude', linewidth=2)
    #plt.scatter(fft_freq[peaks], fft_amplitude[peaks], color='red', marker='v', label='Peaks')

    # ピークの描画 (最大のものだけ赤、それ以外は黒)
    for i, peak in enumerate(peaks):
        freq = fft_freq[peak]
        amplitude = 20 * np.log10(fft_amplitude[peak])

        if i == max_height_index:
            # 最大のピークは赤
            plt.scatter(freq, amplitude, color='red', marker='v', label='Max Peak')
            plt.text(freq, amplitude + 2, f'{freq:.2f} Hz', fontsize=10, color='red', ha='center')
        else:
            # その他のピークは黒
            plt.scatter(freq, amplitude, color='black', marker='v', label='Peak')
            plt.text(freq, amplitude + 2, f'{freq:.2f} Hz', fontsize=10, color='black', ha='center')

    plt.xscale('log')
    plt.xlabel('Frequency [Hz]')
    plt.ylabel('Amplitude [dB]')
    plt.title(f'FFT of Event Counts - {base_filename}')
    plt.grid(True)

    # PNGファイルとして保存
    output_image_file = os.path.join(fft_results_dir, f'{base_filename}_fft_analysis.png')
    plt.tight_layout()
    plt.savefig(output_image_file)
    plt.close()
    print(f"FFT plot saved to {output_image_file}")

input_path = args.input

if os.path.isdir(input_path):
    # ディレクトリ内のすべてのファイルを処理
    for filename in os.listdir(input_path):
        if filename.endswith('.pkl'):
            file_path = os.path.join(input_path, filename)
            print(f"Processing file: {file_path}")
            process_pickle_file(file_path)
elif os.path.isfile(input_path) and input_path.endswith('.pkl'):
    # 単一ファイルを処理
    print(f"Processing file: {input_path}")
    process_pickle_file(input_path)
else:
    print(f"Error: {input_path} is not a valid pickle file or directory.")