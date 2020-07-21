#!/usr/bin/env python3

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='sysstat-applet',
    version='1.0.0',
    author='Joerg Mechnich',
    author_email='joerg.mechnich@gmail.com',
    description='Tray applet for system monitoring',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/jmechnich/sysstat-applet',
    packages=['sysstatapplet'],
    install_requires=["appletlib"],
    scripts=['sysstat-applet'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: POSIX :: Linux",
        "Environment :: X11 Applications :: Qt",
    ],
    python_requires='>=3.6',
)
