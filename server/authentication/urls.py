from django.urls import path
from .views import LoginView, LogoutView, RegisterDoctorView, RegisterPatientView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("register/doctor/", RegisterDoctorView.as_view(), name="register-doctor"),
    path("register/patient/", RegisterPatientView.as_view(), name="register-patient"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
