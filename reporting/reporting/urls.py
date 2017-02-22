"""reporting URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^database$', views.database, name='database'),
    url(r'^database/graderesults$', views.upload_grade_results, name='upload_grade_results'),
    url(r'^database/supervisors$', views.upload_supervisors, name='upload_supervisors'),
    url(r'^database/studentdates', views.populate_studentdates, name='populate_studentdates'),
    url(r'^leave/', include('leave.urls')),
    url(r'^lpp/', include('lpp.urls')),
    url(r'^supervisors/', include('supervisors.urls')),
    url(r'^admin/', admin.site.urls),
]
