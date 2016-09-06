"""cython-dist Version File
"""

import subprocess

major = 0
minor = 1
patch = 0

dev = False

if dev is False:
    __version__ = '{}.{}.{}'.format(major, minor, patch)
else:
    branch = subprocess.check_call(['git', 'rev-parse', '--abbrev-ref', 'HEAD'])
    sha = subprocess.check_call(['git', 'rev-parse', 'HEAD'])
    __version__ = '{}.{}.{}+{}-sha.{}'.format(major, minor, patch, branch, sha)
__version_info__ = (major, minor, patch)

__all__ = ['__version__', '__version_info__']
