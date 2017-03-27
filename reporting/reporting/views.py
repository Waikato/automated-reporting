from django.http import HttpResponse
from django.template import loader
import reporting.applist as applist
from django.template.defaulttags import register
from . import dbimport
from datetime import date, datetime

from reporting.models import TableStatus, GradeResults
from supervisors.models import Supervisors, StudentDates

def index(request):
    template = loader.get_template('applist.html')
    context = applist.template_context()
    return HttpResponse(template.render(context, request))

def database_graderesults(request):
    years = []
    for year in range(2003, date.today().year + 1):
        years.append(year)
    years.reverse()
    template = loader.get_template('import_graderesults.html')
    context = applist.template_context()
    context['title'] = 'Import grade results'
    context['years'] = years
    return HttpResponse(template.render(context, request))

def database_supervisors(request):
    template = loader.get_template('import_supervisors.html')
    context = applist.template_context()
    context['title'] = 'Import supervisors'
    return HttpResponse(template.render(context, request))

def database_studentdates(request):
    template = loader.get_template('update_studentdates.html')
    context = applist.template_context()
    context['title'] = 'Update student dates'
    return HttpResponse(template.render(context, request))

def database_tablestatus(request):
    template = loader.get_template('table_status.html')
    tables = {}
    for t in TableStatus.objects.all():
        tables[t.table] = {}
        tables[t.table]['timestamp'] = t.timestamp
    context = applist.template_context()
    context['title'] = 'Table status'
    context['tables'] = tables
    return HttpResponse(template.render(context, request))

def import_supervisors(request):
    # configure template
    csv = request.FILES['datafile']
    msg = dbimport.import_supervisors(csv.temporary_file_path())
    template = loader.get_template('message.html')
    context = applist.template_context()
    if msg is None:
        context['message'] = "Successful upload of supervisors!"
        dbimport.update_tablestatus(Supervisors._meta.db_table)
    else:
        context['message'] = "Failed to upload supervisors: " + msg
    return HttpResponse(template.render(context, request))

def import_graderesults(request):
    # configure template
    csv = request.FILES['datafile']
    year = int(request.POST['year'])
    gzip = (request.POST['gzip'] == "on")
    msg = dbimport.import_grade_results(year, csv.temporary_file_path(), gzip)
    template = loader.get_template('message.html')
    context = applist.template_context()
    if msg is None:
        context['message'] = "Successful upload of grade results!"
        dbimport.update_tablestatus(GradeResults._meta.db_table)
    else:
        context['message'] = "Failed to upload grade results: " + msg
    return HttpResponse(template.render(context, request))

def update_studentdates(request):
    # configure template
    msg = dbimport.populate_student_dates()
    template = loader.get_template('message.html')
    context = applist.template_context()
    if msg is None:
        context['message'] = "Successful student dates recalculation!"
        dbimport.update_tablestatus(StudentDates._meta.db_table)
    else:
        context['message'] = "Failed to recalculate student dates: " + msg
    return HttpResponse(template.render(context, request))

@register.filter
def get_item(dictionary, key):
    """
    Filter method for retrieving the value of a dictionary.

    Taken from here:
    http://stackoverflow.com/a/8000091

    {{ mydict|get_item:item.NAME }}
    """
    return dictionary.get(key)
