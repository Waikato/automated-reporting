from __future__ import unicode_literals

from django.db import models


class HyperlinkGrades(models.Model):
    """
    Fake model to get permissions.
    """

    class Meta:
        managed = False
        permissions = (
            ("can_access_hyperlinkgrades", "Can access Hyperlink Grades"),
            ("can_manage_hyperlinkgrades", "Can manage Hyperlink Grades"),
        )
