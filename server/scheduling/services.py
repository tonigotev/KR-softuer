from datetime import datetime, timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import (
    DoctorProfile,
    PermanentScheduleSlot,
    TemporaryScheduleChange,
    Visit,
    WeeklyScheduleSlot,
)


def _interval_inside_slots(start_dt, end_dt, slots):
    for slot in slots:
        slot_start = datetime.combine(start_dt.date(), slot.start_time, tzinfo=start_dt.tzinfo)
        slot_end = datetime.combine(start_dt.date(), slot.end_time, tzinfo=start_dt.tzinfo)
        if start_dt >= slot_start and end_dt <= slot_end:
            return True
    return False


def validate_day_slots_do_not_overlap(slots):
    grouped = {}
    for slot in slots:
        weekday = slot["weekday"]
        grouped.setdefault(weekday, []).append(slot)

    for day_slots in grouped.values():
        ordered = sorted(day_slots, key=lambda s: s["start_time"])
        for idx in range(1, len(ordered)):
            previous = ordered[idx - 1]
            current = ordered[idx]
            if current["start_time"] < previous["end_time"]:
                raise ValidationError("Schedule slots on the same weekday must not overlap.")


def get_effective_slots(doctor, start_dt):
    temporary_change = (
        TemporaryScheduleChange.objects.filter(
            doctor=doctor, start_datetime__lte=start_dt, end_datetime__gte=start_dt
        )
        .order_by("-start_datetime")
        .first()
    )
    weekday = start_dt.weekday()
    if temporary_change:
        return temporary_change.slots.filter(weekday=weekday).order_by("start_time")

    permanent_change = (
        doctor.permanent_changes.filter(effective_from__lte=start_dt.date())
        .order_by("-effective_from")
        .first()
    )
    if permanent_change:
        return PermanentScheduleSlot.objects.filter(
            change=permanent_change, weekday=weekday
        ).order_by("start_time")

    return WeeklyScheduleSlot.objects.filter(doctor=doctor, weekday=weekday).order_by("start_time")


def validate_visit_creation(patient, doctor, starts_at, ends_at):
    if patient.primary_doctor_id != doctor.id:
        raise ValidationError("Patient can create visits only with their personal doctor.")

    if starts_at.date() != ends_at.date():
        raise ValidationError("Visits must start and end on the same day.")

    if starts_at <= timezone.now() + timedelta(hours=24):
        raise ValidationError("Visit must be created at least 24 hours in advance.")

    slots = get_effective_slots(doctor, starts_at)
    if not _interval_inside_slots(starts_at, ends_at, slots):
        raise ValidationError("Visit must be inside doctor's working hours.")

    overlapping = Visit.objects.filter(
        doctor=doctor,
        status=Visit.STATUS_SCHEDULED,
        starts_at__lt=ends_at,
        ends_at__gt=starts_at,
    )
    if overlapping.exists():
        raise ValidationError("Visit overlaps with another scheduled visit.")


@transaction.atomic
def create_visit(patient, doctor, starts_at, ends_at):
    # Lock doctor row to serialize booking checks per doctor.
    DoctorProfile.objects.select_for_update().get(pk=doctor.pk)
    validate_visit_creation(patient, doctor, starts_at, ends_at)
    return Visit.objects.create(
        doctor=doctor,
        patient=patient,
        starts_at=starts_at,
        ends_at=ends_at,
    )


def cancel_visit(visit, actor):
    if visit.status == Visit.STATUS_CANCELLED:
        raise ValidationError("Visit is already cancelled.")
    if actor.id not in {visit.patient.user_id, visit.doctor.user_id}:
        raise ValidationError("Only the patient or doctor can cancel this visit.")
    if timezone.now() > visit.starts_at - timedelta(hours=12):
        raise ValidationError("Cancellation is allowed at least 12 hours before start.")

    visit.status = Visit.STATUS_CANCELLED
    visit.cancelled_at = timezone.now()
    visit.cancelled_by = actor
    visit.save(update_fields=["status", "cancelled_at", "cancelled_by"])
    return visit
