from django.urls import path
from .views import (
    DoctorSlotsAvailabilityView,
    BookAppointmentView,
    PatientAppointmentsView,
    PatientCancelAppointmentView,
    DoctorAppointmentsView,
    DoctorUpdateAppointmentStatusView,
    PrescriptionManageView,
    PrescriptionDetailView,
)

urlpatterns = [
    # Availability
    path('doctors/<int:doctor_id>/availability/', DoctorSlotsAvailabilityView.as_view(), name='doctor_availability'),
    
    # Booking
    path('book/', BookAppointmentView.as_view(), name='book_appointment'),
    
    # Patient Appointments
    path('patient/my-appointments/', PatientAppointmentsView.as_view(), name='patient_appointments'),
    path('patient/appointments/<int:appointment_id>/cancel/', PatientCancelAppointmentView.as_view(), name='patient_cancel_appointment'),
    
    # Doctor Appointments
    path('doctor/appointments/', DoctorAppointmentsView.as_view(), name='doctor_appointments'),
    path('doctor/appointments/<int:appointment_id>/status/', DoctorUpdateAppointmentStatusView.as_view(), name='doctor_update_status'),
    
    # Prescriptions
    path('appointments/<int:appointment_id>/prescription/', PrescriptionManageView.as_view(), name='prescription_manage'),
    path('appointments/<int:appointment_id>/prescription/view/', PrescriptionDetailView.as_view(), name='prescription_detail'),
]
