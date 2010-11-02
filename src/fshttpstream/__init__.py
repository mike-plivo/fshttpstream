'''
fshttpstream package
'''
import gevent.monkey
gevent.monkey.patch_all()

__version__ = '0.2.2'

__author__ = 'Michael Ricordeau'

__author_email__ = 'michael.ricordeau@gmail.com'

__maintainer__ = 'Michael Ricordeau'

__maintainer_email__ = 'michael.ricordeau@gmail.com'

__licence__ = 'GNU Library or Lesser General Public License (LGPL)'

__all__ = ['fsclients',
           'fsconnector',
           'fsevents',
           'fsfilter',
           'fslogger',
           'fstools',
           'fswsgi']

