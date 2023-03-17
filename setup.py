#!/usr/bin/env python3
from setuptools import setup

setup(
    name="xiaogpt",
    description="Play ChatGPT with xiaomi AI speaker",
    version="0.3.1",
    license="MIT",
    author="yihong0618",
    author_email="zouzou0208@gmail.com",
    url="https://github.com/yihong0618/xiaogpt",
    python_requires=">=3.7",
    install_requires=["openai", "miservice_fork", "requests", "revChatGPT", "rich"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": ["xiaogpt = xiaogpt.cli:main"],
    },
)
