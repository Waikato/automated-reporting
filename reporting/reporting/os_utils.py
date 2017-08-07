import reporting.applist as applist
import logging
import os

apps = applist.get_apps()

logger = logging.getLogger(__name__)


def remove_file(fname):
    """
    Quiet deletion of the specified file.

    :param fname: the file to delete
    :type fname: str
    :return: True is successful
    :rtype: bool
    """

    try:
        os.remove(fname)
    except:
        pass


def remove_files(files):
    """
    Removes the specified files.

    :param files: the files to remove
    :type files: list
    """

    for f in files:
        remove_file(f)


def close_file(fd):
    """
    Closes the file with the specified file descriptor.

    :param fd: the file descriptor
    :return: True if successful
    :rtype: bool
    """
    try:
        fd.close()
        return True
    except:
        return False


def close_files(fds):
    """
    Closes the files with the specified file descriptor.

    :param fds: the list of file descriptors
    """

    for fd in fds:
        close_file(fd)
