from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^graderesults$', views.database_graderesults, name='database_graderesults'),
    url(r'^coursedefs$', views.database_coursedefs, name='database_coursedefs'),
    url(r'^bulk$', views.database_bulk, name='database_bulk'),
    url(r'^supervisors$', views.database_supervisors, name='database_supervisors'),
    url(r'^scholarships$', views.database_scholarships, name='database_scholarships'),
    url(r'^studentdates$', views.database_studentdates, name='database_studentdates'),
    url(r'^tablestatus', views.database_tablestatus, name='database_tablestatus'),
    url(r'^import/graderesults$', views.import_graderesults, name='import_graderesults'),
    url(r'^import/coursedefs$', views.import_coursedefs, name='import_coursedefs'),
    url(r'^import/bulk$', views.import_bulk, name='import_bulk'),
    url(r'^import/supervisors$', views.import_supervisors, name='import_supervisors'),
    url(r'^import/scholarships$', views.import_scholarships, name='import_scholarships'),
    url(r'^update/studentdates', views.update_studentdates, name='update_studentdates'),
]
