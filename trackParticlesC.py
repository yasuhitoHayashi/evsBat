import pandas as pd
import argparse
import pickle
import os
from particle_tracking import track_particles_cpp  # C++ モジュールのインポート

parser = argparse.ArgumentParser(description='Particle tracking script.')
parser.add_argument('-i', '--input', required=True, help='Path to the input directory or file.')
args = parser.parse_args()

input_path = args.input

# 粒子トラッキング用のパラメータ
sigma_x = 6.0  # 空間的なスケールパラメータ, 精子は6, マリンスノー9
sigma_t = 10000.0  # 時間的なスケールパラメータ, 精子は10000,
gaussian_threshold = 0.8  # ガウス分布による閾値, 0.8くらいがよさそう
m_threshold = 500  # 質量のしきい値, 100くらい

def process_file(file_path):
    print(f"Processing file: {file_path}")
    
    # CSVファイル読み込み
    data_filtered = pd.read_csv(file_path, header=None, names=['x', 'y', 'polarity', 'time'])
    
    # posiデータに制限
    #data_filtered = data[data['polarity'] == 1].copy()
    
    data_list = [tuple(row) for row in data_filtered[['x', 'y', 'time']].itertuples(index=False, name=None)]
    
    print(f"Number of data points after filtering: {len(data_filtered)}")
    
    try:
        # C++の関数を呼び出す (sigma_x, sigma_t, gaussian_threshold を使用)
        particles = track_particles_cpp(data_list, sigma_x, sigma_t, gaussian_threshold, m_threshold)
    
        particle_output = {}
        for p in particles:
            particle_output[p.particle_id] = {
                'centroid_history': p.centroid_history,  # 重心座標 (x, y)
                'events': p.events       # 全イベント [(x, y, time), ...]
            }
    
        # インプットファイルと同じディレクトリにpickleファイルを保存
        output_file = os.path.join(os.path.dirname(file_path), f'particle_tracking_results_both_{os.path.basename(file_path).split(".")[0]}.pkl')
        with open(output_file, 'wb') as f:
            pickle.dump(particle_output, f)
    
        print(f"Particle tracking results saved to {output_file}")
    
    except Exception as e:
        print("An error occurred during the particle tracking process.")
        print(f"Error message: {e}")

# インプットがディレクトリの場合、ディレクトリ内の全てのCSVファイルを処理
if os.path.isdir(input_path):
    for filename in os.listdir(input_path):
        if filename.endswith('.csv'):
            file_path = os.path.join(input_path, filename)
            process_file(file_path)

# インプットがCSVファイルの場合、そのファイルを処理
elif os.path.isfile(input_path) and input_path.endswith('.csv'):
    process_file(input_path)

else:
    print("Invalid input. Please provide a valid CSV file or directory.")