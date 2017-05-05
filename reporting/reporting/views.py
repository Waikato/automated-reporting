from django.http import HttpResponse
from django.template import loader
import reporting.applist as applist
from django.template.defaulttags import register
from django.contrib.auth.decorators import login_required


@login_required
def index(request):
    template = loader.get_template('applist.html')
    context = applist.template_context()
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
