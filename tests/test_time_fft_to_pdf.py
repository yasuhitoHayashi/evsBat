import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
from time_fft_to_pdf import (
    plot_and_save_time_series_fft_to_pdf,
    plot_and_save_time_series_stft_to_pdf,
    plot_and_save_violin_to_pdf,
)


def test_pdf_outputs(tmp_path):
    data = [np.sin(2 * np.pi * 5 * np.arange(100) / 1000.0) for _ in range(2)]
    names = ["file1.csv", "file2.csv"]
    fft_pdf = tmp_path / "fft.pdf"
    stft_pdf = tmp_path / "stft.pdf"
    violin_pdf = tmp_path / "violin.pdf"

    plot_and_save_time_series_fft_to_pdf("folder", data, names, fft_pdf)
    plot_and_save_time_series_stft_to_pdf("folder", data, stft_pdf)
    plot_and_save_violin_to_pdf([[5, 6], [7, 8]], violin_pdf, ["a", "b"])

    assert fft_pdf.exists()
    assert stft_pdf.exists()
    assert violin_pdf.exists()
