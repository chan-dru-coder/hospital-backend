from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from .models import DoctorProfile, PatientProfile

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Extend JWT Token serializer to include user details in login response."""

    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        data['user'] = {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.get_full_name(),
            'role': user.role,
            'phone': user.phone,
        }
        if user.role == 'DOCTOR' and hasattr(user, 'doctor_profile'):
            data['user']['doctor_id'] = user.doctor_profile.id
            data['user']['specialization'] = user.doctor_profile.specialization
            data['user']['hospital'] = user.doctor_profile.hospital
            data['user']['photo_url'] = user.doctor_profile.photo_url
        elif user.role == 'PATIENT' and hasattr(user, 'patient_profile'):
            data['user']['patient_id'] = user.patient_profile.id

        return data


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True, min_length=6)
    
    # Optional fields for Doctor
    specialization = serializers.CharField(required=False, allow_blank=True)
    hospital = serializers.CharField(required=False, allow_blank=True)
    experience_years = serializers.IntegerField(required=False, default=3)
    consultation_fee = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=500.00)
    bio = serializers.CharField(required=False, allow_blank=True)
    photo_url = serializers.CharField(required=False, allow_blank=True)

    # Optional fields for Patient
    age = serializers.IntegerField(required=False, allow_null=True)
    gender = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'password', 'confirm_password',
            'first_name', 'last_name', 'role', 'phone',
            'specialization', 'hospital', 'experience_years',
            'consultation_fee', 'bio', 'photo_url', 'age', 'gender'
        ]

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        
        role = data.get('role', 'PATIENT')
        if role == 'DOCTOR':
            if not data.get('specialization'):
                raise serializers.ValidationError({"specialization": "Specialization is required for doctors."})
            if not data.get('hospital'):
                raise serializers.ValidationError({"hospital": "Hospital or Clinic name is required for doctors."})

        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        role = validated_data.get('role', 'PATIENT')

        # Pop profile-specific fields
        spec = validated_data.pop('specialization', '')
        hosp = validated_data.pop('hospital', '')
        exp = validated_data.pop('experience_years', 3)
        fee = validated_data.pop('consultation_fee', 500.00)
        bio = validated_data.pop('bio', '')
        photo = validated_data.pop('photo_url', '')

        age = validated_data.pop('age', None)
        gender = validated_data.pop('gender', '')

        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)

        if role == 'DOCTOR':
            # Default doctor avatar if not provided
            if not photo:
                photo = f"https://images.unsplash.com/photo-1622253692010-333f2da6031d?auto=format&fit=crop&q=80&w=400"
            DoctorProfile.objects.create(
                user=user,
                specialization=spec or 'General Physician',
                hospital=hosp or 'City Care Hospital',
                experience_years=exp or 3,
                consultation_fee=fee or 500.00,
                bio=bio or f"Dedicated {spec or 'doctor'} committed to quality patient healthcare.",
                photo_url=photo,
            )
        else:
            PatientProfile.objects.create(
                user=user,
                age=age,
                gender=gender or 'Male'
            )

        return user


class DoctorProfileSerializer(serializers.ModelSerializer):
    doctor_id = serializers.IntegerField(source='id', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    full_name = serializers.SerializerMethodField()
    email = serializers.EmailField(source='user.email', read_only=True)
    phone = serializers.CharField(source='user.phone', read_only=True)

    class Meta:
        model = DoctorProfile
        fields = [
            'doctor_id',
            'user_id',
            'full_name',
            'email',
            'phone',
            'specialization',
            'hospital',
            'experience_years',
            'consultation_fee',
            'rating',
            'total_reviews',
            'bio',
            'photo_url',
            'is_verified',
            'created_at',
        ]

    def get_full_name(self, obj):
        return f"Dr. {obj.user.get_full_name()}"


class PatientProfileSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    phone = serializers.CharField(source='user.phone', read_only=True)

    class Meta:
        model = PatientProfile
        fields = [
            'id',
            'user_id',
            'full_name',
            'email',
            'phone',
            'age',
            'gender',
            'blood_group',
            'address',
        ]


class UserProfileSerializer(serializers.ModelSerializer):
    doctor_profile = DoctorProfileSerializer(read_only=True)
    patient_profile = PatientProfileSerializer(read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'role',
            'phone',
            'doctor_profile',
            'patient_profile',
        ]
