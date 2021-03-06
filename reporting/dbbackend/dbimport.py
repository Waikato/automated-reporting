from dbbackend.models import GradeResults, TableStatus, CourseDefs
from supervisors.models import Supervisors, StudentDates, Scholarship, AssociatedRole
from reporting.db import truncate_strings, encode_strings, string_cell, int_cell, float_cell, bool_cell
from csv import DictReader
import gzip
import traceback
import sys
import re
import os
from datetime import datetime
from django.db import connection
from maintenance_mode.core import set_maintenance_mode
from reporting.email_utils import send_email
import logging

logger = logging.getLogger(__name__)


FULL_TIME_CREDITS = 120
""" the minimum number of credits in order to be considered full time student """


def fix_org_unit(unit):
    """
    Fixes the organizational unit, e.g., SASS becomes FASS.

    :param unit: the unit to fix
    :type unit: str
    :return: the (potentially) fixed unit
    :rtype: str
    """
    if unit == "SASS":
        return "FASS"
    if unit == "SHUM":
        return "FASS"
    if unit == "SCMS":
        return "FCMS"
    if unit == "SEDU":
        return "FEDU"
    if unit == "SLAW":
        return "FLAW"
    if unit == "SMST":
        return "FMGT"
    if unit == "SMPD":
        return "FMIS"
    if unit == "SSEN":
        return "FSEN"
    if unit == "SSTE":
        return "FSEN"
    if unit == "PVCM":
        return "FMIS"
    return unit


def parse_grade_results_date(name, value):
    """
    Parses the various date formats of the grade results.
    :param name: the field name
    :type name: str
    :param value: the value to parse
    :type value: str
    :return: the fixed date
    :rtype: str
    """
    if value == "" or value is None:
        return "0001-01-01"
    if name == "achievement_date":
        dformat = "%m/%d/%y"
    elif name == "query_date":
        dformat = "%d %B %Y"
    elif name in ["dateofbirth", "dateofdeath", "occurrence_startdate", "occurrence_enddate", "award_completion_date", "award_completion_confirmed_date"]:
        dformat = "%d-%b-%Y"
    else:
        dformat = "%d/%m/%y"
    try:
        d = datetime.strptime(value, dformat)
        return d.strftime("%Y-%m-%d")
    except Exception as ex:
        logger.exception("name=" + name + ", value=" + value + ", format=" + dformat)
        return None


def queue_import_grade_results(year, csv, isgzip, encoding, email=None):
    """
    Queues the import of the grade results for a specific year (Brio/Hyperion export).

    :param year: the year to import the results for (eg 2015)
    :type year: int
    :param csv: the CSV file to import, can be gzip compressed
    :type csv: str
    :param isgzip: true if GZIP compressed
    :type isgzip: bool
    :param encoding: the file encoding (eg utf-8)
    :type encoding: str
    :param email: the (optional) email address to send a notification to
    :type email: str
    """

    update_tablestatus(GradeResults._meta.db_table, "Importing...")
    msg = import_grade_results(year, csv, isgzip, encoding, email=email)
    # query date from import is used when current year
    if (msg is not None) or (datetime.today().year != year):
        update_tablestatus(GradeResults._meta.db_table, msg=msg)


