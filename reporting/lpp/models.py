from __future__ import unicode_literals

from django.db import models

class LowPerformingPassRates(models.Model):
    """
    Fake model to get permissions.
    """

    class Meta:
        managed = False
        permissions = (
            ("can_use_lpp", "Can use LPP"),
            ("can_update_lpp", "Can update LPP"),
        )
