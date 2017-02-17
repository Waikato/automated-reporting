from django.http import HttpResponse
from django.template import loader
import reporting.applist as applist
from django.template.defaulttags import register
from . import dbimport
from datetime import date

def index(request):
    template = loader.get_template('applist.html')
    context = applist.template_context()
    return HttpResponse(template.render(context, request))

def database(request):
    years = []
    for year in range(2004, date.today().year + 1):
        years.append(year)
    years.reverse()
    template = loader.get_template('database.html')
    context = applist.template_context()
    context['title'] = 'Database management'
    context['years'] = years
    return HttpResponse(template.render(context, request))

def upload_supervisors(request):
    # configure template
    csv = request.FILES['datafile']
    msg = dbimport.import_supervisors(csv.temporary_file_path())
    template = loader.get_template('message.html')
    context = applist.template_context()
    if msg is None:
        context['message'] = "Successful upload of supervisors!"
    else:
        context['message'] = "Failed to upload supervisors: " + msg
    return HttpResponse(template.render(context, request))

def upload_grade_results(request):
    # configure template
    csv = request.FILES['datafile']
    year = int(request.POST['year'])
    gzip = (request.POST['gzip'] == "on")
    msg = dbimport.import_grade_results(year, csv.temporary_file_path(), gzip)
    template = loader.get_template('message.html')
    context = applist.template_context()
    if msg is None:
        context['message'] = "Successful upload of grade results!"
    else:
        context['message'] = "Failed to upload grade results: " + msg
    return HttpResponse(template.render(context, request))

def studentdates(request):
    # configure template
    msg = dbimport.populate_student_dates()
    template = loader.get_template('message.html')
    context = applist.template_context()
    if msg is None:
        context['message'] = "Successful student dates recalculation!"
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
