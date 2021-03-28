#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Post commit tasks.

The script generates tasks(another scripts) that will be run by the external
    scheduler

REQUIREMENTS:
    Python >=3.6, because of:
        f-strings (https://docs.python.org/3.6/reference/lexical_analysis.html#f-strings)

KNOWN BUGS:
 - Troubles with unicode messages when running in non-unicode console.
    lasy lame fix: run from inside the bash script with LC_ALL and LANG
      set to C.UTF-8

EXAMPLE OF EXTERNAL module import:
    sys.path.insert(1, os.path.dirname(os.path.realpath(__file__)) + r'/../_shared_scripts_')
    from teamcitybuildprofiler.api import *
"""

import atexit
import codecs
import sys
import os
import re
import json
import subprocess
import shlex
from urllib.request import Request, urlopen
from logsystem import Logging

LOG = Logging()
ENABLE_DEBUG_LOG = True
YT_TOKEN = os.environ['YT_TOKEN']
YT_GET_FIELD = r'Fix%20versions'
# list names lowcased, please.
SKIP_AUTHORS = ('buildbot', )
# where all of the scripts will be created

TASKS_HOMEDIR = r'/home/svn/post-commit.tasks' if os.name != 'nt' else r'C:\git_projects\svnhooks\.test'


class YoutrackHandler:
    """Handle youtrack methods."""

    token = YT_TOKEN
    url = r'https://youtrack.corp.ru'
    issue_id = None

    def __init__(self, commit):
        """init."""
        self.__update_issue_id(commit.message)

    def __update_issue_id(self, message):
        """Extract issue id from log message. And store it in self.issue_id."""
        try:
            self.issue_id=re.search(r'\b#?([A-Z]+-\d+).*', message).group(1)
        except AttributeError:
            pass


    def __urlrequest(self, url):
        headers = {'Accept': 'application/json',
                    'Authorization': 'Bearer {}'.format(self.token)}
        req = Request(url, headers=headers)
        try:
            resp = urlopen(req)
            data = resp.read()
            return data.decode()
        except Exception as e:
            warn_msg = ('[WARN] Your commit was accepted,'
                        ' but there were some problems:\n {}'.format(e))
            print(warn_msg, file=sys.stderr)
            return None

    def get_field_value(self, field):
        """Return given youtrack field value."""
        url = '{0}/api/issues/{1}/customFields/{2}?fields=value(name)'.format(
                self.url, self.issue_id, field)
        data = self.__urlrequest(url)

        LOG.debug(f'youtrack api answer: {data}')

        try:
            result = json.loads(data)
            return result['value']['name']
        except Exception as e:
            warn_msg = ('[WARN] Your commit was accepted, '
                        'but i couldnt parse the results\n {}'.format(e))
            print(warn_msg, file=sys.stderr)
            return None


class CommitHandler():
    """Handles commit parts.
        On init harvest commit author and commit message.
        when unittesting, set message and author props.
    """

    def __init__(self, repos=None, rev=None,
                txn=None, message=None, author=None, skip_authors=()):
        """init."""
        self.author = author
        self.message = message
        self.repos = repos
        self.rev = rev
        self.txn = txn
        self.skip_authors = skip_authors

        self.__load_commit_message()
        self.__load_commit_author()

    def __load_commit_message(self):
        """Get commit message from transaction.
            return if we are in unittesting mode.
        """
        if self.message:
            return

        cmd = 'svnlook log "{0}" -r {1}'.format(self.repos, self.rev)
        args = shlex.split(cmd)
        p = subprocess.run(args, capture_output=True)
        if p.returncode == 0:
            try:
                self.message = p.stdout.decode("utf-8")
            except UnicodeDecodeError:
                self.message = p.stdout.decode("cp1251")


    def __load_commit_author(self):
        """Get commit's author.
            return if we are in unittesting mode.
        """

        if self.author:
            return

        cmd = 'svnlook author "{0}" -r {1}'.format(self.repos, self.rev)
        args = shlex.split(cmd)
        p = subprocess.run(args, capture_output=True)
        if p.returncode == 0:
            self.author = p.stdout.decode().lower().strip()


class TaskPatchCommitMessageHandler:
    """Generate pathched commit task."""

    def __init__(self, commit_msg_file=None,
                 task_file=None):
        """init."""
        self.commit_msg_file = commit_msg_file
        self.task_file = task_file

    def write(self, filename, content):
        """Write file content."""
        with codecs.open(filename, 'w', "utf-8") as f:
            f.write(content)


@atexit.register
def close_log_handlers():
    """Close all of the logging handlers."""
    LOG.close()


def init():
    """Initialize handlers."""
    commit = CommitHandler(
        repos=sys.argv[1],
        rev=sys.argv[2],
        txn=sys.argv[3],
        skip_authors=SKIP_AUTHORS
    )

    files_prefix = r'{}/{}-changelog-{}'.format(
                     TASKS_HOMEDIR,
                     os.path.split(commit.repos)[1],
                     commit.rev)

    task = TaskPatchCommitMessageHandler(
        commit_msg_file = files_prefix + r'.logmessage',
        task_file       = files_prefix + r'.task'
    )

    LOG.enable_console(formatter="[%(levelname)s] %(message)s", level="warn")
    if ENABLE_DEBUG_LOG:
        LOG.enable_file(files_prefix + r'.script.log', level="debug")

    LOG.debug(f'repos:{commit.repos} rev:{commit.rev} txn:{commit.txn}\n'
              f'author:{commit.author}\n'
              f'orig.msg:{commit.message}')

    if not commit.message:
        LOG.error('something went wrong while reading commit message')
        sys.exit(0)

    if commit.author in commit.skip_authors:
        LOG.warn(f'skip commits from {commit.author}')
        sys.exit(0)

    yt = YoutrackHandler(commit)

    if not yt.issue_id:
        LOG.warn('issue pattern not found in logmessage')
        sys.exit(0)

    return yt, task, commit


def main():
    """Enter logic."""
    yt, task, commit = init()

    youtrack_fix_in_vers = yt.get_field_value(YT_GET_FIELD)
    if not youtrack_fix_in_vers:
        LOG.warn(f'youtrack field {YT_GET_FIELD} not found in {yt.issue_id}')
        sys.exit(0)

    commit.message = '[{0}] '.format(youtrack_fix_in_vers) + commit.message

    LOG.debug(f"changed logmsg: {commit.message}")
    task.write(task.commit_msg_file, commit.message)

    cmd = (
        f'svnadmin setlog "{commit.repos}" -r {commit.rev} --bypass-hooks {task.commit_msg_file}\n'
        f'mv {task.commit_msg_file} {task.commit_msg_file}.done\n'
    )
    LOG.debug(f"task cmd: {cmd}")
    task.write(task.task_file, cmd)


if __name__ == "__main__":
    main()
