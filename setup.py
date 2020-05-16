#!/usr/bin/env python
from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='aaisp2mqtt',
    version='0.3.0',
    description='A script to publish Andrews & Arnold / AAISP broadband quota and sync rates to MQTT',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='MIT',
    author='Nat Morris, Andrew Williams',
    author_email='nat@nuqe.net, andy@tensixtyone.com',
    url='https://github.com/nikdoof/aaisp2mqtt',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
    ],
    python_requires='>=3.7',
    entry_points={
        'console_scripts': [
            'aaisp2mqtt = aaisp2mqtt:main',
        ],
    },
    install_requires=[
        'paho-mqtt>=1.2',
        'humanfriendly>=2.1',
        'requests>=2.23.0',
    ]
)