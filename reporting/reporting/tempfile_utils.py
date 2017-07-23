import tempfile
import time
import shutil
import os
import reporting.settings


def gettempdir():
    """
    Returns either a custom temp directory of the default system one.

    :return: the temp directory
    :rtype: str
    """

    if reporting.settings.TMP_DIR is not None:
        return reporting.settings.TMP_DIR
    else:
        return tempfile.gettempdir()


def create_temp_copy(infile):
    """
    Creates a copy (temp file) of the incoming file, returns
    the new filename.

    Taken from here:
    https://stackoverflow.com/a/6587648/4698227

    :param infile: the file to create a copy of
    :type infile: str
    :return: the file name of the temp file (copy)
    :rtype: str
    """

    temp_dir = gettempdir()
    result = os.path.join(temp_dir, str(time.time()))
    shutil.copy2(infile, result)
    return result
