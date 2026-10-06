from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Q
from django.contrib.auth import get_user_model

from .models import DoctorProfile, PatientProfile
from .serializers import (
    CustomTokenObtainPairSerializer,
    UserRegistrationSerializer,
    DoctorProfileSerializer,
    UserProfileSerializer,
)

User = get_user_model()


class CustomLoginView(TokenObtainPairView):
    """Obtain JWT token pair with user profile info included."""
    permission_classes = (permissions.AllowAny,)
    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(APIView):
    """Register a new user (Patient or Doctor)."""
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            user_data = UserProfileSerializer(user).data
            return Response({
                'message': 'Registration successful.',
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': user_data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CurrentUserView(APIView):
    """Retrieve logged-in user profile details."""
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)


class DoctorListView(generics.ListAPIView):
    """Public listing of all verified doctors with filtering and search."""
    permission_classes = (permissions.AllowAny,)
    serializer_class = DoctorProfileSerializer

    def get_queryset(self):
        queryset = DoctorProfile.objects.select_related('user').filter(is_verified=True)
        
        # Filter by specialization
        specialization = self.request.query_params.get('specialization', '').strip()
        if specialization and specialization.lower() != 'all':
            queryset = queryset.filter(specialization__iexact=specialization)

        # Search query (by doctor name, hospital, specialization)
        search_query = self.request.query_params.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(hospital__icontains=search_query) |
                Q(specialization__icontains=search_query)
            )

        return queryset.order_by('-rating', '-experience_years')


class DoctorDetailView(generics.RetrieveAPIView):
    """Retrieve single doctor profile by doctor_id (pk)."""
    permission_classes = (permissions.AllowAny,)
    serializer_class = DoctorProfileSerializer
    queryset = DoctorProfile.objects.select_related('user').all()


class SpecializationListView(APIView):
    """Return distinct doctor specializations with counts."""
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        specs = DoctorProfile.objects.values_list('specialization', flat=True).distinct()
        cleaned_specs = sorted(list(set(s for s in specs if s)))
        if not cleaned_specs:
            cleaned_specs = [
                'Cardiologist',
                'Dermatologist',
                'Pediatrician',
                'Neurologist',
                'Orthopedic',
                'General Physician',
                'Gynecologist',
                'Psychiatrist'
            ]
        return Response(cleaned_specs)
