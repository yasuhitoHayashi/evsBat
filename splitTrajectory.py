import numpy as np
import pickle
from scipy.signal import savgol_filter
import argparse
import os

parser = argparse.ArgumentParser(description='Split the densest particle trajectory into upper and lower event sets.')
parser.add_argument('-i', '--input', required=True, help='Path to the input pickle file or directory.')
args = parser.parse_args()


def compute_smoothed_centroid(centroid_history):
    centroids = np.asarray(centroid_history, dtype=np.float32)
    if centroids.shape[0] < 3:
        return centroids[:, 1], centroids[:, 2]

    window_length = max(3, int(centroids.shape[0] * 0.3))
    if window_length % 2 == 0:
        window_length += 1
    if window_length > centroids.shape[0]:
        window_length = centroids.shape[0] if centroids.shape[0] % 2 == 1 else centroids.shape[0] - 1
    if window_length < 3:
        return centroids[:, 1], centroids[:, 2]

    smoothed_x = savgol_filter(centroids[:, 1], window_length=window_length, polyorder=2)
    smoothed_y = savgol_filter(centroids[:, 2], window_length=window_length, polyorder=2)
    return smoothed_x, smoothed_y


def split_events_by_centroid(particle_info):
    events = np.asarray(particle_info.get('events', []), dtype=np.float32)
    if events.size == 0 or 'centroid_history' not in particle_info:
        return np.empty((0, 3), dtype=np.float32), np.empty((0, 3), dtype=np.float32)

    centroid_history = np.asarray(particle_info['centroid_history'], dtype=np.float32)
    if centroid_history.shape[0] == 0:
        return np.empty((0, 3), dtype=np.float32), np.empty((0, 3), dtype=np.float32)

    smoothed_x, smoothed_y = compute_smoothed_centroid(centroid_history)

    upper_events = []
    lower_events = []
    for event in events:
        time_index = int(np.argmin(np.abs(centroid_history[:, 0] - event[2])))
        if event[1] > smoothed_y[time_index]:
            upper_events.append(event)
        else:
            lower_events.append(event)

    return np.asarray(upper_events, dtype=np.float32), np.asarray(lower_events, dtype=np.float32)


def save_event_sets(output_root, base_filename, particle_id, upper_events, lower_events):
    upper_dir = os.path.join(output_root, 'upper')
    lower_dir = os.path.join(output_root, 'lower')
    os.makedirs(upper_dir, exist_ok=True)
    os.makedirs(lower_dir, exist_ok=True)

    upper_file = os.path.join(upper_dir, f'{base_filename}_particle{particle_id}_upper.pkl')
    lower_file = os.path.join(lower_dir, f'{base_filename}_particle{particle_id}_lower.pkl')

    with open(upper_file, 'wb') as f:
        pickle.dump(upper_events, f)
    with open(lower_file, 'wb') as f:
        pickle.dump(lower_events, f)

    print(f'Saved upper events to {upper_file}')
    print(f'Saved lower events to {lower_file}')


def process_particle_file(pickle_file, output_root):
    with open(pickle_file, 'rb') as f:
        particle_data = pickle.load(f)

    particle_event_counts = {
        particle_id: len(info.get('events', []))
        for particle_id, info in particle_data.items()
        if len(info.get('events', []))
    }

    if not particle_event_counts:
        print(f'Warning: No events found in {pickle_file}')
        return

    target_particle = max(particle_event_counts, key=particle_event_counts.get)
    print(f'Processing particle {target_particle} with {particle_event_counts[target_particle]} events')

    upper_events, lower_events = split_events_by_centroid(particle_data[target_particle])

    base_filename = os.path.basename(pickle_file).replace('.pkl', '')
    if not base_filename:
        base_filename = os.path.splitext(os.path.basename(pickle_file))[0]

    save_event_sets(output_root, base_filename, target_particle, upper_events, lower_events)


def process_directory(input_directory, output_root):
    for filename in sorted(os.listdir(input_directory)):
        if filename.endswith('.pkl'):
            file_path = os.path.join(input_directory, filename)
            print(f'Processing file: {file_path}')
            process_particle_file(file_path, output_root)


input_path = args.input

if os.path.isdir(input_path):
    process_directory(input_path, input_path)
elif os.path.isfile(input_path) and input_path.endswith('.pkl'):
    output_root = os.path.dirname(input_path)
    print(f'Processing file: {input_path}')
    process_particle_file(input_path, output_root)
else:
    print(f'Error: {input_path} is not a valid pickle file or directory.')
