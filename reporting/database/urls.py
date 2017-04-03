from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^graderesults$', views.database_graderesults, name='database_graderesults'),
    url(r'^supervisors$', views.database_supervisors, name='database_supervisors'),
    url(r'^studentdates$', views.database_studentdates, name='database_studentdates'),
    url(r'^tablestatus', views.database_tablestatus, name='database_tablestatus'),
    url(r'^import/graderesults$', views.import_graderesults, name='import_graderesults'),
    url(r'^import/supervisors$', views.import_supervisors, name='import_supervisors'),
    url(r'^update/studentdates', views.update_studentdates, name='update_studentdates'),
]
