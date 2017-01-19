from django.apps import apps

def get_apps():
    """
    Returns a list of all apps in the project.

    :return: list of app names
    :rtype: list
    """

    result = []
    for app in apps.get_app_configs():
        if app.name.startswith("django"):
            continue
        if app.name.startswith("applist"):
            continue
        result.append(app.name)

    return result