from datetime import datetime, timedelta, timezone

from src.appointment_notifications import AppointmentRequest, decide_notification


def test_urgent_reminder_is_sent_within_one_day():
    now = datetime(2026, 8, 21, 8, tzinfo=timezone.utc)
    appointment = AppointmentRequest("PT-1", "Dr. Lee", now + timedelta(hours=12), "UTC")

    result = decide_notification(appointment, now)

    assert result.level == "urgent"
    assert result.send is True


def test_distant_appointment_stays_scheduled():
    now = datetime(2026, 8, 21, 8, tzinfo=timezone.utc)
    appointment = AppointmentRequest("PT-2", "Dr. Lee", now + timedelta(days=5), "UTC")

    result = decide_notification(appointment, now)

    assert result.level == "scheduled"
    assert result.send is False
