from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class DoctorProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="doctor_profile"
    )
    physical_address = models.TextField()

    def clean(self):
        if self.user.role != "doctor":
            raise ValidationError("DoctorProfile user must have doctor role.")

    def __str__(self):
        return self.user.full_name


class PatientProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="patient_profile"
    )
    phone_number = models.CharField(max_length=20)
    primary_doctor = models.ForeignKey(
        DoctorProfile, on_delete=models.PROTECT, related_name="patients"
    )

    def clean(self):
        if self.user.role != "patient":
            raise ValidationError("PatientProfile user must have patient role.")

    def __str__(self):
        return self.user.full_name


class WeeklyScheduleSlot(models.Model):
    doctor = models.ForeignKey(
        DoctorProfile, on_delete=models.CASCADE, related_name="weekly_slots"
    )
    weekday = models.IntegerField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        unique_together = ("doctor", "weekday", "start_time", "end_time")
        ordering = ("weekday", "start_time")

    def clean(self):
        if self.weekday < 0 or self.weekday > 6:
            raise ValidationError("weekday must be between 0 and 6.")
        if self.start_time >= self.end_time:
            raise ValidationError("start_time must be earlier than end_time.")


class TemporaryScheduleChange(models.Model):
    doctor = models.ForeignKey(
        DoctorProfile, on_delete=models.CASCADE, related_name="temporary_changes"
    )
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-start_datetime",)

    def clean(self):
        if self.start_datetime >= self.end_datetime:
            raise ValidationError("start_datetime must be earlier than end_datetime.")
        overlapping = TemporaryScheduleChange.objects.filter(
            doctor=self.doctor,
            start_datetime__lt=self.end_datetime,
            end_datetime__gt=self.start_datetime,
        )
        if self.pk:
            overlapping = overlapping.exclude(pk=self.pk)
        if overlapping.exists():
            raise ValidationError("Overlapping temporary schedule change exists.")


class TemporaryScheduleSlot(models.Model):
    change = models.ForeignKey(
        TemporaryScheduleChange, on_delete=models.CASCADE, related_name="slots"
    )
    weekday = models.IntegerField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        unique_together = ("change", "weekday", "start_time", "end_time")
        ordering = ("weekday", "start_time")

    def clean(self):
        if self.weekday < 0 or self.weekday > 6:
            raise ValidationError("weekday must be between 0 and 6.")
        if self.start_time >= self.end_time:
            raise ValidationError("start_time must be earlier than end_time.")


class PermanentScheduleChange(models.Model):
    doctor = models.ForeignKey(
        DoctorProfile, on_delete=models.CASCADE, related_name="permanent_changes"
    )
    effective_from = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-effective_from",)

    def clean(self):
        minimum = timezone.localdate() + timedelta(days=7)
        if self.effective_from < minimum:
            raise ValidationError("effective_from must be at least 7 days in the future.")


class PermanentScheduleSlot(models.Model):
    change = models.ForeignKey(
        PermanentScheduleChange, on_delete=models.CASCADE, related_name="slots"
    )
    weekday = models.IntegerField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        unique_together = ("change", "weekday", "start_time", "end_time")
        ordering = ("weekday", "start_time")

    def clean(self):
        if self.weekday < 0 or self.weekday > 6:
            raise ValidationError("weekday must be between 0 and 6.")
        if self.start_time >= self.end_time:
            raise ValidationError("start_time must be earlier than end_time.")


class Visit(models.Model):
    STATUS_SCHEDULED = "scheduled"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = (
        (STATUS_SCHEDULED, "Scheduled"),
        (STATUS_CANCELLED, "Cancelled"),
    )

    doctor = models.ForeignKey(
        DoctorProfile, on_delete=models.PROTECT, related_name="visits"
    )
    patient = models.ForeignKey(
        PatientProfile, on_delete=models.PROTECT, related_name="visits"
    )
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SCHEDULED)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("starts_at",)
        indexes = [models.Index(fields=["doctor", "starts_at", "ends_at"])]

    def clean(self):
        if self.starts_at >= self.ends_at:
            raise ValidationError("Visit end must be after start.")
