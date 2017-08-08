from django.template import loader
from collections import OrderedDict
import reporting.applist as applist
import reporting.form_utils as form_utils
from reporting.form_utils import get_variable_with_error, get_variable
from dbbackend.models import GradeResults, TableStatus
from django.db import connection
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, permission_required
import django_excel as excel
import logging
from datetime import datetime
from dbbackend.models import read_last_parameter, write_last_parameter
import tempfile
import reporting.tempfile_utils as tempfile_utils
import reporting
from reporting.error import create_error_response
import csv
import os
import subprocess
import reporting.os_utils as os_utils

logger = logging.getLogger(__name__)

MIN_AGE = 25
""" the minimum age for adult learners. """

MIN_CREDITS = 96
""" the minimum credits a student must have. """

PROGRAM_CODES = ['BC', 'BD', 'BH', 'BHC', 'UC', 'UD']
""" the programme_type_code values that are eligible. """

MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
""" the months for calculating the GPA. """


@login_required
@permission_required("al.can_access_al")
def index(request):
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
    template = loader.get_template('al/index.html')
    context = applist.template_context('al')
    context['schools'] = schools
    context['query_date'] = query_date
    context['last_school'] = read_last_parameter(request.user, 'al.school', "")
    context['last_cutoff'] = read_last_parameter(request.user, 'al.cutoff', "")
    context['last_min_age'] = read_last_parameter(request.user, 'al.min_age', MIN_AGE)
    context['last_min_gpa'] = read_last_parameter(request.user, 'al.min_gpa', "")
    context['last_min_points'] = read_last_parameter(request.user, 'al.min_points', MIN_CREDITS)
    return HttpResponse(template.render(context, request))


