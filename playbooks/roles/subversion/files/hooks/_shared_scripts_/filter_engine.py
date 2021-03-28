#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Filtering engine classes."""

import os
import re
import sys
from subprocess import PIPE, STDOUT, Popen
import subprocess
import shlex

def get_linefeeds(content):
    """Return line-feed style."""
    if '\r\n' in content:
        return 'dos'
    elif '\n' in content:
        return 'unix'
    elif '\r' in content:
        return 'mac'
    else:
        return None


def utf8encoded(content):
    """Return True if content is encoded with given codepage."""
    try:
        content.decode('utf-8')
        return True
    except UnicodeDecodeError:
        return False


def sysexec(cmd, decode=True):
    """Execute system utility."""
    p = subprocess.run(shlex.split(cmd), stdout=PIPE, stderr=STDOUT)

    if decode:
        try:
            output = p.stdout.decode("utf-8").strip()
        except UnicodeDecodeError:
            output = p.stdout.decode("cp1251").strip()
    else:
        output = p.stdout

    return (output, p.returncode)


def get_extension(path, locased=False):
    """Return file extension with dot. I.e. '.txt'."""
    ext = os.path.splitext(path)[-1]
    if locased:
        return ext.lower()
    return ext


class Commit(object):
    """Commit class."""

    data = {
        "repos": None,
        "revision": None,
        "txn" : None,
        "log_msg" : None,
        "revision_files" : (),
        "info" : None,
        "dirs_changed" : None,
    }

    def __init__(self, data=None):
        """Load commit metainfo."""
        if not data:
            data = {}

        if data:
            self.data.update(data)
        else:
            self.__check_args()
            self.data["repos"] = sys.argv[1]

            try:
                self.__update_rev_txn(sys.argv[2])
            except IndexError:
                pass

            self.data["log_msg"] = self.__svnlook("log")
            self.data["info"] = self.__svnlook("info")
            self.data["dirs_changed"] = self.__svnlook("dirs-changed")

            # define changelist generator and generate a tuple from it.
            changelist = self.__svnlook("changed")
            self.data["revision_files"] = self.__changelist_to_tuple(changelist)


    def __changelist_to_tuple(self, changelist):
        """Convert changelist to tuple."""
        changed_paths = re.split('\n| {2,}|\t+', changelist)
        it = iter(changed_paths)
        return tuple(zip(it, it))


    def __update_rev_txn(self, n):
        """Update commit transaction id and revision number props."""
        try:
            self.data["revision"] = int(n)
        except ValueError:
            self.data["txn"] = n


    def __svnlook(self, cmd: str = "log", filename=None, decode=True) -> str:
        """Return svnlook command output."""
        cmd = f'svnlook {cmd} "{self.data["repos"]}"'

        if self.data["txn"]:
            cmd = cmd + f' -t "{self.data["txn"]}"'

        if self.data["revision"]:
            cmd = cmd + f' -r "{self.data["revision"]}"'

        if filename:
            cmd = f'{cmd} "{filename}"'

        output, exitcode = sysexec(cmd, decode)
        if exitcode == 0:
            return output

        print(output)
        sys.exit(exitcode)


    def __check_args(self):
        """Check script arguments."""
        if len(sys.argv) < 2:
            print("Usage: <repository path> [<transaction>]")
            sys.exit(1)


