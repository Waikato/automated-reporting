from django.template import loader
import reporting.settings
import reporting.applist as applist
import reporting.form_utils as form_utils
from reporting.form_utils import get_variable_with_error, get_variable
from reporting.error import create_error_response
from dbbackend.models import GradeResults
from django.db import connection
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, permission_required
import tempfile
import csv
import os
import os.path
import subprocess
import django_excel as excel
import logging
import reporting.tempfile_utils as tempfile_utils

logger = logging.getLogger(__name__)


@login_required
@permission_required("lpp.can_access_lpp")
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


@login_required
@permission_required("lpp.can_access_lpp")
def output(request):
    # get parameters
    response, year = get_variable_with_error(request, 'lpp', 'year')
    if response is not None:
        return response

    response, school = get_variable_with_error(request, 'lpp', 'school', as_list=True)
    if response is not None:
        return response

    response, ptype = get_variable_with_error(request, 'lpp', 'type')
    if response is not None:
        return response
    if ptype not in ["master", "occurrence"]:
        return create_error_response(request, 'lpp', 'Unsupported type: {0}'.format(ptype))

    formattype = get_variable(request, 'format')

    # load data from DB
    if len(school) == 0:
        schoolsql = ""
    else:
        schoolsql = "AND owning_school_clevel IN ('" + "','".join(school) + "')"
    cols = "owning_school_clevel,paper_master_code,paper_occurrence,prog_abbr,grade,isdomestic,result_status"
    cursor = connection.cursor()
    sql = """
        SELECT
            {0}
        FROM
            {3}
        WHERE
            year = {1}
            {2}
        ORDER BY
            paper_master_code ASC
        """.format(cols, year, schoolsql, GradeResults._meta.db_table)
    logger.debug(sql)
    cursor.execute(sql)

    # generate CSV
    fd, outname = tempfile.mkstemp(suffix=".csv", prefix="reporting-", dir=tempfile_utils.gettempdir())
    logger.info("Generating CSV: {0}".format(outname))
    with open(outname, 'w') as outfile:
        writer = csv.writer(outfile, quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(cols.split(","))
        for row in cursor.fetchall():
            writer.writerow(row)
        outfile.flush()
    logger.info("Generated CSV ({0}) exists: ".format(outname, os.path.isfile(outname)))

    # call LPP
    genname = outname.replace(".csv", "-gen.csv")
    stdoutname = outname.replace(".csv", "-stdout.csv")
    stdoutfile = open(stdoutname, 'wb')
    stderrname = outname.replace(".csv", "-stderr.txt")
    stderrfile = open(stderrname, 'wb')
    if reporting.settings.PERLLIB is not None:
        env = dict(os.environ)
        env['PERL5LIB'] = reporting.settings.PERLLIB
    else:
        env = None
    params = [
        reporting.settings.PERL,
        reporting.settings.LPP_SCRIPT,
        outname,
        genname,
    ]
    if ptype == "occurrence":
        params.append("-o")
    logger.info("Command: {0}".format(" ".join(params)))
    retval = subprocess.call(
        params,
        stdout=stdoutfile,
        stderr=stderrfile,
        env=env,
    )
    if not os.path.isfile(genname):
        msg = 'Failed to execute lpp! exit code: {1}, command: {0}'.format(" ".join(params), retval)
        logger.error(msg)
        return create_error_response(request, 'lpp', msg)

    # read data
    header = []
    body = []
    with open(genname, 'r') as infile:
        reader = csv.reader(infile)
        first = True
        for row in reader:
            if first:
                header = row
                first = False
            else:
                body.append(row)

    # generate output
    if formattype in ["csv", "xls"]:
        book = excel.pe.Book({'LPP': [header] + body})
        response = excel.make_response(book, formattype, file_name="lpp-{0}.{1}".format(year, formattype))
        return response
    else:
        template = loader.get_template('lpp/list.html')
        context = applist.template_context('lpp')
        context['header'] = header
        context['body'] = body
        form_utils.add_export_urls(request, context, "/lpp/output", ['csv', 'xls'])
        response = HttpResponse(template.render(context, request))

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
