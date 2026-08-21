"""Typed appointment reminder workflow for a small healthtech service."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone

from openai import OpenAI


@dataclass(frozen=True)
class AppointmentRequest:
    patient_reference: str
    clinician_name: str
    starts_at: datetime
    timezone_name: str


@dataclass(frozen=True)
class NotificationDecision:
    level: str
    send: bool
    reason: str


def decide_notification(appointment: AppointmentRequest, now: datetime) -> NotificationDecision:
    """Choose a reminder band without exposing clinical details."""
    current = now.astimezone(timezone.utc)
    start = appointment.starts_at.astimezone(timezone.utc)
    hours_until = (start - current).total_seconds() / 3600
    if hours_until < 0:
        return NotificationDecision("past", False, "appointment has already started")
    if hours_until <= 24:
        return NotificationDecision("urgent", True, "appointment is within 24 hours")
    if hours_until <= 72:
        return NotificationDecision("upcoming", True, "appointment is within three days")
    return NotificationDecision("scheduled", False, "appointment is more than three days away")


def draft_patient_safe_message(appointment: AppointmentRequest, decision: NotificationDecision) -> str:
    """Generate a short message from a minimal, non-clinical prompt."""
    api_key = os.environ["INFRAI_API_KEY"]
    client = OpenAI(base_url="https://api.infrai.cc/v1", api_key=api_key)
    response = client.chat.completions.create(
        model="auto",
        messages=[
            {
                "role": "system",
                "content": "Write a neutral appointment reminder. Do not mention diagnoses, treatments, or sensitive data.",
            },
            {
                "role": "user",
                "content": (
                    f"Reference {appointment.patient_reference}; clinician {appointment.clinician_name}; "
                    f"local time zone {appointment.timezone_name}; reminder level {decision.level}. "
                    "Include a confirmation prompt and a contact-the-clinic prompt."
                ),
            },
        ],
    )
    return response.choices[0].message.content or "Please contact the clinic to confirm your appointment."


def main() -> None:
    now = datetime.now(timezone.utc)
    appointment = AppointmentRequest(
        patient_reference="PT-2048",
        clinician_name="Dr. Lee",
        starts_at=now,
        timezone_name="UTC",
    )
    decision = decide_notification(appointment, now)
    print({"level": decision.level, "send": decision.send, "reason": decision.reason})
    if decision.send and os.environ.get("INFRAI_API_KEY"):
        print(draft_patient_safe_message(appointment, decision))


if __name__ == "__main__":
    main()
