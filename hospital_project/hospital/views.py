from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, F

from .models import Patient, Department, OPDToken, Bed, Admission, Medicine, Dispensing
from .forms import (
    LoginForm,
    PatientForm,
    OPDRegistrationForm,
    BedForm,
    AdmissionForm,
    MedicineForm,
    DispenseForm,
)


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('login')


@login_required
def dashboard_view(request):
    today = timezone.localdate()

    total_patients = Patient.objects.count()
    today_opd_count = OPDToken.objects.filter(date=today).count()
    available_beds = Bed.objects.filter(status='Available').count()
    occupied_beds = Bed.objects.filter(status='Occupied').count()
    total_medicines = Medicine.objects.count()
    low_stock_medicines_qs = Medicine.objects.filter(quantity__lte=F('minimum_stock'))
    low_stock_count = low_stock_medicines_qs.count()

    # Active queues for today
    today_tokens = OPDToken.objects.filter(date=today).select_related('patient', 'department').order_by('department', 'token_number')[:10]
    # Active admitted patients
    active_admissions = Admission.objects.filter(status='Admitted').select_related('patient', 'bed').order_by('-admission_date')[:5]
    # Low stock items for alert panel
    low_stock_items = low_stock_medicines_qs[:5]

    context = {
        'total_patients': total_patients,
        'today_opd_count': today_opd_count,
        'available_beds': available_beds,
        'occupied_beds': occupied_beds,
        'total_medicines': total_medicines,
        'low_stock_count': low_stock_count,
        'today_tokens': today_tokens,
        'active_admissions': active_admissions,
        'low_stock_items': low_stock_items,
        'today': today,
    }
    return render(request, 'dashboard.html', context)


# --- Patient Management ---

@login_required
def patient_list(request):
    query = request.GET.get('q', '').strip()
    gender = request.GET.get('gender', '').strip()

    patients = Patient.objects.all()
    if query:
        patients = patients.filter(
            Q(name__icontains=query) |
            Q(patient_id__icontains=query) |
            Q(phone__icontains=query)
        )
    if gender:
        patients = patients.filter(gender=gender)

    context = {
        'patients': patients,
        'query': query,
        'gender': gender,
    }
    return render(request, 'patients/list.html', context)


