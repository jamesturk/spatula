#!/usr/bin/env python
from setuptools import setup, find_packages

setup(name="spatula",
      version='0.3.0',
      py_modules=['spatula'],
      author="James Turk",
      author_email='dev@jamesturk.net',
      license="MIT",
      url="https://github.com/jamesturk/spatula",
      long_description="",
      packages=find_packages(),
      description="spatula is for scraping",
      platforms=["any"],
      classifiers=["Development Status :: 2 - Pre-Alpha",
                   "Intended Audience :: Developers",
                   "License :: OSI Approved :: MIT License",
                   "Natural Language :: English",
                   "Operating System :: OS Independent",
                   "Programming Language :: Python :: 3.7",
                   "Programming Language :: Python :: 3.8",
                   "Programming Language :: Python :: 3.9",
                   "Topic :: Software Development :: Libraries :: Python Modules",
                   ],
      install_requires=['scrapelib>=1.0.0'],
      entry_points="""
[console_scripts]
spatula = spatula.cli:cli
"""
      )
