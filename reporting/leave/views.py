from django.template import loader
from django.http import HttpResponse

import reporting.applist as applist

def index(request):
    # configure template
    template = loader.get_template('leave/index.html')
    context = applist.template_context('leave')
    return HttpResponse(template.render(context, request))

def upload(request):
    # configure template
    template = loader.get_template('leave/output.html')
    context = applist.template_context('leave')
    return HttpResponse(template.render(context, request))
