from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="alex-mcp",
    version="4.2.5",
    author="OpenAlex MCP Team",
    description="OpenAlex Author Disambiguation MCP Server",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/drAbreu/alex-mcp",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",  # Added this since pyalex requires Python 3.8+
    install_requires=[
        "fastmcp>=2.8.1",
        "httpx>=0.28.1",
        "pydantic>=2.7.2",
        "rich>=13.9.4",
        "pyalex==0.18",
    ],
    entry_points={
        "console_scripts": [
            "alex-mcp=alex_mcp.server:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)