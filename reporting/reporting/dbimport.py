from reporting.models import GradeResults
from supervisors.models import Supervisors, StudentDates
from reporting.db import truncate_strings, string_cell, int_cell, float_cell
from csv import DictReader
import gzip
import traceback
import sys
from datetime import datetime
from django.db import connection

def parse_grade_results_date(name, value):
    """
    Parses the various date formats of the grade results.
    :param name:
    :param value:
    :return:
    """
    if value == "" or value is None:
        return "0001-01-01"
    if name == "achievement_date":
        dformat = "%m/%d/%y"
    elif name == "query_date":
        dformat = "%d %B %Y"
    elif name in ["dateofbirth","dateofdeath","occurrence_startdate","occurrence_enddate","award_completion_date","award_completion_confirmed_date"]:
        dformat = "%d-%b-%Y"
    else:
        dformat = "%d/%m/%y"
    try:
        d = datetime.strptime(value, dformat)
        return d.strftime("%Y-%m-%d")
    except Exception as ex:
        print("name=" + name + ", value=" + value + ", format=" + dformat)
        traceback.print_exc(file=sys.stdout)
        return None

def import_grade_results(year, csv, isgzip):
    """
    Imports the grade results for a specific year (Brio/Hyperion export).

    :param year: the year to import the results for (eg 2015)
    :type year: int
    :param csv: the CSV file to import, can be gzip compressed
    :type csv: str
    :param isgzip: true if GZIP compressed
    :type isgzip: bool
    :return: None if successful, otherwise error message
    :rtype: str
    """
    # delete previous rows for year
    GradeResults.objects.all().filter(year=year).delete()
    # import
    try:
        if isgzip:
            csvfile = gzip.open(csv, mode='rt', encoding='ISO-8859-1')
        else:
            csvfile = open(csv, encoding='ISO-8859-1')
        reader = DictReader(csvfile)
        reader.fieldnames = [name.lower().replace(" ", "_") for name in reader.fieldnames]
        for row in reader:
            truncate_strings(row, 250)
            r = GradeResults()
            r.year = year
            r.student_id = string_cell(row, ['student_id'])
            r.name = string_cell(row, ['name'])
            r.title = string_cell(row, ['title'])
            r.prefered_given_name = string_cell(row, ['prefered_given_name'], defvalue='')
            r.given_name = string_cell(row, ['given_name'], defvalue='')
            r.other_given_names = string_cell(row, ['other_given_names'], defvalue='')
            r.family_name = string_cell(row, ['family_name'], defvalue='')
            r.previous_name = string_cell(row, ['previous_name'])
            r.address1 = string_cell(row, ['address1', 'address_line_1'])
            r.address2 = string_cell(row, ['address2', 'address_line_2'])
            r.address2a = string_cell(row, ['address2a'])
            r.address2b = string_cell(row, ['address2b'])
            r.address3 = string_cell(row, ['address3', 'address_line_3'])
            r.address4 = string_cell(row, ['address4', 'address_line_4'])
            r.postcode = string_cell(row, ['postcode', 'postal_area_code'])
            r.telephone = string_cell(row, ['telephone', 'perm_phone_number'])
            r.cellphone = string_cell(row, ['cellphone', 'perm_cellphone_number'])
            r.email = string_cell(row, ['email', 'perm_email_address'])
            r.hasdisability = int_cell(row, ['hasdisability'])
            r.isdomestic = int_cell(row, ['isdomestic', 'domestic_indicator'])
            r.is_domiciled_locally = int_cell(row, ['is_domiciled_locally'])
            r.citizenship = string_cell(row, ['citizenship'])
            r.residency_status = string_cell(row, ['residency_status'])
            r.origin = string_cell(row, ['origin'])
            r.gender = string_cell(row, ['gender'])
            r.ethnicity = string_cell(row, ['ethnicity'])
            r.ethnic_group = string_cell(row, ['ethnic_group'])
            r.all_ethnicities_string = string_cell(row, ['all_ethnicities_string'])
            r.all_iwi_string = string_cell(row, ['all_iwi_string'])
            r.dateofbirth = parse_grade_results_date('dateofbirth', string_cell(row, ['dateofbirth', 'date_of_birth']))
            r.dateofdeath = string_cell(row, ['dateofdeath'])
            r.waikato_1st = int_cell(row, ['waikato_1st'])
            r.nz_1st = int_cell(row, ['nz_1st'])
            r.last_year_sec = int_cell(row, ['last_year_sec'])
            r.sec_qual_year = int_cell(row, ['sec_qual_year'])
            r.last_sec_school = string_cell(row, ['last_sec_school'])
            r.last_sec_school_region = string_cell(row, ['last_sec_school_region'])
            r.highest_sec_qual = string_cell(row, ['highest_sec_qual'])
            r.main_activity = string_cell(row, ['main_activity'])
            r.award_title = string_cell(row, ['award_title'])
            r.prog_abbr = string_cell(row, ['prog_abbr'])
            r.programme = string_cell(row, ['programme'])
            r.programme_type_code = string_cell(row, ['programme_type_code'])
            r.programme_type = string_cell(row, ['programme_type'])
            r.ishigherdegree = int_cell(row, ['ishigherdegree'])
            r.school_of_study = string_cell(row, ['school_of_study'])
            r.school_of_study_clevel = string_cell(row, ['school_of_study_clevel'])
            r.paper_master_code = string_cell(row, ['paper_master_code', 'paper_master'])
            r.paper_occurrence = string_cell(row, ['paper_occurrence'])
            r.paper_title = string_cell(row, ['paper_title'])
            r.occurrence_startdate = parse_grade_results_date('occurrence_startdate', string_cell(row, ['occurrence_startdate']))
            r.occurrence_startyear = int_cell(row, ['occurrence_startyear'])
            r.occurrence_startweek = int_cell(row, ['occurrence_startweek'])
            r.occurrence_enddate = parse_grade_results_date('occurrence_enddate', string_cell(row, ['occurrence_enddate']))
            r.stage = int_cell(row, ['stage'])
            r.credits = float_cell(row, ['credits'])
            r.student_credit_points = float_cell(row, ['student_credit_points'])
            r.iscancelled = int_cell(row, ['iscancelled'])
            r.isoncampus = int_cell(row, ['isoncampus'])
            r.issemesteracourse = int_cell(row, ['issemesteracourse'])
            r.issemesterbcourse = int_cell(row, ['issemesterbcourse'])
            r.iswholeyearcourse = int_cell(row, ['iswholeyearcourse'])
            r.location_code = string_cell(row, ['location_code'])
            r.location = string_cell(row, ['location'])
            r.owning_school_clevel = string_cell(row, ['owning_school_clevel'])
            r.owning_school = string_cell(row, ['owning_school'])
            r.owning_department_clevel = string_cell(row, ['owning_department_clevel'])
            r.owning_department = string_cell(row, ['owning_department'])
            r.owning_level4_clevel = string_cell(row, ['owning_level4_clevel'])
            r.owning_level4_department = string_cell(row, ['owning_level4_department'])
            r.owning_level4or3_department = string_cell(row, ['owning_level4or3_department'])
            r.owning_level4or3_clevel = string_cell(row, ['owning_level4or3_clevel'])
            r.delivery_mode_code = string_cell(row, ['delivery_mode_code'])
            r.delivery_mode = string_cell(row, ['delivery_mode'])
            r.semester_code = string_cell(row, ['semester_code'])
            r.semester_description = string_cell(row, ['semester_description'])
            r.isselfpaced = int_cell(row, ['isselfpaced'])
            r.source_of_funding = string_cell(row, ['source_of_funding'])
            r.funding_category_code = string_cell(row, ['funding_category_code'])
            r.funding_category = string_cell(row, ['funding_category'])
            r.cost_category_code = string_cell(row, ['cost_category_code'])
            r.cost_category = string_cell(row, ['cost_category'])
            r.research_supplement_code = int_cell(row, ['research_supplement_code'])
            r.research_supplement = string_cell(row, ['research_supplement'])
            r.classification_code = float_cell(row, ['classification_code'])
            r.classification = string_cell(row, ['classification'])
            r.division = string_cell(row, ['division'])
            r.division_code = string_cell(row, ['division_code'])
            r.specified_programme = string_cell(row, ['specified_programme'])
            r.major = string_cell(row, ['major'])
            r.second_major = string_cell(row, ['second_major'])
            r.major2 = string_cell(row, ['major2'])
            r.second_major2 = string_cell(row, ['second_major2'])
            r.main_subject = string_cell(row, ['main_subject'])
            r.second_subject = string_cell(row, ['second_subject'])
            r.supporting_subject = string_cell(row, ['supporting_subject'])
            r.teaching_1 = string_cell(row, ['teaching_1'])
            r.teaching_2 = string_cell(row, ['teaching_2'])
            r.teaching_3 = string_cell(row, ['teaching_3'])
            r.teaching_4 = string_cell(row, ['teaching_4'])
            r.subject = string_cell(row, ['subject'])
            r.field = string_cell(row, ['field'])
            r.specialisation = string_cell(row, ['specialisation'])
            r.stream = string_cell(row, ['stream'])
            r.endorsement = string_cell(row, ['endorsement'])
            r.award_year = int_cell(row, ['award_year'])
            r.award_completion_status = string_cell(row, ['award_completion_status'])
            r.award_completion_date = parse_grade_results_date('award_completion_date', string_cell(row, ['award_completion_date']))
            r.award_completion_confirmed_date = parse_grade_results_date('award_completion_confirmed_date', string_cell(row, ['award_completion_confirmed_date']))
            r.admission_year = int_cell(row, ['admission_year'])
            r.admission_reason = string_cell(row, ['admission_reason'])
            r.admission_criteria = string_cell(row, ['admission_criteria'])
            r.admission_status = string_cell(row, ['admission_status'])
            r.grade = string_cell(row, ['grade'])
            r.grade_status = string_cell(row, ['grade_status'])
            r.result_status_code = string_cell(row, ['result_status_code'])
            r.result_status = string_cell(row, ['result_status'])
            r.grade_ranking = int_cell(row, ['grade_ranking'])
            r.mark = float_cell(row, ['mark'])
            r.moe_completion_code = int_cell(row, ['moe_completion_code'])
            r.iscontinuinggrade = int_cell(row, ['iscontinuinggrade'])
            r.ispassgrade = int_cell(row, ['ispassgrade'])
            r.query_date = parse_grade_results_date('query_date', string_cell(row, ['query_date']))
            r.enr_year = int_cell(row, ['enr_year', 'enrolment_year'])
            r.enrolment_status = string_cell(row, ['enrolment_status'])
            r.final_grade = string_cell(row, ['final_grade'])
            r.final_grade_ranking = int_cell(row, ['final_grade_ranking'])
            r.final_grade_status = string_cell(row, ['final_grade_status'])
            r.final_grade_result_status = string_cell(row, ['final_grade_result_status'])
            r.papers_per_student = int_cell(row, ['papers_per_student'])
            r.credits_per_student = float_cell(row, ['credits_per_student'])
            r.gpa = float_cell(row, ['gpa'])
            r.ones = int_cell(row, ['ones'])
            r.allgradeones = int_cell(row, ['allgradeones'])
            r.passgradeones = int_cell(row, ['passgradeones'])
            r.retentionones = int_cell(row, ['retentionones'])
            r.award_completion_year = int_cell(row, ['award_completion_year'])
            r.personoid = float_cell(row, ['personoid'])
            r.courseoccurrenceoid = float_cell(row, ['courseoccurrenceoid'])
            r.awardenrolmentoid = float_cell(row, ['awardenrolmentoid'])
            r.enrolmentorcosuoid = float_cell(row, ['enrolmentorcosuoid'])
            r.isformalprogramme = int_cell(row, ['isformalprogramme'])
            r.citizenship_simple = string_cell(row, ['citizenship_simple'])
            r.moe_pbrf_code = string_cell(row, ['moe_pbrf_code'])
            r.moe_pbrf = string_cell(row, ['moe_pbrf'])
            r.achievement_date = parse_grade_results_date('achievement_date', string_cell(row, ['achievement_date']))
            r.te_reo = int_cell(row, ['te_reo'])
            r.save()

        # close file
        csvfile.close()
    except Exception as ex:
        traceback.print_exc(file=sys.stdout)
        return str(ex)

    return None