def import_grade_results(year, csv, isgzip, encoding, email=None, delete=True):
    """
    Imports the grade results for a specific year (Brio/Hyperion export).

    :param year: the year to import the results for (eg 2015)
    :type year: int
    :param csv: the CSV file to import, can be gzip compressed
    :type csv: str
    :param isgzip: true if GZIP compressed
    :type isgzip: bool
    :param encoding: the file encoding (eg utf-8)
    :type encoding: str
    :param email: the (optional) email address to send a notification to
    :type email: str
    :param delete: whether to delete the data file
    :type delete: bool
    :return: None if successful, otherwise error message
    :rtype: str
    """

    result = None

    set_maintenance_mode(True)

    query_date = None

    # delete previous rows for year
    GradeResults.objects.all().filter(year=year).delete()
    # import
    try:
        if isgzip:
            csvfile = gzip.open(csv, mode='rt', encoding=encoding)
        else:
            csvfile = open(csv, encoding=encoding)
        reader = DictReader(csvfile)
        reader.fieldnames = [name.lower().replace(" ", "_") for name in reader.fieldnames]
        count = 0
        for row in reader:
            count += 1
            truncate_strings(row, 250)
            encode_strings(row, 'utf-8')
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
            r.award_title = string_cell(row, ['award_title', 'award'])
            r.prog_abbr = string_cell(row, ['prog_abbr', 'prog_-_abbr'])
            r.programme = string_cell(row, ['programme'])
            r.programme_type_code = string_cell(row, ['programme_type_code'])
            r.programme_type = string_cell(row, ['programme_type'])
            r.ishigherdegree = int_cell(row, ['ishigherdegree'])
            r.school_of_study = string_cell(row, ['school_of_study'])
            r.school_of_study_clevel = fix_org_unit(string_cell(row, ['school_of_study_clevel']))
            r.paper_master_code = string_cell(row, ['paper_master_code', 'paper_master'])
            r.paper_occurrence = string_cell(row, ['paper_occurrence'])
            r.paper_title = string_cell(row, ['paper_title'])
            r.occurrence_startdate = parse_grade_results_date('occurrence_startdate', string_cell(row, ['occurrence_startdate']))
            r.occurrence_startyear = int_cell(row, ['occurrence_startyear'])
            r.occurrence_startweek = int_cell(row, ['occurrence_startweek'])
            r.occurrence_enddate = parse_grade_results_date('occurrence_enddate', string_cell(row, ['occurrence_enddate']))
            r.stage = int_cell(row, ['stage'])
            r.credits = float_cell(row, ['credits'])
            r.student_credit_points = float_cell(row, ['student_credit_points', 'student_credits'])
            r.iscancelled = int_cell(row, ['iscancelled'])
            r.isoncampus = int_cell(row, ['isoncampus'])
            r.issemesteracourse = int_cell(row, ['issemesteracourse'])
            r.issemesterbcourse = int_cell(row, ['issemesterbcourse'])
            r.iswholeyearcourse = int_cell(row, ['iswholeyearcourse'])
            r.location_code = string_cell(row, ['location_code'])
            r.location = string_cell(row, ['location'])
            r.owning_school_clevel = fix_org_unit(string_cell(row, ['owning_school_clevel']))
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
            if (query_date is None) and (r.query_date is not None):
                query_date = datetime.strptime(parse_grade_results_date('query_date', string_cell(row, ['query_date'])), "%Y-%m-%d")
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
            r.citizenship_simple = string_cell(row, ['citizenship_simple', 'citizenship_code'])
            r.moe_pbrf_code = string_cell(row, ['moe_pbrf_code'])
            r.moe_pbrf = string_cell(row, ['moe_pbrf'])
            r.achievement_date = parse_grade_results_date('achievement_date', string_cell(row, ['achievement_date']))
            r.te_reo = int_cell(row, ['te_reo'])
            r.save()
            # progress
            if (count % 1000) == 0:
                update_tablestatus(GradeResults._meta.db_table, "Imported " + str(count) + " rows...")

        # close file
        csvfile.close()
    except Exception as ex:
        msg = traceback.format_exc()
        logger.error(msg=msg)
        return msg
    finally:
        if delete:
            try:
                os.remove(csv)
            except Exception as ex:
                msg = traceback.format_exc()
                logger.error(msg=msg)
                result = msg

    #
    if (result is None) and (query_date is not None) and (query_date.year == datetime.today().year):
        update_tablestatus(GradeResults._meta.db_table, timestamp=query_date)

    if email is not None:
        send_email(email, 'Import: grade results', 'Import succeeded' if (result is None) else 'Import failed: ' + result)

    return result


def queue_import_coursedefs(year, csv, encoding, email=None):
    """
    Queues the import of the course definitions for a specific year (Brio/Hyperion export).

    :param year: the year to import the results for (eg 2015)
    :type year: int
    :param csv: the CSV file to import, can be gzip compressed
    :type csv: str
    :param encoding: the file encoding (eg utf-8)
    :type encoding: str
    :param email: the (optional) email address to send a notification to
    :type email: str
    """

    update_tablestatus(CourseDefs._meta.db_table, "Importing...")
    msg = import_coursedefs(year, csv, encoding, email=email)
    update_tablestatus(CourseDefs._meta.db_table, msg=msg)


