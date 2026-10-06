import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediconnect_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.models import DoctorProfile, PatientProfile
from appointments.models import DoctorSlot, Appointment, Prescription
from datetime import date, timedelta

User = get_user_model()

def seed():
    print("Seeding MediConnect database...")

    # Clear previous seed if any
    Appointment.objects.all().delete()
    DoctorSlot.objects.all().delete()
    DoctorProfile.objects.all().delete()
    PatientProfile.objects.all().delete()
    User.objects.filter(email__in=[
        'patient@mediconnect.com',
        'doctor@mediconnect.com',
        'dr.david@mediconnect.com',
        'dr.priya@mediconnect.com',
        'dr.marcus@mediconnect.com',
        'dr.elena@mediconnect.com',
        'dr.james@mediconnect.com',
        'dr.aisha@mediconnect.com',
    ]).delete()

    # 1. Create Demo Patient
    patient_user = User.objects.create_user(
        email='patient@mediconnect.com',
        password='Password123',
        first_name='Alex',
        last_name='Johnson',
        role='PATIENT',
        phone='+1 (555) 234-5678'
    )
    PatientProfile.objects.create(
        user=patient_user,
        age=32,
        gender='Male',
        blood_group='O+',
        address='742 Evergreen Terrace, Springfield'
    )
    print("Created demo patient: patient@mediconnect.com / Password123")

    # 2. Doctor Data List
    doctors_data = [
        {
            'email': 'doctor@mediconnect.com',
            'password': 'Password123',
            'first_name': 'Sarah',
            'last_name': 'Mitchell',
            'specialization': 'Cardiologist',
            'hospital': 'Metro Heart & Vascular Institute',
            'experience_years': 14,
            'consultation_fee': 750.00,
            'rating': 4.9,
            'total_reviews': 142,
            'phone': '+1 (555) 890-1234',
            'photo_url': 'https://images.unsplash.com/photo-1559839734-2b71ea197ec2?auto=format&fit=crop&q=80&w=450',
            'bio': 'Board-certified cardiologist specializing in preventive cardiology, coronary artery disease, and hypertension management with over 14 years of clinical excellence.'
        },
        {
            'email': 'dr.david@mediconnect.com',
            'password': 'Password123',
            'first_name': 'David',
            'last_name': 'Chen',
            'specialization': 'Neurologist',
            'hospital': 'Neurological Science Medical Center',
            'experience_years': 16,
            'consultation_fee': 850.00,
            'rating': 4.9,
            'total_reviews': 98,
            'phone': '+1 (555) 345-6789',
            'photo_url': 'https://images.unsplash.com/photo-1622253692010-333f2da6031d?auto=format&fit=crop&q=80&w=450',
            'bio': 'Senior neurologist focused on headache disorders, movement diagnostics, neuro-rehabilitation, and modern therapeutic neurological care.'
        },
        {
            'email': 'dr.priya@mediconnect.com',
            'password': 'Password123',
            'first_name': 'Priya',
            'last_name': 'Sharma',
            'specialization': 'Dermatologist',
            'hospital': 'Apex Derma & Aesthetics Clinic',
            'experience_years': 9,
            'consultation_fee': 600.00,
            'rating': 4.8,
            'total_reviews': 165,
            'phone': '+1 (555) 456-7890',
            'photo_url': 'https://images.unsplash.com/photo-1594824813626-d6679b940986?auto=format&fit=crop&q=80&w=450',
            'bio': 'Specialist in clinical and cosmetic dermatology, psoriasis, eczema, acne solutions, and advanced laser dermatological procedures.'
        },
        {
            'email': 'dr.marcus@mediconnect.com',
            'password': 'Password123',
            'first_name': 'Marcus',
            'last_name': 'Vance',
            'specialization': 'Orthopedic',
            'hospital': 'St. Jude Bone & Joint Hospital',
            'experience_years': 18,
            'consultation_fee': 700.00,
            'rating': 4.7,
            'total_reviews': 114,
            'phone': '+1 (555) 567-8901',
            'photo_url': 'https://images.unsplash.com/photo-1537368910025-700350fe46c7?auto=format&fit=crop&q=80&w=450',
            'bio': 'Specialized orthopedic surgeon in sports injuries, knee and hip arthroplasty, spine health, and non-surgical musculoskeletal therapies.'
        },
        {
            'email': 'dr.elena@mediconnect.com',
            'password': 'Password123',
            'first_name': 'Elena',
            'last_name': 'Rostova',
            'specialization': 'Pediatrician',
            'hospital': 'Sunrise Children’s Healthcare Hospital',
            'experience_years': 11,
            'consultation_fee': 550.00,
            'rating': 5.0,
            'total_reviews': 210,
            'phone': '+1 (555) 678-9012',
            'photo_url': 'https://images.unsplash.com/photo-1614608682850-e0d6ed316d47?auto=format&fit=crop&q=80&w=450',
            'bio': 'Compassionate child health specialist offering comprehensive infant care, developmental milestones tracking, immunizations, and pediatric wellness.'
        },
        {
            'email': 'dr.james@mediconnect.com',
            'password': 'Password123',
            'first_name': 'James',
            'last_name': 'Wilson',
            'specialization': 'General Physician',
            'hospital': 'City Central Community Health Care',
            'experience_years': 12,
            'consultation_fee': 500.00,
            'rating': 4.8,
            'total_reviews': 130,
            'phone': '+1 (555) 789-0123',
            'photo_url': 'https://images.unsplash.com/photo-1582750433449-648ed127bb54?auto=format&fit=crop&q=80&w=450',
            'bio': 'Primary care physician focusing on holistic wellness, chronic illness supervision, preventive screenings, and personalized lifestyle medicine.'
        },
        {
            'email': 'dr.aisha@mediconnect.com',
            'password': 'Password123',
            'first_name': 'Aisha',
            'last_name': 'Khan',
            'specialization': 'Psychiatrist',
            'hospital': 'MindCare Behavioral Health Pavilion',
            'experience_years': 8,
            'consultation_fee': 800.00,
            'rating': 4.9,
            'total_reviews': 89,
            'phone': '+1 (555) 890-2345',
            'photo_url': 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&q=80&w=450',
            'bio': 'Compassionate mental healthcare physician helping patients navigate anxiety, depression, adult ADHD, stress management, and emotional resilience.'
        }
    ]

    doctor_profiles = []
    standard_slots = [
        ("09:00:00", "10:00:00", "09:00 AM - 10:00 AM"),
        ("10:00:00", "11:00:00", "10:00 AM - 11:00 AM"),
        ("11:00:00", "12:00:00", "11:00 AM - 12:00 PM"),
        ("02:00:00", "03:00:00", "02:00 PM - 03:00 PM"),
        ("03:00:00", "04:00:00", "03:00 PM - 04:00 PM"),
        ("04:00:00", "05:00:00", "04:00 PM - 05:00 PM"),
        ("05:00:00", "06:00:00", "05:00 PM - 06:00 PM"),
    ]

    for doc in doctors_data:
        u = User.objects.create_user(
            email=doc['email'],
            password=doc['password'],
            first_name=doc['first_name'],
            last_name=doc['last_name'],
            role='DOCTOR',
            phone=doc['phone']
        )
        dp = DoctorProfile.objects.create(
            user=u,
            specialization=doc['specialization'],
            hospital=doc['hospital'],
            experience_years=doc['experience_years'],
            consultation_fee=doc['consultation_fee'],
            rating=doc['rating'],
            total_reviews=doc['total_reviews'],
            bio=doc['bio'],
            photo_url=doc['photo_url']
        )
        doctor_profiles.append(dp)

        # Create slots
        for start, end, label in standard_slots:
            DoctorSlot.objects.create(
                doctor=dp,
                day_of_week='All',
                start_time=start,
                end_time=end,
                slot_label=label
            )

    print(f"Created {len(doctor_profiles)} doctors with active availability slots.")

    # 3. Create Sample Appointments for demo patient and demo doctor (Dr. Sarah Mitchell)
    demo_doc = doctor_profiles[0]  # Dr. Sarah Mitchell
    d_chen = doctor_profiles[1]    # Dr. David Chen
    d_priya = doctor_profiles[2]   # Dr. Priya Sharma

    today = date.today()

    # Appointment 1: Completed with Prescription
    appt_completed = Appointment.objects.create(
        patient=patient_user,
        doctor=demo_doc,
        appointment_date=today - timedelta(days=2),
        time_slot="10:00 AM - 11:00 AM",
        status='COMPLETED',
        reason_for_visit="Routine cardiovascular checkup and mild chest tightness after exercise.",
        doctor_notes="Patient showed regular sinus rhythm. Recommended lifestyle adjustments and mild beta blocker."
    )
    Prescription.objects.create(
        appointment=appt_completed,
        doctor=demo_doc,
        patient=patient_user,
        diagnosis="Stage 1 Primary Hypertension & Exercise-Induced Palpitations",
        medicines=[
            {
                "name": "Metoprolol Succinate",
                "dosage": "25 mg",
                "frequency": "Once daily (Morning)",
                "duration": "30 days",
                "notes": "Take with breakfast"
            },
            {
                "name": "Atorvastatin",
                "dosage": "10 mg",
                "frequency": "Once daily (Night)",
                "duration": "30 days",
                "notes": "Take before bedtime"
            },
            {
                "name": "CoQ10 Supplement",
                "dosage": "100 mg",
                "frequency": "Once daily",
                "duration": "60 days",
                "notes": "Supports muscle & heart health"
            }
        ],
        medical_notes="ECG normal. Resting BP 138/86 mmHg. Blood work shows borderline LDL. Follow low-sodium DASH diet.",
        advice="30 minutes moderate cardio walk 5 days/week. Drink minimum 2.5L water daily. Reduce caffeine intake.",
        follow_up_date=today + timedelta(days=28)
    )

    # Appointment 2: Accepted upcoming appointment
    Appointment.objects.create(
        patient=patient_user,
        doctor=d_priya,
        appointment_date=today + timedelta(days=1),
        time_slot="02:00 PM - 03:00 PM",
        status='ACCEPTED',
        reason_for_visit="Skin rash consultation on forearm and allergic dermatitis examination.",
        doctor_notes="Confirmed for tomorrow. Please bring previous allergy history."
    )

    # Appointment 3: Pending appointment
    Appointment.objects.create(
        patient=patient_user,
        doctor=demo_doc,
        appointment_date=today + timedelta(days=3),
        time_slot="09:00 AM - 10:00 AM",
        status='PENDING',
        reason_for_visit="Follow-up on blood pressure monitor readings and dietary review."
    )

    # Appointment 4: Another patient booking with Dr. Mitchell for doctor's tab view
    p2 = User.objects.create_user(
        email='robert.smith@example.com',
        password='Password123',
        first_name='Robert',
        last_name='Smith',
        role='PATIENT',
        phone='+1 (555) 912-3456'
    )
    PatientProfile.objects.create(user=p2, age=45, gender='Male')

    Appointment.objects.create(
        patient=p2,
        doctor=demo_doc,
        appointment_date=today + timedelta(days=2),
        time_slot="11:00 AM - 12:00 PM",
        status='PENDING',
        reason_for_visit="ECG review and second opinion on cholesterol medications."
    )

    print("Created demo appointments and prescription successfully!")
    print("\nDEMO CREDENTIALS:")
    print("1. Patient: email='patient@mediconnect.com' password='Password123'")
    print("2. Doctor:  email='doctor@mediconnect.com'  password='Password123'")

if __name__ == '__main__':
    seed()
