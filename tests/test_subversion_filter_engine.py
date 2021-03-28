#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pytest tests."""

import os
import sys
sys.path.insert(1, os.path.dirname(os.path.realpath(__file__)) +
                '/../playbooks/roles/subversion/files/hooks/_shared_scripts_')


from filter_engine import Filters, get_extension, utf8encoded, get_linefeeds


DATA= {
        "repos": None,
        "revision": None,
        "txn" : None,
        "log_msg" : "abcde",
        "revision_files" : (
            ("A", "master/art/source/someUpper.txt"),
            ("D", "deletedfile"),
        ),
        "info" : None,
        "dirs_changed" : None,
    }
f = Filters(DATA)
f.default_filter_paths = ('/work_version/pc/data/', '/art/source/',)

def test_message_len():
    """test check_comment_len() method."""
    assert f.check_comment_len(10) is False
    assert len(f.errors) == 1
    assert f.check_comment_len(4) is True

def test_filenames_len():
    """test check_filenames_len() method."""
    f.data["revision_files"] = (
            ("A", "master/art/source/someUpper.txt"),
            ("A", "master/art/source/somelongnameblblblblblblblblblblblblb.txt"),
        )
    assert f.check_filenames_len(20) is False
    assert f.check_filenames_len(128) is True

def test_filenames_len_deleted():
    """test check_filenames_len() method with deleted files."""
    f.data["revision_files"] = (
            ("A", "master/art/source/someUpper.txt"),
            ("D", "master/art/source/somelongnameblblblblblblblblblblblblb.txt"),
        )
    assert f.check_filenames_len(20) is True

def test_filenames_len_misspath():
    """test check_filenames_len() method with missed paths."""
    f.data["revision_files"] = (
            ("A", "master/art/source/someUpper.txt"),
            ("A", "master/none/source/somelongnameblblblblblblblblblblblblb.txt"),
        )
    assert f.check_filenames_len(20) is True

def test_filepath_validchars():
    """test check_filepath_validchars() method."""
    f.data["revision_files"] = (
            ("A", "master/art/source/validfilename.txt"),
        )
    assert f.check_filepath_validchars() is True

def test_filepath_validchars_wrong_chars():
    """test check_filepath_validchars() method."""
    f.data["revision_files"] = (
            ("A", "master/art/source/invali dfilename.txt"),
        )
    assert f.check_filepath_validchars() is False

def test_filepath_validchars_wrong_chars_deleted_file():
    """test check_filepath_validchars() method."""
    f.data["revision_files"] = (
            ("D", "master/art/source/invali dfilename.txt"),
            ("A", "master/art/source/validfilename.txt"),
        )
    assert f.check_filepath_validchars() is True

def test_filepath_validchars_wrong_chars_misspath():
    """test check_filepath_validchars() method."""
    f.data["revision_files"] = (
            ("A", "master/somepath/invali dfilename.txt"),
        )
    assert f.check_filepath_validchars() is True

def test_changelist_to_tuple():
    """test converting changelist to tuple."""
    changelist = ("A  master/one.txt\n"
                 "A   master/two.txt\n"
                 "D   master/three.txt")

    # should return a tuple of tuples:
    # (('A', 'master/one.txt'), ('A', 'master/two.txt'), ...
    t = f._Commit__changelist_to_tuple(changelist)
    assert type(t) is tuple
    assert t[1][1] == 'master/two.txt'

def test_can_be_skipped_by_op():
    """test Filter.__can_be_skipped()."""
    op = "A"
    paths = ("/work_version/",)
    fname = "master/work_version/data/file.txt"
    skip_ops=('D', 'A')
    assert f._Filters__can_be_skipped(op=op, fname=fname, paths=paths, skip_ops=skip_ops) is True

def test_can_be_skipped_by_paths():
    """test Filter.__can_be_skipped()."""
    op = "A"
    paths = ("/work_version/",)
    fname = "master/miss_path/data/file.txt"
    skip_ops=()
    assert f._Filters__can_be_skipped(op=op, fname=fname, paths=paths, skip_ops=skip_ops) is True

def test_can_be_skipped_false():
    """test Filter.__can_be_skipped()."""
    op = "D"
    fname = "master/work_version/data/file.txt"
    paths = ("/work_version/",)
    assert f._Filters__can_be_skipped(op=op, fname=fname, skip_ops=('A','U',), paths=paths) is False


