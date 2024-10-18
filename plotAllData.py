import pandas as pd
import numpy as np
import pickle
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import argparse
import os

# コマンドライン引数の設定
parser = argparse.ArgumentParser(description='Particle tracking script.')
parser.add_argument('-i', '--input', help='Path to the input pickle file.')
args = parser.parse_args()

# デフォルトのpickleファイルのパス
default_pickle_path = './sampleData/particle_tracking_results_recording_2023-09-14_20-42-19_39.pkl'
pickle_file_path = args.input if args.input else default_pickle_path

# CSVファイルのパス
csv_file_path = './sampleData/recording_2023-09-14_20-42-19_39.csv'

# CSVファイルの読み込み
csv_data = pd.read_csv(csv_file_path, header=None, names=['x', 'y', 'polarity', 'time'])
csv_data['time'] = csv_data['time'] * 1e-3

dataP = csv_data[csv_data['polarity'] == 1]
dataN = csv_data[csv_data['polarity'] == 0]

# pickleファイルの読み込み
with open(pickle_file_path, 'rb') as f:
    particle_data = pickle.load(f)

# プロットの作成
fig = plt.figure(figsize=(14, 7))

# 左上：CSVファイルのデータプロット
ax1 = fig.add_subplot(221, projection='3d')
ax1.scatter(dataP['time'], dataP['x'], dataP['y'], s=2, c='orange', alpha=1, edgecolors='none', marker='o')
ax1.scatter(dataN['time'], dataN['x'], dataN['y'], s=2, c='blue', alpha=1, edgecolors='none', marker='.')
ax1.set_xlabel('Time (milliseconds)')
ax1.set_ylabel('X Coordinate')
ax1.set_zlabel('Y Coordinate')
ax1.set_ylim([0, 1280])
ax1.set_zlim([720, 0])

# 左下：pickleファイルのデータプロット
ax2 = fig.add_subplot(223, projection='3d')
sampling_ratio = 0.1
plot_events = True

for particle_id, particle_info in particle_data.items():
    if 'centroid_history' in particle_info:
        centroid_history = np.array(particle_info['centroid_history'])

        if len(centroid_history) > 1:
            ax2.plot(centroid_history[:, 0] * 1e-3, centroid_history[:, 1], centroid_history[:, 2], label=f'Particle {particle_id} Centroid Trajectory')

    if plot_events:
        events = particle_info['events']
        event_coords = np.array(events)
        event_times = event_coords[:, 2] * 1e-3

        num_events = len(events)
        if sampling_ratio < 1.0:
            sample_size = int(num_events * sampling_ratio)
            if sample_size > 0:
                sampled_indices = np.random.choice(num_events, sample_size, replace=False)
                sampled_events = event_coords[sampled_indices]
                sampled_event_times = event_times[sampled_indices]
                ax2.scatter(sampled_event_times, sampled_events[:, 0], sampled_events[:, 1], alpha=0.3, marker='.')
        else:
            ax2.scatter(event_times, event_coords[:, 0], event_coords[:, 1], alpha=0.3, marker='.')

ax2.set_xlabel('Time (milliseconds)')
ax2.set_ylabel('X Coordinate')
ax2.set_zlabel('Y Coordinate')
ax2.set_ylim([0, 1280])
ax2.set_zlim([720, 0])

# イベント数が最大の粒子を抽出
max_particle_id = max(particle_data, key=lambda p: len(particle_data[p]['events']))
particle_info = particle_data[max_particle_id]
event_coords = np.array(particle_info['events'])

# ミリ秒に変換
event_times = event_coords[:, 2] * 1e-3
x_coords = event_coords[:, 0]
y_coords = event_coords[:, 1]

# 右上：1ms間隔で5つの時間データを重ねてプロット
ax3 = fig.add_subplot(222, projection='3d')
start_times = [560, 600, 640, 680, 720, 760, 805, 845, 910]  # 任意の時間範囲
colors = ['black', 'blue', 'green', 'red', 'purple', 'orange', 'brown', 'pink', 'gray']

for i, start_time in enumerate(start_times):
    end_time = start_time + 5
    filtered_indices = (event_times >= start_time) & (event_times < end_time)
    ax3.scatter(event_times[filtered_indices], x_coords[filtered_indices], y_coords[filtered_indices],
                s=2, c=colors[i], alpha=1, edgecolors='none', marker='.')

ax3.set_xlabel('Time (milliseconds)')
ax3.set_ylabel('X Coordinate')
ax3.set_zlabel('Y Coordinate')
ax3.set_xlim([0, 1450])
ax3.set_ylim([0, 500])
ax3.set_zlim([720, 500])
ax3.set_box_aspect([4, 1, 1])  # x軸: y軸: z軸のアスペクト比を調整
ax3.view_init(elev=30, azim=-120)  # 視点を調整してz軸が斜めになるように

# 右下：イベント数のプロット（サイズを小さく）
ax4 = fig.add_subplot(224)
min_time, max_time = np.min(event_times), np.max(event_times)
time_bin_size = 1  # ms
time_bins = np.arange(min_time, max_time + time_bin_size, time_bin_size)
event_counts, _ = np.histogram(event_times, bins=time_bins)

ax4.plot(time_bins[:-1], event_counts, label='Event Count', linewidth=2)
ax4.set_xlabel('Time (milliseconds)')
ax4.set_ylabel('Number of Events')
ax4.set_xlim([0, 1450])

# ハイライトする時間範囲を塗りつぶし
for i, start_time in enumerate(start_times):
    end_time = start_time + 5
    ax4.axvspan(start_time, end_time, color=colors[i], alpha=0.5)

ax4.grid(True)
plt.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.02, hspace=0.05, wspace=0.05)

# 右下プロットのサイズと位置調整（小さくする）
ax3.set_position([0.4, 0.4, 0.5, 0.6])
ax4.set_position([0.5, 0.1, 0.3, 0.3])

# 視点の設定
elev = 13  # 仰角
azim = -75  # 方位角
ax1.view_init(elev=30, azim=-70)
ax2.view_init(elev=30, azim=-70)
ax3.view_init(elev=20, azim=-50)

plt.show()

#plt.savefig("./sampleData/plotAllData.png")
#plt.close()