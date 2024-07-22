import pandas as pd
import pickle
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

# サンプリング率（0 < sampling_rate <= 1）
sampling_rate = 1

# Pickleファイルのパス
pkl_file_path = 'clustering_bat_results.pkl'
pkl_file_posi_path = 'clustering_bat_Posi_results.pkl'

# Pickleファイルの読み込み
with open(pkl_file_path, 'rb') as f:
    results_df = pickle.load(f)

with open(pkl_file_posi_path, 'rb') as f:
    results_posi_df = pickle.load(f)

print("Pickleファイルの読み込みに成功しました")

# 全データの抽出
all_points = np.concatenate(results_df['cluster_points'].values)
all_points_ = np.concatenate(results_posi_df['cluster_points'].values)

# データをサンプリング
np.random.seed(0)  # 再現性のために乱数シードを固定
sample_indices = np.random.choice(all_points.shape[0], int(all_points.shape[0] * sampling_rate), replace=False)
sample_indices_ = np.random.choice(all_points_.shape[0], int(all_points_.shape[0] * sampling_rate), replace=False)

sampled_points = all_points[sample_indices]
sampled_points_ = all_points_[sample_indices_]

# 3次元プロットの作成
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')

# サンプリングされたデータをプロット
scatter1 = ax.scatter(sampled_points[:, 2] * 1e-3, sampled_points[:, 0], sampled_points[:, 1], s=1, c='blue',edgecolors='none' , alpha=0.5, label='Negative Event',marker='.')
scatter2 = ax.scatter(sampled_points_[:, 2] * 1e-3, sampled_points_[:, 0], sampled_points_[:, 1], s=1, c='black',edgecolors='none' , alpha=1, label='Positive Event',marker='.')

# 軸ラベルの設定
ax.set_xlabel('Time (ms)', fontsize=12, color='black')
ax.set_ylabel('X (pix)', fontsize=12, color='black')
ax.set_zlabel('Y (pix)', fontsize=12, color='black')

# 軸の範囲設定
ax.set_ylim(0, 1280)
ax.set_zlim(720, 0)
ax.set_xlim(0, 1500)

# 背景色の設定
fig.patch.set_facecolor('white')
ax.set_facecolor('white')

# グリッドと軸の色の設定
ax.grid(color='gray', linestyle='-', linewidth=0.5)
ax.xaxis.label.set_color('black')
ax.yaxis.label.set_color('black')
ax.zaxis.label.set_color('black')
ax.tick_params(axis='x', colors='black')
ax.tick_params(axis='y', colors='black')
ax.tick_params(axis='z', colors='black')
ax.view_init(elev=10, azim=-30)

# レジェンドの追加
legend = ax.legend(loc='upper right', fontsize=10)
legend.get_frame().set_facecolor('white')
legend.get_frame().set_edgecolor('black')
for text in legend.get_texts():
    text.set_color('black')

# タイトルの追加
ax.set_title('3D Cluster Visualization', color='black', fontsize=15)

# プロットの保存
plt.savefig('yubi_605.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.show()