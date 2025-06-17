from setuptools import setup, find_packages

setup(
    name="alex-mcp",
    version="3.2.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    entry_points={
        "console_scripts": [
            "alex-mcp=src.alex_mcp.server:main",
        ],
    },
    install_requires=[
        "fastmcp>=0.1.0",
        "httpx>=0.25.0",
        "pydantic>=2.0.0",
        "rich>=13.0.0",
    ],
)
