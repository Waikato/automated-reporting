from __future__ import unicode_literals

from django.db import models


class StudentDates(models.Model):
    """
    Start/end dates for students.
    """
    student_id = models.CharField(max_length=20, db_index=True)
    program = models.CharField(max_length=4, db_index=True)  # PD/MD
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(db_index=True)
    months = models.FloatField(null=True)
    school = models.CharField(max_length=20, db_index=True, default='')
    department = models.CharField(max_length=20, db_index=True, default='')
    full_time = models.NullBooleanField(default=None, null=True)
    status = models.CharField(max_length=20, null=True)

    class Meta:
        permissions = (
            ("can_access_student_dates", "Can access Student Dates"),
            ("can_manage_student_dates", "Can manage Student Dates"),
        )


class Supervisors(models.Model):
    """
    Supervisor data.
    """
    student_id = models.CharField(max_length=250, db_index=True)
    student = models.CharField(max_length=250)
    supervisor = models.CharField(max_length=250, db_index=True)
    active_roles = models.CharField(max_length=250)
    entity = models.CharField(max_length=250)
    agreement_status = models.CharField(max_length=250)
    date_agreed = models.CharField(max_length=250)
    title = models.CharField(max_length=250)
    quals = models.CharField(max_length=250)
    comments = models.CharField(max_length=250)
    active = models.BooleanField(db_index=True)
    completion_date = models.DateField(null=True, default=None)
    proposed_enrolment_date = models.DateField(null=True, default=None)
    proposed_research_topic = models.CharField(max_length=250, blank=True, default='')
    program = models.CharField(max_length=20, db_index=True, blank=True, default='')

    class Meta:
        permissions = (
            ("can_access_supervisors", "Can access Supervisors"),
            ("can_manage_supervisors", "Can manage Supervisors"),
        )


class Scholarship(models.Model):
    """
    Scholarship data.
    """
    student_id = models.CharField(max_length=250, db_index=True)
    name = models.CharField(max_length=250, db_index=True, default='')
    status = models.CharField(max_length=50, db_index=True, default='')
    decision = models.CharField(max_length=50, db_index=True, default='')
    year = models.IntegerField(null=True, db_index=True)

    class Meta:
        permissions = (
            ("can_access_scholarship", "Can access Scholarship"),
            ("can_manage_scholarship", "Can manage Scholarship"),
        )


class AssociatedRole(models.Model):
    """
    Associated role data.
    """
    role = models.CharField(max_length=250, db_index=True)
    person = models.CharField(max_length=250, db_index=True)
    entity = models.CharField(max_length=250)
    valid_from = models.DateField(null=True, default=None)
    valid_to = models.DateField(null=True, default=None)
    student_id = models.CharField(max_length=250, db_index=True, null=True, default=None)

    class Meta:
        permissions = (
            ("can_access_associatedrole", "Can access Associated Role"),
            ("can_manage_associatedrole", "Can manage Associated Role"),
        )
