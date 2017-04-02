from django.template import loader
from django.http import HttpResponse
from django.db import connection
from supervisors.models import StudentDates, Supervisors
from reporting.models import GradeResults

import reporting.applist as applist
from reporting.form_utils import get_variable_with_error, get_variable
import traceback
import sys
from datetime import date
import csv

YEARS_BACK = 5
""" the default number of years to go back """

def index(request):
    # get all schools
    cursor = connection.cursor()
    cursor.execute("""
        SELECT DISTINCT(school)
        FROM %s
        ORDER BY school ASC
        """ % StudentDates._meta.db_table)
    schools = []
    for row in cursor.fetchall():
        schools.append(row[0])
    # get year from earliest start date
    cursor.execute("""
        select extract(year from min(start_date))
        from %s
        where start_date > '1900-01-01'
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
    context['max_years'] = int(max_years) if max_years is not None else YEARS_BACK
    return HttpResponse(template.render(context, request))

def search_by_faculty(request):
    # get parameters
    response, schools = get_variable_with_error(request, 'supervisors', 'school', as_list=True)
    if response is not None:
        return response

    response, years_back_str = get_variable_with_error(request, 'supervisors', 'years_back')
    if response is not None:
        return response
    years_back = int(years_back_str)

    sql = """
        select distinct(owning_department_clevel)
        from %s
        where owning_school_clevel in ('%s')
        order by owning_department_clevel
        """ % (GradeResults._meta.db_table, "','".join(schools))
    cursor = connection.cursor()
    cursor.execute(sql)
    departments = []
    for row in cursor.fetchall():
        departments.append(row[0])

    # configure template
    template = loader.get_template('supervisors/search_by_faculty.html')
    context = applist.template_context('supervisors')
    context['schools'] = schools
    context['departments'] = departments
    context['max_years'] = years_back
    return HttpResponse(template.render(context, request))

def add_student(data, school, department, supervisor, studentid, program, supervisor_type, study_type, only_current):
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
              - status

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
    :param program: the program (PhD/Master)
    :type program: str
    :param supervisor_type: the type of supervisors to list ["chief", "other"]
    :type supervisor_type: list
    :param study_type: list of study type ["full", "part"]
    :type study_type: list
    :param only_current: whether to list only current students
    :type only_current: bool
    """

    if program == "DP":
        program_display = "PhD"
    elif program == "MD":
        program_display = "Master"
    else:
        program_display = program

    # ensure data structures are present
    if school not in data:
        data[school] = {}
    if department not in data[school]:
        data[school][department] = {}
    if supervisor not in data[school][department]:
        data[school][department][supervisor] = {}
    if program_display not in data[school][department][supervisor]:
        data[school][department][supervisor][program_display] = {}

    # load student data
    today = date.today().strftime("%Y-%m-%d")
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

        end_date = s.end_date.strftime("%Y-%m-%d")
        if end_date == "9999-12-31" or end_date <= "1900-01-01":
            end_date = "N/A"

        status = s.status
        if status is None:
            if end_date == "N/A":
                status = "current"
            elif s.end_date.strftime("%Y-%m-%d") >= today:
                status = "current"
            else:
                status = "finished"

        # check conditions
        if chief == "Yes" and "chief" not in supervisor_type:
            continue
        if chief == "No" and "other" not in supervisor_type:
            continue
        if full_time == "Yes" and "full" not in study_type:
            continue
        if full_time == "No" and "part" not in study_type:
            continue
        if only_current and status == "finished":
            continue

        if studentid not in data[school][department][supervisor][program_display]:
            data[school][department][supervisor][program_display][studentid] = {}

        sdata = data[school][department][supervisor][program_display][studentid]
        sdata['name'] = sname
        sdata['start_date'] = s.start_date.strftime("%Y-%m-%d")
        sdata['end_date'] = end_date
        sdata['months'] = s.months
        sdata['full_time'] = full_time
        sdata['chief_supervisor'] = chief
        sdata['status'] = status

def list_by_faculty(request):
    # get parameters
    response, schools = get_variable_with_error(request, 'supervisors', 'school', as_list=True)
    if response is not None:
        return response

    response, departments = get_variable_with_error(request, 'supervisors', 'department', as_list=True)
    if response is not None:
        return response

    response, years_back_str = get_variable_with_error(request, 'supervisors', 'years_back')
    if response is not None:
        return response
    years_back = int(years_back_str)
    start_year = date.today().year - years_back

    programs = get_variable(request, 'programs', as_list=True, def_value=["DP", "MD"])
    supervisor_type = get_variable(request, 'supervisor_type', as_list=True, def_value=["chief", "other"])
    study_type = get_variable(request, 'study_type', as_list=True, def_value=["full", "part"])
    only_current = get_variable(request, 'only_current', def_value="off") == "on"
    export = get_variable(request, 'csv')

    sql = """
        select sd.school, sd.department, s.supervisor, s.student_id, sd.program
        from %s sd, %s s
        where sd.student_id = s.student_id
        and sd.school in ('%s')
        and sd.department in ('%s')
        and sd.start_date >= '%s-01-01'
        and s.active = True
        group by sd.school, sd.department, s.supervisor, s.student_id, sd.program
        order by sd.school, sd.department, s.supervisor, s.student_id, sd.program
        """ % (StudentDates._meta.db_table, Supervisors._meta.db_table, "','".join(schools), "','".join(departments), str(start_year))
    cursor = connection.cursor()
    cursor.execute(sql)
    result = {}
    for row in cursor.fetchall():
        try:
            if row[4] not in programs:
                continue
            add_student(data=result, school=row[0], department=row[1], supervisor=row[2], studentid=row[3],
                        program=row[4], supervisor_type=supervisor_type, study_type=study_type,
                        only_current=only_current)
        except Exception as ex:
            print("row=" + str(row))
            traceback.print_exc(file=sys.stdout)

    # CSV or HTML?
    if export == "csv":
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="faculty-%s.csv"' % date.today().strftime("%Y-%m-%d")
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
            'Status',
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
                                sdata['status'],
                            ])
        return response
    else:
        template = loader.get_template('supervisors/list_by_faculty.html')
        context = applist.template_context('supervisors')
        context['results'] = result
        return HttpResponse(template.render(context, request))

