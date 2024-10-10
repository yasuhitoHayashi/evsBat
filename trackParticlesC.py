import argparse
import pickle
import os
from particle_tracking import track_particles_from_stream  # C++ モジュールの新しい関数をインポート

parser = argparse.ArgumentParser(description='Particle tracking script using AEStream.')
parser.add_argument('-i', '--input', required=True, help='Path to the input directory or file.')
args = parser.parse_args()

input_path = args.input

# 粒子トラッキング用のパラメータ
sigma_x = 6.0  # 空間的なスケールパラメータ
sigma_t = 10000.0  # 時間的なスケールパラメータ
gaussian_threshold = 0.8  # ガウス分布による閾値
m_threshold = 500  # 質量のしきい値

def process_file(file_path):
    print(f"Processing file: {file_path}")
    
    try:
        # C++の関数を呼び出す（AEStreamによる逐次処理）
        particles = track_particles_from_stream(file_path, sigma_x, sigma_t, gaussian_threshold, m_threshold)
    
        particle_output = {}
        for p in particles:
            particle_output[p.particle_id] = {
                'centroid_history': p.centroid_history,  # 重心座標 (x, y)
                'events': p.events       # 全イベント [(x, y, time), ...]
            }
    
        # 出力ファイルのパス
        output_file = os.path.join(os.path.dirname(file_path), f'particle_tracking_results_both_{os.path.basename(file_path).split(".")[0]}.pkl')
        with open(output_file, 'wb') as f:
            pickle.dump(particle_output, f)
    
        print(f"Particle tracking results saved to {output_file}")
    
    except Exception as e:
        print("An error occurred during the particle tracking process.")
        print(f"Error message: {e}")

# ディレクトリ内の全てのイベントファイルを処理
if os.path.isdir(input_path):
    for filename in os.listdir(input_path):
        if filename.endswith('.dat') or filename.endswith('.raw'):  # AEStreamが扱うファイル拡張子
            file_path = os.path.join(input_path, filename)
            process_file(file_path)

# 単一のイベントファイルを処理
elif os.path.isfile(input_path) and (input_path.endswith('.dat') or input_path.endswith('.raw')):
    process_file(input_path)

else:
    print("Invalid input. Please provide a valid event file or directory.")
