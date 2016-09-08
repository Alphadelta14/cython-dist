# cython-dist
Provide cython source distributions.

This will convert `.py` and `.pyx` files into `.c` source files to be provided
with your package. Upon package installation, these files will automatically
be compiled to shared objects (`.so` files).

## Installation
```bash
pip install cython-dist
```

## Usage

cython-dist provides an extra setuptools command.

```bash
python setup.py cdist
```

## Configuration
Add a `[cdist]` section to your `setup.cfg`. Example:

```ini
[cdist]
exclude-sources=setup.py,**/__init__.py,tests/
include-path=lib/python2.7/site-packages/numpy/core/include/
```

Run `python setup.py --help cdist` for information on configuration options.
