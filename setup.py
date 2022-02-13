#!/usr/bin/env python
# _*_ coding:UTF-8 _*_
"""
__author__ = 'shede333'
"""

from pathlib import Path

from setuptools import find_packages
from setuptools import setup

README = Path(__file__).resolve().with_name("ReadMe.md").read_text()

print("{} - {}".format("*" * 10, find_packages()))

setup(
    name='OKAppleAPI',  # 包名字
    version='1.1.0',  # 包版本
    author='shede333',  # 作者
    author_email='333wshw@163.com',  # 作者邮箱
    keywords='ios ok apple appstore connect api',
    description='OK AppStore Connect API',  # 简单描述
    long_description=README,
    long_description_content_type='text/markdown',
    url='https://github.com/shede333/OKAppleAPI',  # 包的主页
    packages=find_packages(),  # 包
    install_requires=['PyJWT~=2.0', 'PyMobileProvision~=1.4', 'requests~=2.20'],
    python_requires="~=3.7",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
)