def populate_student_dates():
    """
    Populates the studentdates table. Truncates the table first.

    :return: None if successful, otherwise error message
    :rtype: str
    """
    # delete old rows
    StudentDates.objects.all().delete()

    # get all students that are supervised
    cursor = connection.cursor()
    cursor.execute("""
        SELECT DISTINCT(student_id)
        FROM %s
        """ % Supervisors._meta.db_table)

    cursor2 = connection.cursor()
    for row in cursor.fetchall():
        id = str(row[0]).strip()
        table = GradeResults._meta.db_table
        print(id)

        master_months = None
        master_start = None
        master_end = None
        master_school = ''
        phd_months = None
        phd_start = None
        phd_end = None
        phd_school = ''
        try:
            # master - months
            sql = "select sum(credits / cast(regexp_replace(paper_occurrence, '([A-Z]+)59([3456789])-(.*)', '\\2') as integer) / 30 * 12), count(*) " \
                + "from " + table + " " \
                + "where student_id = '" + id + "' " \
                + "and programme_type_code = 'MD' " \
                + "and paper_occurrence ~ '([A-Z]+)59([3456789])-(.*)' " \
                + "group by student_id"
            cursor2.execute(sql)
            for row2 in cursor2.fetchall():
                master_months = row2[0]
                break

            # master - start date
            sql = "select min(occurrence_startdate), owning_school_clevel " \
                + "from " + table + " " \
                + "where student_id = '" + id + "' " \
                + "and programme_type_code = 'MD' " \
                + "and paper_occurrence ~ '([A-Z]+)59([3456789])-(.*)' " \
                + "group by student_id, owning_school_clevel"
            cursor2.execute(sql)
            for row2 in cursor2.fetchall():
                master_start = row2[0]
                master_school = row2[1]
                break

            # master - end date
            sql = "select max(occurrence_enddate) " \
                + "from " + table + " " \
                + "where student_id = '" + id + "' " \
                + "and programme_type_code = 'MD' " \
                + "and paper_occurrence ~ '([A-Z]+)59([3456789])-(.*)' " \
                + "and final_grade is not null " \
                + "group by student_id"
            cursor2.execute(sql)
            for row2 in cursor2.fetchall():
                master_end = row2[0]
                break

            # PhD - months
            sql = "select sum(coalesce(student_credit_points, credits_per_student) / credits) * 12, count(*) " \
                + "from " + table + " " \
                + "where student_id = '" + id + "' " \
                + "and programme_type_code = 'DP' " \
                + "group by student_id"
            cursor2.execute(sql)
            for row2 in cursor2.fetchall():
                phd_months = row2[0]
                break

            # PhD - start date
            sql = "select min(occurrence_startdate), owning_school_clevel " \
                + "from " + table + " " \
                + "where student_id = '" + id + "' " \
                + "and programme_type_code = 'DP' " \
                + "group by student_id, owning_school_clevel"
            cursor2.execute(sql)
            for row2 in cursor2.fetchall():
                phd_start = row2[0]
                phd_school = row2[1]
                break

            # PhD - end date
            sql = "select occurrence_enddate " \
                + "from " + table + " " \
                + "where student_id = '" + id + "' " \
                + "and programme_type_code = 'DP' " \
                + "and not final_grade = '...'"
            cursor2.execute(sql)
            for row2 in cursor2.fetchall():
                phd_end = row2[0]
                break

            # save
            if phd_start is not None:
                r = StudentDates()
                r.student_id = id
                r.program = "DP"
                r.start_date = phd_start
                r.end_date = phd_end if phd_end is not None else '9999-12-31'
                r.months = phd_months
                r.school = phd_school
                r.save()
            if master_start is not None:
                r = StudentDates()
                r.student_id = id
                r.program = "MD"
                r.start_date = master_start
                r.end_date = master_end if master_end is not None else '9999-12-31'
                r.months = master_months
                r.school = master_school
                r.save()

        except Exception as ex:
            print("PhD: id=%s, start=%s, end=%s, months=%s" % (id, phd_start, phd_end, phd_months))
            print("Master: id=%s, start=%s, end=%s, months=%s" % (id, master_start, master_end, master_months))
            traceback.print_exc(file=sys.stdout)

    return None

def import_supervisors(csv):
    """
    Imports the supervisors (Jade Export).

    :param csv: the CSV file to import
    :type csv: str
    :return: None if successful, otherwise error message
    :rtype: str
    """
    # empty table
    Supervisors.objects.all().delete()
    # import
    try:
        with open(csv, encoding='ISO-8859-1') as csvfile:
            reader = DictReader(csvfile)
            reader.fieldnames = [name.lower().replace(" ", "_") for name in reader.fieldnames]
            for row in reader:
                truncate_strings(row, 250)
                r = Supervisors()
                r.student_id = row['student'][row['student'].rfind(' ')+1:]  # extract ID at end of string
                r.student = row['student']
                r.supervisor = row['supervisor']
                r.active_roles = row['active_roles']
                r.entity = row['entity']
                r.agreement_status = row['agreement_status']
                r.date_agreed = row['date_agreed']
                r.title = row['title']
                r.quals = row['quals']
                r.comments = row['comments']
                r.save()
    except Exception as ex:
        traceback.print_exc(file=sys.stdout)
        return str(ex)

    return None
