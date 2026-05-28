from hermes_youtube_curator.cli.morning_run import run_morning_run
from hermes_youtube_curator.delivery.telegram import TelegramDeliveryService


def test_delivery_records_success(app_context):
    payload = run_morning_run(app_context)
    assert payload["digest_id"] is not None
    assert app_context.sqlite.count_rows("deliveries") == 1


def test_delivery_records_failure(app_context):
    app_context.delivery = TelegramDeliveryService(
        app_context.settings.telegram_outbox,
        fail_delivery=True,
    )
    payload = run_morning_run(app_context)
    assert payload["run_status"] == "partial"
    assert app_context.sqlite.count_rows("deliveries") == 1
