Reporting - Django
==================

Requirements
------------

* PostgreSQL support - [psycopg2](http://stackoverflow.com/questions/5394331/how-to-setup-postgresql-database-in-django/5421511#5421511)


Changing models
---------------

Run the following commands after changing any data models:

* python3 manage.py makemigrations
* python3 manage.py migrate
