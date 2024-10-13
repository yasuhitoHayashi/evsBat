import particle_tracking
import pickle
import argparse
import os

# コマンドライン引数の設定
parser = argparse.ArgumentParser(description='Particle tracking using C++ extension with raw input files.')
parser.add_argument('-i', '--input', required=True, help='Path to the input raw file or directory.')
args = parser.parse_args()
input_path = args.input

# トラッキングパラメータの設定
sigma_x = 6.0  # 空間的スケール
sigma_t = 10000.0  # 時間的スケール
gaussian_threshold = 0.8  # ガウス分布の閾値
m_threshold = 500  # 質量のしきい値

# ファイル処理関数
def process_file(file_path):
    print(f"Processing file: {file_path}")
    
    # 粒子追跡を実行 (C++で直接.rawファイルを処理)
    results = particle_tracking.track_particles_from_raw(file_path, sigma_x, sigma_t, gaussian_threshold, m_threshold)
    
    # 結果を辞書形式で保存
    output = {result.particle_id: {'centroid_history': result.centroid_history, 'events': result.events} for result in results}
    
    # 結果をpickleファイルに保存
    output_file = os.path.splitext(file_path)[0] + '_tracking_results.pkl'
    with open(output_file, 'wb') as f:
        pickle.dump(output, f)
    
    print(f"Results saved to {output_file}")

# 指定されたファイルまたはディレクトリを処理
if os.path.isfile(input_path) and input_path.endswith('.raw'):
    process_file(input_path)
elif os.path.isdir(input_path):
    for file_name in os.listdir(input_path):
        if file_name.endswith('.raw'):
            process_file(os.path.join(input_path, file_name))
else:
    print("Invalid input path. Please provide a valid .raw file or directory.")