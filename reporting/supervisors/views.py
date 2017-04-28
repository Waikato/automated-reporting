from django.template import loader
from django.template.defaulttags import register
from django.http import HttpResponse
from django.db import connection
from django.contrib.auth.decorators import login_required, permission_required
from supervisors.models import StudentDates, Supervisors, Scholarship
from database.models import GradeResults
from reporting.error import create_error_response
from reporting.settings import REPORTING_OPTIONS

import reporting.applist as applist
from reporting.form_utils import get_variable_with_error, get_variable
import traceback
import sys
from datetime import date
import csv
import reporting.form_utils as form_utils

YEARS_BACK = 5
""" the default number of years to go back """

STUDY_TYPES = ["full", "part"]
""" all study types """

PROGRAM_TYPES = ["DP", "MD"]
""" all program types """

SUPERVISOR_TYPES = ["chief", "other"]
""" all supervisor types """

NO_SCHOLARSHIP = "-none-"
""" the indicator for 'no' scholarship """

@register.filter
def get_item(dictionary, key):
    """
    Filter method for retrieving the value of a dictionary.

    Taken from here:
    http://stackoverflow.com/a/8000091

    {{ mydict|get_item:item.NAME }}
    """
    return dictionary.get(key)

def get_max_years():
    """
    Determines the maximum number of available years to go back.

    :return: the number of years
    :rtype: int
    """

    cursor = connection.cursor()
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

    return int(max_years)

def get_schools():
    """
    Retrieves a sorted list of all the deparments.

    :return: the list of departments
    :rtype: list
    """

    cursor = connection.cursor()
    cursor.execute("""
        SELECT DISTINCT(school)
        FROM %s
        WHERE char_length(school) > 0
        ORDER BY school ASC
        """ % StudentDates._meta.db_table)
    result = []
    for row in cursor.fetchall():
        result.append(row[0])
    return result

def get_departments(schools):
    """
    Retrieves a sorted list of all the departments.

    :param schools: the list of schools to list the departments for.
    :type schools: list
    :return: the list of departments
    :rtype: list
    """

    sql = """
        select distinct(owning_department_clevel)
        from %s
        where owning_school_clevel in ('%s')
        order by owning_department_clevel
        """ % (GradeResults._meta.db_table, "','".join(schools))
    cursor = connection.cursor()
    cursor.execute(sql)
    result = []
    for row in cursor.fetchall():
        result.append(row[0])
    return result

def get_scholarships():
    """
    Retrieves a sorted list of all scholarships available.

    :return: the list of scholarships
    :rtype: list
    """
    cursor = connection.cursor()
    cursor.execute("""
        SELECT DISTINCT(name)
        FROM %s
        WHERE char_length(name) > 0
        ORDER BY name ASC
        """ % Scholarship._meta.db_table)
    result = []
    for row in cursor.fetchall():
        result.append(row[0])
    return result

@login_required
def index(request):
    # configure template
    template = loader.get_template('supervisors/index.html')
    context = applist.template_context('supervisors')
    context['schools'] = get_schools()
    return HttpResponse(template.render(context, request))

@login_required
def search_by_faculty(request):
    # get parameters
    response, schools = get_variable_with_error(request, 'supervisors', 'school', as_list=True)
    if response is not None:
        return response

    # get year from earliest start date
    max_years = get_max_years()

    # configure template
    template = loader.get_template('supervisors/search_by_faculty.html')
    context = applist.template_context('supervisors')
    context['schools'] = schools
    context['departments'] = get_departments(schools)
    context['max_years'] = int(max_years) if max_years is not None else YEARS_BACK
    context['scholarships'] = get_scholarships()
    return HttpResponse(template.render(context, request))

