import pandas as pd
import numpy as np
import pickle
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import argparse
import os

parser = argparse.ArgumentParser(description='Particle tracking script.')
parser.add_argument('-i', '--input', required=True, help='Path to the input pickle file or directory.')
args = parser.parse_args()

# Threshold for number of events
event_threshold = 1000

# Ratio for sampling events for plotting
sampling_ratio = 0.1

# Flag to determine whether to plot events  
plot_events = True  # Set to False to plot only centroids

def process_pickle_file(particle_output_file):
    output_directory = os.path.dirname(particle_output_file)
    
    # Create output folder (fft_results)
    fft_results_dir = os.path.join(output_directory, 'plotTrajectory_results')
    os.makedirs(fft_results_dir, exist_ok=True)  # Do not raise error if it already exists
    
    # Process the file name: use the part after the third "_" from the beginning and remove ".pkl"
    base_filename = os.path.basename(particle_output_file)
    base_filename = '_'.join(base_filename.split('_')[3:]).replace('.pkl', '')

    with open(particle_output_file, 'rb') as f:
        particle_data = pickle.load(f)

    # Create a 3D plot using Matplotlib
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    # Plot particle trajectories and events
    for particle_id, particle_info in particle_data.items():
        if 'centroid_history' in particle_info:
            centroid_history = np.array(particle_info['centroid_history'])  # (time, centroid_x, centroid_y)

            # Check if there is at least one centroid in the history
            if len(centroid_history) > 1:
                # Plot the trajectory of the centroid
                ax.plot(centroid_history[:, 0] * 1e-3, centroid_history[:, 1], centroid_history[:, 2], label=f'Particle {particle_id} Centroid Trajectory')

        # If the flag is True, plot the events
        if plot_events:
            events = particle_info['events']
            event_coords = np.array(events)
            event_times = event_coords[:, 2] * 1e-3  # Convert event times to milliseconds

            # Downsample for visualization
            num_events = len(events)
            if sampling_ratio < 1.0:
                sample_size = int(num_events * sampling_ratio)
                if sample_size > 0:
                    sampled_indices = np.random.choice(num_events, sample_size, replace=False)
                    sampled_events = event_coords[sampled_indices]
                    sampled_event_times = event_times[sampled_indices]
                    
                    # Scatter plot
                    ax.scatter(sampled_event_times, sampled_events[:, 0], sampled_events[:, 1], alpha=0.3, marker='.')
            else:
                # If not downsampling
                ax.scatter(event_times, event_coords[:, 0], event_coords[:, 1], alpha=0.3, marker='.')

    ax.set_ylabel('X Coordinate')
    ax.set_zlabel('Y Coordinate')
    ax.set_xlabel('Time (milliseconds)')

    #ax.set_xlim([0, 1000])
    ax.set_ylim([0, 1280])
    ax.set_zlim([720, 0])

    output_image_file = os.path.join(fft_results_dir, f'{base_filename}_trajectory.png')

    plt.show()
    #plt.savefig(output_image_file)
    #plt.close()

input_path = args.input

if os.path.isdir(input_path):
    # Process all files in the directory
    for filename in os.listdir(input_path):
        if filename.endswith('.pkl'):
            file_path = os.path.join(input_path, filename)
            print(f"Processing file: {file_path}")
            process_pickle_file(file_path)
elif os.path.isfile(input_path) and input_path.endswith('.pkl'):
    # Process a single file
    print(f"Processing file: {input_path}")
    process_pickle_file(input_path)
else:
    print(f"Error: {input_path} is not a valid pickle file or directory.")
