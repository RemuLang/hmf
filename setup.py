from setuptools import setup, find_packages
from datetime import datetime
from pathlib import Path


with Path('README.md').open() as readme:
    readme = readme.read()

version = 1.0

setup(
    name='hmf',
    version=version if isinstance(version, str) else str(version),
    keywords="", # keywords of your project that separated by comma ","
    description="", # a conceise introduction of your project
    long_description=readme,
    long_description_content_type="text/markdown",
    license='mit',
    python_requires='>=3.6.0',
    url='https://github.com/thautawarm/hmf',
    author='thautawarm',
    author_email='twshere@outlook.com',
    packages=find_packages(),
    entry_points={"console_scripts": []},
    extras = {'REPL': ['pygments', 'prompt_toolkit']},
    install_requires=['rbnf-rts'],
    platforms="any",
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
    zip_safe=False,
)
