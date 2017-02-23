from django.template import loader
from django.http import HttpResponse
from django.db import connection

import reporting.applist as applist
from reporting.error import create_error_response
import traceback
import sys

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
    # configure template
    template = loader.get_template('supervisors/index.html')
    context = applist.template_context('supervisors')
    context['schools'] = schools
    context['years_back'] = YEARS_BACK
    return HttpResponse(template.render(context, request))

def list(request):
    # get parameters
    if "school" not in request.POST:
        return create_error_response(request, 'supervisors', 'No school defined!')
    schools = request.POST.getlist("school")

    if "years_back" not in request.POST:
        return create_error_response(request, 'supervisors', 'No number of years back defined!')
    years_back = int(request.POST["years_back"])

    # TODO

    template = loader.get_template('supervisors/list.html')
    context = applist.template_context('supervisors')
    return HttpResponse(template.render(context, request))
