from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import DoctorProfile, PatientProfile, Visit, WeeklyScheduleSlot

User = get_user_model()


def auth_client(client, user):
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")


class SchedulingApiTests(APITestCase):
    def setUp(self):
        self.doctor_user = User.objects.create_user(
            email="doc@test.com",
            full_name="Doctor",
            role="doctor",
            password="StrongPass123",
        )
        self.patient_user = User.objects.create_user(
            email="pat@test.com",
            full_name="Patient",
            role="patient",
            password="StrongPass123",
        )
        self.doctor = DoctorProfile.objects.create(
            user=self.doctor_user,
            physical_address="Sofia",
        )
        self.patient = PatientProfile.objects.create(
            user=self.patient_user,
            phone_number="0888123456",
            primary_doctor=self.doctor,
        )
        WeeklyScheduleSlot.objects.create(
            doctor=self.doctor,
            weekday=0,
            start_time="08:30:00",
            end_time="18:30:00",
        )

    def test_doctor_updates_weekly_schedule(self):
        auth_client(self.client, self.doctor_user)
        payload = {
            "slots": [
                {"weekday": 1, "start_time": "09:00:00", "end_time": "17:00:00"},
            ]
        }
        response = self.client.put(
            "/v1/scheduling/doctors/me/weekly-schedule/",
            payload,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(WeeklyScheduleSlot.objects.filter(doctor=self.doctor).count(), 1)

    def test_doctor_cannot_set_overlapping_weekly_slots(self):
        auth_client(self.client, self.doctor_user)
        payload = {
            "slots": [
                {"weekday": 1, "start_time": "09:00:00", "end_time": "12:00:00"},
                {"weekday": 1, "start_time": "11:30:00", "end_time": "15:00:00"},
            ]
        }
        response = self.client.put(
            "/v1/scheduling/doctors/me/weekly-schedule/",
            payload,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patient_can_create_visit(self):
        auth_client(self.client, self.patient_user)
        next_monday = timezone.now() + timedelta(days=(7 - timezone.now().weekday()) % 7 + 7)
        starts_at = next_monday.replace(hour=9, minute=0, second=0, microsecond=0)
        ends_at = starts_at + timedelta(minutes=30)
        response = self.client.post(
            "/v1/scheduling/visits/",
            {"starts_at": starts_at.isoformat(), "ends_at": ends_at.isoformat()},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Visit.objects.count(), 1)

    def test_doctor_cannot_create_visit(self):
        auth_client(self.client, self.doctor_user)
        start = timezone.now() + timedelta(days=8)
        response = self.client.post(
            "/v1/scheduling/visits/",
            {"starts_at": start.isoformat(), "ends_at": (start + timedelta(minutes=30)).isoformat()},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_overlap_is_blocked(self):
        Visit.objects.create(
            doctor=self.doctor,
            patient=self.patient,
            starts_at=timezone.now() + timedelta(days=8),
            ends_at=timezone.now() + timedelta(days=8, minutes=30),
        )

        auth_client(self.client, self.patient_user)
        starts = timezone.now() + timedelta(days=8, minutes=15)
        ends = starts + timedelta(minutes=20)
        response = self.client.post(
            "/v1/scheduling/visits/",
            {"starts_at": starts.isoformat(), "ends_at": ends.isoformat()},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cancel_requires_12_hours(self):
        starts = timezone.now() + timedelta(hours=10)
        visit = Visit.objects.create(
            doctor=self.doctor,
            patient=self.patient,
            starts_at=starts,
            ends_at=starts + timedelta(minutes=15),
        )
        auth_client(self.client, self.patient_user)
        response = self.client.post(f"/v1/scheduling/visits/{visit.id}/cancel/", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_my_visits_returns_current_user_data(self):
        starts = timezone.now() + timedelta(days=8)
        Visit.objects.create(
            doctor=self.doctor,
            patient=self.patient,
            starts_at=starts,
            ends_at=starts + timedelta(minutes=20),
        )
        auth_client(self.client, self.patient_user)
        response = self.client.get("/v1/scheduling/visits/me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_permanent_schedule_requires_future_date(self):
        auth_client(self.client, self.doctor_user)
        response = self.client.post(
            "/v1/scheduling/doctors/me/permanent-schedule/",
            {
                "effective_from": timezone.localdate().isoformat(),
                "slots": [{"weekday": 0, "start_time": "10:00:00", "end_time": "16:00:00"}],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_my_visits_rejects_invalid_status_filter(self):
        auth_client(self.client, self.patient_user)
        response = self.client.get("/v1/scheduling/visits/me/?status=invalid")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
