from __future__ import unicode_literals

from django.db import models

class Leave(models.Model):
    """
    Fake model to get permissions.
    """

    class Meta:
        managed = False
        permissions = (
            ("can_access_leave", "Can access Leave"),
            ("can_manage_leave", "Can manage Leave"),
        )
