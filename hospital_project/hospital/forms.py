from django import forms
from django.db.models import Q
from django.contrib.auth.forms import AuthenticationForm
from .models import Patient, OPDToken, Bed, Admission, Medicine, Dispensing, Department


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter username',
        'autofocus': True,
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter password',
    }))


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['name', 'age', 'gender', 'phone', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'age': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Age in years', 'min': 0, 'max': 130}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. +91 9876543210'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Residential Address'}),
        }


class OPDRegistrationForm(forms.ModelForm):
    class Meta:
        model = OPDToken
        fields = ['patient', 'department', 'doctor_name', 'notes']
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-select'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'doctor_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Doctor Name (Optional)'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Chief complaints / symptoms (Optional)'}),
        }


class BedForm(forms.ModelForm):
    class Meta:
        model = Bed
        fields = ['bed_number', 'category', 'status', 'daily_charge', 'notes']
        widgets = {
            'bed_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. BED-101, ICU-02'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'daily_charge': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'notes': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ward location / special equipment'}),
        }


class AdmissionForm(forms.ModelForm):
    class Meta:
        model = Admission
        fields = ['patient', 'bed', 'reason']
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-select'}),
            'bed': forms.Select(attrs={'class': 'form-select'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Reason for admission / diagnosis'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Show available beds only, or include current bed if editing
        if self.instance and self.instance.pk:
            self.fields['bed'].queryset = Bed.objects.filter(
                Q(status='Available') | Q(pk=self.instance.bed_id)
            )
        else:
            self.fields['bed'].queryset = Bed.objects.filter(status='Available')


class MedicineForm(forms.ModelForm):
    class Meta:
        model = Medicine
        fields = ['name', 'category', 'quantity', 'price', 'expiry_date', 'minimum_stock']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Medicine Name'}),
            'category': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Tablet, Syrup, Antibiotic, Injection'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'minimum_stock': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }


class DispenseForm(forms.ModelForm):
    class Meta:
        model = Dispensing
        fields = ['medicine', 'patient', 'quantity', 'notes']
        widgets = {
            'medicine': forms.Select(attrs={'class': 'form-select', 'id': 'id_medicine'}),
            'patient': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'id': 'id_quantity'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Dosage / remarks (Optional)'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        medicine = cleaned_data.get('medicine')
        quantity = cleaned_data.get('quantity')
        if medicine and quantity:
            if quantity > medicine.quantity:
                self.add_error(
                    'quantity',
                    f"Insufficient stock! Available: {medicine.quantity} units, Requested: {quantity} units."
                )
        return cleaned_data
