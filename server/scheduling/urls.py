from django.urls import path

from .views import (
    DoctorWeeklyScheduleView,
    MyVisitsView,
    PermanentScheduleView,
    TemporaryScheduleView,
    VisitCancelView,
    VisitCreateView,
)

urlpatterns = [
    path("doctors/me/weekly-schedule/", DoctorWeeklyScheduleView.as_view(), name="doctor-weekly"),
    path("doctors/me/temporary-schedule/", TemporaryScheduleView.as_view(), name="doctor-temporary"),
    path("doctors/me/permanent-schedule/", PermanentScheduleView.as_view(), name="doctor-permanent"),
    path("visits/", VisitCreateView.as_view(), name="visit-create"),
    path("visits/me/", MyVisitsView.as_view(), name="visit-me"),
    path("visits/<int:visit_id>/cancel/", VisitCancelView.as_view(), name="visit-cancel"),
]
