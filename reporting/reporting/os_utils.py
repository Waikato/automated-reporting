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
