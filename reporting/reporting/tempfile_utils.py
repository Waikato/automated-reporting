import tempfile
import time
import shutil
import os

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

    temp_dir = tempfile.gettempdir()
    result = os.path.join(temp_dir, str(time.time()))
    shutil.copy2(infile, result)
    return result
