import importlib
import pickle
import sys

import numpy as np
import pytest

pytest.importorskip("scipy.signal")


@pytest.fixture(scope="module")
def split_module(tmp_path_factory):
    tmp_input = tmp_path_factory.mktemp("split_input")
    original_argv = sys.argv[:]
    sys.modules.pop("splitTrajectory", None)
    sys.argv = ["splitTrajectory.py", "-i", str(tmp_input)]
    try:
        module = importlib.import_module("splitTrajectory")
    finally:
        sys.argv = original_argv
    return module


def test_compute_smoothed_centroid_short_series(split_module):
    history = [(0, 1.0, 2.0), (1, 3.0, 4.0)]
    smooth_x, smooth_y = split_module.compute_smoothed_centroid(history)
    assert np.allclose(smooth_x, [1.0, 3.0])
    assert np.allclose(smooth_y, [2.0, 4.0])


def test_compute_smoothed_centroid_uses_savgol(split_module):
    history = [
        (0, 0.0, 0.0),
        (1, 2.0, 2.0),
        (2, 4.0, 4.0),
        (3, 6.0, 6.0),
        (4, 8.0, 8.0),
    ]
    smooth_x, smooth_y = split_module.compute_smoothed_centroid(history)
    expected = split_module.savgol_filter(
        np.array([0.0, 2.0, 4.0, 6.0, 8.0], dtype=np.float32),
        window_length=3,
        polyorder=2,
    )
    assert np.allclose(smooth_x, expected)
    assert np.allclose(smooth_y, expected)


def test_split_events_by_centroid_assigns_upper_lower(split_module):
    particle = {
        "events": [
            (0.0, 1.0, 0.0),
            (0.0, 15.0, 1.0),
            (0.0, 25.0, 2.0),
        ],
        "centroid_history": [
            (0.0, 0.0, 5.0),
            (1.0, 0.0, 10.0),
            (2.0, 0.0, 20.0),
        ],
    }
    upper, lower = split_module.split_events_by_centroid(particle)
    assert upper.shape[0] == 2
    assert lower.shape[0] == 1
    assert np.allclose(lower[0], [0.0, 1.0, 0.0])
    assert np.allclose(upper[0], [0.0, 15.0, 1.0])
    assert np.allclose(upper[1], [0.0, 25.0, 2.0])


def test_save_event_sets_writes_pickles(tmp_path, split_module):
    upper = np.array([[0.0, 2.0, 3.0]], dtype=np.float32)
    lower = np.array([[0.0, -1.0, 1.0]], dtype=np.float32)
    split_module.save_event_sets(
        str(tmp_path), "example", 7, upper, lower
    )

    upper_file = tmp_path / "upper" / "example_particle7_upper.pkl"
    lower_file = tmp_path / "lower" / "example_particle7_lower.pkl"
    assert upper_file.exists()
    assert lower_file.exists()

    with upper_file.open("rb") as f:
        loaded_upper = pickle.load(f)
    with lower_file.open("rb") as f:
        loaded_lower = pickle.load(f)

    assert np.allclose(loaded_upper, upper)
    assert np.allclose(loaded_lower, lower)
