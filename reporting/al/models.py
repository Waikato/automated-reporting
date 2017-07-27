from __future__ import unicode_literals

from django.db import models


class AdultLearners(models.Model):
    """
    Fake model to get permissions.
    """

    class Meta:
        managed = False
        permissions = (
            ("can_access_al", "Can access Adult Learners"),
            ("can_manage_al", "Can manage Adult Learners"),
        )
