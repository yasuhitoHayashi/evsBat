from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext  # Use build_ext from setuptools
import pybind11

ext_modules = [
    Extension(
        'particle_tracking',  # Module name
        ['particle_tracking.cpp'],  # C++ source file to compile
        include_dirs=[pybind11.get_include()],  # Directory for pybind11 header files
        extra_compile_args=['-O3', '-std=c++11'],  # Add options to enable C++11 and optimization
    ),
]

setup(
    name='particle_tracking',  # Package name
    ext_modules=ext_modules,
    cmdclass={'build_ext': build_ext},  # Specify build_ext from setuptools
)
