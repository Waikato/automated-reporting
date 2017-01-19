from django.http import HttpResponse
from django.template import loader
import reporting.applist as applist

def index(request):
    apps = applist.get_apps()
    template = loader.get_template('applist.html')
    context = {
        'title': 'Automated Reporting',
        'applist': apps,
    }
    return HttpResponse(template.render(context, request))
