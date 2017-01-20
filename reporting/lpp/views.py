from django.template import loader
import reporting.applist as applist
import reporting.settings
from reporting.error import create_error_response
from django.db import connection
from django.http import HttpResponse
import tempfile
import csv
import os
import subprocess
import django_tables2 as tables

apps = applist.get_apps()

TITLE = "Low Performing Pass-rates"

def index(request):
    # get all years
    cursor = connection.cursor()
    cursor.execute("""
        SELECT DISTINCT(year)
        FROM grade_results
        ORDER BY year DESC
        """)
    years = []
    for row in cursor.fetchall():
        years.append(row[0])

    # configure template
    template = loader.get_template('lpp/index.html')
    context = {
        'title': TITLE,
        'applist': apps,
        'years': years,
    }
    return HttpResponse(template.render(context, request))

def output(request):
    # get parameters
    if "year" not in request.POST:
        return create_error_response(request, TITLE, 'No year defined!')
    year = request.POST["year"]

    if "type" not in request.POST:
        return create_error_response(request, TITLE, 'No paper type defined!')
    type = request.POST["type"]
    if type not in ["master", "occurrence"]:
        return create_error_response(request, TITLE, 'Unsupported type: {0}'.format(type))

    if "output" not in request.POST:
        return create_error_response(request, TITLE, 'No output type defined!')
    output = request.POST["output"]
    if output not in ["html", "csv"]:
        return create_error_response(request, TITLE, 'Unsupported output: {0}'.format(type))

    # load data from DB
    cols = "owning_school_clevel,paper_master_code,paper_occurrence,prog_abbr,grade,isdomestic,result_status"
    cursor = connection.cursor()
    cursor.execute("""
        SELECT
            {0}
        FROM
            grade_results
        WHERE
            year = {1}
        ORDER BY
            paper_master_code ASC
        """.format(cols, year))

    # generate CSV
    fd, outname = tempfile.mkstemp(suffix=".csv", prefix="reporting-")
    with open(outname, 'wb') as outfile:
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
        return create_error_response(request, TITLE, 'Failed to execute lpp: {0}'.format(retval))

    # generate output
    if output == "csv":
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="lpp-{0}.csv"'.format(year)

        with open(genname, 'rb') as infile:
            reader = csv.reader(infile)
            writer = csv.writer(response)
            for row in reader:
                writer.writerow(row)
    elif output == "html":
        html = []
        with open(genname, 'rb') as infile:
            reader = csv.reader(infile)
            for row in reader:
                html.append(row)
        template = loader.get_template('lpp/output.html')
        context = {
            'title': TITLE + " - Output",
            'applist': apps,
            'output': html,
        }
        response = HttpResponse(template.render(context, request, {
            'table': tables.Table(html)
        }))

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
