"""
Setup script for NetWalker
"""

from setuptools import setup, find_packages
from netwalker.version import __version__, __author__

with open("requirements.txt", "r") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="netwalker",
    version=__version__,
    author=__author__,
    description="Network Topology Discovery Tool",
    long_description="NetWalker automatically discovers and maps Cisco network topologies using CDP and LLDP protocols",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "netwalker=main:main",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)