from __future__ import unicode_literals

from django.db import models

class StudentDates(models.Model):
    """
    Start/end dates for students.
    """
    student_id = models.CharField(max_length=20, db_index=True)
    program = models.CharField(max_length=4, db_index=True)
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(db_index=True)
    months = models.FloatField(null=True)
    programme_code_type = models.CharField(max_length=10, db_index=True, null=True)  # MD=master, PD=PhD

class Supervisors(models.Model):
    """
    Grade results.
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
