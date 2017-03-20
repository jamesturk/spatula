#!/usr/bin/env python
import sys
from setuptools import setup, find_packages

setup(name="spatula",
      version='0.0.2',
      py_modules=['spatula'],
      author="James Turk",
      author_email='james.p.turk@gmail.com',
      license="MIT",
      url="http://github.com/jamesturk/spatula",
      long_description="",
      packages=find_packages(),
      description="spatula is for scraping",
      platforms=["any"],
      classifiers=["Development Status :: 2 - Pre-Alpha",
                   "Intended Audience :: Developers",
                   "License :: OSI Approved :: MIT License",
                   "Natural Language :: English",
                   "Operating System :: OS Independent",
                   "Programming Language :: Python :: 3.5",
                   "Topic :: Software Development :: Libraries :: Python Modules",
                   ],
      install_requires=['scrapelib>=1.0.0'],
#      entry_points="""
#[console_scripts]
#scrapeshell = scrapelib.__main__:scrapeshell
#"""
      )
