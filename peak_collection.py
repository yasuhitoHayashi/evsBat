import os
import pandas as pd
import argparse
import matplotlib.pyplot as plt
import seaborn as sns

# Argument parser setup
parser = argparse.ArgumentParser(description="Process files and extract peak frequencies.")
parser.add_argument('-i', '--input_dir', required=True, help="Input directory containing .txt files.")
parser.add_argument('-A', '--all_files', action='store_true', help="Process all files regardless of their names.")
args = parser.parse_args()

# Directory where the files are stored (from command line argument)
directory = args.input_dir

# List of identifiers
identifiers = ['abura', 'kiku', 'momoziro', 'yubi']

# Create a dictionary to store maximum frequencies for each identifier
max_frequencies = {identifier: [] for identifier in identifiers}
# Add 'all_files' entry for processing all files when -A option is used
if args.all_files:
    max_frequencies['all_files'] = []

# Iterate over the files in the directory
for filename in os.listdir(directory):
    if filename.endswith('.txt'):
        file_path = os.path.join(directory, filename)
        try:
            # Read the data from the file
            df = pd.read_csv(file_path, sep='\t')

            # Check if the required columns exist and are not empty
            if df.empty or 'Height [%]' not in df.columns or df['Height [%]'].dropna().empty:
                print(f"Skipping {filename}: No valid 'Height [%]' data")
                continue

            if args.all_files:
                # Process all files regardless of identifiers
                max_frequency = df.loc[df['Height [%]'].idxmax(), 'Frequency [Hz]']
                max_frequencies['all_files'].append(max_frequency)
            else:
                # Process files based on identifiers in the filename
                for identifier in identifiers:
                    if identifier in filename:
                        # Get the frequency corresponding to the max Height
                        max_frequency = df.loc[df['Height [%]'].idxmax(), 'Frequency [Hz]']
                        max_frequencies[identifier].append(max_frequency)

        except Exception as e:
            print(f"Error processing {filename}: {e}")
            continue

# Save results into peak_'x'.txt files and also collect data for violin plot
for identifier, frequencies in max_frequencies.items():
    if frequencies:  # Only save if there's data
        output_file = os.path.join(directory, f'peak_{identifier}.txt')
        with open(output_file, 'w') as f:
            for frequency in frequencies:
                f.write(f'{frequency}\n')

# Create a violin plot
plt.figure(figsize=(10, 6))

# Prepare the data for seaborn violinplot
data = []
categories = []


for identifier, frequencies in max_frequencies.items():
    if frequencies:
        data.extend(frequencies)
        categories.extend([identifier] * len(frequencies))

# Convert to a DataFrame for easier plotting with seaborn
df_violin = pd.DataFrame({'Frequency [Hz]': data, 'Category': categories})

# Violin plot
sns.violinplot(x='Category', y='Frequency [Hz]', data=df_violin, hue='Category')
sns.swarmplot(x='Category', y='Frequency [Hz]', data=df_violin, color='k', alpha=0.6)

# Set the plot labels and title
plt.title('Peak Frequency Distribution by Category')
plt.xlabel('Category')
plt.ylabel('Frequency [Hz]')
plt.grid(True)

# Save the plot to a file
plt.savefig(os.path.join(directory, 'peak_frequency_violin_plot.png'))

# Show the plot (optional)
plt.show()

print("Peak frequency extraction and violin plot creation completed!")