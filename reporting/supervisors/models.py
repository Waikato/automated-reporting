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