def add_student(data, school, department, supervisor, studentid, program, supervisor_type, study_type, only_current, scholarship):
    """
    Adds the student to the "data" structure. Overview of the data structure (<name> is
    a key in a dictionary):

    <faculty>
        - department
        - supervisor
        - program
        - studentid
        - name (string)
        - start_date (date)
        - end_date (date)
        - months (float)
        - full_time
        - chief_supervisor
        - status
        - scholarship -- present only if looking for scholarship other than '-none-'

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
    :param scholarship: the scholarship name to check whether the student has it
    :type scholarship: str
    """

    if program == "DP":
        program_display = "PhD"
    elif program == "MD":
        program_display = "Master"
    else:
        program_display = program

    # load student data
    today = date.today().strftime("%Y-%m-%d")
    for s in StudentDates.objects.all().filter(school=school, department=department, student_id=studentid, program=program):
        sname = None
        for g in GradeResults.objects.all().filter(student_id=studentid):
            sname = g.name
            break

        # chief?
        chief = None
        for sv in Supervisors.objects.all().filter(student_id=studentid, supervisor=supervisor):
            if sv.active_roles == "":
                chief = "N/A"
            else:
                chief = "Yes" if "Chief" in sv.active_roles else "No"
        if s.full_time is None:
            full_time = 'N/A'
        elif s.full_time:
            full_time = 'Yes'
        else:
            full_time = 'No'

        # dates
        start_date = s.start_date.strftime("%Y-%m-%d")
        end_date = s.end_date.strftime("%Y-%m-%d")
        if end_date == "9999-12-31" or end_date <= "1900-01-01":
            end_date = "N/A"

        # status
        status = s.status
        if status is None:
            if end_date == "N/A":
                status = "current"
            elif s.end_date.strftime("%Y-%m-%d") >= today:
                status = "current"
            else:
                status = "finished"

        # scholarship
        scholarship_status = None
        if scholarship != NO_SCHOLARSHIP:
            scholarship_status = "No"
            for sch in Scholarship.objects.all().filter(student_id=studentid, name=scholarship, decision="Active"):
                if str(sch.year) >= start_date[0:4]:
                    if end_date == "N/A":
                        scholarship_status = "Yes"
                        break
                    if str(sch.year) <= end_date[0:4]:
                        scholarship_status = "Yes"
                        break

        # check conditions
        if chief == "Yes" and "chief" not in supervisor_type:
            continue
        if chief == "No" and "other" not in supervisor_type:
            continue
        if full_time == "Yes" and "full" not in study_type:
            continue
        if full_time == "No" and "part" not in study_type:
            continue
        if only_current and not status == "current":
            continue

        # ensure data structures are present
        if school not in data:
            data[school] = []

        sdata = {}
        sdata['department'] = department
        sdata['supervisor'] = supervisor
        sdata['program'] = program_display
        sdata['id'] = studentid
        sdata['name'] = sname
        sdata['start_date'] = start_date
        sdata['end_date'] = end_date
        sdata['months'] = s.months
        sdata['full_time'] = full_time
        sdata['chief_supervisor'] = chief
        sdata['status'] = status
        sdata['scholarship'] = scholarship_status
        data[school].append(sdata)

@login_required
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

    programs = get_variable(request, 'program', as_list=True, def_value=PROGRAM_TYPES)
    if REPORTING_OPTIONS['supervisor.only_phd']:
        programs = ['DP']
    supervisor_type = get_variable(request, 'supervisor_type', as_list=True, def_value=SUPERVISOR_TYPES)
    study_type = get_variable(request, 'study_type', as_list=True, def_value=STUDY_TYPES)
    only_current = get_variable(request, 'only_current', def_value="off") == "on"
    min_months = float(get_variable(request, 'min_months', def_value="-1", blank=False))
    scholarship = str(get_variable(request, 'scholarship', def_value="NO_SCHOLARSHIP"))
    sort_column = get_variable(request, 'sort_column', def_value="supervisor")
    sort_order = get_variable(request, 'sort_order', def_value="asc")
    export = get_variable(request, 'csv')

    sql = """
        select sd.school, sd.department, s.supervisor, s.student_id, sd.program
        from %s sd, %s s
        where sd.student_id = s.student_id
        and sd.program = s.program
        and sd.school in ('%s')
        and sd.department in ('%s')
        and sd.start_date >= '%s-01-01'
        and s.active = True
        and sd.months >= %f
        group by sd.school, sd.department, s.supervisor, s.student_id, sd.program
        order by sd.school, sd.department, s.supervisor, s.student_id, sd.program
        """ % (StudentDates._meta.db_table, Supervisors._meta.db_table, "','".join(schools), "','".join(departments), str(start_year), min_months)
    cursor = connection.cursor()
    cursor.execute(sql)
    result = {}
    for row in cursor.fetchall():
        try:
            if row[4] not in programs:
                continue
            add_student(data=result, school=row[0], department=row[1], supervisor=row[2], studentid=row[3],
                        program=row[4], supervisor_type=supervisor_type, study_type=study_type,
                        only_current=only_current, scholarship=scholarship)
        except Exception as ex:
            print("row=" + str(row))
            traceback.print_exc(file=sys.stdout)

    # sort
    for school in result:
        school_data = result[school]
        school_data_sorted = sorted(school_data, key=lambda row: row[sort_column], reverse=(sort_order == "desc"))
        result[school] = school_data_sorted

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
            'Scholarship (' + scholarship + ')',
        ])
        for school in result:
            for row in result[school]:
                writer.writerow([
                    school,
                    row['department'],
                    row['supervisor'],
                    row['program'],
                    row['id'],
                    row['name'],
                    row['start_date'],
                    row['end_date'],
                    row['months'],
                    row['full_time'],
                    row['chief_supervisor'],
                    row['status'],
                    row['scholarship'],
                ])
        return response
    else:
        template = loader.get_template('supervisors/list_by_faculty.html')
        context = applist.template_context('supervisors')
        context['results'] = result
        context['csv_url'] = form_utils.request_to_url(request, "/supervisors/list-by-faculty", {'csv': 'csv'})
        context['scholarship'] = scholarship
        context['show_scholarship'] = scholarship != NO_SCHOLARSHIP
        return HttpResponse(template.render(context, request))

