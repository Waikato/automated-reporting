from django.template import loader
import reporting.applist as applist
from django.http import HttpResponse, HttpRequest

apps = applist.get_apps()


def create_error_response(request, app, error):
    """
    Generates an HttpResponse object with the specified title/error.
    :param request: the HttpRequest that triggered this error
    :type request: HttpRequest
    :param app: the app name (' - Error' gets appended)
    :type app: str
    :param error: the error message
    :type error: str
    :return: the HttpResponse object
    :rtype: HttpResponse
    """

    template = loader.get_template('error.html')
    context = {
        'title': applist.get_appname_long(app) + ' - Error',
        'applist': apps,
        'error': error,
    }

    return HttpResponse(template.render(context, request))
