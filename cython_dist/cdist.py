"""Adds a cdist setup command
"""

from distutils import dir_util, log
import fnmatch
import os

from Cython.Compiler.Main import compile_multiple, CompilationOptions
from setuptools.command.sdist import sdist as SDistCommand


def globstar_match(filename, pattern):
    """Check if ``filename`` matches ``pattern``

    From the glob (7) manpage:

        Matching is defined by:

        A '?' matches any single character.

        A '*' matches any string, including the empty string.

        An expression "[...]" where the first character after the leading '['
        is not an '!' mathes a single character, namely any of the characters
        enclosed by the brackets. The string enclosed by the brackets cannot
        be empty; therefor ']' can be allowed between brackets.

    globstar:
        the pattern ** used in a pathname expansion context will
        match all files and zero or more directories and subdirectories.
        If the pattern is followed by a /, only directories and
        subdirectories match.
    """
    if '**' in pattern:
        pattern = pattern.replace('/**', '*').replace('**', '*')
        return fnmatch.fnmatch(filename, pattern)
    fparts = filename.split('/')
    pparts = pattern.split('/')
    while fparts:
        fhead = fparts.pop(0)
        try:
            phead = pparts.pop(0)
        except IndexError():
            return True
        if not phead:
            return True
        if not fnmatch.fnmatch(fhead, phead):
            return False
    if pparts:
        return False
    return True


class CDistCommand(SDistCommand):
    """Source Distribution that provides .c files instead of python sources
    """
    # pylint: disable=attribute-defined-outside-init
    description = 'create a source distribution with .c files replacing python sources'

    user_options = [
        ('exclude-sources=', None,
         'Do not convert these files into .c files. [default: __init__.py,setup.py]'),
        ('source-extensions=', None,
         'Convert files with these extensions into .c files [default: py,pyx]'),
        ('include-path=', None,
         'Include these paths to search for headers. Comma-separated list [default: ,]'),
    ]+SDistCommand.user_options

    def initialize_options(self):
        """Set initial values for options before reading.
        """
        SDistCommand.initialize_options(self)
        self.exclude_sources = None
        self.source_extensions = None
        self.include_path = None

    def finalize_options(self):
        """Sanitize and set defaults for final values of options.
        """
        SDistCommand.finalize_options(self)
        self.ensure_string_list('exclude_sources')
        self.ensure_string_list('source_extensions')
        self.ensure_string_list('include_path')
        if self.exclude_sources is None:
            self.exclude_sources = ['**/__init__.py', '**/setup.py']
        if self.source_extensions is None:
            self.source_extensions = ['py', 'pyx']
        self.python_sources = []
        self.compilation_options = CompilationOptions()
        self.compilation_options.cplus = False
        self.compilation_options.include_path = self.include_path or []

    def get_file_list(self):
        """Get the filelist and updates it with C filenames.
        """
        SDistCommand.get_file_list(self)
        old_filelist, self.filelist.files = self.filelist.files[:], []
        for filename in old_filelist:
            for pattern in self.exclude_sources:
                if globstar_match(filename, pattern):
                    self.filelist.append(filename)
                    break
            else:
                root, ext = os.path.splitext(filename)
                if ext[1:] in self.source_extensions:
                    self.python_sources.append(filename)
                    filename = root+'.c'
                self.filelist.append(filename)

        self.filelist.sort()

        # Now we can write the manifest
        SDistCommand.write_manifest(self)

    def write_manifest(self):
        """Do not write manifest file until the filelist is updated with C replacements

        Manifest writing will happen at the end of `get_file_list` instead
        """
        self_ = self
        return

    def make_release_tree(self, base_dir, files):
        """Create the directory tree that will become the dist archive.
        """
        self.mkpath(base_dir)
        dir_util.create_tree(base_dir, files, dry_run=self.dry_run)
        # Original hard link logic from distutils
        # However, /most/ files will not be linked, just compiled over
        if hasattr(os, 'link'):  # can make hard links on this system
            link = 'hard'
            log.info('making hard links in {}...'.format(base_dir))
        else:
            link = None
            log.info('copying files to {}...'.format(base_dir))
        if self.dry_run:
            compiled_files = [os.path.splitext(src)[0]+'.c' for src in self.python_sources]
        else:
            results = compile_multiple(self.python_sources, self.compilation_options)
            compiled_files = [result.c_file for result in results.values()]
        for c_file in compiled_files:
            dest = os.path.join(base_dir, c_file)
            self.move_file(c_file, dest)
        for filename in files:
            if filename not in compiled_files:
                if not os.path.isfile(filename):
                    log.warn('"{}" not a regular file -- skipping'.format(filename))
                else:
                    dest = os.path.join(base_dir, filename)
                    self.copy_file(filename, dest, link=link)

        self.distribution.metadata.write_pkg_info(base_dir)
