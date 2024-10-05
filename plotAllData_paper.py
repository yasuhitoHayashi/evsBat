import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

# CSVファイルのパス
file_path = 'yubi_605.csv'

# CSVファイルの読み込み
data = pd.read_csv(file_path, header=None, names=['x', 'y', 'polarity', 'time'])
data['time'] = data['time'] * 1e-3
data = data[(data['time'] > 0) & (data['time'] < 2000)]

dataP = data[data['polarity'] == 1]
dataN = data[data['polarity'] == 0]

# プロットの作成
fig = plt.figure(figsize=(16, 10))

# 上段に2Dプロットを3つ配置
ax2d_1 = fig.add_subplot(231)
ax2d_2 = fig.add_subplot(232)
ax2d_3 = fig.add_subplot(233)

# 時間範囲でデータをフィルタリングして、XY平面にプロット
time_ranges = [(500, 550), (1000, 1050), (1500, 1550)]
colors = ['red', 'green', 'purple']  # 各時間範囲に対応する色
axes_2d = [ax2d_1, ax2d_2, ax2d_3]

for i, (start_time, end_time) in enumerate(time_ranges):
    filtered_data = dataP[(dataP['time'] >= start_time) & (dataP['time'] <= end_time)]
    
    # 各XY平面にプロット
    axes_2d[i].scatter(filtered_data['x'], filtered_data['y'], s=2, c=colors[i], edgecolors='none', marker='.')
    axes_2d[i].set_title(f'{start_time}ms - {end_time}ms')
    axes_2d[i].set_xlim([0, 1280])
    axes_2d[i].set_ylim([0, 720])
    axes_2d[i].set_xlabel('X Coordinate')
    axes_2d[i].set_ylabel('Y Coordinate')

# 下段に3Dプロットを配置
ax3d = fig.add_subplot(212, projection='3d')  # 2行目（下段）に大きな3Dプロットを配置
ax3d.scatter(dataP['time'], dataP['x'], dataP['y'], s=2, c='blue', edgecolors='none', marker='.')

# 各時間範囲を3Dボックスで塗りつぶす
for i, (start_time, end_time) in enumerate(time_ranges):
    # ボックスの面を構成するための頂点を設定
    verts = [
        # 前面
        [[start_time, 0, 0], [start_time, 1280, 0], [start_time, 1280, 720], [start_time, 0, 720]],
        # 背面
        [[end_time, 0, 0], [end_time, 1280, 0], [end_time, 1280, 720], [end_time, 0, 720]],
        # 左側面
        [[start_time, 0, 0], [start_time, 0, 720], [end_time, 0, 720], [end_time, 0, 0]],
        # 右側面
        [[start_time, 1280, 0], [start_time, 1280, 720], [end_time, 1280, 720], [end_time, 1280, 0]],
        # 底面
        [[start_time, 0, 0], [start_time, 1280, 0], [end_time, 1280, 0], [end_time, 0, 0]],
        # 上面
        [[start_time, 0, 720], [start_time, 1280, 720], [end_time, 1280, 720], [end_time, 0, 720]],
    ]
    
    # 透明色で各面を描画
    poly = Poly3DCollection(verts, color=colors[i], alpha=0.3)
    ax3d.add_collection3d(poly)

# ラベルの設定
ax3d.set_ylabel('X Coordinate')
ax3d.set_zlabel('Y Coordinate')
ax3d.set_xlabel('Time (milliseconds)')
ax3d.set_xlim([0, 2000])
ax3d.set_ylim([0, 1280])
ax3d.set_zlim([0, 720])

# レイアウトの調整
plt.tight_layout()
plt.show()