from __future__ import unicode_literals

from django.db import models

class StudentDates(models.Model):
    """
    Start/end dates for students.
    """
    student_id = models.CharField(max_length=20)
    program = models.CharField(max_length=4)
    start_date = models.DateField()
    end_date = models.DateField()
