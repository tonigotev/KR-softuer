from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers

from scheduling.models import DoctorProfile, PatientProfile, WeeklyScheduleSlot
from scheduling.services import validate_day_slots_do_not_overlap

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "full_name", "role")


class WeeklyScheduleSlotInputSerializer(serializers.Serializer):
    weekday = serializers.IntegerField(min_value=0, max_value=6)
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()

    def validate(self, attrs):
        if attrs["start_time"] >= attrs["end_time"]:
            raise serializers.ValidationError("start_time must be earlier than end_time.")
        return attrs


class DoctorRegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    full_name = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True)
    physical_address = serializers.CharField()
    weekly_schedule = WeeklyScheduleSlotInputSerializer(many=True)

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError("Passwords do not match.")
        if User.objects.filter(email=attrs["email"]).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        if not attrs["weekly_schedule"]:
            raise serializers.ValidationError("weekly_schedule is required.")
        validate_day_slots_do_not_overlap(attrs["weekly_schedule"])
        return attrs

    def create(self, validated_data):
        schedule = validated_data.pop("weekly_schedule")
        validated_data.pop("password2")

        user = User.objects.create_user(
            email=validated_data["email"],
            full_name=validated_data["full_name"],
            role="doctor",
            password=validated_data["password"],
        )
        doctor = DoctorProfile.objects.create(
            user=user, physical_address=validated_data["physical_address"]
        )
        WeeklyScheduleSlot.objects.bulk_create(
            [
                WeeklyScheduleSlot(
                    doctor=doctor,
                    weekday=slot["weekday"],
                    start_time=slot["start_time"],
                    end_time=slot["end_time"],
                )
                for slot in schedule
            ]
        )
        return user


class PatientRegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    full_name = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True)
    phone_number = serializers.CharField(max_length=20)
    primary_doctor_id = serializers.IntegerField()

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError("Passwords do not match.")
        if User.objects.filter(email=attrs["email"]).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        if not DoctorProfile.objects.filter(id=attrs["primary_doctor_id"]).exists():
            raise serializers.ValidationError("primary_doctor_id is invalid.")
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        doctor = DoctorProfile.objects.get(id=validated_data["primary_doctor_id"])
        user = User.objects.create_user(
            email=validated_data["email"],
            full_name=validated_data["full_name"],
            role="patient",
            password=validated_data["password"],
        )
        PatientProfile.objects.create(
            user=user,
            phone_number=validated_data["phone_number"],
            primary_doctor=doctor,
        )
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(username=attrs["email"], password=attrs["password"])
        if not user:
            raise serializers.ValidationError("Incorrect email or password.")
        attrs["user"] = user
        return attrs