@login_required
def patient_detail(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    opd_history = patient.opd_tokens.select_related('department').order_by('-date', '-token_number')
    admissions_history = patient.admissions.select_related('bed').order_by('-admission_date')
    dispensed_history = patient.dispensings.select_related('medicine').order_by('-dispensed_date')

    context = {
        'patient': patient,
        'opd_history': opd_history,
        'admissions_history': admissions_history,
        'dispensed_history': dispensed_history,
    }
    return render(request, 'patients/detail.html', context)


@login_required
def patient_add(request):
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            patient = form.save()
            messages.success(request, f"Patient {patient.name} ({patient.patient_id}) registered successfully!")
            return redirect('patient_list')
    else:
        form = PatientForm()
    return render(request, 'patients/form.html', {'form': form, 'title': 'Register New Patient'})


@login_required
def patient_edit(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == 'POST':
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, f"Patient {patient.name} details updated successfully!")
            return redirect('patient_detail', pk=patient.pk)
    else:
        form = PatientForm(instance=patient)
    return render(request, 'patients/form.html', {'form': form, 'title': f'Edit Patient - {patient.name}', 'patient': patient})


@login_required
def patient_delete(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == 'POST':
        name = patient.name
        patient.delete()
        messages.success(request, f"Patient {name} has been deleted.")
        return redirect('patient_list')
    return render(request, 'patients/delete_confirm.html', {'patient': patient})


# --- OPD Queue Management ---

@login_required
def opd_queue(request):
    today = timezone.localdate()
    dept_id = request.GET.get('department', '')
    status_filter = request.GET.get('status', '')

    tokens = OPDToken.objects.filter(date=today).select_related('patient', 'department')

    if dept_id:
        tokens = tokens.filter(department_id=dept_id)
    if status_filter:
        tokens = tokens.filter(status=status_filter)

    departments = Department.objects.all()
    waiting_count = OPDToken.objects.filter(date=today, status='Waiting').count()
    in_progress_count = OPDToken.objects.filter(date=today, status='In Progress').count()
    completed_count = OPDToken.objects.filter(date=today, status='Completed').count()

    context = {
        'tokens': tokens,
        'departments': departments,
        'today': today,
        'selected_dept': dept_id,
        'selected_status': status_filter,
        'waiting_count': waiting_count,
        'in_progress_count': in_progress_count,
        'completed_count': completed_count,
    }
    return render(request, 'opd/queue.html', context)


@login_required
def opd_register(request):
    if request.method == 'POST':
        form = OPDRegistrationForm(request.POST)
        if form.is_valid():
            token = form.save(commit=False)
            token.date = timezone.localdate()
            token.save()
            messages.success(
                request,
                f"Token #{token.token_number} generated for {token.patient.name} in {token.department.name}!"
            )
            return redirect('opd_queue')
    else:
        initial_patient = request.GET.get('patient')
        form = OPDRegistrationForm(initial={'patient': initial_patient} if initial_patient else None)

    return render(request, 'opd/register.html', {'form': form})


@login_required
def opd_update_status(request, pk):
    token = get_object_or_404(OPDToken, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(OPDToken.STATUS_CHOICES):
            token.status = new_status
            token.save()
            messages.success(request, f"Token #{token.token_number} status updated to {new_status}.")
        else:
            messages.error(request, "Invalid status.")
    return redirect('opd_queue')


# --- Bed Availability & Admission ---

@login_required
def bed_list(request):
    category = request.GET.get('category', '')
    status = request.GET.get('status', '')

    beds = Bed.objects.all()
    if category:
        beds = beds.filter(category=category)
    if status:
        beds = beds.filter(status=status)

    total_beds = Bed.objects.count()
    available_count = Bed.objects.filter(status='Available').count()
    occupied_count = Bed.objects.filter(status='Occupied').count()

    context = {
        'beds': beds,
        'total_beds': total_beds,
        'available_count': available_count,
        'occupied_count': occupied_count,
        'selected_category': category,
        'selected_status': status,
        'categories': Bed.CATEGORY_CHOICES,
    }
    return render(request, 'beds/list.html', context)


@login_required
def bed_add(request):
    if request.method == 'POST':
        form = BedForm(request.POST)
        if form.is_valid():
            bed = form.save()
            messages.success(request, f"Bed {bed.bed_number} ({bed.category}) added successfully!")
            return redirect('bed_list')
    else:
        form = BedForm()
    return render(request, 'beds/form.html', {'form': form, 'title': 'Add New Bed'})


@login_required
def admission_list(request):
    status = request.GET.get('status', '')
    admissions = Admission.objects.select_related('patient', 'bed').all()
    if status:
        admissions = admissions.filter(status=status)

    active_count = Admission.objects.filter(status='Admitted').count()
    discharged_count = Admission.objects.filter(status='Discharged').count()

    context = {
        'admissions': admissions,
        'selected_status': status,
        'active_count': active_count,
        'discharged_count': discharged_count,
    }
    return render(request, 'admissions/list.html', context)


@login_required
def admission_create(request):
    if request.method == 'POST':
        form = AdmissionForm(request.POST)
        if form.is_valid():
            try:
                admission = form.save()
                messages.success(
                    request,
                    f"Patient {admission.patient.name} admitted to Bed {admission.bed.bed_number} successfully!"
                )
                return redirect('admission_list')
            except Exception as e:
                messages.error(request, str(e))
    else:
        initial_patient = request.GET.get('patient')
        form = AdmissionForm(initial={'patient': initial_patient} if initial_patient else None)

    return render(request, 'admissions/admit.html', {'form': form})


@login_required
def admission_discharge(request, pk):
    admission = get_object_or_404(Admission, pk=pk)
    if request.method == 'POST':
        if admission.status == 'Admitted':
            admission.status = 'Discharged'
            admission.discharge_date = timezone.now()
            admission.save()
            messages.success(
                request,
                f"Patient {admission.patient.name} discharged. Bed {admission.bed.bed_number} is now Available."
            )
        else:
            messages.warning(request, "Patient is already discharged.")
        return redirect('admission_list')
    return render(request, 'admissions/discharge_confirm.html', {'admission': admission})


# --- Medicine & Inventory Management ---

@login_required
def medicine_list(request):
    query = request.GET.get('q', '').strip()
    filter_low_stock = request.GET.get('low_stock', '')

    medicines = Medicine.objects.all()
    if query:
        medicines = medicines.filter(
            Q(name__icontains=query) | Q(category__icontains=query)
        )
    if filter_low_stock == '1':
        medicines = medicines.filter(quantity__lte=F('minimum_stock'))

    total_count = Medicine.objects.count()
    low_stock_count = Medicine.objects.filter(quantity__lte=F('minimum_stock')).count()

    context = {
        'medicines': medicines,
        'query': query,
        'filter_low_stock': filter_low_stock,
        'total_count': total_count,
        'low_stock_count': low_stock_count,
    }
    return render(request, 'medicines/list.html', context)


@login_required
def medicine_add(request):
    if request.method == 'POST':
        form = MedicineForm(request.POST)
        if form.is_valid():
            med = form.save()
            messages.success(request, f"Medicine '{med.name}' added to inventory!")
            return redirect('medicine_list')
    else:
        form = MedicineForm()
    return render(request, 'medicines/form.html', {'form': form, 'title': 'Add New Medicine'})


@login_required
def medicine_edit(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)
    if request.method == 'POST':
        form = MedicineForm(request.POST, instance=medicine)
        if form.is_valid():
            form.save()
            messages.success(request, f"Medicine '{medicine.name}' updated successfully!")
            return redirect('medicine_list')
    else:
        form = MedicineForm(instance=medicine)
    return render(request, 'medicines/form.html', {'form': form, 'title': f'Edit Medicine - {medicine.name}', 'medicine': medicine})


@login_required
def medicine_delete(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)
    if request.method == 'POST':
        name = medicine.name
        medicine.delete()
        messages.success(request, f"Medicine '{name}' removed from inventory.")
        return redirect('medicine_list')
    return render(request, 'medicines/delete_confirm.html', {'medicine': medicine})


@login_required
def medicine_dispense(request):
    if request.method == 'POST':
        form = DispenseForm(request.POST)
        if form.is_valid():
            dispense = form.save(commit=False)
            dispense.dispensed_by = request.user
            dispense.save()

            messages.success(
                request,
                f"Successfully dispensed {dispense.quantity} units of {dispense.medicine.name}. Remaining stock: {dispense.medicine.quantity}."
            )

            # Check for low-stock warning immediately
            if dispense.medicine.is_low_stock:
                messages.warning(
                    request,
                    f"Warning: Low stock alert! {dispense.medicine.name} has only {dispense.medicine.quantity} units remaining (Minimum threshold: {dispense.medicine.minimum_stock})."
                )

            return redirect('medicine_list')
    else:
        initial_med = request.GET.get('medicine')
        form = DispenseForm(initial={'medicine': initial_med} if initial_med else None)

    medicines = Medicine.objects.all()
    return render(request, 'medicines/dispense.html', {'form': form, 'medicines': medicines})
