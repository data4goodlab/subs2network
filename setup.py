#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages
import codecs, os

here = os.path.abspath(os.path.dirname(__file__))

with codecs.open(os.path.join(here, "README.md"), encoding="utf-8") as f:
    readme = "\n" + f.read()

requirements = [
    'networkx>=2.2',
    'pysrt',
    'babelfish',
    'numpy',
    'turicreate',
    'IMDbPY @ git+https://github.com/alberanid/imdbpy.git@3bcd8412e3ab1f0566bb4093288d3ee1c6142a6c#egg=IMDbPY',
    'subliminal @ git+https://github.com/Kagandi/subliminal.git@2ac3ea23e84554c366548415c5d1b0002387ced7#egg=subliminal',
    'stop-words',
    'fuzzywuzzy',
    'spacy',
    'python-dotenv',
    'tmdbsimple',
    'tqdm',
    'scikit-learn>=0.20.1'
]
setup_requirements = ['pytest-runner', ]

test_requirements = ['pytest', ]

setup(
    author="Dima Kagan",
    author_email='kagandi@post.bgu.ac.il',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',

        'Programming Language :: Python :: 3.6',
    ],
    description="Python Boilerplate contains all the boilerplate you need to create a Python package.",
    install_requires=requirements,
    license="Apache Software License 2.0",
    long_description=readme,
    include_package_data=True,
    keywords='subs2network',
    name='subs2network',
    packages=find_packages(include=['subs2network']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/data4goodlab/subs2network/',
    version='0.4.0',
    zip_safe=False,
)
