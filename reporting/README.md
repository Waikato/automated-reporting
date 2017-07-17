# Reporting - Django

## Requirements

* PostgreSQL: [psycopg2](http://stackoverflow.com/questions/5394331/how-to-setup-postgresql-database-in-django/5421511#5421511)
* Excel: [django-excel](http://django-excel.readthedocs.io/en/latest/)
* Dictionaries in models: [django-jsonfield](https://github.com/bradjasper/django-jsonfield)

See also the `setup.py` file for complete list of required modules.


## PostgreSQL

* give permissions to user `reporting` on current database's schema `public`:

  ```sql
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

  ```sql
  truncate database_graderesults;
  truncate database_lastparameters;
  truncate database_tablestatus;
  truncate supervisors_scholarship;
  truncate supervisors_supervisors;
  ```

* dropping Postgresql tables

  * Connect to database using `psql` command-line tool and run the following command:

    ```sql
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


## Email

* add the following to `custom_settings.py` if you want to enable email 
  notifications, e.g., when imports have finished. The following just uses
  port 25 on the localhost for sending out emails: 

  ```
  EMAIL_ENABLED = True
  EMAIL_HOST = 127.0.0.1
  EMAIL_PORT = 25
  EMAIL_HOST_USER = None
  EMAIL_HOST_PASSWORD = None
  EMAIL_USE_TLS = None
  EMAIL_USE_SSL = None
  EMAIL_SSL_KEYFILE = None
  EMAIL_SSL_CERTFILE = None
  EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
  ADMIN_EMAIL = 'admin@somewhere.com'
  ```

## Authentication

There are three different ways of using authentication (only one can be used 
at any given time):

* local users
* LDAP
* Shibboleth


### Local users

* add the following to `custom_settings.py`

  ```python
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

  ```bash
  python3 manage.py createsuperuser --username=<name> --email=<email>
  ```

* log into admin interface

  ```
  http://127.0.0.1:8000/admin/
  ```


### LDAP

* add the following to `settings_custom.py`:

  ```python
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

  ```sql
  ALTER TABLE public.auth_user ALTER COLUMN first_name TYPE varchar(75);
  ALTER TABLE public.auth_user ALTER COLUMN last_name TYPE varchar(75);
  ```

* syncing the users with the LDAP server:

  ```bash
  python3 manage.py ldap_sync_users
  ```

* Turning a user into a superuser:

  ```bash
  python3 manage.py ldap_promote <username>
  ```


### Shibboleth

* add the following to `settings_custom.py`:

  ```python
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

## Permissions

Below are the application-specific permissions:

* Leave

  * `leave.can_access_leave` - is allowed to use the application
  * `leave.can_manage_leave` - *reserved*

* Hyperlink Grades

  * `hyperlinkgrades.can_access_hyperlinkgrades` - is allowed to use the application
  * `hyperlinkgrades.can_manage_hyperlinkgrades` - *reserved*

* Low performing pass-rates

  * `lpp.can_access_lpp` - is allowed to use the application 
  * `lpp.can_manage_lpp` - *reserved*

* Supervisor Register

  * `supervisors.can_access_student_dates` - *reserved*
  * `supervisors.can_manage_student_dates` - for recalculating the student dates
  * `supervisors.can_access_supervisors` - is allowed to use the application
  * `supervisors.can_manage_supervisors` - for importing supervisor data
  * `supervisors.can_access_scholarship` - *reserved*
  * `supervisors.can_manage_scholarship` - for importing scholarship data
  * `supervisors.can_access_associatedrole` - *reserved*
  * `supervisors.can_manage_associatedrole` - for importing associated role data
  * `dbbackend.can_access_table_status` - for checking the table status
  * `dbbackend.can_manage_table_status` - *reserved*
  * `dbbackend.can_access_grade_results` - *reserved*
  * `dbbackend.can_manage_grade_results` - for importing grade results data
