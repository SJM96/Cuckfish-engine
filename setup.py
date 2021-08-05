from setuptools import setup, find_packages
from Cython.Build import cythonize

with open("requirements.txt") as reqs:
    requirements = reqs.read().splitlines()

setup(
    name="cuckfish",
    version="0.0.1",
    packages=find_packages(exclude=["tests"]),
    include_package_data=True,
    install_requires=requirements,
    entry_points='''
        [console_scripts]
        cuckfish=engine.__main__:cli
    ''',
)
