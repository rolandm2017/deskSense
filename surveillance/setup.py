from setuptools import setup, find_packages

setup(
    name="deskSense",
    version="0.3",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
)
