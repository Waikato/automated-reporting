from django.template import loader
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

logger = logging.getLogger(__name__)

MIN_AGE = 25
""" the minimum age for adult learners. """

MIN_CREDITS = 96
""" the minimum credits a student must have. """

MIN_GPA = 8
""" the minimum GPA that a student has to have. """

PROGRAM_CODES = ['BC', 'BD', 'BH', 'BHC', 'UC', 'UD']
""" the programme_type_code values that are eligible. """


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
    context['last_schools'] = read_last_parameter(request.user, 'al.schools', schools)
    context['last_cutoff'] = read_last_parameter(request.user, 'al.cutoff', "")
    return HttpResponse(template.render(context, request))


@login_required
@permission_required("al.can_access_al")
def output(request):
    # get parameters
    response, school = get_variable_with_error(request, 'al', 'school', as_list=True)
    if response is not None:
        return response

    response, cutoff = get_variable_with_error(request, 'al', 'cutoff')
    if response is not None:
        return response
    cutoff_date = datetime.strptime(cutoff, "%Y-%m-%d")

    formattype = get_variable(request, 'format')

    # save parameters
    write_last_parameter(request.user, 'al.schools', school)
    write_last_parameter(request.user, 'al.cutoff', cutoff)

    cursor = connection.cursor()
    cursor2 = connection.cursor()

    last_year = cutoff_date.year - 1
    curr_year = cutoff_date.year
    sql = """
          select student_id, owning_school_clevel
          from {8}
          where
              (    ((year = {0}) and (issemesteracourse = 1))
                or ((year = {0}) and (issemesterbcourse = 1))
                or ((year = {1}) and (issemesteracourse = 1)))
          and (dateofbirth < date '{2}' - interval '{3} year')
          and (credits_per_student >= {4})
          and (programme_type_code in ('{5}'))
          and owning_school_clevel in ('{6}')
          and (gpa >= {7})
          group by student_id, name, owning_school_clevel
          having count(distinct(year)) = 2
          order by owning_school_clevel, name
          """.format(last_year, curr_year, cutoff, MIN_AGE, MIN_CREDITS, "', '".join(PROGRAM_CODES),
                     "', '".join(school), MIN_GPA, GradeResults._meta.db_table)
    logger.debug(sql)
    cursor.execute(sql)
    header = ['Student ID', 'Name', 'Faculty']
    body = []
    for row in cursor.fetchall():
        studentid = row[0]
        logger.debug("Student ID: " + studentid)

        # check for full enrollment in prior year
        sql = """
              select student_id, sum(issemesteracourse) a_sem, sum(issemesterbcourse) b_sem
              from {2}
              where student_id = '{0}'
              and year = {1}
              group by year, student_id
              having sum(issemesteracourse) > 0
              and sum(issemesterbcourse) > 0
              """.format(studentid, last_year, GradeResults._meta.db_table)
        logger.debug(sql)
        cursor2.execute(sql)
        full = False
        for row2 in cursor2.fetchall():
            full = (row2[1] >= 1) and (row2[2] >= 1)
            logger.info("not full time enrolled")
            break
        if not full:
            continue

        # get student details
        sql = """
              select name
              from {2}
              where student_id = '{0}'
              and year = {1}
              limit 1
              """.format(studentid, curr_year, GradeResults._meta.db_table)
        logger.debug(sql)
        cursor2.execute(sql)
        name = ""
        for row2 in cursor2.fetchall():
            name = row2[0]
            break

        bodyrow = dict()
        bodyrow['id'] = row[0]
        bodyrow['name'] = name
        bodyrow['school'] = row[1]
        body.append(bodyrow)

    # generate output
    if formattype in ["csv", "xls"]:
        book = excel.pe.Book({'Adult Learners': [header] + body})
        response = excel.make_response(book, formattype, file_name="al-{0}.{1}".format(cutoff, formattype))
        return response
    else:
        template = loader.get_template('al/list.html')
        context = applist.template_context('al')
        context['header'] = header
        context['body'] = body
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
