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

parser = argparse.ArgumentParser(description='Particle tracking script.')
parser.add_argument('-i', '--input', required=True, help='Path to the input pickle file or directory.')
args = parser.parse_args()

sampling_ratio = 0.5

def process_pickle_file(particle_output_file, outputs_dir):
    os.makedirs(outputs_dir, exist_ok=True)

    base_filename = os.path.basename(particle_output_file)
    base_filename = '_'.join(base_filename.split('_')[3:]).replace('.pkl', '')
    if not base_filename:
        base_filename = os.path.splitext(os.path.basename(particle_output_file))[0]

    with open(particle_output_file, 'rb') as f:
        particle_data = pickle.load(f)

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')

    for particle_id, particle_info in particle_data.items():
        if 'centroid_history' in particle_info:
            centroid_history = np.array(particle_info['centroid_history'])

            if len(centroid_history) > 1:
                ax.plot(centroid_history[:, 0] * 1e-3, centroid_history[:, 1], centroid_history[:, 2], label=f'Particle {particle_id} Centroid Trajectory')

        events = particle_info.get('events', [])
        if events:
            event_coords = np.array(events)
            event_times = event_coords[:, 2] * 1e-3

            num_events = len(events)
            if sampling_ratio < 1.0:
                sample_size = int(num_events * sampling_ratio)
                if sample_size > 0:
                    sampled_indices = np.random.choice(num_events, sample_size, replace=False)
                    sampled_events = event_coords[sampled_indices]
                    sampled_event_times = event_times[sampled_indices]
                    
                    ax.scatter(sampled_event_times, sampled_events[:, 0], sampled_events[:, 1], alpha=0.3, marker='.')
            else:
                ax.scatter(event_times, event_coords[:, 0], event_coords[:, 1], alpha=0.3, marker='.')

    ax.set_xlabel('Time (milliseconds)')
    ax.set_ylabel('X Coordinate (pixels)')
    ax.set_zlabel('Y Coordinate (pixels)')

    ax.set_ylim([0, 1280])
    ax.set_zlim([720, 0])
    ax.view_init(elev=4, azim=-40)

    output_image_file = os.path.join(outputs_dir, f'{base_filename}_trajectory.png')
    plt.tight_layout()
    plt.savefig(output_image_file)
    plt.close()

input_path = args.input

if os.path.isdir(input_path):
    outputs_dir = os.path.join(input_path, 'outputs')
    for filename in os.listdir(input_path):
        if filename.endswith('.pkl'):
            file_path = os.path.join(input_path, filename)
            print(f"Processing file: {file_path}")
            process_pickle_file(file_path, outputs_dir)
elif os.path.isfile(input_path) and input_path.endswith('.pkl'):
    outputs_dir = os.path.join(os.path.dirname(input_path), 'outputs')
    print(f"Processing file: {input_path}")
    process_pickle_file(input_path, outputs_dir)
else:
    print(f"Error: {input_path} is not a valid pickle file or directory.")
