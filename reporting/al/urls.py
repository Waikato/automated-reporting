from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^output$', views.output, name='output'),
    url(r'^details$', views.details, name='details'),
]
