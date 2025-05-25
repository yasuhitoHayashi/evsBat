import os
import csv
import pickle
from unittest import mock
from trackParticlesC import process_file


class DummyParticle:
    def __init__(self, pid):
        self.particle_id = pid
        self.centroid_history = [(0, 0, 0)]
        self.events = [(0, 0, 0)]


def test_process_file_creates_pickle(tmp_path):
    csv_path = tmp_path / "data.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([0, 0, 1, 0])

    with mock.patch("trackParticlesC.track_particles_cpp", return_value=[DummyParticle(1)]):
        process_file(str(csv_path))

    output = tmp_path / "particle_tracking_results_both_data.pkl"
    assert output.exists()
    with open(output, "rb") as f:
        data = pickle.load(f)
    assert 1 in data