@login_required
def search_by_supervisor(request):
    # get parameters
    response, name = get_variable_with_error(request, 'supervisors', 'name')
    if response is not None:
        return response

    if len(name) == 0:
        return create_error_response(request, 'supervisors', 'No supervisor name provided!')

    # get year from earliest start date
    max_years = get_max_years()

    sql = """
        select distinct(s.supervisor)
        from %s sd, %s s
        where lower(s.supervisor) like '%%%s%%'
        and s.active = True
        order by s.supervisor
        """ % (StudentDates._meta.db_table, Supervisors._meta.db_table, name.lower())
    cursor = connection.cursor()
    cursor.execute(sql)
    results = []
    for row in cursor.fetchall():
        data = {}
        data['supervisor'] = row[0]
        results.append(data)

    # configure template
    template = loader.get_template('supervisors/search_by_supervisor.html')
    context = applist.template_context('supervisors')
    context['results'] = results
    context['max_years'] = max_years
    context['scholarships'] = get_scholarships()
    return HttpResponse(template.render(context, request))

@login_required
def list_by_supervisor(request):
    # get parameters
    response, name = get_variable_with_error(request, 'supervisors', 'name')
    if response is not None:
        return response

    years_back_str = get_variable(request, 'years_back', def_value=str(get_max_years()))
    years_back = int(years_back_str)
    start_year = date.today().year - years_back

    programs = get_variable(request, 'program', as_list=True, def_value=PROGRAM_TYPES)
    if REPORTING_OPTIONS['supervisor.only_phd']:
        programs = ['DP']
    supervisor_type = get_variable(request, 'supervisor_type', as_list=True, def_value=SUPERVISOR_TYPES)
    study_type = get_variable(request, 'study_type', as_list=True, def_value=STUDY_TYPES)
    only_current = get_variable(request, 'only_current', def_value="off") == "on"
    min_months = float(get_variable(request, 'min_months', def_value="-1", blank=False))
    scholarship = str(get_variable(request, 'scholarship', def_value="NO_SCHOLARSHIP"))
    sort_column = get_variable(request, 'sort_column', def_value="supervisor")
    sort_order = get_variable(request, 'sort_order', def_value="asc")
    export = get_variable(request, 'csv')

    sql = """
        select sd.school, sd.department, s.supervisor, s.student_id, sd.program
        from %s sd, %s s
        where sd.student_id = s.student_id
        and sd.program = s.program
        and s.supervisor = '%s'
        and sd.start_date >= '%s-01-01'
        and s.active = True
        and sd.months >= %f
        group by sd.school, sd.department, s.supervisor, s.student_id, sd.program
        order by sd.school, sd.department, s.supervisor, s.student_id, sd.program
        """ % (StudentDates._meta.db_table, Supervisors._meta.db_table, name, start_year, min_months)
    cursor = connection.cursor()
    cursor.execute(sql)
    result = {}
    for row in cursor.fetchall():
        try:
            if len(row[0]) < 1:
                print("empty school: " + str(row))
                continue
            if row[4] not in programs:
                continue
            add_student(data=result, school=row[0], department=row[1], supervisor=row[2], studentid=row[3],
                        program=row[4], supervisor_type=supervisor_type, study_type=study_type,
                        only_current=only_current, scholarship=scholarship)
        except Exception as ex:
            print("row=" + str(row))
            traceback.print_exc(file=sys.stdout)

    # sort
    for school in result:
        school_data = result[school]
        school_data_sorted = sorted(school_data, key=lambda row: row[sort_column], reverse=(sort_order == "desc"))
        result[school] = school_data_sorted

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
            'Scholarship (' + scholarship + ')',
        ])
        for school in result:
            for row in result[school]:
                writer.writerow([
                    school,
                    row['department'],
                    row['supervisor'],
                    row['program'],
                    row['id'],
                    row['name'],
                    row['start_date'],
                    row['end_date'],
                    row['months'],
                    row['full_time'],
                    row['chief_supervisor'],
                    row['status'],
                    row['scholarship'],
                ])
        return response
    else:
        template = loader.get_template('supervisors/list_by_supervisor.html')
        context = applist.template_context('supervisors')
        context['results'] = result
        context['csv_url'] = form_utils.request_to_url(request, "/supervisors/list-by-supervisor", {'csv': 'csv'})
        context['scholarship'] = scholarship
        context['show_scholarship'] = scholarship != NO_SCHOLARSHIP
        return HttpResponse(template.render(context, request))

