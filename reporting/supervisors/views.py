from django.template import loader
from django.http import HttpResponse
from django.db import connection
from supervisors.models import StudentDates, Supervisors
from reporting.models import GradeResults

import reporting.applist as applist
from reporting.error import create_error_response
import traceback
import sys
from datetime import date
import csv

YEARS_BACK = 5

def index(request):
    # get all schools
    cursor = connection.cursor()
    cursor.execute("""
        SELECT DISTINCT(owning_school_clevel)
        FROM %s
        ORDER BY owning_school_clevel ASC
        """ % GradeResults._meta.db_table)
    schools = []
    for row in cursor.fetchall():
        schools.append(row[0])
    # get year from earliest start date
    cursor.execute("""
        select extract(year from min(start_date))
        from %s
        """ % StudentDates._meta.db_table)
    min_year = None
    max_years = None
    for row in cursor.fetchall():
        min_year = row[0]
    if min_year is not None:
        max_years = date.today().year - min_year
    # configure template
    template = loader.get_template('supervisors/index.html')
    context = applist.template_context('supervisors')
    context['schools'] = schools
    context['years_back'] = YEARS_BACK
    if max_years is not None:
        context['max_years'] = int(max_years)
    return HttpResponse(template.render(context, request))

def add_student(data, school, department, supervisor, studentid, program):
    """
    Adds the student to the "data" structure. Overview of the data structure (<name> is
    a key in a dictionary):

    <faculty>
      - <department>
        - <supervisor>
          - <program> (PD, MD)
            - <studentid>
              - name (string)
              - start_date (date)
              - end_date (date)
              - months (float)
              - full_time (True|False)
              - chief_supervisor (True|False|None)
              - current (True|False)

    :param data: the data structure to extend
    :type data: dict
    :param school: the name of the school/faculty
    :type school: str
    :param department: the name of the department
    :type department: str
    :param supervisor: the name of the supervisor
    :type supervisor: str
    :param studentid: the student id
    :type studentid: str
    :param program: the program (PD/MD)
    :type program: str
    """

    # ensure data structures are present
    if school not in data:
        data[school] = {}
    if department not in data[school]:
        data[school][department] = {}
    if supervisor not in data[school][department]:
        data[school][department][supervisor] = {}
    if program not in data[school][department][supervisor]:
        data[school][department][supervisor][program] = {}
    if studentid not in data[school][department][supervisor][program]:
        data[school][department][supervisor][program][studentid] = {}

    # load student data
    today = date.today().strftime("%Y-%m-%d")
    sdata = data[school][department][supervisor][program][studentid]
    for s in StudentDates.objects.all().filter(school=school, department=department, student_id=studentid, program=program):
        sname = None
        for g in GradeResults.objects.all().filter(student_id=studentid):
            sname = g.name
            break
        chief = None
        for sv in Supervisors.objects.all().filter(student_id=studentid, supervisor=supervisor):
            chief = "Yes" if "Chief" in sv.active_roles else "No"
        if s.full_time is None:
            full_time = 'N/A'
        elif s.full_time:
            full_time = 'Yes'
        else:
            full_time = 'No'
        sdata['name'] = sname
        sdata['start_date'] = s.start_date.strftime("%Y-%m-%d")
        sdata['end_date'] = s.end_date.strftime("%Y-%m-%d")
        sdata['months'] = s.months
        sdata['full_time'] = full_time
        sdata['chief_supervisor'] = chief
        sdata['current'] = s.end_date.strftime("%Y-%m-%d") < today

def list_supervisors(request):
    # get parameters
    if "school" not in request.POST:
        return create_error_response(request, 'supervisors', 'No school defined!')
    schools = request.POST.getlist("school")

    if "years_back" not in request.POST:
        return create_error_response(request, 'supervisors', 'No number of years back defined!')
    years_back = int(request.POST["years_back"])
    start_year = date.today().year - years_back

    if "csv" not in request.POST:
        export = None
    else:
        export = "csv"

    sql = """
        select sd.school, sd.department, s.supervisor, s.student_id, sd.program
        from supervisors_studentdates sd, supervisors_supervisors s
        where sd.student_id = s.student_id
        and sd.school in ('%s')
        and sd.start_date >= '%s-01-01'
        group by sd.school, sd.department, s.supervisor, s.student_id, sd.program
        order by sd.school, sd.department, s.supervisor, s.student_id, sd.program
        """ % ("','".join(schools), str(start_year))
    cursor = connection.cursor()
    cursor.execute(sql)
    result = {}
    for row in cursor.fetchall():
        try:
            add_student(data=result, school=row[0], department=row[1], supervisor=row[2], studentid=row[3], program=row[4])
        except Exception as ex:
            print("row=" + str(row))
            traceback.print_exc(file=sys.stdout)

    # CSV or HTML?
    if export == "csv":
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="supervisors-%s.csv"' % date.today().strftime("%Y-%m-%d")
        writer = csv.writer(response)
        writer.writerow([
            'Faculty/School',
            'Department',
            'Supervisor',
            'Program',
            'ID',
            'Name',
            'Start date',
            'End date',
            'Months',
            'Full time',
            'Chief supervisor',
            'Current',
        ])
        for school in result:
            for dept in result[school]:
                for supervisor in result[school][dept]:
                    for program in result[school][dept][supervisor]:
                        for student in result[school][dept][supervisor][program]:
                            sdata = result[school][dept][supervisor][program][student]
                            writer.writerow([
                                school,
                                dept,
                                supervisor,
                                program,
                                student,
                                sdata['name'],
                                sdata['start_date'],
                                sdata['end_date'],
                                sdata['months'],
                                sdata['full_time'],
                                sdata['chief_supervisor'],
                                sdata['current'],
                            ])
        return response
    else:
        template = loader.get_template('supervisors/list.html')
        context = applist.template_context('supervisors')
        context['results'] = result
        return HttpResponse(template.render(context, request))