def test_utf8encoded():
    """test utf8encoded()."""
    content = "тест".encode('utf-8')
    assert utf8encoded(content=content) is True

def test_get_extension():
    """test get_extension func."""
    fn = '/master/art/source/file name.Ext'
    assert get_extension(fn) == '.Ext'
    assert get_extension(path=fn, locased=True) == '.ext'

def test_get_extension_noext():
    """test get_extension func."""
    fn = '/master/art/source/filename'
    assert get_extension(fn) == ''


def test_check_locase():
    f.data["revision_files"] = (
            ("A", "master/art/source/Filename.txt"),
        )
    paths=('/art/source/',)
    extensions=('.dae', '.txt',)
    assert f.check_locase(paths, extensions) is False

def test_check_locase_misspatterns():
    f.data["revision_files"] = (
            ("A", "master/no/source/MissPath.txt"),
            ("A", "master/art/source/MissExtension.tt"),
            ("A", "master/art/source/excluded/Im In Excluded path.txt"),
            ("D", "master/art/source/DeletedFile.txt"),
        )
    paths=('/art/source/',)
    extensions=('.dae', '.txt',)
    exclude_paths=('/blackhole/','/excluded/',)
    assert f.check_locase(paths, extensions,exclude_paths=exclude_paths) is True

def test_banned_extensions_misspatterns():
    f.data["revision_files"] = (
        ("A", "master/art/source/extension.tt"),
        ("A", "master/art/misspath/extension.txt"),
    )
    paths=('/art/source/',)
    extensions=('.dae', '.txt',)
    assert f.check_banned_extensions(paths, extensions) is True

def test_banned_extensions():
    f.data["revision_files"] = (
        ("A", "master/art/source/extension.txt"),
    )
    paths=('/art/source/',)
    extensions=('.dae', '.txt',)
    assert f.check_banned_extensions(paths, extensions) is False

def test_banned_path_patterns():
    f.data["revision_files"] = (
        ("A", "master/art/source/extension.txt"),
        ("A", "master/art/source/mayaSwatches/extension.txt"),
        ("A", "master/art/source/extension.blend1"),
    )
    regex_patterns=(r'.*/mayaSwatches/.*',
                    r'.*\.(txt|blend\d+)$',)
    assert f.check_banned_path_patterns(regex_patterns) is False

def test_banned_path_patterns_ext():
    f.data["revision_files"] = (
        ("A", "master/work_version/pc/data/extension.txt"),
        ("A", "master/art/source/extension.blend1"),
    )
    regex_patterns=(r'.*/mayaSwatches/.*',
                r'^.*/art/source/.*\.(blend\d+|swatches)$',
                r'.*\.(log|tmp|db|pyc)$',)
    assert f.check_banned_path_patterns(regex_patterns) is False

def test_banned_path_patterns_miss():
    f.data["revision_files"] = (
        ("A", "master/work_version/pc/data/MissedPath.txt"),
        ("D", "master/art/source/DeletedFile.blend"),
        ("A", "master/art/source/OkFile.name"),
    )
    regex_patterns=(r'.*/mayaSwatches/.*',
                r'.*\.(txt|blend\d?)$',)
    paths=('/art/source/',)
    assert f.check_banned_path_patterns(regex_patterns, paths) is True

def test_banned_path_patterns_filename_len():
    f.data["revision_files"] = (
        ("A", "master/work_version/pc/data/verylongfilenames.txt"),
    )
    regex_patterns=(r'.*/[^/]{20,}$',)
    assert f.check_banned_path_patterns(regex_patterns) is False


def test_get_linefeeds():
    assert get_linefeeds('hello\nworld') == 'unix'
    assert get_linefeeds('there are no linefeeds') is None

def test_check_pared_metafiles():
    f.data["revision_files"] = (
        ("A", "master/datafile.txt"),
        ("A", "master/datafile.txt.meta"),
        ("D", "master/tresh/datafile.txt"),
    )
    assert f.check_pared_metafiles(regex_path=r'master/.+', regex_path_exclude='.*/tresh/.*') is True

def test_check_pared_metafiles_failed():
    f.data["revision_files"] = (
        ("A", "master/datafile.txt"),
        ("A", "master/datafile.txt.meta"),
        ("D", "master/tresh/datafile.txt"),
    )
    assert f.check_pared_metafiles(regex_path=r'master/.+') is False