def import_coursedefs(year, csv, encoding, email=None, delete=True):
    """
    Imports the course definitions for a specific year (Brio/Hyperion export).

    :param year: the year to import the results for (eg 2015)
    :type year: int
    :param csv: the CSV file to import, can be gzip compressed
    :type csv: str
    :param encoding: the file encoding (eg utf-8)
    :type encoding: str
    :param email: the (optional) email address to send a notification to
    :type email: str
    :param delete: whether to delete the data file
    :type delete: bool
    :return: None if successful, otherwise error message
    :rtype: str
    """

    result = None

    set_maintenance_mode(True)

    # delete previous rows for year
    CourseDefs.objects.all().filter(year=year).delete()
    # import
    try:
        csvfile = open(csv, encoding=encoding)
        reader = DictReader(csvfile)
        reader.fieldnames = [name.lower().replace(" ", "_") for name in reader.fieldnames]
        count = 0
        for row in reader:
            count += 1
            truncate_strings(row, 250)
            encode_strings(row, 'utf-8')
            r = CourseDefs()
            r.year = year
            r.code = string_cell(row, ['papercode'])
            r.title = string_cell(row, ['papertitle'])
            r.description = string_cell(row, ['paperdescription'])
            r.type = string_cell(row, ['papertype'])
            r.stage = int_cell(row, ['paperstage'])
            r.points = float_cell(row, ['paperpoints'])
            r.delivery_mode = string_cell(row, ['paperdeliverymode'])
            r.owning_programme = string_cell(row, ['paperowningprogramme'])
            r.owning_programme_title = string_cell(row, ['paperowningprogrammetitle'])
            r.fw_level = int_cell(row, ['paperfwlevel'])
            r.hours_contact = int_cell(row, ['paperhourscontact'])
            r.hours_self_directed = int_cell(row, ['paperhoursselfdirected'])
            r.hours_other_directed = int_cell(row, ['paperhoursotherdirected'])
            r.funding_source = string_cell(row, ['paperfundingsource'])
            r.course_factor = float_cell(row, ['papercoursefactor'])
            r.cost_category_code = string_cell(row, ['papercostcategorycode'])
            r.cost_category = string_cell(row, ['papercostcategory'])
            r.funding_class_code = string_cell(row, ['paperfundingclasscode'])
            r.funding_class = string_cell(row, ['paperfundingclass'])
            r.individual_efts = int_cell(row, ['paperindividualefts'])
            r.nzsced_code = string_cell(row, ['nzscedcode'])
            r.nzsced_category = string_cell(row, ['nzscedcategory'])
            r.delivering_school_code = string_cell(row, ['paperdeliveringschoolcode'])
            r.delivering_school = string_cell(row, ['paperdeliveringschool'])
            r.delivering_dept_code = string_cell(row, ['paperdeliveringdeptcode'])
            r.delivering_dept = string_cell(row, ['paperdeliveringdept'])
            r.delivering_unit_code = string_cell(row, ['paperdeliveringunitcode'])
            r.delivering_unit = string_cell(row, ['paperdeliveringunit'])
            r.owning_school_code = string_cell(row, ['paperowningschoolcode'])
            r.owning_school = string_cell(row, ['paperowningschool'])
            r.owning_dept_code = string_cell(row, ['paperowningdepartmentcode'])
            r.owning_dept = string_cell(row, ['paperowningdepartment'])
            r.owning_unit_code = string_cell(row, ['paperowningunitcode'])
            r.owning_unit = string_cell(row, ['paperowningunit'])
            r.self_paced = bool_cell(row, ['papertitle'])
            r.online = bool_cell(row, ['paperonline'])
            r.active = bool_cell(row, ['paperactive'])
            r.pending = bool_cell(row, ['paperpending'])
            r.sub_status = string_cell(row, ['papersubstatus'])
            r.grade_method_code = string_cell(row, ['grademethodcode'])
            r.pbrf_eligibility = string_cell(row, ['pbrfeligibility'])
            r.coe_policy = string_cell(row, ['coepolicy'])
            r.report_academic_result = bool_cell(row, ['reportacademicresult'])
            r.internet_based = string_cell(row, ['paperinternetbased'])
            r.save()
            # progress
            if (count % 1000) == 0:
                update_tablestatus(CourseDefs._meta.db_table, "Imported " + str(count) + " rows...")

        # close file
        csvfile.close()
    except Exception as ex:
        msg = traceback.format_exc()
        logger.error(msg=msg)
        return msg
    finally:
        if delete:
            try:
                os.remove(csv)
            except Exception as ex:
                msg = traceback.format_exc()
                logger.error(msg=msg)
                result = msg

    if email is not None:
        send_email(email, 'Import: course definitions', 'Import succeeded' if (result is None) else 'Import failed: ' + result)

    return result


