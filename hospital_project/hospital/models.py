from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError


class Patient(models.Model):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    patient_id = models.CharField(max_length=20, unique=True, blank=True)
    name = models.CharField(max_length=150)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    registration_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-registration_date']

    def __str__(self):
        return f"{self.patient_id} - {self.name}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new and not self.patient_id:
            self.patient_id = f"PAT-{1000 + self.id}"
            super().save(update_fields=['patient_id'])


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class OPDToken(models.Model):
    STATUS_CHOICES = [
        ('Waiting', 'Waiting'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='opd_tokens')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='opd_tokens')
    token_number = models.PositiveIntegerField()
    date = models.DateField(default=timezone.localdate)
    registration_time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Waiting')
    doctor_name = models.CharField(max_length=100, blank=True, default='')
    notes = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['date', 'token_number']
        unique_together = ('department', 'date', 'token_number')

    def __str__(self):
        return f"Token #{self.token_number} - {self.department.name} ({self.patient.name})"

    def save(self, *args, **kwargs):
        if not self.date:
            self.date = timezone.localdate()
        if not self.token_number:
            latest_token = OPDToken.objects.filter(
                department=self.department,
                date=self.date
            ).order_by('-token_number').first()
            self.token_number = (latest_token.token_number + 1) if latest_token else 1
        super().save(*args, **kwargs)


class Bed(models.Model):
    CATEGORY_CHOICES = [
        ('General', 'General'),
        ('ICU', 'ICU'),
        ('Emergency', 'Emergency'),
        ('Private', 'Private'),
    ]

    STATUS_CHOICES = [
        ('Available', 'Available'),
        ('Occupied', 'Occupied'),
    ]

    bed_number = models.CharField(max_length=30, unique=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='General')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Available')
    daily_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    notes = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['bed_number']

    def __str__(self):
        return f"{self.bed_number} ({self.category}) - {self.status}"


class Admission(models.Model):
    STATUS_CHOICES = [
        ('Admitted', 'Admitted'),
        ('Discharged', 'Discharged'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='admissions')
    bed = models.ForeignKey(Bed, on_delete=models.CASCADE, related_name='admissions')
    admission_date = models.DateTimeField(auto_now_add=True)
    discharge_date = models.DateTimeField(null=True, blank=True)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Admitted')

    class Meta:
        ordering = ['-admission_date']

    def __str__(self):
        return f"Admission: {self.patient.name} - Bed {self.bed.bed_number} ({self.status})"

    def clean(self):
        if self.status == 'Admitted':
            # Check if bed is already occupied by another active admission
            occupied = Admission.objects.filter(
                bed=self.bed,
                status='Admitted'
            ).exclude(pk=self.pk).exists()
            if occupied or (self.bed.status == 'Occupied' and self.pk is None):
                raise ValidationError(f"Bed {self.bed.bed_number} is already occupied. Please select an available bed.")

    def save(self, *args, **kwargs):
        self.clean()
        if self.status == 'Admitted':
            self.bed.status = 'Occupied'
            self.bed.save()
        elif self.status == 'Discharged':
            if not self.discharge_date:
                self.discharge_date = timezone.now()
            self.bed.status = 'Available'
            self.bed.save()
        super().save(*args, **kwargs)


class Medicine(models.Model):
    name = models.CharField(max_length=150, unique=True)
    category = models.CharField(max_length=50)
    quantity = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    expiry_date = models.DateField()
    minimum_stock = models.PositiveIntegerField(default=10)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.quantity} in stock)"

    @property
    def is_low_stock(self):
        return self.quantity <= self.minimum_stock


class Dispensing(models.Model):
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='dispensings')
    patient = models.ForeignKey(Patient, on_delete=models.SET_NULL, null=True, blank=True, related_name='dispensings')
    quantity = models.PositiveIntegerField()
    dispensed_date = models.DateTimeField(auto_now_add=True)
    dispensed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-dispensed_date']

    def __str__(self):
        return f"Dispensed {self.quantity} of {self.medicine.name}"

    def clean(self):
        if self.pk is None and self.quantity > self.medicine.quantity:
            raise ValidationError(
                f"Cannot dispense {self.quantity} units. Only {self.medicine.quantity} units of {self.medicine.name} in stock."
            )

    def save(self, *args, **kwargs):
        self.clean()
        if self.pk is None:
            self.medicine.quantity -= self.quantity
            self.medicine.save()
        super().save(*args, **kwargs)
