from rest_framework import status
from rest_framework.test import APITestCase

from scheduling.models import DoctorProfile


class RegistrationTests(APITestCase):
    def test_register_doctor(self):
        payload = {
            "email": "doctor@example.com",
            "full_name": "Doctor One",
            "password": "StrongPass123",
            "password2": "StrongPass123",
            "physical_address": "Sofia 1",
            "weekly_schedule": [
                {"weekday": 0, "start_time": "08:30:00", "end_time": "12:00:00"},
                {"weekday": 0, "start_time": "13:00:00", "end_time": "18:00:00"},
            ],
        }
        response = self.client.post("/v1/auth/register/doctor/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(DoctorProfile.objects.filter(user__email="doctor@example.com").exists())

    def test_register_patient_requires_valid_doctor(self):
        payload = {
            "email": "patient@example.com",
            "full_name": "Patient One",
            "password": "StrongPass123",
            "password2": "StrongPass123",
            "phone_number": "0888123456",
            "primary_doctor_id": 9999,
        }
        response = self.client.post("/v1/auth/register/patient/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
