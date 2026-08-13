from setuptools import find_packages, setup


setup(
    name="gpu-diagnostic",
    version="0.1.0",
    package_dir={"": "src"},
    packages=find_packages("src"),
    entry_points={"console_scripts": ["gpu-diag=gpu_diagnostic.cli.main:main"]},
)
