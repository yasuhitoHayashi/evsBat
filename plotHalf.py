import numpy as np
import pickle
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

parser = argparse.ArgumentParser(description='Plot paired upper/lower event trajectories.')
parser.add_argument('-i', '--input', required=True, help='Path to the directory containing upper and lower folders.')
parser.add_argument('--2d', dest='plot_2d', action='store_true', help='Plot in 2D instead of 3D.')
args = parser.parse_args()

def load_points(events_path):
    with open(events_path, 'rb') as f:
        events = np.asarray(pickle.load(f), dtype=np.float32)
    if events.size == 0:
        return np.empty((0, 3), dtype=np.float32)
    return np.column_stack((events[:, 2] * 1e-3, events[:, 0], events[:, 1]))

def process_event_pair(upper_file, lower_file, outputs_dir, plot_2d=False):
    upper_points = load_points(upper_file)
    lower_points = load_points(lower_file)

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111) if plot_2d else fig.add_subplot(111, projection='3d')

    if plot_2d:
        has_upper = upper_points.size > 0
        has_lower = lower_points.size > 0
        if has_upper:
            ax.scatter(upper_points[:, 1], upper_points[:, 2], c='gray', marker='.', alpha=0.3, label='Upper Events')
        if has_lower:
            ax.scatter(lower_points[:, 1], lower_points[:, 2], c='red', marker='.', alpha=0.3, label='Lower Events')
        ax.set_xlabel('X Coordinate (pixels)')
        ax.set_ylabel('Y Coordinate (pixels)')
        ax.set_xlim([0, 1280])
        ax.set_ylim([720, 0])
    else:
        has_upper = upper_points.size > 0
        has_lower = lower_points.size > 0
        if has_upper:
            ax.scatter(upper_points[:, 0], upper_points[:, 1], upper_points[:, 2], c='gray', marker='.', alpha=0.3, label='Upper Events')
        if has_lower:
            ax.scatter(lower_points[:, 0], lower_points[:, 1], lower_points[:, 2], c='red', marker='.', alpha=0.3, label='Lower Events')
        ax.set_xlabel('Time (milliseconds)')
        ax.set_ylabel('X Coordinate (pixels)')
        ax.set_zlabel('Y Coordinate (pixels)')

        if has_upper or has_lower:
            all_times = np.concatenate((upper_points[:, 0], lower_points[:, 0]))
        else:
            all_times = np.array([])
        if all_times.size:
            ax.set_xlim([float(all_times.min()), float(all_times.max())])
        ax.set_ylim([0, 1280])
        ax.set_zlim([720, 0])
        ax.view_init(elev=4, azim=-40)

    if (upper_points.size > 0) or (lower_points.size > 0):
        ax.legend()
    plt.tight_layout()

    os.makedirs(outputs_dir, exist_ok=True)
    base_name = os.path.basename(upper_file).replace('_upper.pkl', '')
    if not base_name:
        base_name = os.path.splitext(os.path.basename(upper_file))[0]
    output_image_file = os.path.join(outputs_dir, f'{base_name}_trajectory.png')
    plt.savefig(output_image_file)
    plt.close(fig)


def process_directory(input_directory, outputs_dir, plot_2d=False):
    upper_dir = os.path.join(input_directory, 'upper')
    lower_dir = os.path.join(input_directory, 'lower')

    if not os.path.isdir(upper_dir) or not os.path.isdir(lower_dir):
        print("Error: 'upper' and 'lower' directories do not exist in the specified path.")
        return

    upper_files = sorted(f for f in os.listdir(upper_dir) if f.endswith('_upper.pkl'))
    lower_files = sorted(f for f in os.listdir(lower_dir) if f.endswith('_lower.pkl'))

    upper_map = {f.replace('_upper.pkl', ''): os.path.join(upper_dir, f) for f in upper_files}
    lower_map = {f.replace('_lower.pkl', ''): os.path.join(lower_dir, f) for f in lower_files}

    common_keys = sorted(set(upper_map.keys()) & set(lower_map.keys()))
    if not common_keys:
        print('Error: No matching upper and lower files found.')
        return

    for key in common_keys:
        print(f'Processing pair: {upper_map[key]} and {lower_map[key]}')
        process_event_pair(upper_map[key], lower_map[key], outputs_dir, plot_2d)


input_path = args.input
plot_2d = args.plot_2d

if os.path.isdir(input_path):
    outputs_dir = os.path.join(input_path, 'outputs')
    process_directory(input_path, outputs_dir, plot_2d=plot_2d)
else:
    print(f'Error: {input_path} is not a valid directory.')
