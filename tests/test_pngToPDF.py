import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt
from pngToPDF import collect_png_files, generate_pdfs


def test_collect_and_generate(tmp_path):
    for name in ["abura_1.png", "kiku_1.png", "other.png"]:
        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1])
        fig.savefig(tmp_path / name)
        plt.close(fig)

    categories = collect_png_files(tmp_path, all_mode=False)
    assert len(categories["abura"]) == 1
    assert len(categories["kiku"]) == 1

    generate_pdfs(tmp_path, all_mode=True)
    output_dir = tmp_path / "pdf_results"
    assert any(p.suffix == ".pdf" for p in output_dir.iterdir())
