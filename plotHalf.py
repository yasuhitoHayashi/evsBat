import os
import pickle
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
import argparse
import numpy as np

# ===== スタイル設定（CSV版に合わせる） =====
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

parser = argparse.ArgumentParser(
    description='Plot and save 3D or 2D events from upper and lower pickle files.'
)
parser.add_argument('-i', '--input', required=True,
                    help='Path to the directory containing upper and lower folders.')
parser.add_argument('--show', action='store_true',
                    help='Display plots (default: False).')
parser.add_argument('--2d', action='store_true',
                    help='Plot in 2D instead of 3D (default: False).')
args = parser.parse_args()

def _safe_load(path):
    with open(path, 'rb') as f:
        arr = pickle.load(f)
    return np.asarray(arr, dtype=np.float32)

def plot_and_save_events(upper_file, lower_file, output_dir, show_plot=False, plot_2d=False):
    """Plot 3D or 2D events from upper and lower data."""
    upper_events = _safe_load(upper_file)
    lower_events = _safe_load(lower_file)

    fig = plt.figure()
    ax = fig.add_subplot(111, projection=None if plot_2d else '3d')
    title = os.path.basename(upper_file).replace('_upper.pkl', '')

    # ---- 時間を ms に統一 ----
    def time_ms(a):
        return a[:, 2] * 1e-3 if a.size > 0 else a

    # ---- Upper events ----
    if upper_events.size > 0:
        if plot_2d:
            ax.scatter(
                upper_events[:, 0], upper_events[:, 1],
                c='gray', marker='.', label='Upper Events'
            )
        else:
            ax.scatter(
                time_ms(upper_events), upper_events[:, 0], upper_events[:, 1],
                c='gray', marker='.', label='Upper Events'
            )

    # ---- Lower events ----
    if lower_events.size > 0:
        if plot_2d:
            ax.scatter(
                lower_events[:, 0], lower_events[:, 1],
                s=2, c='red', edgecolors='none', marker='.', label='Lower Events'
            )
        else:
            ax.scatter(
                time_ms(lower_events), lower_events[:, 0], lower_events[:, 1],
                c='red', marker='.', label='Lower Events'
            )

    # ---- 軸ラベル・範囲 ----
    if plot_2d:
        ax.set_xlabel('X Coordinate (pixels)')
        ax.set_ylabel('Y Coordinate (pixels)')
        ax.set_xlim([0, 1280])
        ax.set_ylim([720, 0])
    else:
        ax.set_xlabel('Time (milliseconds)')
        ax.set_ylabel('X Coordinate (pixels)')
        ax.set_zlabel('Y Coordinate (pixels)')

        t_all = np.concatenate([
            time_ms(upper_events) if upper_events.size else np.array([]),
            time_ms(lower_events) if lower_events.size else np.array([])
        ])
        if t_all.size:
            ax.set_xlim([float(np.min(t_all)), float(np.max(t_all))])

        ax.set_ylim([0, 1280])
        ax.set_zlim([720, 0])
        ax.view_init(elev=4, azim=-40)

    ax.legend()
    plt.tight_layout()

    # 保存
    os.makedirs(output_dir, exist_ok=True)
    out_png = os.path.join(output_dir, f'{title}_trajectory.png')
    plt.savefig(out_png, dpi=300)
    if show_plot:
        plt.show()
    plt.close(fig)

def process_plot_directory(input_directory, show_plot=False, plot_2d=False):
    upper_dir = os.path.join(input_directory, 'upper')
    lower_dir = os.path.join(input_directory, 'lower')
    output_dir = os.path.join(input_directory, 'output')
    os.makedirs(output_dir, exist_ok=True)

    if not os.path.exists(upper_dir) or not os.path.exists(lower_dir):
        print("Error: 'upper' and 'lower' directories do not exist in the specified path.")
        return

    upper_files = sorted([f for f in os.listdir(upper_dir) if f.endswith('_upper.pkl')])
    lower_files = sorted([f for f in os.listdir(lower_dir) if f.endswith('_lower.pkl')])

    upper_map = {os.path.splitext(f.replace('_upper.pkl', ''))[0]: os.path.join(upper_dir, f)
                 for f in upper_files}
    lower_map = {os.path.splitext(f.replace('_lower.pkl', ''))[0]: os.path.join(lower_dir, f)
                 for f in lower_files}

    common_keys = set(upper_map.keys()).intersection(set(lower_map.keys()))
    if not common_keys:
        print("Error: No matching upper and lower files found.")
        return

    for key in sorted(common_keys):
        upper_file = upper_map[key]
        lower_file = lower_map[key]
        print(f"Processing and plotting for: {upper_file} and {lower_file}")
        plot_and_save_events(upper_file, lower_file, output_dir, show_plot, plot_2d)

# ===== Main =====
input_path = args.input
show_plot = args.show
plot_2d = args.__dict__.get('2d', False)

if os.path.isdir(input_path):
    process_plot_directory(input_path, show_plot=show_plot, plot_2d=plot_2d)
else:
    print(f"Error: {input_path} is not a valid directory.")