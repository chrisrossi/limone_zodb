import os
import sys

from setuptools import setup, find_packages

VERSION = '0.1a1'

here = os.path.abspath(os.path.dirname(__file__))
try:
    README = open(os.path.join(here, 'README.rst')).read()
    CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()
except IOError:
    README = CHANGES = ''

install_requires = [
    'limone',
    'ZODB3',
    ]

tests_require = install_requires

if sys.version_info[:2] < (2, 7):
    tests_require += ['unittest2']

setup(name='limone_zodb',
      version=VERSION,
      description=('ZODB persistence for Limone content types.'),
      long_description=README + '\n\n' +  CHANGES,
      classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Framework :: Pylons",
        "License :: Repoze Public License",
        ],
      keywords='',
      author="Chris Rossi, Archimedean Company",
      author_email="pylons-devel@googlegroups.com",
      url="http://pylonsproject.org",
      license="BSD-derived (http://www.repoze.org/LICENSE.txt)",
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires = install_requires,
      tests_require = tests_require,
      test_suite="limone_zodb.tests",
      entry_points = """\
      """
      )
