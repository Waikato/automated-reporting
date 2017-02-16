from django.template import loader
from django.http import HttpResponse

from . import dbimport
import reporting.applist as applist

def index(request):
    # configure template
    template = loader.get_template('supervisors/index.html')
    context = applist.template_context('supervisors')
    return HttpResponse(template.render(context, request))

def upload(request):
    # configure template
    csv = request.FILES['datafile']
    msg = dbimport.import_supervisors(csv.temporary_file_path())
    template = loader.get_template('supervisors/upload.html')
    context = applist.template_context('supervisors')
    if msg is None:
        context['message'] = "Successful upload!"
    else:
        context['message'] = "Failed to upload: " + msg
    return HttpResponse(template.render(context, request))

def studentdates(request):
    # configure template
    msg = dbimport.populate_student_dates()
    template = loader.get_template('supervisors/studentdates.html')
    context = applist.template_context('supervisors')
    if msg is None:
        context['message'] = "Successful recalculation!"
    else:
        context['message'] = "Failed to recalculate: " + msg
    return HttpResponse(template.render(context, request))