def import_bulk(csv, email=None):
    """
    Performs a bulk import. The CSV file has to have the following layout
    (headers must match!):

    type,year,file,isgzip,encoding
    graderesults,2007,/some/where/2007.csv.gz,True,iso-8859-1
    graderesults,2006,/some/where/2006.csv,False,iso-8859-1
    scholarships,,/some/where/scholarships.csv,False,iso-8859-1
    supervisors,,/some/where/supervisors.csv,False,iso-8859-1
    ...

    :param csv: the CSV file with the files to bulk import
    :type csv: str
    :param email: the (optional) email address to send a notification to
    :type email: str
    :return: None if successful, otherwise error message
    :rtype: str
    """
    result = []
    set_maintenance_mode(True)
    try:
        csvfile = open(csv)
        reader = DictReader(csvfile)
        for row in reader:
            if len(row) != 5:
                continue
            try:
                logger.debug("Importing: " + str(row))
                if row['type'] == 'graderesults':
                    msg = import_grade_results(int(row['year']), row['file'], (row['isgzip'] == 'True'), row['encoding'], delete=False)
                    if msg is None:
                        update_tablestatus(GradeResults._meta.db_table)
                    else:
                        result.append(msg)
                elif row['type'] == 'coursdefs':
                    msg = import_grade_results(int(row['year']), row['file'], row['encoding'], delete=False)
                    if msg is None:
                        update_tablestatus(CourseDefs._meta.db_table)
                    else:
                        result.append(msg)
                elif row['type'] == 'supervisors':
                    msg = import_supervisors(row['file'], row['encoding'], delete=False)
                    if msg is None:
                        update_tablestatus(Supervisors._meta.db_table)
                    else:
                        result.append(msg)
                elif row['type'] == 'scholarships':
                    msg = import_scholarships(row['file'], row['encoding'], delete=False)
                    if msg is None:
                        update_tablestatus(Scholarship._meta.db_table)
                    else:
                        result.append(msg)
                elif row['type'] == 'associatedrole':
                    msg = import_associatedrole(row['file'], row['encoding'], delete=False)
                    if msg is None:
                        update_tablestatus(AssociatedRole._meta.db_table)
                    else:
                        result.append(msg)
                else:
                    result.append("Unhandled file type: " + str(row['type']))
            except Exception as ex:
                traceback.print_exc(file=sys.stdout)
                result.append(str(ex))
    except Exception as ex:
        traceback.print_exc(file=sys.stdout)
        result.append(str(ex))

    if len(result) == 0:
        logger.info("Populating student dates")
        populate_student_dates()
        update_tablestatus(StudentDates._meta.db_table)
        result_msg = None
    else:
        result_msg = '\n'.join(result)

    if email is not None:
        send_email(email, 'Import: bulk', 'Import succeeded' if (result_msg is None) else 'Import failed: ' + result_msg)

    return result_msg


def queue_populate_student_dates(email=None):
    """
    Queues the population of the student dates.

    :param email: the (optional) email address to send a notification to
    :type email: str
    """

    update_tablestatus(StudentDates._meta.db_table, "Processing...")
    populate_student_dates(email=email)
    update_tablestatus(StudentDates._meta.db_table)