@login_required
def search_by_student(request):
    # get parameters
    response, name = get_variable_with_error(request, 'supervisors', 'name')
    if response is not None:
        return response

    if len(name) == 0:
        return create_error_response(request, 'supervisors', 'No student name/id provided!')

    if name.isdigit():
        sql = """
            select s.student_id, sd.program, s.student
            from %s sd, %s s
            where s.student_id = '%s'
            and s.active = True
            and s.student_id = sd.student_id
            and s.program = sd.program
            group by s.student_id, sd.program, s.student
            order by s.student_id, sd.program, s.student
            """ % (StudentDates._meta.db_table, Supervisors._meta.db_table, name)
    else:
        sql = """
            select s.student_id, sd.program, s.student
            from %s sd, %s s
            where lower(s.student) like '%%%s%%'
            and s.active = True
            and s.student_id = sd.student_id
            and s.program = sd.program
            group by s.student_id, sd.program, s.student
            order by s.student_id, sd.program, s.student
            """ % (StudentDates._meta.db_table, Supervisors._meta.db_table, name.lower())
    cursor = connection.cursor()
    cursor.execute(sql)
    results = []
    for row in cursor.fetchall():
        data = {}
        data['student_id'] = row[0]
        data['program'] = row[1]
        data['student'] = row[2]
        results.append(data)

    # configure template
    template = loader.get_template('supervisors/search_by_student.html')
    context = applist.template_context('supervisors')
    context['results'] = results
    return HttpResponse(template.render(context, request))

@login_required
def list_by_student(request):
    # get parameters
    response, studentid = get_variable_with_error(request, 'supervisors', 'student')
    if response is not None:
        return response

    export = get_variable(request, 'csv')

    # supervisors
    supervisors = []
    for sv in Supervisors.objects.all().filter(student_id=studentid):
        sname = None
        for g in GradeResults.objects.all().filter(student_id=studentid):
            sname = g.name
            break
        data = {}
        data["studentid"] = studentid
        data["studentname"] = sname
        data["supervisor"] = sv.supervisor
        data["role"] = sv.active_roles
        if (data["role"] is None) or (len(data["role"]) == 0):
            data["role"] = "N/A"
        supervisors.append(data)

    # scholarships
    scholarships = []
    for sc in Scholarship.objects.all().filter(student_id=studentid).order_by('-year'):
        data = {}
        data["studentid"] = studentid
        data["studentname"] = sname
        data["scholarship"] = sc.name
        data["status"] = sc.status
        data["decision"] = sc.decision
        data["year"] = sc.year
        scholarships.append(data)

    # CSV or HTML?
    if export == "csv":
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="student-%s.csv"' % date.today().strftime("%Y-%m-%d")
        writer = csv.writer(response)
        writer.writerow([
            'ID',
            'Name',
            'Supervisor',
            'Role',
        ])
        for row in supervisors:
            writer.writerow([
                row["studentid"],
                row["studentname"],
                row["supervisor"],
                row["role"],
            ])
        writer.writerow([])
        writer.writerow([
            'ID',
            'Name',
            'Scholarship',
            'Status',
            'Decision',
            'Year',
        ])
        for row in scholarships:
            writer.writerow([
                row["studentid"],
                row["studentname"],
                row["scholarship"],
                row["status"],
                row["decision"],
                row["year"],
            ])
        return response
    else:
        template = loader.get_template('supervisors/list_by_student.html')
        context = applist.template_context('supervisors')
        context['supervisors'] = supervisors
        context['scholarships'] = scholarships
        context['csv_url'] = form_utils.request_to_url(request, "/supervisors/list-by-student", {'csv': 'csv'})
        return HttpResponse(template.render(context, request))
