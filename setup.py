from setuptools import setup, find_packages

setup(
    name="alex-mcp",
    version="3.2.0",
    py_modules=["server"],
    entry_points={
        "console_scripts": [
            "alex-mcp=server:main",
        ],
    },
    install_requires=[
        "fastmcp",
        "httpx", 
        "pydantic",
    ],
)
