from setuptools import setup
from pybind11.setup_helpers import Pybind11Extension, build_ext

ext_modules = [
    Pybind11Extension(
        "pso_core",                                # Name of the generated Python module
        ["wrapper.cpp", "terrain.cpp", "engine.cpp"], # Your C++ source files
        cxx_std=17,                                # Force C++17 standard
    ),
]

setup(
    name="pso_core",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
)