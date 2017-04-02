import reporting.applist as applist
from django.http import HttpResponse, HttpRequest
from .error import create_error_response

apps = applist.get_apps()

def get_variable_with_error(request, app, var, as_list=False, def_value=None):
    """
    Retrieves the specified variable if present in POST/GET.
    If not, generates a response with an error message.
    Returns a tuple: (HttpResponse, variable value)

    :param request: the request to check
    :type request: HttpRequest
    :param app: the application context
    :type app: str
    :param var: the variable name to look for
    :type app: str
    :param as_list: whether to retriev a list
    :type as_list: bool
    :param def_value: the default value to use if not present
    :type def_value: object or list
    :return: HttpResponse and variable value (either can be None)
    :rtype: tuple
    """

    if (var not in request.POST) and (var not in request.GET):
        return create_error_response(request, app, 'Missing: ' + var), None
    else:
        return None, get_variable(request, var, as_list=as_list, def_value=def_value)

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
