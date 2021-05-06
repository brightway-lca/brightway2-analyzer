from setuptools import setup


v_temp = {}
with open("bw2analyzer/version.py") as fp:
    exec(fp.read(), v_temp)
version = ".".join((str(x) for x in v_temp["version"]))


setup(
    name="bw2analyzer",
    version=version,
    packages=["bw2analyzer"],
    author="Chris Mutel",
    author_email="cmutel@gmail.com",
    license=open("LICENSE.txt").read(),
    install_requires=[
        "bw2calc",
        "bw2data",
        "matplotlib",
        "numpy",
        "pandas",
        "pyprind",
        "requests",
        "scipy",
        "stats_arrays",
        "tabulate",
    ],
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://bitbucket.org/cmutel/brightway2-analyzer",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Scientific/Engineering :: Mathematics",
        "Topic :: Scientific/Engineering :: Visualization",
    ],
)
