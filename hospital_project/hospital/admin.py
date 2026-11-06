from django.contrib import admin
from .models import Patient, Department, OPDToken, Bed, Admission, Medicine, Dispensing


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('patient_id', 'name', 'age', 'gender', 'phone', 'registration_date')
    search_fields = ('patient_id', 'name', 'phone')
    list_filter = ('gender', 'registration_date')


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(OPDToken)
class OPDTokenAdmin(admin.ModelAdmin):
    list_display = ('token_number', 'patient', 'department', 'date', 'status', 'doctor_name')
    list_filter = ('status', 'department', 'date')
    search_fields = ('patient__name', 'token_number', 'doctor_name')


@admin.register(Bed)
class BedAdmin(admin.ModelAdmin):
    list_display = ('bed_number', 'category', 'status', 'daily_charge')
    list_filter = ('category', 'status')
    search_fields = ('bed_number',)


@admin.register(Admission)
class AdmissionAdmin(admin.ModelAdmin):
    list_display = ('patient', 'bed', 'admission_date', 'discharge_date', 'status')
    list_filter = ('status', 'admission_date')
    search_fields = ('patient__name', 'bed__bed_number', 'reason')


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'quantity', 'minimum_stock', 'price', 'expiry_date', 'is_low_stock')
    list_filter = ('category', 'expiry_date')
    search_fields = ('name', 'category')


@admin.register(Dispensing)
class DispensingAdmin(admin.ModelAdmin):
    list_display = ('medicine', 'patient', 'quantity', 'dispensed_date', 'dispensed_by')
    list_filter = ('dispensed_date',)
    search_fields = ('medicine__name', 'patient__name')
