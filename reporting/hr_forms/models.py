from django.db import models


class FormTemplate(models.Model):
    """
    Class for defining a PDF form with its overlay.
    """

    name = models.CharField(max_length=250, db_index=True)
    description = models.TextField()
    version = models.CharField(max_length=50, db_index=True)
    pdf = models.BinaryField()
    overlay = models.TextField()

    class Meta:
        permissions = (
            ("can_access_formtemplate", "Can access Form Template"),
            ("can_manage_formtemplate", "Can manage Form Template"),
        )
