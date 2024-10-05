# evsBat
This repository is an adaptation of the tracking functionality from evsMarineSnow for bat analysis.
It is designed to track objects in event camera data streams without converting the data into event frames or voxels, allowing for direct tracking.
The output data consists of the trajectory of the centroid and point clouds of events that make up the tracked objects. 
In post-analysis, frequency analysis of the variations in event count is also possible.

# Features
- Direct tracking: Processes event-based camera data streams directly, avoiding the need for frame or voxel conversion.
- Trajectory data: Outputs the trajectory of the object’s centroid for further analysis.
- Event point clouds: Provides point clouds of the events that form each tracked object, allowing for detailed post-processing.
- Frequency analysis: Enables the analysis of event count fluctuations over time, useful for observing periodic patterns in the data.

- # Project Structure
```bash
.
├── particle_tracking.cpp       # Handles event-based particle tracking in C++
├── peak_collection.py        # Collects peak frequency data from multiple txt files and generates violin plots
├── plotAllData_paper.py   # Functions for calculating vessel distances
├── plotAllData.py          # Plotting and animation of vessel trajectories
├── plotEventCountFFT_Window.py                   # Main execution script for coordinating the workflow
├── plotTrajectory.py          # Dependencies required for the project
├── pngToPDF.py                 # Project documentation (this file)
├── setup.py                 # Project documentation (this file)
├── trackParticlesC.py                 # Project documentation (this file)
└── README.md                 # Project documentation (this file)
```

