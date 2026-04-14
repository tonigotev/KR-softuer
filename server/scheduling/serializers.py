from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from .models import (
    DoctorProfile,
    PatientProfile,
    PermanentScheduleChange,
    PermanentScheduleSlot,
    TemporaryScheduleChange,
    TemporaryScheduleSlot,
    Visit,
    WeeklyScheduleSlot,
)
from .services import validate_day_slots_do_not_overlap


class ScheduleSlotSerializer(serializers.Serializer):
    weekday = serializers.IntegerField(min_value=0, max_value=6)
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()

    def validate(self, attrs):
        if attrs["start_time"] >= attrs["end_time"]:
            raise serializers.ValidationError("start_time must be earlier than end_time.")
        return attrs


class WeeklyScheduleSlotModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeeklyScheduleSlot
        fields = ("id", "weekday", "start_time", "end_time")


class WeeklyScheduleUpdateSerializer(serializers.Serializer):
    slots = ScheduleSlotSerializer(many=True)

    def validate_slots(self, value):
        validate_day_slots_do_not_overlap(value)
        return value


class TemporaryScheduleCreateSerializer(serializers.Serializer):
    start_datetime = serializers.DateTimeField()
    end_datetime = serializers.DateTimeField()
    slots = ScheduleSlotSerializer(many=True)

    def validate(self, attrs):
        if attrs["start_datetime"] >= attrs["end_datetime"]:
            raise serializers.ValidationError("start_datetime must be earlier than end_datetime.")
        if not attrs["slots"]:
            raise serializers.ValidationError("slots is required.")
        validate_day_slots_do_not_overlap(attrs["slots"])
        return attrs


class PermanentScheduleCreateSerializer(serializers.Serializer):
    effective_from = serializers.DateField()
    slots = ScheduleSlotSerializer(many=True)

    def validate(self, attrs):
        minimum = timezone.localdate() + timedelta(days=7)
        if attrs["effective_from"] < minimum:
            raise serializers.ValidationError(
                "effective_from must be at least 7 days in the future."
            )
        if not attrs["slots"]:
            raise serializers.ValidationError("slots is required.")
        validate_day_slots_do_not_overlap(attrs["slots"])
        return attrs


class VisitCreateSerializer(serializers.Serializer):
    starts_at = serializers.DateTimeField()
    ends_at = serializers.DateTimeField()

    def validate(self, attrs):
        if attrs["starts_at"] >= attrs["ends_at"]:
            raise serializers.ValidationError("starts_at must be before ends_at.")
        return attrs


class VisitSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source="doctor.user.full_name", read_only=True)
    patient_name = serializers.CharField(source="patient.user.full_name", read_only=True)

    class Meta:
        model = Visit
        fields = (
            "id",
            "doctor",
            "doctor_name",
            "patient",
            "patient_name",
            "starts_at",
            "ends_at",
            "status",
            "cancelled_at",
            "created_at",
        )


class MyVisitsQuerySerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=[Visit.STATUS_SCHEDULED, Visit.STATUS_CANCELLED], required=False
    )
    from_date = serializers.DateField(required=False)


def replace_weekly_schedule(doctor, slots):
    with transaction.atomic():
        WeeklyScheduleSlot.objects.filter(doctor=doctor).delete()
        new_slots = []
        for item in slots:
            slot = WeeklyScheduleSlot(
                doctor=doctor,
                weekday=item["weekday"],
                start_time=item["start_time"],
                end_time=item["end_time"],
            )
            slot.full_clean()
            new_slots.append(slot)
        WeeklyScheduleSlot.objects.bulk_create(new_slots)


def create_temporary_change(doctor, validated_data):
    with transaction.atomic():
        change = TemporaryScheduleChange(
            doctor=doctor,
            start_datetime=validated_data["start_datetime"],
            end_datetime=validated_data["end_datetime"],
        )
        change.full_clean()
        change.save()
        slots = []
        for item in validated_data["slots"]:
            slot = TemporaryScheduleSlot(
                change=change,
                weekday=item["weekday"],
                start_time=item["start_time"],
                end_time=item["end_time"],
            )
            slot.full_clean()
            slots.append(slot)
        TemporaryScheduleSlot.objects.bulk_create(slots)
        return change


def create_permanent_change(doctor, validated_data):
    with transaction.atomic():
        change = PermanentScheduleChange(
            doctor=doctor,
            effective_from=validated_data["effective_from"],
        )
        change.full_clean()
        change.save()
        slots = []
        for item in validated_data["slots"]:
            slot = PermanentScheduleSlot(
                change=change,
                weekday=item["weekday"],
                start_time=item["start_time"],
                end_time=item["end_time"],
            )
            slot.full_clean()
            slots.append(slot)
        PermanentScheduleSlot.objects.bulk_create(slots)
        return change


class DoctorProfileSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source="user.email", read_only=True)
    user_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = DoctorProfile
        fields = ("id", "user_email", "user_name", "physical_address")


class PatientProfileSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source="user.email", read_only=True)
    user_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = PatientProfile
        fields = ("id", "user_email", "user_name", "phone_number", "primary_doctor")
