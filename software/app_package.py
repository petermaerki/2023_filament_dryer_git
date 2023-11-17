"""
This file will instruct 'app_packager.py' to deploy a app_package to `web_downloads`.
"""
import pathlib

name = "pico"
directory = pathlib.Path(__file__).parent / "micropython"
globs = ["*.py", "*.txt"]

assert directory.exists(), str(directory)
