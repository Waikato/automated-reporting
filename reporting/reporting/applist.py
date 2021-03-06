from reporting.settings import APPS_LIST
from reporting.settings import APPS_SHORT
from reporting.settings import APPS_LONG
from reporting.settings import APPS_PRODUCTION
from reporting.settings import PRODUCTION
from reporting.settings import REPORTING_OPTIONS
from reporting.settings import LOCAL_USERS
from reporting.settings import AUTHENTICATION_TYPE
from reporting.settings import EMAIL_ENABLED
from maintenance_mode.core import get_maintenance_mode
import dbbackend.models as db_models


def get_apps():
    """
    Returns a list of all apps in the project.

    :return: list of app names
    :rtype: list
    """

    if not PRODUCTION:
        return APPS_LIST

    result = []
    for app in APPS_LIST:
        if APPS_PRODUCTION[app]:
            result.append(app)
    return result


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
        'apps': get_apps(),
        'apps_short': APPS_SHORT,
        'apps_long': APPS_LONG,
        'local_users': LOCAL_USERS,
        'auth_type': AUTHENTICATION_TYPE,
        'email_enabled': EMAIL_ENABLED,
        'announcements': db_models.get_active_announcements()
    }

    if app is not None:
        result['title'] = APPS_LONG[app]
        result['app'] = app
    else:
        result['title'] = 'Automated Reporting'
    result['options'] = REPORTING_OPTIONS
    result['maintenance'] = get_maintenance_mode()

    return result
