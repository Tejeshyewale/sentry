from __future__ import annotations

from django.db import models

from sentry.backup.scopes import RelocationScope
from sentry.db.models import Model, region_silo_model
from sentry.db.models.base import sane_repr
from sentry.db.models.fields.hybrid_cloud_foreign_key import HybridCloudForeignKey


@region_silo_model
class DashboardPermissions(Model):
    """
    Edit permissions for a Dashboard.
    """

    __relocation_scope__ = RelocationScope.Organization

    created_by_id = HybridCloudForeignKey("sentry.User", on_delete="CASCADE")
    is_creator_only_editable = models.BooleanField(default=False)

    class Meta:
        app_label = "sentry"
        db_table = "sentry_dashboardpermissions"

    __repr__ = sane_repr("created_by_id", "is_creator_only_editable")
