"""
setup.py -  setuptools configuration for esc
"""

import setuptools

from esc.consts import VERSION

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="esc-calc",
    version=VERSION,
    author="Soren I. Bjornstad",
    author_email="contact@sorenbjornstad.com",
    description="extensible stack-based RPN calculator based on curses",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sobjornstad/esc",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'windows-curses; platform_system == "Windows"',
    ],
    scripts=['package_scripts/esc'],
    python_requires='>=3.6',
)
