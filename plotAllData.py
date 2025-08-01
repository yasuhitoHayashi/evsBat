import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

# Path to the CSV file
file_path = '/sampleData/yubi_605.csv'

# Read the CSV file
data = pd.read_csv(file_path, header=None, names=['x', 'y', 'polarity', 'time'])
data['time'] = data['time'] * 1e-3
# Filter data within a specific time range
data = data[(data['time'] > 0) & (data['time'] < 2000)]

dataP = data[data['polarity'] == 1]
dataN = data[data['polarity'] == 0]

# Create the plot
fig = plt.figure(figsize=(16, 10))

# Place three 2D plots on the top row
ax2d_1 = fig.add_subplot(231)
ax2d_2 = fig.add_subplot(232)
ax2d_3 = fig.add_subplot(233)

# Filter data by time range and plot on the XY plane
time_ranges = [(500, 550), (1000, 1050), (1500, 1550)]
colors = ['red', 'green', 'purple']  # Plot on each XY plane
axes_2d = [ax2d_1, ax2d_2, ax2d_3]

for i, (start_time, end_time) in enumerate(time_ranges):
    filtered_data = dataP[(dataP['time'] >= start_time) & (dataP['time'] <= end_time)]
    
    # Plot on each XY plane
    axes_2d[i].scatter(filtered_data['x'], filtered_data['y'], s=2, c=colors[i], edgecolors='none', marker='.')
    axes_2d[i].set_title(f'{start_time}ms - {end_time}ms')
    axes_2d[i].set_xlim([0, 1280])
    axes_2d[i].set_ylim([0, 720])
    axes_2d[i].set_xlabel('X Coordinate')
    axes_2d[i].set_ylabel('Y Coordinate')

# Place a 3D plot on the bottom row
ax3d = fig.add_subplot(212, projection='3d')  
ax3d.scatter(dataP['time'], dataP['x'], dataP['y'], s=2, c='blue', edgecolors='none', marker='.')

# Fill each time range with a 3D box
for i, (start_time, end_time) in enumerate(time_ranges):
    # Set vertices to construct the faces of the box
    verts = [
        # Front face
        [[start_time, 0, 0], [start_time, 1280, 0], [start_time, 1280, 720], [start_time, 0, 720]],
        # Back face
        [[end_time, 0, 0], [end_time, 1280, 0], [end_time, 1280, 720], [end_time, 0, 720]],
        # Left face
        [[start_time, 0, 0], [start_time, 0, 720], [end_time, 0, 720], [end_time, 0, 0]],
        # Right face
        [[start_time, 1280, 0], [start_time, 1280, 720], [end_time, 1280, 720], [end_time, 1280, 0]],
        # Bottom face
        [[start_time, 0, 0], [start_time, 1280, 0], [end_time, 1280, 0], [end_time, 0, 0]],
        # Top face
        [[start_time, 0, 720], [start_time, 1280, 720], [end_time, 1280, 720], [end_time, 0, 720]],
    ]
    
    # Draw each face with transparency
    poly = Poly3DCollection(verts, color=colors[i], alpha=0.3)
    ax3d.add_collection3d(poly)

# Set labels
ax3d.set_ylabel('X Coordinate')
ax3d.set_zlabel('Y Coordinate')
ax3d.set_xlabel('Time (milliseconds)')
ax3d.set_xlim([0, 2000])
ax3d.set_ylim([0, 1280])
ax3d.set_zlim([720, 0])

plt.tight_layout()
plt.show()
