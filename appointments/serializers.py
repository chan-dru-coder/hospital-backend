from rest_framework import serializers
from datetime import date
from django.db.models import Q
from .models import DoctorSlot, Appointment, Prescription
from users.models import DoctorProfile


class DoctorSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorSlot
        fields = ['id', 'day_of_week', 'start_time', 'end_time', 'slot_label', 'is_active']


class PrescriptionSerializer(serializers.ModelSerializer):
    doctor_name = serializers.SerializerMethodField()
    doctor_specialization = serializers.CharField(source='doctor.specialization', read_only=True)
    doctor_hospital = serializers.CharField(source='doctor.hospital', read_only=True)
    patient_name = serializers.CharField(source='patient.get_full_name', read_only=True)
    patient_email = serializers.EmailField(source='patient.email', read_only=True)
    patient_phone = serializers.CharField(source='patient.phone', read_only=True)
    patient_age = serializers.SerializerMethodField()
    patient_gender = serializers.SerializerMethodField()

    class Meta:
        model = Prescription
        fields = [
            'id',
            'appointment',
            'doctor',
            'doctor_name',
            'doctor_specialization',
            'doctor_hospital',
            'patient',
            'patient_name',
            'patient_email',
            'patient_phone',
            'patient_age',
            'patient_gender',
            'diagnosis',
            'medicines',
            'medical_notes',
            'advice',
            'follow_up_date',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'doctor', 'patient', 'created_at', 'updated_at']

    def get_doctor_name(self, obj):
        return f"Dr. {obj.doctor.user.get_full_name()}"

    def get_patient_age(self, obj):
        if hasattr(obj.patient, 'patient_profile') and obj.patient.patient_profile.age:
            return obj.patient.patient_profile.age
        return None

    def get_patient_gender(self, obj):
        if hasattr(obj.patient, 'patient_profile') and obj.patient.patient_profile.gender:
            return obj.patient.patient_profile.gender
        return 'Not specified'


class AppointmentSerializer(serializers.ModelSerializer):
    doctor_id = serializers.IntegerField(source='doctor.id', read_only=True)
    doctor_name = serializers.SerializerMethodField()
    doctor_specialization = serializers.CharField(source='doctor.specialization', read_only=True)
    doctor_hospital = serializers.CharField(source='doctor.hospital', read_only=True)
    doctor_photo = serializers.CharField(source='doctor.photo_url', read_only=True)
    doctor_fee = serializers.DecimalField(source='doctor.consultation_fee', max_digits=10, decimal_places=2, read_only=True)

    patient_id = serializers.IntegerField(source='patient.id', read_only=True)
    patient_name = serializers.CharField(source='patient.get_full_name', read_only=True)
    patient_email = serializers.EmailField(source='patient.email', read_only=True)
    patient_phone = serializers.CharField(source='patient.phone', read_only=True)
    patient_age = serializers.SerializerMethodField()
    patient_gender = serializers.SerializerMethodField()

    has_prescription = serializers.SerializerMethodField()
    prescription_id = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = [
            'id',
            'doctor_id',
            'doctor_name',
            'doctor_specialization',
            'doctor_hospital',
            'doctor_photo',
            'doctor_fee',
            'patient_id',
            'patient_name',
            'patient_email',
            'patient_phone',
            'patient_age',
            'patient_gender',
            'appointment_date',
            'time_slot',
            'status',
            'reason_for_visit',
            'doctor_notes',
            'has_prescription',
            'prescription_id',
            'created_at',
            'updated_at',
        ]

    def get_doctor_name(self, obj):
        return f"Dr. {obj.doctor.user.get_full_name()}"

    def get_patient_age(self, obj):
        if hasattr(obj.patient, 'patient_profile') and obj.patient.patient_profile.age:
            return obj.patient.patient_profile.age
        return None

    def get_patient_gender(self, obj):
        if hasattr(obj.patient, 'patient_profile') and obj.patient.patient_profile.gender:
            return obj.patient.patient_profile.gender
        return 'Not specified'

    def get_has_prescription(self, obj):
        return hasattr(obj, 'prescription')

    def get_prescription_id(self, obj):
        if hasattr(obj, 'prescription'):
            return obj.prescription.id
        return None


class BookAppointmentSerializer(serializers.Serializer):
    doctor_id = serializers.IntegerField()
    appointment_date = serializers.DateField()
    time_slot = serializers.CharField(max_length=50)
    reason_for_visit = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_appointment_date(self, value):
        if value < date.today():
            raise serializers.ValidationError("Appointment date cannot be in the past.")
        return value

    def validate(self, data):
        doctor_id = data.get('doctor_id')
        appt_date = data.get('appointment_date')
        slot = data.get('time_slot')

        try:
            doctor = DoctorProfile.objects.get(id=doctor_id)
            data['doctor'] = doctor
        except DoctorProfile.DoesNotExist:
            raise serializers.ValidationError({"doctor_id": "Doctor profile does not exist."})

        # Check if slot is already occupied
        is_taken = Appointment.objects.filter(
            doctor=doctor,
            appointment_date=appt_date,
            time_slot=slot
        ).exclude(status__in=['REJECTED', 'CANCELLED']).exists()

        if is_taken:
            raise serializers.ValidationError(
                {"time_slot": f"This slot ({slot}) on {appt_date} is already booked. Please choose a different time."}
            )

        return data
