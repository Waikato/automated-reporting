Reporting - Django
==================

Requirements
------------

* PostgreSQL: [psycopg2](http://stackoverflow.com/questions/5394331/how-to-setup-postgresql-database-in-django/5421511#5421511)
* Excel: [django-excel](http://django-excel.readthedocs.io/en/latest/)
* Dictionaries in models: [django-jsonfield](https://github.com/bradjasper/django-jsonfield)

Changing models
---------------

Run the following commands after changing any data models:

* `python3 manage.py makemigrations`
* `python3 manage.py migrate`


Setup users/groups
------------------

* enable authentication in `settings.py`

  * authentication backend

    ```
	AUTHENTICATION_BACKENDS = [
		'django.contrib.auth.backends.ModelBackend',
	]
    ```
  * ensure following apps are listed in `INSTALLED_APPS`

    ```
    'django.contrib.auth',
    'django.contrib.contenttypes',
    ```

  * ensure following middleware classes are listed in `MIDDLEWARE_CLASSES`

    ```
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    ```

* run the following command to create superuser

  ```
  python3 manage.py createsuperuser --username=<name> --email=<email>
  ```

* log into admin interface
  ```
  http://127.0.0.1:8000/admin/
  ```

LDAP
----

* Requirement: [django-python3-ldap>=0.9.14](https://github.com/etianen/django-python3-ldap)

* add LDAP support to `INSTALLED_APPS`:

  ```
  INSTALLED_APPS = [
      ...
      'django_python3_ldap',
      ...
  ]
  ```

* create `settings_ldap.py` in the same directory as `settings.py` with something like this:

  ```
  AUTHENTICATION_BACKENDS = [
      'django_python3_ldap.auth.LDAPBackend',
  ]

  LDAP_AUTH_URL = "ldaps://server.example.com:636"
  LDAP_AUTH_USE_TLS = False
  LDAP_AUTH_CONNECTION_USERNAME = None
  LDAP_AUTH_CONNECTION_PASSWORD = None
  LDAP_AUTH_SEARCH_BASE = "ou=Active,ou=People,dc=example,dc=com"
  LOGGING = {
      "version": 1,
      "disable_existing_loggers": False,
      "handlers": {
          "console": {
              "class": "logging.StreamHandler",
          },
      },
      "loggers": {
          "django_python3_ldap": {
              "handlers": ["console"],
              "level": "INFO",
          },
      },
  }
  ```

* By default, the django ldap module limits first and last name to 30 characters.
  After the initial `python3 manage.py migrate` call, alter the `auth_user` table
  as follows:

  ```
  ALTER TABLE public.auth_user ALTER COLUMN first_name TYPE varchar(75);
  ALTER TABLE public.auth_user ALTER COLUMN last_name TYPE varchar(75);
  ```

* syncing the users with the LDAP server:

  ```
  python3 manage.py ldap_sync_users
  ```

* Turning a user into a superuser:

  ```
  python3 manage.py ldap_promote <username>
  ```

PostgreSQL
----------

* give permissions to user `reporting` on current database's schema `public`:

  ```
  GRANT USAGE ON SCHEMA public TO reporting;
  GRANT CREATE ON SCHEMA public TO reporting;
  ```