def query_to_csv(cursor, cols, outname):
    """
    Turns the query into a CSV file for the GPA calculation.

    :param cursor: the database cursor
    :type cursor: DictCursor
    :param cols: the header names
    :type cols: list
    :param outname: the CSV output filename
    :type outname: str
    """

    logger.info("Generating CSV: {0}".format(outname))
    with open(outname, 'w') as outfile:
        writer = csv.writer(outfile, quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(cols.split(","))
        for row in cursor.fetchall():
            writer.writerow(row)
        outfile.flush()
    logger.info("Generated CSV ({0}) exists: ".format(outname, os.path.isfile(outname)))


def compute_gpa(fname, school, cutoff_date, min_gpa, header, body):
    """
    Computes the GPA.

    :param fname: the name of the input CSV file
    :type fname: str
    :param school: the name of the school/faculty
    :type school: str
    :param cutoff_date: the cut-off date
    :type cutoff_date: datetime
    :param min_gpa: the minimum GPA to include
    :type min_gpa: flot
    :param header: the list to store the header information in
    :type header: list
    :param body: the list to store the body information in
    :type body: list
    :return: None if successful, otherwise error message
    :rtype: str
    """

    # filenames
    outgpaname = fname.replace(".csv", "-outgpa.csv")
    sortedname = fname.replace(".csv", "-sorted.csv")
    calcname = fname.replace(".csv", "-calc.csv")
    sorted2name = fname.replace(".csv", "-sorted2.csv")
    tmpfiles = [outgpaname, sortedname, calcname, sorted2name]

    # call GPA_GRADES
    if reporting.settings.PERLLIB is not None:
        env = dict(os.environ)
        env['PERL5LIB'] = reporting.settings.PERLLIB
    else:
        env = None
    params = [
        reporting.settings.PERL,
        reporting.settings.GPA_GRADES,
        fname,
        outgpaname,
        school,
    ]
    logger.info("Command: {0}".format(" ".join(params)))
    retval = subprocess.call(
        params,
        env=env,
    )
    if not os.path.isfile(outgpaname):
        msg = 'Failed to execute gpa-grades! exit code: {1}, command: {0}'.format(" ".join(params), retval)
        logger.error(msg)
        os_utils.remove_files(tmpfiles)
        return msg

    # sort
    retval = subprocess.call(
        ["/usr/bin/sort", outgpaname, "-o", sortedname],
        env=env,
    )

    # call GPA_CALC
    if reporting.settings.PERLLIB is not None:
        env = dict(os.environ)
        env['PERL5LIB'] = reporting.settings.PERLLIB
    else:
        env = None
    params = [
        reporting.settings.PERL,
        reporting.settings.GPA_CALC,
        sortedname,
        calcname,
        MONTHS[cutoff_date.month - 1],
        str(cutoff_date.year - MIN_AGE),
    ]
    logger.info("Command: {0}".format(" ".join(params)))
    retval = subprocess.call(
        params,
        env=env,
    )
    if not os.path.isfile(calcname):
        msg = 'Failed to execute gpacalc! exit code: {1}, command: {0}'.format(" ".join(params), retval)
        logger.error(msg)
        os_utils.remove_files(tmpfiles)
        return msg

    # sort (2)
    retval = subprocess.call(
        ["/usr/bin/sort", calcname, "-o", sorted2name, "-b", "-t", ",", "-n", "-r", "-k", "5,5", "-k", "6,6"],
        env=env,
    )

    # fill header/body
    header.append("Name")
    header.append("ID")
    header.append("DOB (Mon)")
    header.append("DOB (Year)")
    header.append("GPA")
    header.append("Points")
    header.append("Qualification")
    with open(sorted2name, 'r') as infile:
        reader = csv.reader(infile)
        for row in reader:
            if float(row[4]) >= min_gpa:
                body.append(row)

    os_utils.remove_files(tmpfiles)

    return None


@login_required
@permission_required("al.can_access_al")
def output(request):
    # get parameters
    response, school = get_variable_with_error(request, 'al', 'school')
    if response is not None:
        return response

    response, cutoff = get_variable_with_error(request, 'al', 'cutoff')
    if response is not None:
        return response
    cutoff_date = datetime.strptime(cutoff + "-01", "%Y-%m-%d")

    min_age = get_variable(request, 'min_age')
    if (min_age is None) or (len(min_age) == 0):
        min_age = MIN_AGE
    else:
        min_gpa = float(min_age)

    min_gpa = get_variable(request, 'min_gpa')
    if (min_gpa is None) or (len(min_gpa) == 0):
        min_gpa = 0.0
    else:
        min_gpa = float(min_gpa)

    min_points = get_variable(request, 'min_points')
    if (min_points is None) or (len(min_points) == 0):
        min_points = MIN_CREDITS
    else:
        min_points = float(min_points)

    formattype = get_variable(request, 'format')

    # save parameters
    write_last_parameter(request.user, 'al.school', school)
    write_last_parameter(request.user, 'al.cutoff', cutoff)
    write_last_parameter(request.user, 'al.min_age', min_age)
    write_last_parameter(request.user, 'al.min_gpa', min_gpa)
    write_last_parameter(request.user, 'al.min_points', min_points)

    cursor = connection.cursor()

    last_year = cutoff_date.year - 1
    curr_year = cutoff_date.year
    last_year_where = "year = {0}".format(last_year)
    curr_year_where = "(year = {0}) and (issemesteracourse = 1)".format(curr_year)
    cols = "owning_school_clevel,paper_occurrence,credits,name,student_id,school_of_study_clevel,dateofbirth,prog_abbr,result_status,grade"
    query = """
          select 
            {7}
          from 
            {6}
          where 
              ({0})
          and (dateofbirth < date '{1}-01' - interval '{2} year')
          and (credits_per_student >= {3})
          and (programme_type_code in ('{4}'))
          and (owning_school_clevel = '{5}')
          order by student_id
          """

    # last year: query
    sql = query.format(last_year_where, cutoff, min_age, min_points, "', '".join(PROGRAM_CODES),
                     school, GradeResults._meta.db_table, cols)
    logger.debug(sql)
    cursor.execute(sql)

    # last year: generate CSV
    fd, outname = tempfile.mkstemp(suffix=".csv", prefix="reporting-", dir=tempfile_utils.gettempdir())
    query_to_csv(cursor, cols, outname)
    os_utils.close_file(fd)

    # last year: calculate GPA
    last_header = []
    last_body = []
    compute_gpa(outname, school, cutoff_date, min_gpa, last_header, last_body)

    # current year: query
    sql = query.format(curr_year_where, cutoff, min_age, min_points, "', '".join(PROGRAM_CODES),
                     school, GradeResults._meta.db_table, cols)
    logger.debug(sql)
    cursor.execute(sql)

    # current year: generate CSV
    fd, outname = tempfile.mkstemp(suffix=".csv", prefix="reporting-", dir=tempfile_utils.gettempdir())
    query_to_csv(cursor, cols, outname)

    # current year: calculate GPA
    curr_header = []
    curr_body = []
    compute_gpa(outname, school, cutoff_date, min_gpa, curr_header, curr_body)

    # students have to be good in both years
    final_header = last_header[:]
    final_body = []
    id_idx = last_header.index("ID")
    gpa_idx = last_header.index("GPA")
    points_idx = last_header.index("Points")
    final_header.remove("GPA")
    final_header.remove("Points")
    last_ids = [row[id_idx] for row in last_body]
    curr_ids = [row[id_idx] for row in curr_body]
    both = set(last_ids).intersection(set(curr_ids))
    for row in curr_body:
        if row[id_idx] in both:
            arow = []
            for i, c in enumerate(row):
                if (i == gpa_idx) or (i == points_idx):
                    continue
                arow.append(c)
            final_body.append(arow)

    # generate output
    if formattype in ["csv", "xls"]:
        data = OrderedDict()
        data['AL - Recommendations - {0}'.format(school)] = [final_header] + final_body
        data['AL - {1} - {0}'.format(school, curr_year)] = [curr_header] + curr_body
        data['AL - {1} - {0}'.format(school, last_year)] = [last_header] + last_body
        book = excel.pe.Book(data)
        response = excel.make_response(book, formattype, file_name="al-{0}.{1}".format(cutoff, formattype))
        return response
    else:
        template = loader.get_template('al/list.html')
        context = applist.template_context('al')
        context['header'] = final_header
        context['body'] = final_body
        context['curr_year'] = curr_year
        context['curr_header'] = curr_header
        context['curr_body'] = curr_body
        context['last_year'] = last_year
        context['last_header'] = last_header
        context['last_body'] = last_body
        context['school'] = school
        form_utils.add_export_urls(request, context, "/al/output", ['csv', 'xls'])
        response = HttpResponse(template.render(context, request))

    return response


@login_required
@permission_required("al.can_access_al")
def details(request):
    # get parameters
    response, studentid = get_variable_with_error(request, 'al', 'student')
    if response is not None:
        return response

    formattype = get_variable(request, 'format')

    # get name
    sql = """
          select name
          from {1}
          where student_id = '{0}'
          order by year desc
          limit 1
          """.format(studentid, GradeResults._meta.db_table)
    logger.debug(sql)
    cursor = connection.cursor()
    cursor.execute(sql)
    sname = ""
    for row2 in cursor.fetchall():
        sname = row2[0]
        break

    # papers
    papers = []
    for gr in GradeResults.objects.all().filter(student_id=studentid).order_by('-occurrence_startdate'):
        data = dict()
        data["studentid"] = studentid
        data["studentname"] = sname
        data["program"] = gr.prog_abbr
        data["school"] = gr.school_of_study_clevel
        data["paper"] = gr.paper_master_code
        data["start_date"] = gr.occurrence_startdate
        data["classification"] = gr.classification
        data["credits"] = gr.credits
        data["student_credit_points"] = gr.student_credit_points
        data["grade"] = gr.grade
        data["grade_status"] = gr.grade_status
        papers.append(data)

    # CSV or HTML?
    if formattype in ['csv', 'xls']:
        content = dict()

        # papers
        data = list()
        data.append([
            'ID',
            'Name',
            'Program',
            'Faculty/School',
            'Paper code',
            'Start date',
            'Classification',
            'Credits',
            'Student credit points',
            'Grade',
            'Grade status',
        ])
        for row in papers:
            data.append([
                row["studentid"],
                row["studentname"],
                row["program"],
                row["school"],
                row["paper"],
                row["start_date"],
                row["classification"],
                row["credits"],
                row["student_credit_points"],
                row["grade"],
                row["grade_status"],
            ])
        content['Academic history'] = data

        book = excel.pe.Book(content)
        response = excel.make_response(book, formattype, file_name="al-student-{0}.{1}".format(studentid, formattype))
        return response
    else:
        template = loader.get_template('al/details.html')
        context = applist.template_context('al')
        context['papers'] = papers
        form_utils.add_export_urls(request, context, "/al/details", ['csv', 'xls'])
        return HttpResponse(template.render(context, request))
