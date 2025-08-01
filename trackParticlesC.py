import pandas as pd
import argparse
import pickle
import os
from particle_tracking import track_particles_cpp  # import C++ module

parser = argparse.ArgumentParser(description='Particle tracking script.')
parser.add_argument('-i', '--input', required=True, help='Path to the input directory or file.')
args = parser.parse_args()

input_path = args.input

# Parameters for particle tracking
sigma_x = 6.0  # Spatial scale parameter: 6 for sperm, Bat, 9 for marine snow
sigma_t = 10000.0  # Temporal scale parameter: 10000 for sperm, Bat, and marine snow
gaussian_threshold = 0.8  # Threshold for Gaussian score, around 0.8 seems good
m_threshold = 500  # Mass threshold, around 100

def process_file(file_path):
    print(f"Processing file: {file_path}")
    
    # Read CSV file
    data_filtered = pd.read_csv(file_path, header=None, names=['x', 'y', 'polarity', 'time'])
    
    # Restrict to positive polarity data
    #data_filtered = data[data['polarity'] == 1].copy()
    
    data_list = [tuple(row) for row in data_filtered[['x', 'y', 'time']].itertuples(index=False, name=None)]
    
    print(f"Number of data points after filtering: {len(data_filtered)}")
    
    try:
        # Call the C++ function (using sigma_x, sigma_t, gaussian_threshold)
        particles = track_particles_cpp(data_list, sigma_x, sigma_t, gaussian_threshold, m_threshold)
    
        particle_output = {}
        for p in particles:
            particle_output[p.particle_id] = {
                'centroid_history': p.centroid_history,  # Centroid coordinates (x, y)
                'events': p.events       # All events [(x, y, time), ...]
            }
    
        # Save the pickle file in the same directory as the input file
        output_file = os.path.join(os.path.dirname(file_path), f'particle_tracking_results_both_{os.path.basename(file_path).split(".")[0]}.pkl')
        with open(output_file, 'wb') as f:
            pickle.dump(particle_output, f)
    
        print(f"Particle tracking results saved to {output_file}")
    
    except Exception as e:
        print("An error occurred during the particle tracking process.")
        print(f"Error message: {e}")

# If input is a directory, process all CSV files in the directory
if os.path.isdir(input_path):
    for filename in os.listdir(input_path):
        if filename.endswith('.csv'):
            file_path = os.path.join(input_path, filename)
            process_file(file_path)

# If input is a CSV file, process that file
elif os.path.isfile(input_path) and input_path.endswith('.csv'):
    process_file(input_path)

else:
    print("Invalid input. Please provide a valid CSV file or directory.")
