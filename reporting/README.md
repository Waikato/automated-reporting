Reporting - Django
==================

Requirements
------------

* PostgreSQL support - [psycopg2](http://stackoverflow.com/questions/5394331/how-to-setup-postgresql-database-in-django/5421511#5421511)


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

  * for emailing password resets etc

    ```
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    ```


* run the following command to create superuser

  ```
  python3 manage.py createsuperuser --username=<name> --email=<email>
  ```

* log into admin interface
  ```
  http://127.0.0.1:8000/admin/
  ```

