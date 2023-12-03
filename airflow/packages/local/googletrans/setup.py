#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import os.path
from setuptools import setup, find_packages


def get_file(*paths):
    path = os.path.join(*paths)
    try:
        with open(path, 'rb') as f:
            return f.read().decode('utf8')
    except IOError:
        pass


def get_version():
    init_py = get_file(os.path.dirname(__file__), 'googletrans', '__init__.py')
    pattern = r"{0}\W*=\W*'([^']+)'".format('__version__')
    version, = re.findall(pattern, init_py)
    return version


def get_description():
    init_py = get_file(os.path.dirname(__file__), 'googletrans', '__init__.py')
    pattern = r'"""(.*?)"""'
    description, = re.findall(pattern, init_py, re.DOTALL)
    return description


def get_readme():
    return get_file(os.path.dirname(__file__), 'README.md')


with open("requirements.txt", encoding="utf-8") as r:
    install_requires = [i.strip() for i in r if not i.startswith('#')]


setup(
    name='googletrans',
    version=get_version(),
    description=get_description(),
    long_description=get_readme(),
    license='MIT',
    long_description_content_type="text/markdown",
    author='StarkProgrammer',
    author_email='starkbotsindustries@gmail.com',
    url='https://github.com/StarkBotsIndustries/googletrans',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Education',
        'Intended Audience :: End Users/Desktop',
        'License :: Freeware',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: MacOS :: MacOS X',
        'Topic :: Education',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10'
    ],
    packages=find_packages(),
    keywords='google translate translator',
    install_requires=install_requires,
    python_requires='>=3.7',
)