def populate_student_dates(email=None):
    """
    Populates the studentdates table. Truncates the table first.

    :param email: the (optional) email address to send a notification to
    :type email: str
    :return: None if successful, otherwise error message
    :rtype: str
    """

    set_maintenance_mode(True)

    # delete old rows
    StudentDates.objects.all().delete()

    # get all students that are supervised
    table_super = Supervisors._meta.db_table
    cursor = connection.cursor()
    cursor.execute("""
        SELECT DISTINCT(student_id)
        FROM %s
        """ % table_super)

    table = GradeResults._meta.db_table
    cursor2 = connection.cursor()
    count = 0
    for row in cursor.fetchall():
        sid = str(row[0]).strip()
        count += 1
        logger.debug(str(count) + "/studentid: " + sid)

        master_months = None
        master_start = None
        master_end = None
        master_school = ''
        master_dept = ''
        master_fulltime = None
        master_status = None
        phd_months = None
        phd_start = None
        phd_end = None
        phd_school = ''
        phd_dept = ''
        phd_fulltime = None
        phd_status = None
        try:
            # master - months
            sql = """
                select sum(credits / cast(regexp_replace(paper_occurrence, '([A-Z]+)59([3456789])-(.*)', '\\2') as integer) / 30 * 12), count(*)
                from %s
                where student_id = '%s'
                and programme_type_code = 'MD'
                and paper_occurrence ~ '([A-Z]+)59([3456789])-(.*)'
                group by student_id
                """ % (table, sid)
            cursor2.execute(sql)
            for row2 in cursor2.fetchall():
                master_months = row2[0]
                break

            # master - start date
            sql = """
                select min(occurrence_startdate), owning_school_clevel, owning_department_clevel
                from %s
                where student_id = '%s'
                and programme_type_code = 'MD'
                and paper_occurrence ~ '([A-Z]+)59([3456789])-(.*)'
                group by student_id, owning_school_clevel, owning_department_clevel
                """ % (table, sid)
            cursor2.execute(sql)
            for row2 in cursor2.fetchall():
                master_start = row2[0]
                master_school = row2[1]
                master_dept = row2[2]
                break

            # master - end date
            sql = """
                select max(occurrence_enddate)
                from %s
                where student_id = '%s'
                and programme_type_code = 'MD'
                and paper_occurrence ~ '([A-Z]+)59([3456789])-(.*)'
                and final_grade is not null
                group by student_id
                """ % (table, sid)
            cursor2.execute(sql)
            for row2 in cursor2.fetchall():
                master_end = row2[0]
                break

            # master - full time
            sql = """
                select avg(credits) >= %d
                from %s
                where student_id = '%s'
                and programme_type_code = 'MD'
                """ % (FULL_TIME_CREDITS, table, sid)
            cursor2.execute(sql)
            for row2 in cursor2.fetchall():
                master_fulltime = row2[0]
                break

            # master - status
            sql = """
                select student_id, name, year, final_grade_status, final_grade
                from %s
                where student_id = '%s'
                and programme_type_code = 'MD'
                and paper_occurrence ~ '([A-Z]+)59([3456789])-(.*)'
                order by year desc
                """ % (table, sid)
            cursor2.execute(sql)
            for row2 in cursor2.fetchall():
                master_status = row2[3]
                if master_status == "":
                    master_status = None
                if master_status == "C":
                    master_status = "finished"
                if master_status == "N":
                    master_status = "current"
                if row2[4] == "WD":
                    master_status = "withdrawn"
                break

            # PhD - months
            sql = """
                select sum(coalesce(student_credit_points, credits_per_student) / credits) * 12, count(*)
                from %s
                where student_id = '%s'
                and programme_type_code = 'DP'
                group by student_id
                """ % (table, sid)
            cursor2.execute(sql)
            for row2 in cursor2.fetchall():
                phd_months = row2[0]
                break

            # PhD - start date (1)
            sql = """
                select min(occurrence_startdate), owning_school_clevel, owning_department_clevel
                from %s
                where student_id = '%s'
                and programme_type_code = 'DP'
                group by student_id, owning_school_clevel, owning_department_clevel
                """ % (table, sid)
            cursor2.execute(sql)
            for row2 in cursor2.fetchall():
                phd_start = row2[0]
                phd_school = row2[1]
                phd_dept = row2[2]
                break

            # PhD - start date (2)
            sql = """
                select proposed_enrolment_date
                from %s
                where student_id = '%s'
                and active = 'true'
                and program = 'DP'
                """ % (table_super, sid)
            cursor2.execute(sql)
            for row2 in cursor2.fetchall():
                if (phd_start is None) or (row2[0] > phd_start):
                    phd_start = row2[0]
                break

            # PhD - end date (1)
            sql = """
                select completion_date
                from %s
                where student_id = '%s'
                and active = 'true'
                and program = 'DP'
                and completion_date > '1900-01-01'
                """ % (table_super, sid)
            cursor2.execute(sql)
            for row2 in cursor2.fetchall():
                phd_end = row2[0]
                break

            # PhD - end date (2)
            if phd_end is None:
                sql = """
                    select occurrence_enddate
                    from %s
                    where student_id = '%s'
                    and programme_type_code = 'DP'
                    order by occurrence_enddate desc
                    """ % (table, sid)
                cursor2.execute(sql)
                for row2 in cursor2.fetchall():
                    phd_end = row2[0]
                    break

            # PhD - full time
            sql = """
                select avg(credits_per_student) >= %d
                from %s
                where student_id = '%s'
                and programme_type_code = 'DP'
                """ % (FULL_TIME_CREDITS, table, sid)
            cursor2.execute(sql)
            for row2 in cursor2.fetchall():
                phd_fulltime = row2[0]
                break

            # PhD - status
            phd_status = "current"
            sql = """
                select student_id, name, year, final_grade_status, final_grade
                from %s
                where student_id = '%s'
                and programme_type_code = 'DP'
                and final_grade != '...'
                and final_grade != ''
                order by year desc
                """ % (table, sid)
            cursor2.execute(sql)
            for row2 in cursor2.fetchall():
                phd_status = row2[3]
                if phd_status == "":
                    phd_status = None
                if phd_status == "C":
                    phd_status = "finished"
                if phd_status == "N":
                    phd_status = "current"
                if row2[4] == "WD":
                    phd_status = "withdrawn"
                break

            # save
            if phd_start is not None:
                r = StudentDates()
                r.student_id = sid
                r.program = "DP"
                r.start_date = phd_start
                r.end_date = phd_end if phd_end is not None else '9999-12-31'
                r.months = phd_months
                r.school = phd_school
                r.department = phd_dept
                r.full_time = phd_fulltime
                r.status = phd_status
                r.save()
            if master_start is not None:
                r = StudentDates()
                r.student_id = sid
                r.program = "MD"
                r.start_date = master_start
                r.end_date = master_end if master_end is not None else '9999-12-31'
                r.months = master_months
                r.school = master_school
                r.department = master_dept
                r.full_time = master_fulltime
                r.status = master_status
                r.save()

        except Exception as ex:
            msg = "PhD: id=%s, start=%s, end=%s, months=%s" % (sid, phd_start, phd_end, phd_months)
            msg += "\n" + "Master: id=%s, start=%s, end=%s, months=%s" % (sid, master_start, master_end, master_months)
            logger.exception(msg=msg)

        # progress
        if (count % 1000) == 0:
            update_tablestatus(StudentDates._meta.db_table, "Processed " + str(count) + " students...")

    set_maintenance_mode(False)

    if email is not None:
        send_email(email, 'Student dates', 'Finished calculating dates')

    return None


