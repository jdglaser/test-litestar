from setuptools import find_namespace_packages, setup

setup(
    name="test-app-cli",
    version="0.1.0",
    packages=find_namespace_packages(),
    include_package_data=True,
    install_requires=[
        "Click",
    ],
    entry_points={
        "console_scripts": [
            "app = app.cli:cli",
        ],
    },
)
