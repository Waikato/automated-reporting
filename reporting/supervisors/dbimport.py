from supervisors.models import Supervisors
from reporting.db import truncate_strings
from csv import DictReader

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
        print(csv)
        with open(csv, encoding='ISO-8859-1') as csvfile:
            reader = DictReader(csvfile)
            for row in reader:
                truncate_strings(row, 250)
                s = Supervisors()
                s.student_id = row['Student'][row['Student'].rfind(' ')+1:]
                s.student = row['Student']
                s.supervisor = row['Supervisor']
                s.active_roles = row['Active Roles']
                s.entity = row['Entity']
                s.agreement_status = row['Agreement Status']
                s.date_agreed = row['Date Agreed']
                s.title = row['Title']
                s.quals = row['Quals']
                s.comments = row['Comments']
                s.save()
    except Exception as ex:
        return str(ex)

    return None
