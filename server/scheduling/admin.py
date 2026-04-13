from django.contrib import admin

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

admin.site.register(DoctorProfile)
admin.site.register(PatientProfile)
admin.site.register(WeeklyScheduleSlot)
admin.site.register(TemporaryScheduleChange)
admin.site.register(TemporaryScheduleSlot)
admin.site.register(PermanentScheduleChange)
admin.site.register(PermanentScheduleSlot)
admin.site.register(Visit)
