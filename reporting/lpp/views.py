from django.template import loader
import reporting.settings
import reporting.applist as applist
from reporting.error import create_error_response
from reporting.models import GradeResults
from django.db import connection
from django.http import HttpResponse
import tempfile
import csv
import os
import subprocess

def index(request):
    # get all years
    cursor = connection.cursor()
    cursor.execute("""
        SELECT DISTINCT(year)
        FROM %s
        ORDER BY year DESC
        """ % GradeResults._meta.db_table)
    years = []
    for row in cursor.fetchall():
        years.append(row[0])

    # get all schools
    cursor = connection.cursor()
    cursor.execute("""
        SELECT DISTINCT(owning_school_clevel)
        FROM %s
        ORDER BY owning_school_clevel ASC
        """ % GradeResults._meta.db_table)
    schools = []
    for row in cursor.fetchall():
        schools.append(row[0])

    # configure template
    template = loader.get_template('lpp/index.html')
    context = applist.template_context('lpp')
    context['years'] = years
    context['schools'] = schools
    return HttpResponse(template.render(context, request))

def output(request):
    # get parameters
    if "year" not in request.POST:
        return create_error_response(request, 'lpp', 'No year defined!')
    year = request.POST["year"]

    if "school" not in request.POST:
        return create_error_response(request, 'lpp', 'No school defined!')
    school = request.POST.getlist("school")

    if "type" not in request.POST:
        return create_error_response(request, 'lpp', 'No paper type defined!')
    type = request.POST["type"]
    if type not in ["master", "occurrence"]:
        return create_error_response(request, 'lpp', 'Unsupported type: {0}'.format(type))

    # load data from DB
    if len(school) == 0:
        schoolsql = ""
    else:
        schoolsql = "AND owning_school_clevel IN ('" + "','".join(school) + "')"
    cols = "owning_school_clevel,paper_master_code,paper_occurrence,prog_abbr,grade,isdomestic,result_status"
    cursor = connection.cursor()
    cursor.execute("""
        SELECT
            {0}
        FROM
            {3}
        WHERE
            year = {1}
            {2}
        ORDER BY
            paper_master_code ASC
        """.format(cols, year, schoolsql, GradeResults._meta.db_table))

    # generate CSV
    fd, outname = tempfile.mkstemp(suffix=".csv", prefix="reporting-")
    with open(outname, 'w') as outfile:
        writer = csv.writer(outfile, quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(cols.split(","))
        for row in cursor.fetchall():
            writer.writerow(row)

    # call LPP
    genname = outname.replace(".csv", "-gen.csv")
    stdoutname = outname.replace(".csv", "-stdout.csv")
    stdoutfile = open(stdoutname, 'wb')
    params = [
        reporting.settings.PERL,
        reporting.settings.LPP_SCRIPT,
        outname,
        genname,
    ]
    if type == "occurrence":
        params.append("-o")
    retval = subprocess.call(
        params,
        stdout=stdoutfile,
    )
    if retval != 0:
        return create_error_response(request, 'lpp', 'Failed to execute lpp: {0}'.format(retval))

    # generate output
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="lpp-{0}.csv"'.format(year)

    with open(genname, 'r') as infile:
        reader = csv.reader(infile)
        writer = csv.writer(response)
        for row in reader:
            writer.writerow(row)

    # remove temp files again
    try:
        os.remove(outname)
    except:
        pass
    try:
        os.remove(genname)
    except:
        pass
    try:
        os.remove(stdoutname)
    except:
        pass

    return response
