#!/usr/bin/env python3

from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='sysstat-applet',
    author='Joerg Mechnich',
    author_email='joerg.mechnich@gmail.com',
    description='Tray applet for system monitoring',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/jmechnich/sysstat-applet',
    packages=['sysstatapplet'],
    use_scm_version={"local_scheme": "no-local-version"},
    setup_requires=['setuptools_scm'],
    install_requires=["appletlib"],
    scripts=['sysstat-applet'],
    data_files = [
        ('share/applications', ['sysstat-applet.desktop']),
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: POSIX :: Linux",
        "Environment :: X11 Applications :: Qt",
    ],
    python_requires='>=3.6',
)
