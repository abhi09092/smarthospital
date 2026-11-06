from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard_view, name='dashboard'),

    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Patients
    path('patients/', views.patient_list, name='patient_list'),
    path('patients/add/', views.patient_add, name='patient_add'),
    path('patients/<int:pk>/', views.patient_detail, name='patient_detail'),
    path('patients/<int:pk>/edit/', views.patient_edit, name='patient_edit'),
    path('patients/<int:pk>/delete/', views.patient_delete, name='patient_delete'),

    # OPD
    path('opd/', views.opd_queue, name='opd_queue'),
    path('opd/register/', views.opd_register, name='opd_register'),
    path('opd/token/<int:pk>/status/', views.opd_update_status, name='opd_update_status'),

    # Beds & Admissions
    path('beds/', views.bed_list, name='bed_list'),
    path('beds/add/', views.bed_add, name='bed_add'),
    path('admissions/', views.admission_list, name='admission_list'),
    path('admissions/admit/', views.admission_create, name='admission_create'),
    path('admissions/<int:pk>/discharge/', views.admission_discharge, name='admission_discharge'),

    # Medicines
    path('medicines/', views.medicine_list, name='medicine_list'),
    path('medicines/add/', views.medicine_add, name='medicine_add'),
    path('medicines/<int:pk>/edit/', views.medicine_edit, name='medicine_edit'),
    path('medicines/<int:pk>/delete/', views.medicine_delete, name='medicine_delete'),
    path('medicines/dispense/', views.medicine_dispense, name='medicine_dispense'),
]

