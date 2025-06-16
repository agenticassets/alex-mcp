#!/usr/bin/env python3
"""
Setup script for Author Disambiguation MCP Server
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="author-disambiguation-mcp",
    version="0.1.0",
    author="Author Disambiguation Team",
    description="MCP server for author disambiguation across multiple scientific databases",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/author-disambiguation-mcp",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "author-disambiguation-server=main:main",
        ],
    },
)
