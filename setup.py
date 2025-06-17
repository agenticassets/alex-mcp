from setuptools import setup, find_packages

setup(
    name="alex-mcp",
    version="3.1.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    entry_points={
        "console_scripts": [
            "alex-mcp=alex_mcp.server:main",
        ],
    },
    install_requires=[
        "fastmcp>=2.8.1",
        "httpx>=0.28.1",
        "pydantic>=2.7.2",
        "rich>=13.9.4",
    ],
)
