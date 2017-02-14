from django.template import loader
from django.http import HttpResponse

import reporting.applist as applist

def index(request):
    # configure template
    template = loader.get_template('supervisors/index.html')
    context = applist.template_context('supervisors')
    return HttpResponse(template.render(context, request))

def output(request):
    return None