def search_by_supervisor(request):
    # get parameters
    response, name = get_variable_with_error(request, 'supervisors', 'name')
    if response is not None:
        return response

    # TODO

    # configure template
    template = loader.get_template('supervisors/search_by_supervisor.html')
    context = applist.template_context('supervisors')
    return HttpResponse(template.render(context, request))

def list_by_supervisor(request):
    # get parameters
    # TODO

    export = get_variable(request, 'csv')

    # CSV or HTML?
    if export == "csv":
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="supervisor-%s.csv"' % date.today().strftime("%Y-%m-%d")
        writer = csv.writer(response)
        writer.writerow([
            'Blah',
            # TODO headers
        ])
        # TODO data
        return response
    else:
        template = loader.get_template('supervisors/list_by_supervisor.html')
        context = applist.template_context('supervisors')
        context['results'] = None  # TODO
        return HttpResponse(template.render(context, request))

def search_by_student(request):
    # get parameters
    response, name = get_variable_with_error(request, 'supervisors', 'name')
    if response is not None:
        return response

    # TODO

    # configure template
    template = loader.get_template('supervisors/search_by_student.html')
    context = applist.template_context('supervisors')
    return HttpResponse(template.render(context, request))

def list_by_student(request):
    # get parameters
    # TODO

    export = get_variable(request, 'csv')

    # CSV or HTML?
    if export == "csv":
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="student-%s.csv"' % date.today().strftime("%Y-%m-%d")
        writer = csv.writer(response)
        writer.writerow([
            'Blah',
            # TODO headers
        ])
        # TODO data
        return response
    else:
        template = loader.get_template('supervisors/list_by_student.html')
        context = applist.template_context('supervisors')
        context['results'] = None  # TODO
        return HttpResponse(template.render(context, request))
