#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

# To use a consistent encoding
from codecs import open
import os
from os import path

here = path.abspath(path.dirname(__file__))

# Versioning
with open(os.path.join(here, "h26x_extractor", "__init__.py")) as version_file:
    version = eval(version_file.read().split("\n")[0].split("=")[1].strip())

# Get the long description from the README file
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

# Get the history from the CHANGELOG file
with open(path.join(here, "CHANGELOG.md"), encoding="utf-8") as f:
    history = f.read()

setup(
    name="h26x-extractor",
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
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    entry_points={"console_scripts": ["h26x-extractor = h26x_extractor.__main__:main"]},
)
