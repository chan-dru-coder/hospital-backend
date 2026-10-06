from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView,
    CustomLoginView,
    CurrentUserView,
    DoctorListView,
    DoctorDetailView,
    SpecializationListView,
)

urlpatterns = [
    # Auth endpoints
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', CustomLoginView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/me/', CurrentUserView.as_view(), name='current_user'),

    # Doctor directory endpoints
    path('doctors/', DoctorListView.as_view(), name='doctor_list'),
    path('doctors/<int:pk>/', DoctorDetailView.as_view(), name='doctor_detail'),
    path('specializations/', SpecializationListView.as_view(), name='specializations_list'),
]
