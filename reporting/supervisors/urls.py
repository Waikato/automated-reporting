from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),

    url(r'^search-by-faculty', views.search_by_faculty, name='search-by-faculty'),
    url(r'^list-by-faculty$', views.list_by_faculty, name='list-by-faculty'),

    url(r'^search-by-supervisor$', views.search_by_supervisor, name='search-by-supervisor'),
    url(r'^list-by-supervisor$', views.list_by_supervisor, name='list-by-supervisor'),

    url(r'^search-by-student$', views.search_by_student, name='search-by-student'),
    url(r'^list-by-student$', views.list_by_student, name='list-by-student'),
]
