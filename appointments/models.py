from django.db import models
from django.conf import settings
from django.db.models import Q
from users.models import DoctorProfile


class DoctorSlot(models.Model):
    """Preset availability slots that doctors offer each day."""
    DAYS_OF_WEEK = (
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
        ('All', 'All Days'),
    )

    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='slots')
    day_of_week = models.CharField(max_length=20, choices=DAYS_OF_WEEK, default='All')
    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_label = models.CharField(max_length=50)  # e.g., "09:00 AM - 10:00 AM"
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['start_time']

    def __str__(self):
        return f"{self.doctor} | {self.day_of_week} ({self.slot_label})"


class Appointment(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    )

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='patient_appointments'
    )
    doctor = models.ForeignKey(
        DoctorProfile,
        on_delete=models.CASCADE,
        related_name='doctor_appointments'
    )
    appointment_date = models.DateField()
    time_slot = models.CharField(max_length=50)  # e.g. "10:00 AM - 11:00 AM"
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    reason_for_visit = models.TextField(blank=True)
    doctor_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-appointment_date', 'time_slot']

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.status not in ['REJECTED', 'CANCELLED']:
            conflict = Appointment.objects.filter(
                doctor=self.doctor,
                appointment_date=self.appointment_date,
                time_slot=self.time_slot
            ).exclude(id=self.id).exclude(status__in=['REJECTED', 'CANCELLED']).exists()
            if conflict:
                raise ValidationError(f"Slot '{self.time_slot}' on {self.appointment_date} is already booked for this doctor.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Appt #{self.id}: {self.patient.get_full_name()} with Dr. {self.doctor.user.get_full_name()} on {self.appointment_date} ({self.status})"


class Prescription(models.Model):
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name='prescription'
    )
    doctor = models.ForeignKey(
        DoctorProfile,
        on_delete=models.CASCADE,
        related_name='prescriptions'
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='prescriptions'
    )
    diagnosis = models.TextField()
    # List of items: [{"name": "Amoxicillin", "dosage": "500mg", "frequency": "3 times/day", "duration": "5 days", "notes": "After food"}]
    medicines = models.JSONField(default=list)
    medical_notes = models.TextField(blank=True)
    advice = models.TextField(blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Prescription for Appt #{self.appointment.id} ({self.patient.get_full_name()})"
