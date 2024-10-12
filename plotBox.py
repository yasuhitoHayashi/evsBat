import pandas as pd
import numpy as np
import pickle
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.gridspec as gridspec
import argparse
import os

# 引数の解析
parser = argparse.ArgumentParser(description='Particle tracking script.')
parser.add_argument('-i', '--input', required=True, help='Path to the input pickle file.')
args = parser.parse_args()

particle_output_file = args.input

with open(particle_output_file, 'rb') as f:
    particle_data = pickle.load(f)

# 最もイベント数が多い粒子を特定
max_particle_id = max(particle_data, key=lambda p: len(particle_data[p]['events']))
max_particle_info = particle_data[max_particle_id]
events = np.array(max_particle_info['events'])
event_times = events[:, 2] * 1e-3  # ミリ秒に変換

# イベントの描画設定
overall_sampling_ratio = 0.01  # 下段の全体プロット用
individual_sampling_ratio = 0.05  # 各時間範囲プロット用

# 図の作成（サイズを半分に設定）
fig = plt.figure(figsize=(8, 5))
gs = gridspec.GridSpec(3, 3, height_ratios=[1, 1, 2])  # 下段のプロットを2倍の高さに設定

# 上段に3Dプロットを3つ配置
ax3d_1 = fig.add_subplot(gs[0, 0], projection='3d')
ax3d_2 = fig.add_subplot(gs[0, 1], projection='3d')
ax3d_3 = fig.add_subplot(gs[0, 2], projection='3d')

# 下段に大きな3Dプロットを配置（2倍の高さ）
ax3d = fig.add_subplot(gs[1:, :], projection='3d')

# 時間範囲ごとに異なる色を設定
time_ranges = [(490, 550), (650, 740), (1020, 1150)]
colors = ['red', 'green', 'purple']
axes_3d = [ax3d_1, ax3d_2, ax3d_3]

# 対象時間範囲以外のイベントを灰色でプロット
excluded_mask = ~((event_times >= time_ranges[0][0]) & (event_times <= time_ranges[0][1]) |
                  (event_times >= time_ranges[1][0]) & (event_times <= time_ranges[1][1]) |
                  (event_times >= time_ranges[2][0]) & (event_times <= time_ranges[2][1]))

excluded_events = events[excluded_mask]
excluded_event_times = event_times[excluded_mask]

# 下段の全体イベントのダウンサンプリング
if overall_sampling_ratio < 1.0:
    sample_size = int(len(excluded_events) * overall_sampling_ratio)
    if sample_size > 0:
        sampled_indices = np.random.choice(len(excluded_events), sample_size, replace=False)
        sampled_excluded_events = excluded_events[sampled_indices]
        sampled_excluded_event_times = excluded_event_times[sampled_indices]
    else:
        sampled_excluded_events = excluded_events
        sampled_excluded_event_times = excluded_event_times
else:
    sampled_excluded_events = excluded_events
    sampled_excluded_event_times = excluded_event_times

ax3d.scatter(sampled_excluded_event_times, sampled_excluded_events[:, 0], sampled_excluded_events[:, 1], 
             c='gray', alpha=0.3, s=1, marker='.')

# 対象時間範囲ごとに個別プロットと強調表示
for i, (start_time, end_time) in enumerate(time_ranges):
    mask = (event_times >= start_time) & (event_times <= end_time)
    filtered_events = events[mask]
    filtered_event_times = event_times[mask]

    # ダウンサンプリング
    if individual_sampling_ratio < 1.0:
        sample_size = int(len(filtered_events) * individual_sampling_ratio)
        if sample_size > 0:
            sampled_indices = np.random.choice(len(filtered_events), sample_size, replace=False)
            sampled_events = filtered_events[sampled_indices]
            sampled_event_times = filtered_event_times[sampled_indices]
        else:
            sampled_events = filtered_events
            sampled_event_times = filtered_event_times
    else:
        sampled_events = filtered_events
        sampled_event_times = filtered_event_times

    # 上段の3Dプロット（Y-Z平面からの視点）
    axes_3d[i].scatter(sampled_event_times, sampled_events[:, 0], sampled_events[:, 1], s=2, c=colors[i], alpha=0.3, marker='.')
    axes_3d[i].view_init(elev=0, azim=90)
    axes_3d[i].set_xlim([start_time, end_time])
    axes_3d[i].set_ylim([sampled_events[:, 0].min() - 50, sampled_events[:, 0].max() + 50])
    axes_3d[i].set_zlim([sampled_events[:, 1].min() - 50, sampled_events[:, 1].max() + 50])
    axes_3d[i].set_title(f'{start_time}ms - {end_time}ms (Particle {max_particle_id})')
    axes_3d[i].set_xlabel('Time (milliseconds)')
    axes_3d[i].set_ylabel('X Coordinate')
    axes_3d[i].set_zlabel('Y Coordinate')

    # 下段の3Dプロット
    ax3d.scatter(sampled_event_times, sampled_events[:, 0], sampled_events[:, 1], c=colors[i], alpha=1, s=2, marker='.')

# 下段プロットのラベルと範囲設定
ax3d.set_xlabel('Time (milliseconds)')
ax3d.set_ylabel('X Coordinate')
ax3d.set_zlabel('Y Coordinate')
ax3d.set_xlim([0, 2000])
ax3d.set_ylim([0, 1280])
ax3d.set_zlim([720, 0])

plt.tight_layout()
plt.show()