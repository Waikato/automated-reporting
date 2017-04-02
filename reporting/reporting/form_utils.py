import reporting.applist as applist
from django.http import HttpResponse, HttpRequest
from .error import create_error_response

apps = applist.get_apps()

def check_variable_presence(request, app, var):
    """
    Checks whether the specified variable is present in POST/GET.
    If not, generates a response with an error message.

    :param request: the request to check
    :type request: HttpRequest
    :param app: the application context
    :type app: str
    :param var: the variable name to look for
    :type app: str
    :return: None if present, otherwise http response with error message
    :rtype: HttpResponse
    """

    if (var not in request.POST) and (var not in request.GET):
        return create_error_response(request, app, 'Missing: ' + var)
    return None

def get_variable(request, var, as_list=False, def_value=None):
    """
    Returns the specified variable from POST/GET.

    :param request: the request to use
    :type request: HttpRequest
    :param var: the variable name to look for
    :type app: str
    :param as_list: whether to retriev a list
    :type as_list: bool
    :param def_value: the default value to use if not present
    :type def_value: object or list
    :return: the default value if variable not present, otherwise value
    :rtype: object or list
    """

    if var in request.POST:
        if as_list:
            return request.POST.getlist(var)
        else:
            return request.POST.get(var)

    if var in request.GET:
        if as_list:
            return request.GET.getlist(var)
        else:
            return request.GET.get(var)

    return def_value
