import itertools
import logging
from datetime import datetime, timezone

from sentry import options
from sentry.flags.providers import FlagAuditLogItem, handle_flag_pole_event_internal
from sentry.runner.commands.presenters.webhookpresenter import WebhookPresenter

logger = logging.getLogger()


class AuditLogPresenter(WebhookPresenter):
    @staticmethod
    def is_webhook_enabled() -> bool:
        return (
            options.get("flags:options-audit-log-is-enabled") is True
            and options.get("flags:options-audit-log-organization-id") is not None
        )

    def flush(self) -> None:
        if not self.is_webhook_enabled():
            logger.warning("Options audit log webhook is disabled.")
            return None

        items = self._create_audit_log_items()
        handle_flag_pole_event_internal(
            items, organization_id=options.get("flags:options-audit-log-organization-id")
        )

    def _create_audit_log_items(self) -> list[FlagAuditLogItem]:
        return [
            {
                "action": action,
                "created_at": datetime.now(tz=timezone.utc).isoformat(),
                "created_by": "internal",
                "flag": flag,
                "tags": tags,
            }
            for flag, action, tags in itertools.chain(
                ((flag, "created", {"value": v}) for flag, v in self.set_options),
                ((flag, "deleted", {}) for flag in self.unset_options),
                ((flag, "updated", {"value": v}) for flag, _, v in self.updated_options),
                ((flag, "updated", {}) for flag, _ in self.drifted_options),
            )
        ]
