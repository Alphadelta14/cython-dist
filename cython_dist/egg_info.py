"""Modified egg_info for capturing new C files instead of Python sources
"""

from distutils import dir_util, log
import fnmatch
import os

from setuptools.command.egg_info import egg_info as _EggInfoCommand
from setuptools.command.egg_info import manifest_maker as _ManifestMaker
from setuptools.command.egg_info import FileList
from setuptools.command.sdist import sdist as SDistCommand
from setuptools.command.sdist import walk_revctrl


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
        pattern = pattern.replace('/**', '*').replace('**/', '*').replace('**', '*')
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


class EggInfoCommand(_EggInfoCommand):
    """Modified egg_info command class to use our ManifestMaker.
    """
    def finalize_options(self):
        """Keep the real egg_info's options.
        """
        self.__dict__ = self.get_finalized_command('egg_info').__dict__

    def find_sources(self):
        """Find sources using our ManifestMaker.
        """
        manifest_filename = os.path.join(self.egg_info, 'SOURCES.txt')
        m_maker = ManifestMaker(self.distribution)
        m_maker.manifest = manifest_filename
        m_maker.prefix = self.egg_info
        m_maker.run()
        self.filelist = m_maker.filelist


class ManifestMaker(_ManifestMaker):
    """Generate a Manifest using Cythonized source files
    """
    def run(self):
        """Run the command.
        """
        self.filelist = FileList()
        if not os.path.exists(self.manifest):
            self.write_manifest()
        self.filelist.findall()
        self.add_defaults()
        if os.path.exists(self.template):
            self.read_template()
        self.prune_file_list()
        # Replace python with c files
        self.update_sources()
        self.filelist.sort()
        self.filelist.remove_duplicates()
        self.write_manifest()

    def update_sources(self):
        """Update the Python files with the C files using cdist options.
        """
        cdist_cmd = self.get_finalized_command('cdist')
        old_filelist, self.filelist.files = self.filelist.files[:], []
        for filename in old_filelist:
            for pattern in cdist_cmd.exclude_sources:
                if globstar_match(filename, pattern):
                    self.filelist.append(filename)
                    break
            else:
                root, ext = os.path.splitext(filename)
                if ext[1:] in cdist_cmd.source_extensions:
                    original = filename
                    filename = root+'.c'
                    cdist_cmd.python_sources[original] = filename
                self.filelist.append(filename)
