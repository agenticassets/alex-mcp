from setuptools import setup, find_packages

setup(
    name="alex-mcp",
    version="3.2.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    entry_points={
        "console_scripts": [
            "alex-mcp=alex_mcp.server:main",
        ],
    },
    install_requires=[
        "mcp @ git+https://github.com/modelcontextprotocol/python-sdk.git",
        "httpx>=0.25.0",
        "rich>=13.0.0",
    ],
)
