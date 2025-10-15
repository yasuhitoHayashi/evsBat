import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import argparse
import os

plt.rcParams.update({
    'lines.linewidth': 2,
    'grid.linestyle': '--',
    'axes.grid': True,
    'axes.facecolor': 'white',
    'axes.edgecolor': 'gray',
    'font.size': 11,
    'axes.labelsize': 14,
    'xtick.labelsize': 11,
    'ytick.labelsize': 11,
    'figure.figsize': (12, 8),
})

parser = argparse.ArgumentParser(description='Plot all events from CSV files.')
parser.add_argument('-i', '--input', required=True, help='Path to the input CSV file or directory.')
args = parser.parse_args()

sampling_ratio = 0.5

def process_csv_file(csv_file, outputs_dir):
    os.makedirs(outputs_dir, exist_ok=True)

    data = pd.read_csv(csv_file, header=None, names=['x', 'y', 'polarity', 'time'])
    data['time'] *= 1e-3

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')

    colors = {1: 'black', 0: 'gray'}
    for polarity, group_data in data.groupby('polarity'):
        group_points = group_data[['time', 'x', 'y']].to_numpy()

        num_events = len(group_points)
        if sampling_ratio < 1.0:
            sample_size = int(num_events * sampling_ratio)
            if sample_size > 0:
                sampled_indices = np.random.choice(num_events, sample_size, replace=False)
                sampled_points = group_points[sampled_indices]

                ax.scatter(sampled_points[:, 0], sampled_points[:, 1], sampled_points[:, 2], c=colors.get(polarity, 'gray'), marker='.', alpha=0.3)
        else:
            ax.scatter(group_points[:, 0], group_points[:, 1], group_points[:, 2], c=colors.get(polarity, 'gray'), marker='.', alpha=0.3)

    ax.set_xlabel('Time (milliseconds)')
    ax.set_ylabel('X Coordinate (pixels)')
    ax.set_zlabel('Y Coordinate (pixels)')

    ax.set_xlim([data['time'].min(), data['time'].max()])
    ax.set_ylim([0, 1280])
    ax.set_zlim([720, 0])
    ax.view_init(elev=4, azim=-40)

    ax.legend()

    base_filename = os.path.splitext(os.path.basename(csv_file))[0]
    output_image_file = os.path.join(outputs_dir, f'{base_filename}_all.png')
    plt.tight_layout()
    plt.savefig(output_image_file)
    plt.close()


input_path = args.input

if os.path.isdir(input_path):
    outputs_dir = os.path.join(input_path, 'outputs')
    for filename in os.listdir(input_path):
        if filename.endswith('.csv'):
            file_path = os.path.join(input_path, filename)
            print(f"Processing file: {file_path}")
            process_csv_file(file_path, outputs_dir)
elif os.path.isfile(input_path) and input_path.endswith('.csv'):
    outputs_dir = os.path.join(os.path.dirname(input_path), 'outputs')
    print(f"Processing file: {input_path}")
    process_csv_file(input_path, outputs_dir)
else:
    print(f"Error: {input_path} is not a valid CSV file or directory.")