def parse_supervisors_date(name, value):
    """
    Parses the various date formats of the supervisors.
    :param name:
    :param value:
    :return:
    """
    if (value == "") or (value == "*invalid*") or (value is None):
        return "0001-01-01"
    if name == "date_agreed":
        dformat = "%d/%m/%Y"
    else:
        dformat = "%d %b %Y"
    try:
        d = datetime.strptime(value, dformat)
        return d.strftime("%Y-%m-%d")
    except Exception as ex:
        logger.exception(msg="name=" + name + ", value=" + value + ", format=" + dformat)
        return None


def parse_associatedrole_date(name, value):
    """
    Parses the various date formats of the associated role.
    :param name:
    :param value:
    :return:
    """
    if (value == "") or (value == "*invalid*") or (value is None):
        return "0001-01-01"
    dformat = "%d/%m/%Y"
    try:
        d = datetime.strptime(value, dformat)
        return d.strftime("%Y-%m-%d")
    except Exception as ex:
        logger.exception(msg="name=" + name + ", value=" + value + ", format=" + dformat)
        return None


def award_to_program(award):
    """
    Turns the award (eg PHD) into the program (ie DP).

    :param award: the award to convert
    :type award: str
    :return: the program
    :rtype: str
    """

    if award in ["PHD", 'DMA', 'EDD', "SJD"]:
        return "DP"
    elif award in ["MPHIL"]:
        return "MD"
    # other types: IPC, ...
    else:
        return "Other"


def queue_import_supervisors(csv, encoding, email=None):
    """
    Queues the import of supervisors.

    :param csv: the CSV file to import
    :type csv: str
    :param encoding: the file encoding (eg utf-8)
    :type encoding: str
    :param email: the (optional) email address to send a notification to
    :type email: str
    """

    update_tablestatus(Supervisors._meta.db_table, "Importing...")
    msg = import_supervisors(csv, encoding, email=email)
    update_tablestatus(Supervisors._meta.db_table, msg=msg)


