import pandas as pd
import numpy as np
import glob
import pickle
import matplotlib.pyplot as plt
from scipy.fft import fft, fftfreq
from scipy.signal import find_peaks
import argparse
import os

from time_fft_to_pdf import *
from process_fft import *
from detect_peaks import *


parser = argparse.ArgumentParser(description="Particle tracking script.")
parser.add_argument(
    "-i",
    "--input",
    required=True,
    help="Path to the input pickle file or directory.",
)
args = parser.parse_args()
input_path = args.input
# FOLDERS = ["momojiro"]
# DATA_LABELS = [
#     "$Myotis\\ macrodactylus$",
# ]

# FOLDERS = ["kiku", "yubi", "momojiro"]
# DATA_LABELS = [
#     "$Rhinolophus\\ nippon$",
#     "$Miniopterus\\ fuliginosus$",
#     "$Myotis\\ macrodactylus$",
# ]
FOLDERS = ["move_objects"]
DATA_LABELS = [
    "$moveing\\ objects$",
]


def read_pickles(input_path, folder_name):
    files = glob.glob(f"{input_path}/{folder_name}/*.pkl")

    return files


def process_pickle_file(particle_output_file):
    output_directory = os.path.dirname(particle_output_file)

    fft_results_dir = os.path.join(output_directory, "windowed_fft_results")
    os.makedirs(
        fft_results_dir, exist_ok=True
    )

    # File name handling: use the part after the third "_" from the beginning, and remove ".pkl"
    base_filename = os.path.basename(particle_output_file)
    base_filename = "_".join(base_filename.split("_")[3:]).replace(".pkl", "")

    with open(particle_output_file, "rb") as f:
        particle_data = pickle.load(f)

    # Extract the particle with the maximum number of events
    # max_particle_id = max(
    #     particle_data, key=lambda p: len(particle_data[p]["events"])
    # )
    # particle_info = particle_data[max_particle_id]
    particle_info = particle_data
    event_coords = np.array(particle_info)

    # Convert to milliseconds
    event_times = event_coords[:, 2] * 1e-3

    # Get minimum and maximum time
    min_time, max_time = np.min(event_times), np.max(event_times)

    # Create time bins with 1ms intervals
    time_bin_size = 1  # ms
    time_bins = np.arange(min_time, max_time + time_bin_size, time_bin_size)

    # Count number of events in each time bin
    event_counts, _ = np.histogram(event_times, bins=time_bins)

if os.path.isdir(input_path):
    # Process all files in the directory
    all_peak_freqs = []
    dict_peak_freqs = {}
    dict_file_names = {}
    for folder_name in FOLDERS:
        pickle_list = read_pickles(input_path, folder_name)
        event_num_list = []
        folder_peak_freqs = []
        folder_file_names = []
        for pkl_data in pickle_list:
            base_name = os.path.basename(pkl_data)
            print(f"Processing file: {base_name}")
            event_num_arr = process_pickle_file(pkl_data)
            freqs, fft_magnitude = calc_fft(event_num_arr)
            peak_indices, max_peak_idx = calc_peak(freqs, fft_magnitude)
            if len(peak_indices) == 0:
                event_num_list.append(event_num_arr)
                folder_peak_freqs.append(np.nan)
                folder_file_names.extend([base_name])
            else:
                peak_freqs = freqs[peak_indices]
                max_peak_freq = freqs[max_peak_idx]
                peak_freqs = detect_wingfreq(peak_freqs, max_peak_freq)
                folder_peak_freqs.append(round(peak_freqs, 1))
                folder_file_names.extend([base_name])
                event_num_list.append(event_num_arr)

        dict_peak_freqs[folder_name] = folder_peak_freqs
        dict_file_names[folder_name] = folder_file_names

        all_peak_freqs.append(folder_peak_freqs)

        output_pdf_path = os.path.join(
            input_path, f"{folder_name}_analysis.pdf"
        )
        plot_and_save_time_series_fft_to_pdf(
            folder_name, event_num_list, folder_file_names, output_pdf_path
        )

    # Save violin plot to a single PDF
    violin_pdf_path = os.path.join(input_path, "peak_frequency_comparison.pdf")
    plot_and_save_violin_to_pdf(all_peak_freqs, violin_pdf_path, DATA_LABELS)

    # Save data to CSV (including peak frequency and file names)
    df_peak_freqs = pd.DataFrame(
        dict([(k, pd.Series(v)) for k, v in dict_peak_freqs.items()])
    )
    print(df_peak_freqs)
    df_file_names = pd.DataFrame(
        dict([(k + "_file", pd.Series(v)) for k, v in dict_file_names.items()])
    )

    # Combine file names and peak frequencies into one DataFrame
    df_combined = pd.concat([df_peak_freqs, df_file_names], axis=1)

    # Save the results to "peak_freqs.csv"
    df_combined.to_csv(os.path.join(input_path, "peak_freqs.csv"))

elif os.path.isfile(input_path) and input_path.endswith(".pkl"):
    print(f"Processing file: {input_path}")
    process_pickle_file(input_path)
else:
    print(f"Error: {input_path} is not a valid pickle file or directory.")
