from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import DoctorProfile, PatientProfile, Visit, WeeklyScheduleSlot
from .permissions import IsDoctor
from .serializers import (
    PermanentScheduleCreateSerializer,
    TemporaryScheduleCreateSerializer,
    VisitCreateSerializer,
    VisitSerializer,
    WeeklyScheduleSlotModelSerializer,
    WeeklyScheduleUpdateSerializer,
    create_permanent_change,
    create_temporary_change,
    replace_weekly_schedule,
)
from .services import cancel_visit, create_visit


class DoctorWeeklyScheduleView(APIView):
    permission_classes = [IsAuthenticated, IsDoctor]

    def get(self, request):
        doctor = get_object_or_404(DoctorProfile, user=request.user)
        slots = WeeklyScheduleSlot.objects.filter(doctor=doctor).order_by("weekday", "start_time")
        serializer = WeeklyScheduleSlotModelSerializer(slots, many=True)
        return Response(serializer.data)

    def put(self, request):
        doctor = get_object_or_404(DoctorProfile, user=request.user)
        serializer = WeeklyScheduleUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        replace_weekly_schedule(doctor, serializer.validated_data["slots"])
        return Response({"detail": "Weekly schedule updated."}, status=status.HTTP_200_OK)


class TemporaryScheduleView(APIView):
    permission_classes = [IsAuthenticated, IsDoctor]

    def post(self, request):
        doctor = get_object_or_404(DoctorProfile, user=request.user)
        serializer = TemporaryScheduleCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        create_temporary_change(doctor, serializer.validated_data)
        return Response({"detail": "Temporary schedule created."}, status=status.HTTP_201_CREATED)


class PermanentScheduleView(APIView):
    permission_classes = [IsAuthenticated, IsDoctor]

    def post(self, request):
        doctor = get_object_or_404(DoctorProfile, user=request.user)
        serializer = PermanentScheduleCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        create_permanent_change(doctor, serializer.validated_data)
        return Response({"detail": "Permanent schedule change created."}, status=status.HTTP_201_CREATED)


class VisitCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != "patient":
            return Response({"detail": "Only patients can create visits."}, status=status.HTTP_403_FORBIDDEN)

        patient = get_object_or_404(PatientProfile, user=request.user)
        serializer = VisitCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        visit = create_visit(
            patient=patient,
            doctor=patient.primary_doctor,
            starts_at=serializer.validated_data["starts_at"],
            ends_at=serializer.validated_data["ends_at"],
        )
        return Response(VisitSerializer(visit).data, status=status.HTTP_201_CREATED)


class VisitCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, visit_id):
        visit = get_object_or_404(Visit, id=visit_id)
        visit = cancel_visit(visit, request.user)
        return Response(VisitSerializer(visit).data, status=status.HTTP_200_OK)


class MyVisitsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = Visit.objects.none()
        if request.user.role == "patient":
            queryset = Visit.objects.filter(patient__user=request.user)
        elif request.user.role == "doctor":
            queryset = Visit.objects.filter(doctor__user=request.user)

        status_filter = request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        from_date = request.query_params.get("from")
        if from_date:
            queryset = queryset.filter(starts_at__date__gte=from_date)

        queryset = queryset.order_by("starts_at")
        return Response(VisitSerializer(queryset, many=True).data)
