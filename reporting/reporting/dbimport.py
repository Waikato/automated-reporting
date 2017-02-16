from reporting.models import GradeResults
from supervisors.models import Supervisors
from reporting.db import null_empty_cells, truncate_strings
from csv import DictReader
import gzip

def import_grade_results(year, csv, gzip):
    """
    Imports the grade results for a specific year (Brio/Hyperion export).

    :param year: the year to import the results for (eg 2015)
    :type year: int
    :param csv: the CSV file to import, can be gzip compressed
    :type csv: str
    :param gzip: true if GZIP compressed
    :type gzip: bool
    :return: None if successful, otherwise error message
    :rtype: str
    """
    return None

def populate_student_dates():
    """
    Populates the studentdates table. Truncates the table first.

    :return: None if successful, otherwise error message
    :rtype: str
    """
    return None

def import_supervisors(csv):
    """
    Imports the supervisors (Jade Export).

    :param csv: the CSV file to import
    :type csv: str
    :return: None if successful, otherwise error message
    :rtype: str
    """
    Supervisors.objects.all().delete()
    try:
        with open(csv, encoding='ISO-8859-1') as csvfile:
            reader = DictReader(csvfile)
            reader.fieldnames = [name.lower().replace(" ", "_") for name in reader.fieldnames]
            for row in reader:
                truncate_strings(row, 250)
                s = Supervisors()
                s.student_id = row['student'][row['student'].rfind(' ')+1:]
                s.student = row['student']
                s.supervisor = row['supervisor']
                s.active_roles = row['active_roles']
                s.entity = row['entity']
                s.agreement_status = row['agreement_status']
                s.date_agreed = row['date_agreed']
                s.title = row['title']
                s.quals = row['quals']
                s.comments = row['comments']
                s.save()
    except Exception as ex:
        return str(ex)

    return None
