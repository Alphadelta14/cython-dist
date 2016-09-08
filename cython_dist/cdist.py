"""Adds a cdist setup command
"""

from distutils import dir_util, log
import os

from Cython.Compiler.Main import compile_multiple, CompilationOptions
from setuptools.command.sdist import sdist as SDistCommand

from cython_dist.egg_info import EggInfoCommand


class CDistCommand(SDistCommand):
    """Source Distribution that provides .c files instead of python sources
    """
    # pylint: disable=attribute-defined-outside-init
    description = 'create a source distribution with .c files replacing python sources'

    user_options = [
        ('exclude-sources=', None,
         'Do not convert these files into .c files. [default: setup.py,**/__init__.py]'),
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
            self.exclude_sources = ['setup.py', '**/__init__.py']
        if self.source_extensions is None:
            self.source_extensions = ['py', 'pyx']
        self.python_sources = {}
        self.compilation_options = CompilationOptions()
        self.compilation_options.cplus = False
        self.compilation_options.include_path = self.include_path or []

    def run(self):
        """Run the sdist command, but use our patched egg_info and dist_file signature
        """
        # cython_dist.egg_info.EggInfoCommand
        ei_cmd = EggInfoCommand(self.distribution)
        ei_cmd.finalize_options()
        ei_cmd.run()
        self.filelist = ei_cmd.filelist
        self.filelist.append(os.path.join(ei_cmd.egg_info, 'SOURCES.txt'))
        self.check_readme()

        # Run sub commands
        for cmd_name in self.get_sub_commands():
            self.run_command(cmd_name)

        # Call check_metadata only if no 'check' command
        # (distutils <= 2.6)
        import distutils.command

        if 'check' not in distutils.command.__all__:
            self.check_metadata()

        self.make_distribution()

        dist_files = getattr(self.distribution, 'dist_files', [])
        for file in self.archive_files:
            # Use our signature
            data = ('cdist', '', file)
            if data not in dist_files:
                dist_files.append(data)

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
        compiled_files = self.python_sources.values()
        if not self.dry_run:
            compile_multiple(self.python_sources.keys(), self.compilation_options)
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
