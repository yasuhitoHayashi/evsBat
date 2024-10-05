import pandas as pd
import numpy as np
import pickle
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import argparse

parser = argparse.ArgumentParser(description='Particle tracking script.')
parser.add_argument('-i', '--input', required=True, help='Path to the input CSV file.')
args = parser.parse_args()

particle_output_file = args.input

with open(particle_output_file, 'rb') as f:
    particle_data = pickle.load(f)

# イベント数の閾値
event_threshold = 1000

# プロット用にイベントを抽出
sampling_ratio = 0.1

# イベントをプロットするか否かのフラグ  
plot_events = True  # Falseにすることで、重心のみをプロット

# Create a 3D plot using Matplotlib
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# 粒子の軌跡とイベントをプロット
for particle_id, particle_info in particle_data.items():
    if 'centroid_history' in particle_info:
        centroid_history = np.array(particle_info['centroid_history'])  # (time, centroid_x, centroid_y)

        # 重心の履歴、1以上あるかどうか
        if len(centroid_history) > 1:
            # 重心の軌跡をプロット
            ax.plot(centroid_history[:, 0] * 1e-3, centroid_history[:, 1], centroid_history[:, 2], label=f'Particle {particle_id} Centroid Trajectory')

    # フラグがTrueの場合、イベントをプロット
    if plot_events:
        events = particle_info['events']
        event_coords = np.array(events)
        event_times = event_coords[:, 2] * 1e-3  # Convert event times to milliseconds

        # 描画のためのダウンサンプリング
        num_events = len(events)
        if sampling_ratio < 1.0:
            sample_size = int(num_events * sampling_ratio)
            if sample_size > 0:
                sampled_indices = np.random.choice(num_events, sample_size, replace=False)
                sampled_events = event_coords[sampled_indices]
                sampled_event_times = event_times[sampled_indices]
                
                # Scatter plot
                ax.scatter(sampled_event_times, sampled_events[:, 0], sampled_events[:, 1], alpha=0.3, marker='.')
        else:
            # ダウンサンプリングしない場合
            ax.scatter(event_times, event_coords[:, 0], event_coords[:, 1], alpha=0.3, marker='.')

ax.set_ylabel('X Coordinate')
ax.set_zlabel('Y Coordinate')
ax.set_xlabel('Time (milliseconds)')

#ax.set_xlim([0, 1000])
ax.set_ylim([0, 1280])
ax.set_zlim([720, 0])

plt.show()