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
import reporting.os_utils as os_utils
from dbbackend.models import read_last_parameter, write_last_parameter, TableStatus

logger = logging.getLogger(__name__)


DEFAULT_COLUMNS = [
    "Total Enrolment",
    "Total Passed",
    "Total Passed %",
    "Domestic Total",
    "Domestic Passed",
    "Domestic Passed %",
    "International Total",
    "International Passed",
    "International Passed %",
    "Domestic Level 7 Total",
    "Domestic Level 7 Passed",
    "Domestic Level 7 Passed %",
    "Domestic Level >=8 Total",
    "Domestic Level >=8 Passed",
    "Domestic Level >=8 Passed %",
    "International Level 7 Total",
    "International Level 7 Passed",
    "International Level 7 Passed %",
    "International Level >=8 Total",
    "International Level >=8 Passed",
    "International Level >=8 Passed %",
]
""" The default columns to display. """

DEFAULT_TYPE = "master"
""" the default type. """


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
        years.append(str(row[0]))

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

    # get query date
    query_date = None
    rs = TableStatus.objects.all().filter(table=GradeResults._meta.db_table)
    for r in rs:
        query_date = r.timestamp
        break

    # configure template
    template = loader.get_template('lpp/index.html')
    context = applist.template_context('lpp')
    context['years'] = years
    context['schools'] = schools
    context['query_date'] = query_date
    context['last_year'] = read_last_parameter(request.user, 'lpp.year', str(years[0]))
    context['last_schools'] = read_last_parameter(request.user, 'lpp.schools', schools)
    context['last_paper'] = read_last_parameter(request.user, 'lpp.paper', "")
    context['last_type'] = read_last_parameter(request.user, 'lpp.type', DEFAULT_TYPE)
    context['last_columns'] = read_last_parameter(request.user, 'lpp.columns', DEFAULT_COLUMNS)
    context['last_filter1'] = read_last_parameter(request.user, 'lpp.filter1', "")
    context['last_operator1'] = read_last_parameter(request.user, 'lpp.operator1', "lt")
    context['last_value1'] = read_last_parameter(request.user, 'lpp.value1', "")
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

    response, paper = get_variable_with_error(request, 'lpp', 'paper')
    if paper is None:
        paper = ''

    response, columns = get_variable_with_error(request, 'lpp', 'columns', as_list=True)
    if response is not None:
        return response

    response, filter1 = get_variable_with_error(request, 'lpp', 'filter1')
    if filter1 is None:
        filter1 = ''
    response, operator1 = get_variable_with_error(request, 'lpp', 'operator1')
    if operator1 is None:
        operator1 = 'lt'
    response, value1 = get_variable_with_error(request, 'lpp', 'value1')
    if (value1 is None) or (len(value1) == 0):
        value1 = '0'

    formattype = get_variable(request, 'format')

    # save parameters
    write_last_parameter(request.user, 'lpp.year', str(year))
    write_last_parameter(request.user, 'lpp.schools', school)
    write_last_parameter(request.user, 'lpp.type', ptype)
    write_last_parameter(request.user, 'lpp.paper', paper)
    write_last_parameter(request.user, 'lpp.columns', columns)
    write_last_parameter(request.user, 'lpp.filter1', filter1)
    write_last_parameter(request.user, 'lpp.operator1', operator1)
    write_last_parameter(request.user, 'lpp.value1', value1)

    # add paper code
    columns.append("Paper Code")

    # load data from DB
    if len(paper) > 0:
        if ptype == "master":
            where = "AND paper_master_code LIKE '" + paper + "' "
        else:
            where = "AND paper_occurrence LIKE '" + paper + "' "
    elif len(school) > 0:
        where = "AND owning_school_clevel IN ('" + "','".join(school) + "')"
    else:
        where = ""
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
            paper_occurrence ASC
        """.format(cols, year, where, GradeResults._meta.db_table)
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
    try:
        stdoutfile.close()
    except:
        pass
    try:
        stderrfile.close()
    except:
        pass
    if not os.path.isfile(genname):
        msg = 'Failed to execute lpp! exit code: {1}, command: {0}'.format(" ".join(params), retval)
        logger.error(msg)
        return create_error_response(request, 'lpp', msg)

    # read data
    header = []
    body = []
    display = []
    filter1_idx = -1
    value1_num = float(value1)
    with open(genname, 'r') as infile:
        reader = csv.reader(infile)
        first = True
        for row in reader:
            if first:
                for i, c in enumerate(row):
                    if c in columns:
                        display.append(i)
                    if c == filter1:
                        filter1_idx = i
                header = [row[i] for i in display]
                first = False
            else:
                arow = [row[i] for i in display]
                if filter1_idx > -1:
                    if len(row[filter1_idx]) == 0:
                        continue
                    try:
                        curr1 = float(row[filter1_idx].replace('%', ''))
                    except Exception as e:
                        continue
                    if (operator1 == "lt") and (curr1 >= value1_num):
                        continue
                    if (operator1 == "le") and (curr1 > value1_num):
                        continue
                    if (operator1 == "eq") and (curr1 != value1_num):
                        continue
                    if (operator1 == "ge") and (curr1 < value1_num):
                        continue
                    if (operator1 == "gt") and (curr1 <= value1_num):
                        continue
                body.append(arow)

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
    os_utils.remove_file(outname)
    os_utils.remove_file(genname)
    os_utils.remove_file(stdoutname)
    os_utils.remove_file(stderrname)

    return response


@login_required
@permission_required("lpp.can_access_lpp")
def disclaimer(request):
    template = loader.get_template('lpp/disclaimer.html')
    context = applist.template_context('lpp')
    context['disclaimer_title'] = 'Information & Disclaimer'
    return HttpResponse(template.render(context, request))
