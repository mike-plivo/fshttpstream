#!/usr/bin/env python

from setuptools import find_packages, setup
from fshttpstream import (__version__, __author__, __author_email__, __maintainer__, __maintainer_email__, __licence__)

setup(name='fshttpstream',
      version=__version__,
      description='Proxy to send freeswitch events to push http stream and/or websocket.',
      url='http://github.com/tamiel/fshttpstream',
      author=__author__,
      author_email=__author_email__,
      maintainer=__maintainer__,
      maintainer_email=__maintainer_email__,
      platforms=['linux'],
      long_description='Proxy to send freeswitch events to push http stream and/or websocket.',
      packages=['fshttpstream'],
      license=__licence__,
      install_requires=['gevent'],
      zip_safe=False,
      classifiers=[
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
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

