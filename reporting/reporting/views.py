from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
import reporting.applist as applist
from django.template.defaulttags import register
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import login
import reporting.settings

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

def custom_login(request):
    """
    A custom login page.

    :param request: the current request object
    :type request: HttpRequest
    """
    if request.user.is_authenticated():
        if reporting.settings.LOCAL_USERS:
            return login(request)
        else:
            template = loader.get_template('no_permission.html')
            context = applist.template_context()
            return HttpResponse(template.render(context, request))
    else:
        if reporting.settings.AUTHENTICATION_TYPE == "shibboleth":
            return HttpResponseRedirect("/Shibboleth.sso/Login")
        else:
            return login(request)