def import_supervisors(csv, encoding, email=None, delete=True):
    """
    Imports the supervisors (Jade Export).

    :param csv: the CSV file to import
    :type csv: str
    :param encoding: the file encoding (eg utf-8)
    :type encoding: str
    :param email: the (optional) email address to send a notification to
    :type email: str
    :param delete: whether to delete the data file
    :type delete: bool
    :return: None if successful, otherwise error message
    :rtype: str
    """

    result = None

    set_maintenance_mode(True)

    # empty table
    Supervisors.objects.all().delete()
    # import
    p1 = re.compile('.*\/')
    p2 = re.compile(' .*')
    try:
        with open(csv, encoding=encoding) as csvfile:
            reader = DictReader(csvfile)
            reader.fieldnames = [name.lower().replace(" ", "_") for name in reader.fieldnames]
            count = 0
            for row in reader:
                count += 1
                truncate_strings(row, 250)
                encode_strings(row, 'utf-8')
                r = Supervisors()
                r.student_id = row['student'][row['student'].rfind(' ')+1:]  # extract ID at end of string
                r.student = row['student']
                r.supervisor = row['supervisor']
                r.active_roles = row['active_roles']
                r.entity = row['entity']
                r.agreement_status = row['agreement_status']
                r.date_agreed = parse_supervisors_date('date_agreed', row['date_agreed'])
                r.completion_date = parse_supervisors_date('completion_date', row['completion_date'])
                r.proposed_enrolment_date = parse_supervisors_date('proposed_enrolment_date', row['proposed_enrolment_date'])
                r.proposed_research_topic = row['proposed_research_topic']
                # normalize title a bit
                title = row['title']
                title = title.lower()
                title = title.replace(".", "").replace("/", "").replace(" ", "")
                title = title.replace("associate", "a").replace("assoc", "a")
                title = title.replace("professor", "prof").replace("pro", "prof").replace("proff", "prof")
                title = title.replace("doctor", "dr")
                title = title.replace("sir", "")
                r.title = title
                r.quals = row['quals']
                r.comments = row['comments']
                # active if not withdrawn
                r.active = ("removed" not in title) and ("replaced" not in title) and ("informal" not in title)
                # determine program type
                program = p2.sub('', p1.sub('', row['entity'])).upper()
                r.program = award_to_program(program)
                r.save()
                # progress
                if (count % 1000) == 0:
                    update_tablestatus(Supervisors._meta.db_table, "Imported " + str(count) + " rows...")
    except Exception as ex:
        msg = traceback.format_exc()
        logger.error(msg=msg)
        result = msg
    finally:
        if delete:
            try:
                os.remove(csv)
            except Exception as ex:
                msg = traceback.format_exc()
                logger.error(msg=msg)
                result = msg

    if email is not None:
        send_email(email, 'Import: supervisors', 'Import succeeded' if (result is None) else 'Import failed: ' + result)

    return result


def queue_import_scholarships(csv, encoding, email=None):
    """
    Queues the import of scholarships.

    :param csv: the CSV file to import
    :type csv: str
    :param encoding: the file encoding (eg utf-8)
    :type encoding: str
    :param email: the (optional) email address to send a notification to
    :type email: str
    """

    update_tablestatus(Scholarship._meta.db_table, "Importing...")
    msg = import_scholarships(csv, encoding, email=email)
    update_tablestatus(Scholarship._meta.db_table, msg=msg)


def import_scholarships(csv, encoding, email=None, delete=True):
    """
    Imports the scholarships (Jade Export).

    :param csv: the CSV file to import
    :type csv: str
    :param encoding: the file encoding (eg utf-8)
    :type encoding: str
    :param email: the (optional) email address to send a notification to
    :type email: str
    :param delete: whether to delete the data file
    :type delete: bool
    :return: None if successful, otherwise error message
    :rtype: str
    """

    result = None

    set_maintenance_mode(True)

    # empty table
    Scholarship.objects.all().delete()
    # import
    try:
        with open(csv, encoding=encoding) as csvfile:
            reader = DictReader(csvfile)
            reader.fieldnames = [name.lower().replace(" ", "_") for name in reader.fieldnames]
            count = 0
            for row in reader:
                count += 1
                truncate_strings(row, 250)
                encode_strings(row, 'utf-8')
                r = Scholarship()
                r.student_id = row['person_id']
                r.name = row['template']
                r.status = row['status']
                r.decision = row['decision']
                r.year = int(row['year'])
                r.save()
                # progress
                if (count % 1000) == 0:
                    update_tablestatus(Scholarship._meta.db_table, "Imported " + str(count) + " rows...")

    except Exception as ex:
        msg = traceback.format_exc()
        logger.error(msg=msg)
        result = msg
    finally:
        if delete:
            try:
                os.remove(csv)
            except Exception as ex:
                msg = traceback.format_exc()
                logger.error(msg=msg)
                result = msg

    if email is not None:
        send_email(email, 'Import: scholarships', 'Import succeeded' if (result is None) else 'Import failed: ' + result)

    return result


