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
    print(request.FILES)
    csv = request.FILES['datafile']
    print(csv.temporary_file_path())
    msg = dbimport.import_supervisors(csv.temporary_file_path())
    template = loader.get_template('supervisors/upload.html')
    context = applist.template_context('supervisors')
    if msg is None:
        context['message'] = "Sucessful upload!"
    else:
        context['message'] = "Failed to upload: " + msg
    return HttpResponse(template.render(context, request))
