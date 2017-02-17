from reporting.models import GradeResults
from supervisors.models import Supervisors, StudentDates
from reporting.db import truncate_strings
from csv import DictReader
import gzip
import traceback
import sys
from datetime import datetime

def parse_grade_results_date(name, value):
    """
    Parses the various date formats of the grade results.
    :param name:
    :param value:
    :return:
    """
    if value == "":
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
            r.student_id = row['student_id']
            r.name = row['name']
            r.title = row['title']
            r.prefered_given_name = row['prefered_given_name']
            r.given_name = row['given_name']
            r.other_given_names = row['other_given_names']
            r.family_name = row['family_name']
            r.previous_name = row['previous_name']
            r.address1 = row['address1']
            r.address2 = row['address2']
            r.address2a = row['address2a']
            r.address2b = row['address2b']
            r.address3 = row['address3']
            r.address4 = row['address4']
            r.postcode = row['postcode']
            r.telephone = row['telephone']
            r.cellphone = row['cellphone']
            r.email = row['email']
            r.hasdisability = None if (row['hasdisability'] == '') else int(row['hasdisability'])
            r.isdomestic = None if (row['isdomestic'] == '') else int(row['isdomestic'])
            r.is_domiciled_locally = None if (row['is_domiciled_locally'] == '') else int(row['is_domiciled_locally'])
            r.citizenship = row['citizenship']
            r.residency_status = row['residency_status']
            r.origin = row['origin']
            r.gender = row['gender']
            r.ethnicity = row['ethnicity']
            r.ethnic_group = row['ethnic_group']
            r.all_ethnicities_string = row['all_ethnicities_string']
            r.all_iwi_string = row['all_iwi_string']
            r.dateofbirth = parse_grade_results_date('dateofbirth', row['dateofbirth'])
            r.dateofdeath = row['dateofdeath']
            r.waikato_1st = None if (row['waikato_1st'] == '') else int(row['waikato_1st'])
            r.nz_1st = None if (row['nz_1st'] == '') else int(row['nz_1st'])
            r.last_year_sec = None if (row['last_year_sec'] == '') else int(row['last_year_sec'])
            r.sec_qual_year = None if (row['sec_qual_year'] == '') else int(row['sec_qual_year'])
            r.last_sec_school = row['last_sec_school']
            r.last_sec_school_region = row['last_sec_school_region']
            r.highest_sec_qual = row['highest_sec_qual']
            r.main_activity = row['main_activity']
            r.award_title = row['award_title']
            r.prog_abbr = row['prog_abbr']
            r.programme = row['programme']
            r.programme_type_code = row['programme_type_code']
            r.programme_type = row['programme_type']
            r.ishigherdegree = None if (row['ishigherdegree'] == '') else int(row['ishigherdegree'])
            r.school_of_study = row['school_of_study']
            r.school_of_study_clevel = row['school_of_study_clevel']
            r.paper_master_code = row['paper_master_code']
            r.paper_occurrence = row['paper_occurrence']
            r.paper_title = row['paper_title']
            r.occurrence_startdate = parse_grade_results_date('occurrence_startdate', row['occurrence_startdate'])
            r.occurrence_startyear = None if (row['occurrence_startyear'] == '') else int(row['occurrence_startyear'])
            r.occurrence_startweek = None if (row['occurrence_startweek'] == '') else int(row['occurrence_startweek'])
            r.occurrence_enddate = parse_grade_results_date('occurrence_enddate', row['occurrence_enddate'])
            r.stage = None if (row['stage'] == '') else int(row['stage'])
            r.credits = None if (row['credits'] == '') else float(row['credits'])
            r.student_credit_points = None if (row['student_credit_points'] == '') else float(row['student_credit_points'])
            r.iscancelled = None if (row['iscancelled'] == '') else int(row['iscancelled'])
            r.isoncampus = None if (row['isoncampus'] == '') else int(row['isoncampus'])
            r.issemesteracourse = None if (row['issemesteracourse'] == '') else int(row['issemesteracourse'])
            r.issemesterbcourse = None if (row['issemesterbcourse'] == '') else int(row['issemesterbcourse'])
            r.iswholeyearcourse = None if (row['iswholeyearcourse'] == '') else int(row['iswholeyearcourse'])
            r.location_code = row['location_code']
            r.location = row['location']
            r.owning_school_clevel = row['owning_school_clevel']
            r.owning_school = row['owning_school']
            r.owning_department_clevel = row['owning_department_clevel']
            r.owning_department = row['owning_department']
            r.owning_level4_clevel = row['owning_level4_clevel']
            r.owning_level4_department = row['owning_level4_department']
            r.owning_level4or3_department = row['owning_level4or3_department']
            r.owning_level4or3_clevel = row['owning_level4or3_clevel']
            r.delivery_mode_code = row['delivery_mode_code']
            r.delivery_mode = row['delivery_mode']
            r.semester_code = row['semester_code']
            r.semester_description = row['semester_description']
            r.isselfpaced = None if (row['isselfpaced'] == '') else int(row['isselfpaced'])
            r.source_of_funding = row['source_of_funding']
            r.funding_category_code = row['funding_category_code']
            r.funding_category = row['funding_category']
            r.cost_category_code = row['cost_category_code']
            r.cost_category = row['cost_category']
            r.research_supplement_code = None if (row['research_supplement_code'] == '') else int(row['research_supplement_code'])
            r.research_supplement = row['research_supplement']
            r.classification_code = None if (row['classification_code'] == '') else float(row['classification_code'])
            r.classification = row['classification']
            r.division = row['division']
            r.division_code = row['division_code']
            r.specified_programme = row['specified_programme']
            r.major = row['major']
            r.second_major = row['second_major']
            r.major2 = row['major2']
            r.second_major2 = row['second_major2']
            r.main_subject = row['main_subject']
            r.second_subject = row['second_subject']
            r.supporting_subject = row['supporting_subject']
            r.teaching_1 = row['teaching_1']
            r.teaching_2 = row['teaching_2']
            r.teaching_3 = row['teaching_3']
            r.teaching_4 = row['teaching_4']
            r.subject = row['subject']
            r.field = row['field']
            r.specialisation = row['specialisation']
            r.stream = row['stream']
            r.endorsement = row['endorsement']
            r.award_year = None if (row['award_year'] == '') else int(row['award_year'])
            r.award_completion_status = row['award_completion_status']
            r.award_completion_date = parse_grade_results_date('award_completion_date', row['award_completion_date'])
            r.award_completion_confirmed_date = parse_grade_results_date('award_completion_confirmed_date', row['award_completion_confirmed_date'])
            r.admission_year = None if (row['admission_year'] == '') else int(row['admission_year'])
            r.admission_reason = row['admission_reason']
            r.admission_criteria = row['admission_criteria']
            r.admission_status = row['admission_status']
            r.grade = row['grade']
            r.grade_status = row['grade_status']
            r.result_status_code = row['result_status_code']
            r.result_status = row['result_status']
            r.grade_ranking = None if (row['grade_ranking'] == '') else int(row['grade_ranking'])
            r.mark = None if (row['mark'] == '') else float(row['mark'])
            r.moe_completion_code = None if (row['moe_completion_code'] == '') else int(row['moe_completion_code'])
            r.iscontinuinggrade = None if (row['iscontinuinggrade'] == '') else int(row['iscontinuinggrade'])
            r.ispassgrade = None if (row['ispassgrade'] == '') else int(row['ispassgrade'])
            r.query_date = parse_grade_results_date('query_date', row['query_date'])
            r.enr_year = None if (row['enr_year'] == '') else int(row['enr_year'])
            r.enrolment_status = row['enrolment_status']
            r.final_grade = row['final_grade']
            r.final_grade_ranking = None if (row['final_grade_ranking'] == '') else int(row['final_grade_ranking'])
            r.final_grade_status = row['final_grade_status']
            r.final_grade_result_status = row['final_grade_result_status']
            r.papers_per_student = None if (row['papers_per_student'] == '') else int(row['papers_per_student'])
            r.credits_per_student = None if (row['credits_per_student'] == '') else float(row['credits_per_student'])
            r.gpa = None if (row['gpa'] == '') else float(row['gpa'])
            r.ones = None if (row['ones'] == '') else int(row['ones'])
            r.allgradeones = None if (row['allgradeones'] == '') else int(row['allgradeones'])
            r.passgradeones = None if (row['passgradeones'] == '') else int(row['passgradeones'])
            r.retentionones = None if (row['retentionones'] == '') else int(row['retentionones'])
            r.award_completion_year = None if (row['award_completion_year'] == '') else int(row['award_completion_year'])
            r.personoid = None if (row['personoid'] == '') else float(row['personoid'])
            r.courseoccurrenceoid = None if (row['courseoccurrenceoid'] == '') else float(row['courseoccurrenceoid'])
            r.awardenrolmentoid = None if (row['awardenrolmentoid'] == '') else float(row['awardenrolmentoid'])
            r.enrolmentorcosuoid = None if (row['enrolmentorcosuoid'] == '') else float(row['enrolmentorcosuoid'])
            r.isformalprogramme = None if (row['isformalprogramme'] == '') else int(row['isformalprogramme'])
            r.citizenship_simple = row['citizenship_simple']
            r.moe_pbrf_code = row['moe_pbrf_code']
            r.moe_pbrf = row['moe_pbrf']
            r.achievement_date = parse_grade_results_date('achievement_date', row['achievement_date'])
            r.te_reo = None if (row['te_reo'] == '') else int(row['te_reo'])
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
    # TODO
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
