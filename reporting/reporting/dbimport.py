from reporting.models import GradeResults
from reporting.db import null_empty_cells
from csv import DictReader
import gzip

def import_grade_results(year, csv):
    """
    Imports the grade results for a specific year (Brio/Hyperion export).
2
    :param year: the year to import the results for (eg 2015)
    :type year: int
    :param csv: the CSV file to import, can be gzip compressed
    :type csv: str
    :return: None if successful, otherwise error message
    :rtype: str
    """
    return None
