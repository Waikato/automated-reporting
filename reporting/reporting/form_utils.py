import reporting.applist as applist
from django.http import HttpRequest
from .error import create_error_response
import urllib.parse

apps = applist.get_apps()


def get_variable_with_error(request, app, var, as_list=False, def_value=None, blank=True):
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
    :param blank: whether the field can be blank
    :type blank: bool
    :return: HttpResponse and variable value (either can be None)
    :rtype: tuple
    """

    if (var not in request.POST) and (var not in request.GET):
        return create_error_response(request, app, 'Missing: ' + var), None
    else:
        return None, get_variable(request, var, as_list=as_list, def_value=def_value, blank=blank)


def get_variable(request, var, as_list=False, def_value=None, blank=True):
    """
    Returns the specified variable from POST/GET.

    :param request: the request to use
    :type request: HttpRequest
    :param var: the variable name to look for
    :type var: str
    :param as_list: whether to retriev a list
    :type as_list: bool
    :param def_value: the default value to use if not present
    :type def_value: object or list
    :param blank: whether the field can be blank
    :type blank: bool
    :return: the default value if variable not present, otherwise value
    :rtype: object or list
    """

    result = def_value

    if var in request.POST:
        if as_list:
            result = request.POST.getlist(var)
        else:
            result = request.POST.get(var)

    if var in request.GET:
        if as_list:
            result = request.GET.getlist(var)
        else:
            result = request.GET.get(var)

    if not blank and (len(result) == 0):
        result = def_value

    return result


def request_to_url(request, url_prefix, override=None):
    """
    Generates a URL from the request, using all the GET/POST variables in the URL.
    The values from the request van be overridden with the "override" dictionary.

    :param request: the request to turn into a URL
    :type request: HttpRequest
    :param url_prefix: the URL prefix to use; ? gets added automatically
    :type url_prefix: str
    :param override: the dictionary with the parameters to override
    :type override: dict
    :return: the generated URL
    :rtype: str
    """

    # combine all parameters
    params = {}
    for key in request.POST.keys():
        params[key] = request.POST.getlist(key)
    for key in request.GET.keys():
        params[key] = request.GET.getlist(key)
    if override is not None:
        for key in override.keys():
            params[key] = override[key]

    # generate url
    result = url_prefix
    if not result.endswith("?"):
        result += "?"
    first = True
    for key in params.keys():
        value = params[key]
        if not first:
            result += "&"
        if type(value) is list:
            first_inner = True
            for v in value:
                if not first_inner:
                    result += "&"
                    result += key
                else:
                    result += key
                result += "="
                result += urllib.parse.quote_plus(v)
                first_inner = False
        else:
            result += key
            result += "="
            result += urllib.parse.quote_plus(value)
        first = False

    return result


def add_export_urls(request, context, url, formats):
    """
    Adds export urls to the template context. Uses the parameter 'format'
    and '<format>_url' for the context.

    :param request: the request to extract the parameters for the URL from
    :type request: HttpRequest
    :param context: the template context
    :type context: dict
    :param url: the URL to use
    :type url: str
    :param formats: the formats to generated URLs for and add as parameters
                    to the context (eg {'csv', 'xls'})
    :type formats: list
    """

    for f in formats:
        context[f + '_url'] = request_to_url(request, url, {'format': f})
