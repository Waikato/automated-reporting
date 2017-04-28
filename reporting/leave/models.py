from __future__ import unicode_literals

from django.db import models

class Leave(models.Model):
    """
    Fake model to get permissions.
    """

    class Meta:
        permissions = (
            ("can_use_leave", "Can use Leave"),
            ("can_update_leave", "Can update Leave"),
        )
