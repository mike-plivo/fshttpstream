#!/usr/bin/env python
import glob
import shutil
import os.path
from setuptools import find_packages, setup
from fshttpstream import (__version__, __author__, __author_email__, __maintainer__, __maintainer_email__, __licence__)

setup(name='fshttpstream',
      version=__version__,
      description='Websocket proxy server to send freeswitch events to websocket client.',
      url='http://github.com/tamiel/fshttpstream',
      author=__author__,
      author_email=__author_email__,
      maintainer=__maintainer__,
      maintainer_email=__maintainer_email__,
      platforms=['linux'],
      long_description='Websocket proxy server to send freeswitch events to websocket client.',
      packages=['fshttpstream'],
      include_package_data = True,
      license=__licence__,
      install_requires=['telephonie', 'gevent-websocket'],
      zip_safe=False,
      classifiers=[
        "License :: OSI Approved :: Mozilla Public License 1.1 (MPL 1.1)",
        "Programming Language :: Python",
        "Operating System :: POSIX",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Communications",
        "Topic :: Multimedia",
        "Environment :: Web Environment",
        "Programming Language :: JavaScript",
        "Intended Audience :: Developers",
        "Intended Audience :: Telecommunications Industry",
        "Development Status :: 4 - Beta"]
     )

