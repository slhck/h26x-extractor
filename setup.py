#!/usr/bin/env python

import os

from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))

# Versioning
with open(os.path.join(here, "h26x_extractor", "__init__.py")) as version_file:
    for line in version_file:
        if line.startswith("__version__"):
            version = line.split("=")[1].strip().strip('"')
            break
    else:
        raise RuntimeError("Unable to find version string.")

# Get the long description from the README file
with open(os.path.join(here, "README.md")) as f:
    long_description = f.read()

# Get the history from the CHANGELOG file
with open(os.path.join(here, "CHANGELOG.md")) as f:
    history = f.read()

setup(
    name="h26x_extractor",
    version=version,
    description="Extract NAL units from H.264 bitstreams",
    long_description=long_description + "\n\n" + history,
    long_description_content_type="text/markdown",
    author="Werner Robitza",
    author_email="werner.robitza@gmail.com",
    url="https://github.com/slhck/h26x-extractor",
    packages=["h26x_extractor"],
    include_package_data=True,
    install_requires=["docopt", "tabulate", "bitstring"],
    license="MIT",
    zip_safe=False,
    keywords="video, h264",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Video",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    entry_points={"console_scripts": ["h26x-extractor = h26x_extractor.__main__:main"]},
)
