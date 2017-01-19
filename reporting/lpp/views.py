from django.template import loader
import reporting.applist as applist

from django.http import HttpResponse

def index(request):
    apps = applist.get_apps()
    template = loader.get_template('lpp/index.html')
    context = {
        'title': 'Low Performing Pass-rates',
        'applist': apps,
    }
    return HttpResponse(template.render(context, request))
