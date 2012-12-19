from distutils.core import setup

setup(
  name='bw2analyzer',
  version="0.1.1",
  packages=["bw2analyzer"],
  author="Chris Mutel",
  author_email="cmutel@gmail.com",
  license=open('LICENSE.txt').read(),
  requires=["brightway2"],
  long_description=open('README.txt').read(),
)
