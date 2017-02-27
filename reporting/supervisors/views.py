from django.template import loader
from django.http import HttpResponse
from django.db import connection

import reporting.applist as applist
from reporting.error import create_error_response
import traceback
import sys
from datetime import date

YEARS_BACK = 5

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
    # get year from earliest start date
    cursor.execute("""
        select extract(year from min(start_date))
        from supervisors_studentdates
    """)
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

def list_supervisors(request):
    # get parameters
    if "school" not in request.POST:
        return create_error_response(request, 'supervisors', 'No school defined!')
    schools = request.POST.getlist("school")

    if "years_back" not in request.POST:
        return create_error_response(request, 'supervisors', 'No number of years back defined!')
    years_back = int(request.POST["years_back"])
    start_year = date.today().year - years_back

    sql = """
        select sd.school, s.supervisor, s.student_id
        from supervisors_studentdates sd, supervisors_supervisors s
        where sd.student_id = s.student_id
        and sd.school in ('%s')
        and sd.start_date >= '%s-01-01'
        group by sd.school, s.supervisor, s.student_id
        order by sd.school, s.supervisor, s.student_id
        """ % ("','".join(schools), str(start_year))
    cursor = connection.cursor()
    cursor.execute(sql)
    result = {}
    school_set = set()
    for row in cursor.fetchall():
        school = row[0]
        school_set.add(school)
        if school not in result:
            result[school] = []
        result[school].append({'supervisor': row[1], 'student': row[2]})
    school_list = list(school_set)
    sorted(school_list)

    template = loader.get_template('supervisors/list.html')
    context = applist.template_context('supervisors')
    context['schools'] = school_list
    context['results'] = result
    return HttpResponse(template.render(context, request))
