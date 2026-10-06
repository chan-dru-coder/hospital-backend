from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Q
from datetime import datetime, date

from .models import DoctorSlot, Appointment, Prescription
from users.models import DoctorProfile
from .serializers import (
    DoctorSlotSerializer,
    AppointmentSerializer,
    BookAppointmentSerializer,
    PrescriptionSerializer,
)


DEFAULT_SLOTS = [
    "09:00 AM - 10:00 AM",
    "10:00 AM - 11:00 AM",
    "11:00 AM - 12:00 PM",
    "02:00 PM - 03:00 PM",
    "03:00 PM - 04:00 PM",
    "04:00 PM - 05:00 PM",
    "05:00 PM - 06:00 PM",
]


class DoctorSlotsAvailabilityView(APIView):
    """
    Get available time slots for a doctor on a specific date.
    Returns list of slots with 'is_booked' status so the UI can disable occupied slots.
    """
    permission_classes = (permissions.AllowAny,)

    def get(self, request, doctor_id):
        try:
            doctor = DoctorProfile.objects.get(id=doctor_id)
        except DoctorProfile.DoesNotExist:
            return Response({"error": "Doctor not found"}, status=status.HTTP_404_NOT_FOUND)

        selected_date_str = request.query_params.get('date')
        if selected_date_str:
            try:
                selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({"error": "Invalid date format, use YYYY-MM-DD"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            selected_date = date.today()

        # Check existing doctor slots configured
        configured_slots = DoctorSlot.objects.filter(doctor=doctor, is_active=True)
        if configured_slots.exists():
            slot_labels = [s.slot_label for s in configured_slots]
        else:
            slot_labels = DEFAULT_SLOTS

        # Find booked slots for this doctor on this date
        booked_slots = set(
            Appointment.objects.filter(
                doctor=doctor,
                appointment_date=selected_date
            ).exclude(status__in=['REJECTED', 'CANCELLED']).values_list('time_slot', flat=True)
        )

        slots_data = []
        for slot in slot_labels:
            slots_data.append({
                "slot": slot,
                "is_booked": slot in booked_slots,
                "is_available": slot not in booked_slots
            })

        return Response({
            "doctor_id": doctor.id,
            "doctor_name": f"Dr. {doctor.user.get_full_name()}",
            "date": str(selected_date),
            "slots": slots_data
        })


class BookAppointmentView(APIView):
    """
    Book an appointment. Requires authenticated Patient.
    Uses database transaction and atomic locking to strictly prevent double-booking.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        if request.user.role != 'PATIENT':
            return Response(
                {"error": "Only registered patients can book appointments."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = BookAppointmentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        doctor = serializer.validated_data['doctor']
        appt_date = serializer.validated_data['appointment_date']
        time_slot = serializer.validated_data['time_slot']
        reason = serializer.validated_data.get('reason_for_visit', '')

        try:
            with transaction.atomic():
                # Double-booking guard with select_for_update to avoid race conditions
                existing_active = Appointment.objects.select_for_update().filter(
                    doctor=doctor,
                    appointment_date=appt_date,
                    time_slot=time_slot
                ).exclude(status__in=['REJECTED', 'CANCELLED']).exists()

                if existing_active:
                    return Response(
                        {"error": f"The slot '{time_slot}' on {appt_date} has just been reserved. Please pick another slot."},
                        status=status.HTTP_409_CONFLICT
                    )

                appointment = Appointment.objects.create(
                    patient=request.user,
                    doctor=doctor,
                    appointment_date=appt_date,
                    time_slot=time_slot,
                    status='PENDING',
                    reason_for_visit=reason
                )

                out_serializer = AppointmentSerializer(appointment)
                return Response(out_serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PatientAppointmentsView(generics.ListAPIView):
    """List all appointments for the authenticated patient."""
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = AppointmentSerializer

    def get_queryset(self):
        queryset = Appointment.objects.select_related('doctor__user', 'patient', 'prescription').filter(
            patient=self.request.user
        )
        status_filter = self.request.query_params.get('status')
        if status_filter and status_filter.upper() != 'ALL':
            queryset = queryset.filter(status=status_filter.upper())
        return queryset


class PatientCancelAppointmentView(APIView):
    """Patient cancels their pending or accepted appointment."""
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, appointment_id):
        try:
            appointment = Appointment.objects.get(id=appointment_id, patient=request.user)
        except Appointment.DoesNotExist:
            return Response({"error": "Appointment not found."}, status=status.HTTP_404_NOT_FOUND)

        if appointment.status in ['COMPLETED', 'REJECTED', 'CANCELLED']:
            return Response(
                {"error": f"Cannot cancel an appointment that is already {appointment.status.lower()}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        appointment.status = 'CANCELLED'
        appointment.save()
        return Response({
            "message": "Appointment cancelled successfully.",
            "appointment": AppointmentSerializer(appointment).data
        })


class DoctorAppointmentsView(generics.ListAPIView):
    """List appointments for the authenticated doctor, filterable by status tabs."""
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = AppointmentSerializer

    def get_queryset(self):
        if not hasattr(self.request.user, 'doctor_profile'):
            return Appointment.objects.none()

        doctor = self.request.user.doctor_profile
        queryset = Appointment.objects.select_related('patient', 'doctor__user', 'prescription').filter(doctor=doctor)

        tab_status = self.request.query_params.get('status')
        if tab_status and tab_status.upper() != 'ALL':
            queryset = queryset.filter(status=tab_status.upper())

        return queryset


class DoctorUpdateAppointmentStatusView(APIView):
    """Doctor accepts, rejects, or completes an appointment."""
    permission_classes = (permissions.IsAuthenticated,)

    def patch(self, request, appointment_id):
        if not hasattr(request.user, 'doctor_profile'):
            return Response({"error": "Only doctors can update appointment statuses."}, status=status.HTTP_403_FORBIDDEN)

        doctor = request.user.doctor_profile
        try:
            appointment = Appointment.objects.get(id=appointment_id, doctor=doctor)
        except Appointment.DoesNotExist:
            return Response({"error": "Appointment not found."}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get('status')
        if not new_status or new_status.upper() not in ['ACCEPTED', 'REJECTED', 'COMPLETED', 'PENDING']:
            return Response({"error": "Invalid status value."}, status=status.HTTP_400_BAD_REQUEST)

        appointment.status = new_status.upper()
        if 'doctor_notes' in request.data:
            appointment.doctor_notes = request.data['doctor_notes']
        appointment.save()

        return Response({
            "message": f"Appointment marked as {appointment.status}.",
            "appointment": AppointmentSerializer(appointment).data
        })


class PrescriptionManageView(APIView):
    """Doctor creates or edits a prescription for an appointment."""
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, appointment_id):
        if not hasattr(request.user, 'doctor_profile'):
            return Response({"error": "Only doctors can issue prescriptions."}, status=status.HTTP_403_FORBIDDEN)

        doctor = request.user.doctor_profile
        try:
            appointment = Appointment.objects.get(id=appointment_id, doctor=doctor)
        except Appointment.DoesNotExist:
            return Response({"error": "Appointment not found."}, status=status.HTTP_404_NOT_FOUND)

        diagnosis = request.data.get('diagnosis', '').strip()
        medicines = request.data.get('medicines', [])
        medical_notes = request.data.get('medical_notes', '')
        advice = request.data.get('advice', '')
        follow_up_date = request.data.get('follow_up_date') or None

        if not diagnosis:
            return Response({"error": "Diagnosis is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Create or update prescription
        prescription, created = Prescription.objects.update_or_create(
            appointment=appointment,
            defaults={
                'doctor': doctor,
                'patient': appointment.patient,
                'diagnosis': diagnosis,
                'medicines': medicines,
                'medical_notes': medical_notes,
                'advice': advice,
                'follow_up_date': follow_up_date
            }
        )

        # Automatically mark appointment as COMPLETED if doctor prescribes
        appointment.status = 'COMPLETED'
        appointment.save()

        return Response({
            "message": "Prescription saved successfully.",
            "prescription": PrescriptionSerializer(prescription).data
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class PrescriptionDetailView(APIView):
    """Retrieve prescription details for either patient or doctor."""
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, appointment_id):
        try:
            appointment = Appointment.objects.get(id=appointment_id)
        except Appointment.DoesNotExist:
            return Response({"error": "Appointment not found."}, status=status.HTTP_404_NOT_FOUND)

        # Ensure user is either the doctor or the patient of this appointment
        is_patient = appointment.patient == request.user
        is_doctor = hasattr(request.user, 'doctor_profile') and appointment.doctor == request.user.doctor_profile

        if not (is_patient or is_doctor or request.user.is_staff):
            return Response({"error": "You do not have permission to view this prescription."}, status=status.HTTP_403_FORBIDDEN)

        if not hasattr(appointment, 'prescription'):
            return Response({"error": "No prescription found for this appointment."}, status=status.HTTP_404_NOT_FOUND)

        serializer = PrescriptionSerializer(appointment.prescription)
        return Response(serializer.data)
