from django.template import loader
from django.http import HttpResponse
from django.db import connection

import reporting.applist as applist
from reporting.error import create_error_response
from csv import DictReader
import django_tables2 as tables
import traceback
import sys

MINIMUM_DAYS = 25

def actual_balance_key(a):
    """
    Custom key function for sorting the results list generated in the 'upload' view.

    :param a: the row
    :type a: dict
    :return: the actual balance
    :rtype: float
    """
    return float(a['actual_balance'])

def index(request):

    # get all schools
    cursor = connection.cursor()
    cursor.execute("""
        SELECT DISTINCT(owning_school_clevel)
        FROM grade_results
        ORDER BY owning_school_clevel ASC
        """)
    schools = []
    for row in cursor.fetchall():
        schools.append(row[0])
    # configure template
    template = loader.get_template('leave/index.html')
    context = applist.template_context('leave')
    context['schools'] = schools
    context['minimum'] = MINIMUM_DAYS
    return HttpResponse(template.render(context, request))

def upload(request):
    # get parameters
    if "school" not in request.POST:
        return create_error_response(request, 'leave', 'No school defined!')
    schools = request.POST.getlist("school")

    if "minimum" not in request.POST:
        return create_error_response(request, 'leave', 'No minimum number of days defined!')
    minimum = int(request.POST["minimum"])

    csv = request.FILES['datafile']

    order = ['school', 'employee', 'manager', 'actual_balance', 'leave_accrued', 'future_leave_bookings', 'current_balance', 'current_allocated_balance']
    header = {}
    header['school'] = 'Faculty/School'
    header['employee'] = 'Employee'
    header['manager'] = 'Manager'
    header['actual_balance'] = 'Actual balance'
    header['leave_accrued'] = 'Leave accrued'
    header['future_leave_bookings'] = 'Future bookings'
    header['current_balance'] = 'Current balance'
    header['current_allocated_balance'] = 'Current allocated balance'
    result = []
    try:
        with open(csv.temporary_file_path(), encoding='ISO-8859-1') as csvfile:
            reader = DictReader(csvfile)
            reader.fieldnames = [name.lower().replace(" ", "_") for name in reader.fieldnames]
            for row in reader:
                school = row['main_clevel']
                if school not in schools:
                    continue
                leave_type = row['leave_type']
                if leave_type != "AL":  # TODO any other types of leave to add/include?
                    continue
                rrow = {}
                rrow['school'] = school
                rrow['employee'] = row['employee_name']
                rrow['manager'] = row['manager']
                rrow['actual_balance'] = float(row['current_allocated_balance']) - float(row['future_leave_bookings'])
                rrow['current_balance'] = row['current_balance']
                rrow['current_allocated_balance'] = row['current_allocated_balance']
                rrow['leave_accrued'] = row['accrual']
                rrow['future_leave_bookings'] = row['future_leave_bookings']
                if int(rrow['actual_balance']) >= minimum:
                    result.append(rrow)
    except Exception as ex:
        traceback.print_exc(file=sys.stdout)
        return create_error_response(request, 'leave', 'Failed to read uploaded CSV file: ' + str(ex))

    # sort
    result.sort(key=actual_balance_key, reverse=True)

    # configure template
    template = loader.get_template('leave/output.html')
    context = applist.template_context('leave')
    context['table'] = result
    context['header'] = header
    context['order'] = order
    return HttpResponse(template.render(context, request))