def queue_import_associatedrole(csv, encoding, email=None):
    """
    Queues the import of associate role.

    :param csv: the CSV file to import
    :type csv: str
    :param encoding: the file encoding (eg utf-8)
    :type encoding: str
    :param email: the (optional) email address to send a notification to
    :type email: str
    """

    update_tablestatus(AssociatedRole._meta.db_table, "Importing...")
    msg = import_associatedrole(csv, encoding, email=email)
    update_tablestatus(AssociatedRole._meta.db_table, msg=msg)


def import_associatedrole(csv, encoding, email=None, delete=True):
    """
    Imports the associated role (Jade Export).

    :param csv: the CSV file to import
    :type csv: str
    :param encoding: the file encoding (eg utf-8)
    :type encoding: str
    :param email: the (optional) email address to send a notification to
    :type email: str
    :param delete: whether to delete the data file
    :type delete: bool
    :return: None if successful, otherwise error message
    :rtype: str
    """

    result = None

    set_maintenance_mode(True)

    # empty table
    AssociatedRole.objects.all().delete()
    # import
    try:
        with open(csv, encoding=encoding) as csvfile:
            reader = DictReader(csvfile)
            reader.fieldnames = [name.lower().replace(" ", "_") for name in reader.fieldnames]
            count = 0
            for row in reader:
                count += 1
                truncate_strings(row, 250)
                encode_strings(row, 'utf-8')
                r = AssociatedRole()
                r.role = row['role']
                r.person = row['person']
                r.entity = row['entity']
                r.valid_from = parse_associatedrole_date('valid_from', row['valid_from'])
                r.valid_to = parse_associatedrole_date('valid_to', row['valid_to'])
                r.active = len(row['valid_to'].strip()) == 0
                if " - " in r.entity:
                    r.student_id = r.entity[(r.entity.index(" - ") + 3):]
                if "Award/" in r.entity:
                    r.student = r.entity[r.entity.index("Award/") + 6:]
                    r.program = award_to_program(r.student[0:r.student.index(" ")].upper())
                    r.student = r.student[r.student.index(" ") + 1:]
                r.save()
                # progress
                if (count % 1000) == 0:
                    update_tablestatus(AssociatedRole._meta.db_table, "Imported " + str(count) + " rows...")

    except Exception as ex:
        msg = traceback.format_exc()
        logger.error(msg=msg)
        result = msg
    finally:
        if delete:
            try:
                os.remove(csv)
            except Exception as ex:
                msg = traceback.format_exc()
                logger.error(msg=msg)
                result = msg

    if email is not None:
        send_email(email, 'Import: associated role', 'Import succeeded' if (result is None) else 'Import failed: ' + result)

    return result


def update_tablestatus(table, msg=None, timestamp=None):
    """
    Updates the table status of the specified table.

    :param table: the table to update the status for
    :type table: str
    :param msg: the optional message
    :type msg: str
    :param timestamp: the timestamp of the import (not all imports record the extraction/query date/time)
    :type timestamp: datetime
    """

    if timestamp is None:
        timestamp = datetime.now()

    TableStatus.objects.all().filter(table=table).delete()
    r = TableStatus()
    r.table = table
    r.timestamp = timestamp
    r.message = msg
    r.save()


def get_tablestatus(table):
    """
    Retrieves the table status for the specified table.

    :param table: the table to update the status for
    :type table: str
    :return: the table status message, None if nothing set
    :rtype: str
    """
    result = None
    for t in TableStatus.objects.all().filter(table=table):
        result = t.message
        break
    return result
