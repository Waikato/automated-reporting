from django.http import HttpResponse
from django.template import loader
import reporting.applist as applist
from django.template.defaulttags import register
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from . import dbimport
from datetime import date

from dbbackend.models import TableStatus, GradeResults
from supervisors.models import Supervisors, StudentDates, Scholarship
from reporting.form_utils import get_variable


@login_required
@user_passes_test(lambda u: u.is_superuser)
def database_bulk(request):
    template = loader.get_template('dbbackend/import_bulk.html')
    context = applist.template_context()
    context['title'] = 'Bulk import'
    return HttpResponse(template.render(context, request))


@login_required
@permission_required("database.can_manage_grade_results")
def database_graderesults(request):
    years = []
    for year in range(2003, date.today().year + 1):
        years.append(year)
    years.reverse()
    template = loader.get_template('dbbackend/import_graderesults.html')
    context = applist.template_context()
    context['title'] = 'Import grade results'
    context['years'] = years
    return HttpResponse(template.render(context, request))


@login_required
@permission_required("supervisors.can_manage_supervisors")
def database_supervisors(request):
    template = loader.get_template('dbbackend/import_supervisors.html')
    context = applist.template_context()
    context['title'] = 'Import supervisors'
    return HttpResponse(template.render(context, request))


@login_required
@permission_required("supervisors.can_manage_scholarships")
def database_scholarships(request):
    template = loader.get_template('dbbackend/import_scholarships.html')
    context = applist.template_context()
    context['title'] = 'Import scholarships'
    return HttpResponse(template.render(context, request))


@login_required
@permission_required("supervisors.can_manage_student_dates")
def database_studentdates(request):
    template = loader.get_template('dbbackend/update_studentdates.html')
    context = applist.template_context()
    context['title'] = 'Update student dates'
    return HttpResponse(template.render(context, request))


@login_required
@permission_required("database.can_manage_table_status")
def database_tablestatus(request):
    template = loader.get_template('dbbackend/table_status.html')
    tables = {}
    for t in TableStatus.objects.all():
        tables[t.table] = {}
        tables[t.table]['timestamp'] = t.timestamp
    context = applist.template_context()
    context['title'] = 'Table status'
    context['tables'] = tables
    return HttpResponse(template.render(context, request))


@login_required
@permission_required("supervisors.can_manage_supervisors")
def import_supervisors(request):
    # configure template
    csv = request.FILES['datafile']
    enc = get_variable(request, 'encoding')
    msg = dbimport.import_supervisors(csv.temporary_file_path(), enc)
    template = loader.get_template('message.html')
    context = applist.template_context()
    if msg is None:
        context['message'] = "Successful upload of supervisors!"
        dbimport.update_tablestatus(Supervisors._meta.db_table)
    else:
        context['message'] = "Failed to upload supervisors: " + msg
    return HttpResponse(template.render(context, request))


@login_required
@permission_required("supervisors.can_manage_scholarships")
def import_scholarships(request):
    # configure template
    csv = request.FILES['datafile']
    enc = get_variable(request, 'encoding')
    msg = dbimport.import_scholarships(csv.temporary_file_path(), enc)
    template = loader.get_template('message.html')
    context = applist.template_context()
    if msg is None:
        context['message'] = "Successful upload of scholarships!"
        dbimport.update_tablestatus(Scholarship._meta.db_table)
    else:
        context['message'] = "Failed to upload scholarships: " + msg
    return HttpResponse(template.render(context, request))


@login_required
@permission_required("database.can_manage_grade_results")
def import_graderesults(request):
    # configure template
    csv = request.FILES['datafile']
    year = int(get_variable(request, 'year', def_value='1900'))
    isgzip = (get_variable(request, 'gzip', def_value='off') == 'on')
    enc = get_variable(request, 'encoding')
    msg = dbimport.import_grade_results(year, csv.temporary_file_path(), isgzip, enc)
    template = loader.get_template('message.html')
    context = applist.template_context()
    if msg is None:
        context['message'] = "Successful upload of grade results!"
        dbimport.update_tablestatus(GradeResults._meta.db_table)
    else:
        context['message'] = "Failed to upload grade results: " + msg
    return HttpResponse(template.render(context, request))


@login_required
@user_passes_test(lambda u: u.is_superuser)
def import_bulk(request):
    # configure template
    csv = request.FILES['datafile']
    msg = dbimport.import_bulk(csv.temporary_file_path())
    template = loader.get_template('message.html')
    context = applist.template_context()
    if msg is None:
        context['message'] = "Successful bulk import!"
        dbimport.update_tablestatus(GradeResults._meta.db_table)
    else:
        context['message'] = "Failed to bulk import: " + msg
    return HttpResponse(template.render(context, request))


@login_required
@permission_required("supervisors.can_manage_student_dates")
def update_studentdates(request):
    # configure template
    msg = dbimport.populate_student_dates()
    template = loader.get_template('message.html')
    context = applist.template_context()
    if msg is None:
        context['message'] = "Successful student dates recalculation!"
        dbimport.update_tablestatus(StudentDates._meta.db_table)
    else:
        context['message'] = "Failed to recalculate student dates: " + msg
    return HttpResponse(template.render(context, request))


@register.filter
def get_item(dictionary, key):
    """
    Filter method for retrieving the value of a dictionary.

    Taken from here:
    http://stackoverflow.com/a/8000091

    {{ mydict|get_item:item.NAME }}
    """
    return dictionary.get(key)
