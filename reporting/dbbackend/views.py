from django.http import HttpResponse
from django.template import loader
import reporting.applist as applist
from django.template.defaulttags import register
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from . import dbimport
from datetime import date
import threading
from reporting.tempfile_utils import create_temp_copy
import reporting.settings

from dbbackend.models import TableStatus, GradeResults
from reporting.form_utils import get_variable


@login_required
@user_passes_test(lambda u: u.is_superuser)
def database_bulk(request):
    template = loader.get_template('dbbackend/import_bulk.html')
    context = applist.template_context()
    context['title'] = 'Bulk import'
    return HttpResponse(template.render(context, request))


@login_required
@permission_required("dbbackend.can_manage_grade_results")
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
@permission_required("dbbackend.can_manage_table_status")
def database_tablestatus(request):
    template = loader.get_template('dbbackend/table_status.html')
    tables = []
    for t in TableStatus.objects.all().order_by('table'):
        row = dict()
        row['table'] = t.table
        row['timestamp'] = t.timestamp
        row['message'] = t.message
        tables.append(row)
    context = applist.template_context()
    context['title'] = 'Table status'
    context['tables'] = tables
    context['refresh_interval'] = reporting.settings.TABLE_STATUS_REFRESH_INTERVAL
    return HttpResponse(template.render(context, request))


@login_required
@permission_required("supervisors.can_manage_supervisors")
def import_supervisors(request):
    # configure template
    csv = create_temp_copy(request.FILES['datafile'].temporary_file_path())
    enc = get_variable(request, 'encoding')
    t = threading.Thread(target=dbimport.queue_import_supervisors, args=(csv, enc), kwargs={})
    t.setDaemon(True)
    t.start()
    template = loader.get_template('message.html')
    context = applist.template_context()
    context['message'] = "Started import of supervisors... Check 'Table status' page for progress."
    return HttpResponse(template.render(context, request))


@login_required
@permission_required("supervisors.can_manage_scholarships")
def import_scholarships(request):
    # configure template
    csv = create_temp_copy(request.FILES['datafile'].temporary_file_path())
    enc = get_variable(request, 'encoding')
    t = threading.Thread(target=dbimport.queue_import_scholarships, args=(csv, enc), kwargs={})
    t.setDaemon(True)
    t.start()
    template = loader.get_template('message.html')
    context = applist.template_context()
    context['message'] = "Started import of scholarships... Check 'Table status' page for progress."
    return HttpResponse(template.render(context, request))


@login_required
@permission_required("dbbackend.can_manage_grade_results")
def import_graderesults(request):
    # configure template
    csv = create_temp_copy(request.FILES['datafile'].temporary_file_path())
    year = int(get_variable(request, 'year', def_value='1900'))
    isgzip = (get_variable(request, 'gzip', def_value='off') == 'on')
    enc = get_variable(request, 'encoding')
    t = threading.Thread(target=dbimport.queue_import_grade_results, args=(year, csv, isgzip, enc), kwargs={})
    t.setDaemon(True)
    t.start()
    template = loader.get_template('message.html')
    context = applist.template_context()
    context['message'] = "Started import of grade results... Check 'Table status' page for progress."
    return HttpResponse(template.render(context, request))


@login_required
@user_passes_test(lambda u: u.is_superuser)
def import_bulk(request):
    # configure template
    csv = request.FILES['datafile'].temporary_file_path()
    msg = dbimport.import_bulk(csv)
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
    t = threading.Thread(target=dbimport.queue_populate_student_dates, args=(), kwargs={})
    t.setDaemon(True)
    t.start()
    template = loader.get_template('message.html')
    context = applist.template_context()
    context['message'] = "Started student dates recalculation... Check 'Table status' page for progress."
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
