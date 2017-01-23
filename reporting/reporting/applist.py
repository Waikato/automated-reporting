from reporting.settings import APPS_LIST
from reporting.settings import APPS_SHORT
from reporting.settings import APPS_LONG

def get_apps():
    """
    Returns a list of all apps in the project.

    :return: list of app names
    :rtype: list
    """

    return APPS_LIST

def get_appname_short(name):
    """
    Returns the short name for the app.

    :param name: the name of the app
    :type name: str
    :return: the short name
    :rtype: str
    """

    return APPS_SHORT[name]


def get_appname_long(name):
    """
    Returns the long name for the app.

    :param name: the name of the app
    :type name: str
    :return: the long name
    :rtype: str
    """

    return APPS_LONG[name]

def template_context(app=None):
    """
    Returns the context for a template.

    :param app: the current active app
    :type app: str
    :return: the context
    :rtype: dict
    """

    result = {
        'apps': APPS_LIST,
        'apps_short': APPS_SHORT,
        'apps_long': APPS_LONG,
    }

    if app is not None:
        result['title'] = APPS_LONG[app]
        result['app'] = app
    else:
        result['title'] = 'Automated Reporting'

    return result