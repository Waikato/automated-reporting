# Reporting - Django

## Requirements

* PostgreSQL: [psycopg2](http://stackoverflow.com/questions/5394331/how-to-setup-postgresql-database-in-django/5421511#5421511)
* Excel: [django-excel](http://django-excel.readthedocs.io/en/latest/)
* Dictionaries in models: [django-jsonfield](https://github.com/bradjasper/django-jsonfield)

See also the `setup.py` file for complete list of required modules.


## PostgreSQL

* give permissions to user `reporting` on current database's schema `public`:

  ```
  GRANT USAGE ON SCHEMA public TO reporting;
  GRANT CREATE ON SCHEMA public TO reporting;
  ```

* backup

  only backup the following tables:

  * database_graderesults;
  * database_lastparameters;
  * database_tablestatus;
  * supervisors_scholarship;
  * supervisors_supervisors;

* restore

  empty the relevant tables first:

  ```
  truncate database_graderesults;
  truncate database_lastparameters;
  truncate database_tablestatus;
  truncate supervisors_scholarship;
  truncate supervisors_supervisors;
  ```

* dropping Postgresql tables

  * Connect to database using `psql` command-line tool and run the following command:

    ```
    drop table auth_group, auth_group_permissions, auth_permission, auth_user, auth_user_groups, auth_user_user_permissions, dbbackend_graderesults, dbbackend_lastparameters, dbbackend_tablestatus, django_admin_log, django_content_type, django_migrations, django_session, supervisors_scholarship, supervisors_studentdates, supervisors_supervisors cascade;
    ```

  * You can use the following command to list all available tables in a database:

    ```
    \dt *.*
    ```

## Changing models

Run the following commands after changing any data models:

* `python3 manage.py makemigrations`
* `python3 manage.py makemigrations dbbackend`
* `python3 manage.py migrate`


## Custom settings

All custom settings are to go into `settings_custom.py`, which resides next to
`settings.py`.


## Authentication

There are three different ways of using authentication (only one can be used 
at any given time):

* local users
* LDAP
* Shibboleth


### Local users

* add the following to `custom_settings.py`

  ```
  AUTHENTICATION_BACKENDS = [
      'django.contrib.auth.backends.ModelBackend',
  ]

  MIDDLEWARE_CLASSES = [
      'django.middleware.security.SecurityMiddleware',
      'django.contrib.sessions.middleware.SessionMiddleware',
      'django.middleware.common.CommonMiddleware',
      'django.middleware.csrf.CsrfViewMiddleware',
      'django.contrib.auth.middleware.AuthenticationMiddleware',
      'django.contrib.messages.middleware.MessageMiddleware',
      'django.middleware.clickjacking.XFrameOptionsMiddleware',
      'maintenance_mode.middleware.MaintenanceModeMiddleware',
  ]  
  ```

* run the following command to create superuser

  ```
  python3 manage.py createsuperuser --username=<name> --email=<email>
  ```

* log into admin interface
  ```
  http://127.0.0.1:8000/admin/
  ```


### LDAP

* add the following to `settings_custom.py`:

  ```
  USE_LDAP = True
  if USE_LDAP:
      AUTHENTICATION_BACKENDS = [
          'django_python3_ldap.auth.LDAPBackend',
      ]
      LDAP_AUTH_URL = "ldaps://server.example.com:636"
      LDAP_AUTH_USE_TLS = False
      LDAP_AUTH_CONNECTION_USERNAME = None
      LDAP_AUTH_CONNECTION_PASSWORD = None
      LDAP_AUTH_SEARCH_BASE = "ou=Active,ou=People,dc=example,dc=com"
      MIDDLEWARE_CLASSES = [
          'django.middleware.security.SecurityMiddleware',
          'django.contrib.sessions.middleware.SessionMiddleware',
          'django.middleware.common.CommonMiddleware',
          'django.middleware.csrf.CsrfViewMiddleware',
          'django.contrib.auth.middleware.AuthenticationMiddleware',
          'django.contrib.messages.middleware.MessageMiddleware',
          'django.middleware.clickjacking.XFrameOptionsMiddleware',
          'maintenance_mode.middleware.MaintenanceModeMiddleware',
      ]
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


### Shibboleth

* add the following to `settings_custom.py`:

  ```
  USE_SHIBBOLETH = True
  if USE_SHIBBOLETH:
      AUTHENTICATION_BACKENDS = [
          'django.contrib.auth.backends.RemoteUserBackend',
      ]

      MIDDLEWARE_CLASSES = [
          'django.middleware.security.SecurityMiddleware',
          'django.contrib.sessions.middleware.SessionMiddleware',
          'django.middleware.common.CommonMiddleware',
          'django.middleware.csrf.CsrfViewMiddleware',
          'django.contrib.auth.middleware.AuthenticationMiddleware',
          'django.contrib.auth.middleware.PersistentRemoteUserMiddleware',
          'django.contrib.messages.middleware.MessageMiddleware',
          'django.middleware.clickjacking.XFrameOptionsMiddleware',
          'maintenance_mode.middleware.MaintenanceModeMiddleware',
      ]

  ```