class Filters(Commit):
    """Filter methods.

    All checks return Boolean.
    """

    errors = []
    default_filter_paths = ('/work_version/pc/data/', '/art/source/',)

    def __init__(self, data=None):
        """Init."""
        if not data:
            data = {}
        super(Filters, self).__init__(data=data)


    def __can_be_skipped(self, op, fname, skip_ops=('D',), paths=(), exclude_paths=()):
        """If the fname can be skipped of the check.
              arg       type    description
              -------------------------------------------
              op        char    operation (D,A,U, etc...)
              fname     string  full path of operation

              skip_ops  tuplet  list of operations to skip

              paths     tuplet  fname should contain named paths elements
              exclude_paths
                        tuplet  ...except these paths elements.
        """
        if op in skip_ops or not any(x in fname for x in paths) \
                or any(y in fname for y in exclude_paths):
            return True
        return False


    def check_linefeeds(self, linefeeds='dos', regex_patterns=(), paths=(), exclude_paths=()):
        """Check the given files have a proper line breaks.

        The known types are: dos, unix, mac
        """
        assert linefeeds in ('dos', 'unix', 'mac',)

        print("*** check line-breaks")
        errors_num = len(self.errors)

        if not regex_patterns:
            regex_patterns = (r'.*\.(cs)$',)

        if not paths:
            paths = self.default_filter_paths

        for pattern in regex_patterns:
            patt_fname = re.compile(pattern)

            for op, fname in self.data["revision_files"]:
                if self.__can_be_skipped(op=op, fname=fname, paths=paths, exclude_paths=exclude_paths):
                    continue
                if patt_fname.match(fname):
                    content = super()._Commit__svnlook("cat", filename=fname, decode=True)
                    lf = get_linefeeds(content)
                    if not lf:
                        continue
                    if not lf == linefeeds:
                        self.errors.append(f'Convert "{fname}" to have {linefeeds} line-breaks. (it has {lf} breaks now)')

        return errors_num == len(self.errors)


    def check_unicode_content(self, regex_patterns=(), paths=(), exclude_paths=()):
        """Check the given files are utf-8 encoded."""
        print("*** check files are unicoded")
        errors_num = len(self.errors)

        if not regex_patterns:
            regex_patterns = (r'.*\.(xml|lua)$',)

        if not paths:
            paths = self.default_filter_paths

        for pattern in regex_patterns:
            patt_fname = re.compile(pattern)

            for op, fname in self.data["revision_files"]:
                if self.__can_be_skipped(op=op, fname=fname, paths=paths, exclude_paths=exclude_paths):
                    continue
                if patt_fname.match(fname):
                    content = super()._Commit__svnlook("cat", filename=fname, decode=False)
                    if not utf8encoded(content):
                        self.errors.append(f'{fname} should be utf-8 encoded')

        return errors_num == len(self.errors)


    def check_comment_len(self, min_bytes=5):
        """Check for the minmum commit message length."""
        print("*** check commit message length")
        if len(self.data["log_msg"].strip()) < min_bytes:
            self.errors.append(f'Log message should be at least {min_bytes} bytes long')
            return False
        else:
            return True


    def check_filenames_len(self, max_chars=128, paths=(), exclude_paths=()):
        """Check for maximum allowed filename length.

        some platforms have a restrictions on filename length.
        as an example, Xenon's FATX has a filename limited to  42 chars.
        """
        print("*** check filenames length")
        errors_num = len(self.errors)
        if not paths:
            paths = self.default_filter_paths

        for op, fname in self.data["revision_files"]:
            if self.__can_be_skipped(op=op, fname=fname, paths=paths, exclude_paths=exclude_paths):
                continue

            flen = len(os.path.split(fname)[-1])
            if flen > max_chars:
                self.errors.append(f'Filename "{fname}" too long ({flen} > {max_chars})')

        return errors_num == len(self.errors)


    def check_filepath_validchars(self, pattern=r'^[-_a-zA-Z0-9/\.\+]+$', paths=(), exclude_paths=()):
        """Check for valid file and directory names."""

        print("*** check filenames are of a valid chars")
        errors_num = len(self.errors)
        if not paths:
            paths = self.default_filter_paths

        patt_fname = re.compile(pattern)

        for op, fname in self.data["revision_files"]:
            if self.__can_be_skipped(op=op, fname=fname, paths=paths, exclude_paths=exclude_paths):
                continue
            if not patt_fname.match(fname):
                self.errors.append(f'Path "{fname}" violates pattern "{pattern}"')

        return errors_num == len(self.errors)


    def check_locase(self, paths=(), extensions=(), exclude_paths=()):
        """Require locase for extensions in given paths."""

        errors_num = len(self.errors)
        print("*** check filenames are in locase.")
        if not paths:
            paths = self.default_filter_paths

        for op, fname in self.data["revision_files"]:
            fname_extention = get_extension(path=fname, locased=True)
            if self.__can_be_skipped(op=op, fname=fname, paths=paths, exclude_paths=exclude_paths) \
                or not fname_extention in extensions:
                continue

            fn = os.path.split(fname)[-1]
            fn_locase = fn.lower()
            if fn != fn_locase:
                self.errors.append(f'"{fn}" should be in locase.')

        return errors_num == len(self.errors)


    def check_lua(self,extensions=('.lua',), luacheck_path='/usr/bin/luacheck', paths=(), exclude_paths=()):
        """Deny extensions in given paths."""
        print("*** Lint lua files.")
        errors_num = len(self.errors)

        if not paths:
            paths = self.default_filter_paths

        for op, fname in self.data["revision_files"]:
            fname_extention = get_extension(path=fname, locased=True)
            if self.__can_be_skipped(op=op, fname=fname, paths=paths, exclude_paths=exclude_paths) \
                or not fname_extention in extensions:
                continue

            content = super()._Commit__svnlook("cat", filename=fname, decode=False)
            p = Popen([luacheck_path, '--no-color', '-'], stdout=PIPE, stdin=PIPE, stderr=STDOUT)
            luacheck_stdout = p.communicate(input=content)[0]
            output = luacheck_stdout.decode()

            # exit code 1: warnings found
            if p.returncode > 1:
                self.errors.append(f'syntax check failed for {fname}:\n{output}')

        return errors_num == len(self.errors)


    def check_banned_extensions(self, paths=(), extensions=(), exclude_paths=()):
        """Deny extensions in given paths."""

        errors_num = len(self.errors)
        print("*** Check for restricted extensions.")
        if not paths:
            paths = self.default_filter_paths

        for op, fname in self.data["revision_files"]:
            fname_extention = get_extension(path=fname, locased=True)
            if self.__can_be_skipped(op=op, fname=fname, paths=paths, exclude_paths=exclude_paths) \
                or not fname_extention in extensions:
                continue
            self.errors.append(f'"{fname}" has been banned by extension.')

        return errors_num == len(self.errors)


    def check_banned_path_patterns(self,
                regex_patterns=(r'.*mayaSwatches.*',
                                r'^.*/art/source/.*\.(blend\d+|swatches)$',
                                r'.*\.(bak|log|tmp|db|pyc)$',),
                paths=(),
                exclude_paths=()):
        """Check for valid file and directory names."""
        print("*** check for banned patterns")
        errors_num = len(self.errors)

        if not paths:
            paths = self.default_filter_paths

        for pattern in regex_patterns:
            patt_fname = re.compile(pattern)

            for op, fname in self.data["revision_files"]:
                if self.__can_be_skipped(op=op, fname=fname, paths=paths, exclude_paths=exclude_paths):
                    continue
                if patt_fname.match(fname):
                    self.errors.append(f'Path "{fname}" was banned by pattern: "{pattern}"')


        return errors_num == len(self.errors)


    def check_pared_metafiles(self,
                              meta_ext='.meta',
                              regex_path=r'^.*/unityclient/assets/.+',
                              regex_path_exclude=r'^.*/unityclient/.*\/(\.+)|(.*~$)'):
        """Check all Deleted and Added files/directories has also Deleted/Added .meta file."""
        print("*** check metafiles exist commit")

        metafiles_regex = re.compile(regex_path)
        metafiles_regex_exclude = re.compile(regex_path_exclude)
        metadata_added = []
        metadata_deleted = []

        errors_num = len(self.errors)

        for op, fname in self.data["revision_files"]:
            if metafiles_regex.match(fname.lower()) \
                and not metafiles_regex_exclude.match(fname.lower()):
                # strip '/' from directories for later checks
                if fname[-1] == r'/': fname = fname[:-1]
                if op == 'A':
                    metadata_added.append(fname)
                elif op == 'D':
                    metadata_deleted.append(fname)

        for f in metadata_added:
            # check for missing .meta for added files and directories
            if not os.path.splitext(f)[1] == meta_ext:
                if not f + meta_ext in metadata_added:
                    self.errors.append(f'- [A] "{f}" lacks of .meta file in this commit')

            # check for missing files for added .meta
            elif not os.path.splitext(f)[0] in metadata_added:
                self.errors.append(f'- [A] "{f}" lacks of its basefile in this commit')

        # same logic for deleted files/dirs
        for f in metadata_deleted:
            if not os.path.splitext(f)[1] == meta_ext:
                if not f + meta_ext in metadata_deleted:
                    self.errors.append(f'- [D] "{f}" lacks of .meta file in this commit')
            elif not os.path.splitext(f)[0] in metadata_deleted:
                self.errors.append(f'- [D] "{f}" lacks of its basefile in this commit')

        return errors_num == len(self.errors)

