from django.http import HttpResponse
from django.template import loader
import reporting.applist as applist
from django.template.defaulttags import register

def index(request):
    template = loader.get_template('applist.html')
    context = applist.template_context()
    print(context)
    return HttpResponse(template.render(context, request))

@register.filter
def get_item(dictionary, key):
    """
    Taken from here:
    http://stackoverflow.com/a/8000091

    {{ mydict|get_item:item.NAME }}
    """
    return dictionary.get(key)