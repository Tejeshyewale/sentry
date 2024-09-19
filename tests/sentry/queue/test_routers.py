import itertools
from collections.abc import Mapping, Sequence

import pytest
from django.conf import settings
from django.test import override_settings

from sentry import options
from sentry.queue.routers import SplitQueueRouter, SplitQueueTaskRouter
from sentry.testutils.pytest.fixtures import django_db_all
from sentry.utils.celery import make_split_queues, make_split_task_queues


@django_db_all
def test_split_router_legacy() -> None:
    queues = [
        "post_process_transactions_1",
        "post_process_transactions_2",
        "post_process_transactions_3",
    ]
    queues_gen = itertools.cycle(queues)
    with override_settings(
        SENTRY_POST_PROCESS_QUEUE_SPLIT_ROUTER={
            "post_process_transactions": lambda: next(queues_gen),
        },
        CELERY_SPLIT_QUEUE_ROUTES={},
    ):
        router = SplitQueueRouter()
        assert router.route_for_queue("save_event") == "save_event"
        assert router.route_for_queue("post_process_transactions") == "post_process_transactions_1"
        assert router.route_for_queue("post_process_transactions") == "post_process_transactions_2"
        assert router.route_for_queue("post_process_transactions") == "post_process_transactions_3"

        legacy_mode = options.get("celery_split_queue_legacy_mode")
        options.set("celery_split_queue_legacy_mode", [])
        try:
            # Disabled legacy mode. As the split queue config is not there
            # split queue does not happen/
            router = SplitQueueRouter()
            assert (
                router.route_for_queue("post_process_transactions") == "post_process_transactions"
            )
        finally:
            options.set("celery_split_queue_legacy_mode", legacy_mode)


@django_db_all
def test_router_not_rolled_out() -> None:
    with override_settings(
        SENTRY_POST_PROCESS_QUEUE_SPLIT_ROUTER={},
    ):
        rollout = options.get("celery_split_queue_rollout")
        options.set(
            "celery_split_queue_rollout",
            {
                "post_process_transactions": 0.0,
            },
        )

        try:
            router = SplitQueueRouter()
            assert (
                router.route_for_queue("post_process_transactions") == "post_process_transactions"
            )
        finally:
            options.set("celery_split_queue_rollout", rollout)


CELERY_SPLIT_QUEUE_ROUTES = {
    "post_process_transactions": {"total": 5, "in_use": 3},
    "post_process_errors": {"total": 5, "in_use": 1},
}


@django_db_all
def test_router_rolled_out() -> None:
    with override_settings(
        SENTRY_POST_PROCESS_QUEUE_SPLIT_ROUTER={},
        CELERY_SPLIT_QUEUE_ROUTES=CELERY_SPLIT_QUEUE_ROUTES,
        CELERY_QUEUES=[
            *settings.CELERY_QUEUES,
            *make_split_queues(CELERY_SPLIT_QUEUE_ROUTES),
        ],
    ):

        legacy_rollout = options.get("celery_split_queue_legacy_mode")
        rollout = options.get("celery_split_queue_rollout")
        options.set("celery_split_queue_legacy_mode", [])
        options.set(
            "celery_split_queue_rollout",
            {"post_process_transactions": 1.0, "post_process_errors": 1.0},
        )
        try:
            router = SplitQueueRouter()
            assert (
                router.route_for_queue("post_process_transactions") == "post_process_transactions_1"
            )
            assert (
                router.route_for_queue("post_process_transactions") == "post_process_transactions_2"
            )
            assert (
                router.route_for_queue("post_process_transactions") == "post_process_transactions_3"
            )
            assert (
                router.route_for_queue("post_process_transactions") == "post_process_transactions_1"
            )
            assert router.route_for_queue("post_process_errors") == "post_process_errors_1"
            assert (
                router.route_for_queue("post_process_issue_platform")
                == "post_process_issue_platform"
            )
        finally:
            options.set("celery_split_queue_legacy_mode", legacy_rollout)
            options.set("celery_split_queue_rollout", rollout)


CELERY_SPLIT_QUEUE_TASK_ROUTES = {
    "sentry.tasks.store.save_event_transaction": {
        "default_queue": "events.save_event_transaction",
        "queues_config": {
            "total": 5,
            "in_use": 2,
        },
    }
}


@pytest.mark.parametrize(
    "rollout_option, task_test, expected",
    [
        pytest.param(
            {"sentry.tasks.store.save_event": 1.0},
            "sentry.tasks.store.save_event_transaction",
            [
                {"queue": "events.save_event_transaction"},
                {"queue": "events.save_event_transaction"},
                {"queue": "events.save_event_transaction"},
            ],
            id="Config present, not rolled out",
        ),
        pytest.param(
            {"sentry.tasks.store.save_event": 1.0},
            "sentry.tasks.store.save_event",
            [None, None, None],
            id="No config, rollout option on",
        ),
        pytest.param(
            {"sentry.tasks.store.save_event": 1.0},
            "sentry.tasks.store.save_something_else",
            [None, None, None],
            id="No config, No rollout",
        ),
        pytest.param(
            {"sentry.tasks.store.save_event_transaction": 1.0},
            "sentry.tasks.store.save_event_transaction",
            [
                {"queue": "events.save_event_transaction_1"},
                {"queue": "events.save_event_transaction_2"},
                {"queue": "events.save_event_transaction_1"},
            ],
            id="Config present rolled out",
        ),
    ],
)
@django_db_all
def test_task_rollout(
    rollout_option: Mapping[str, float],
    task_test: str,
    expected: Sequence[Mapping[str, str] | None],
) -> None:

    with override_settings(
        CELERY_SPLIT_QUEUE_TASK_ROUTES=CELERY_SPLIT_QUEUE_TASK_ROUTES,
        CELERY_QUEUES=[
            *settings.CELERY_QUEUES,
            *make_split_task_queues(CELERY_SPLIT_QUEUE_TASK_ROUTES),
        ],
    ):
        current_rollout = options.get("celery_split_queue_task_rollout")
        options.set("celery_split_queue_task_rollout", rollout_option)
        try:
            router = SplitQueueTaskRouter()
            assert router.route_for_task(task_test) == expected[0]
            assert router.route_for_task(task_test) == expected[1]
            assert router.route_for_task(task_test) == expected[2]
        finally:
            options.set("celery_split_queue_task_rollout", current_rollout)
