from __future__ import unicode_literals

from django.db import models


class LowPerformingPassRates(models.Model):
    """
    Fake model to get permissions.
    """

    class Meta:
        managed = False
        permissions = (
            ("can_access_lpp", "Can access LPP"),
            ("can_manage_lpp", "Can manage LPP"),
        )
