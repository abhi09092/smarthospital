from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from hospital.models import Patient, Department, OPDToken, Bed, Admission, Medicine, Dispensing


class Command(BaseCommand):
    help = "Seed database with realistic demo data for college MVP presentation"

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding demo data...")

        # 1. Create Users
        admin_user, created = User.objects.get_or_create(username="admin")
        if created:
            admin_user.set_password("admin123")
            admin_user.is_superuser = True
            admin_user.is_staff = True
            admin_user.first_name = "Chief"
            admin_user.last_name = "Admin"
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Created Admin user: admin / admin123"))

        staff_user, created = User.objects.get_or_create(username="staff")
        if created:
            staff_user.set_password("staff123")
            staff_user.is_staff = True
            staff_user.first_name = "Clinical"
            staff_user.last_name = "Staff"
            staff_user.save()
            self.stdout.write(self.style.SUCCESS("Created Staff user: staff / staff123"))

        # 2. Departments
        depts_data = [
            ("General Medicine", "Primary healthcare, fever, diabetes, routine checkups"),
            ("Cardiology", "Heart health, ECG, blood pressure management"),
            ("Orthopedics", "Bone fractures, joint replacements, trauma care"),
            ("Pediatrics", "Child healthcare, newborn care, vaccination"),
            ("Dermatology", "Skin, hair, allergy and dermatological disorders"),
            ("Emergency & Trauma", "24/7 urgent critical triage and resuscitation"),
        ]
        dept_objs = {}
        for name, desc in depts_data:
            dept, _ = Department.objects.get_or_create(name=name, defaults={"description": desc})
            dept_objs[name] = dept

        # 3. Beds
        beds_data = [
            ("GEN-101", "General", Decimal("500.00"), "General Ward - Floor 1"),
            ("GEN-102", "General", Decimal("500.00"), "General Ward - Floor 1"),
            ("GEN-103", "General", Decimal("500.00"), "General Ward - Floor 1"),
            ("GEN-104", "General", Decimal("500.00"), "General Ward - Floor 1"),
            ("ICU-01", "ICU", Decimal("3500.00"), "Critical Care Unit - Bed with Ventilator"),
            ("ICU-02", "ICU", Decimal("3500.00"), "Critical Care Unit - Cardiac Monitor"),
            ("EMG-01", "Emergency", Decimal("800.00"), "Ground Floor Emergency Bay 1"),
            ("EMG-02", "Emergency", Decimal("800.00"), "Ground Floor Emergency Bay 2"),
            ("PVT-201", "Private", Decimal("2000.00"), "Deluxe Private Suite - Floor 2"),
            ("PVT-202", "Private", Decimal("2000.00"), "Single AC Room - Floor 2"),
        ]
        bed_objs = {}
        for bed_no, cat, charge, notes in beds_data:
            bed, _ = Bed.objects.get_or_create(
                bed_number=bed_no,
                defaults={"category": cat, "status": "Available", "daily_charge": charge, "notes": notes}
            )
            # Ensure fresh seed starts with Available before admissions are created
            bed.status = "Available"
            bed.save()
            bed_objs[bed_no] = bed

        # 4. Patients
        patients_data = [
            ("PAT-1001", "Rahul Sharma", 34, "Male", "+91 9876543210", "Flat 4B, Green Meadows, Civil Lines"),
            ("PAT-1002", "Priya Verma", 28, "Female", "+91 9811223344", "12/A, Model Town, Central District"),
            ("PAT-1003", "Amitabh Sen", 62, "Male", "+91 9723456789", "B-203, Heritage Heights, Old City"),
            ("PAT-1004", "Sunita Devi", 45, "Female", "+91 9456123789", "Village Rampur, Post Office Road"),
            ("PAT-1005", "Aarav Patel", 8, "Male", "+91 9822334455", "304, Sunshine Residency, Ring Road"),
            ("PAT-1006", "Meera Nair", 52, "Female", "+91 9988776655", "Plot 18, Lakeview Enclave, Sector 5"),
        ]
        patient_objs = {}
        for pid, name, age, gender, phone, addr in patients_data:
            patient, created = Patient.objects.get_or_create(
                patient_id=pid,
                defaults={
                    "name": name,
                    "age": age,
                    "gender": gender,
                    "phone": phone,
                    "address": addr,
                }
            )
            patient_objs[pid] = patient

        # 5. OPD Tokens for today
        today = timezone.localdate()
        tokens_data = [
            (patient_objs["PAT-1001"], dept_objs["General Medicine"], 1, "Waiting", "Dr. A. K. Gupta", "Mild fever & headache"),
            (patient_objs["PAT-1002"], dept_objs["General Medicine"], 2, "In Progress", "Dr. A. K. Gupta", "Routine health screening"),
            (patient_objs["PAT-1005"], dept_objs["Pediatrics"], 1, "Completed", "Dr. Shalini Mehta", "Seasonal allergy and cold"),
            (patient_objs["PAT-1004"], dept_objs["Orthopedics"], 1, "Waiting", "Dr. R. K. Singhal", "Knee joint stiffness"),
            (patient_objs["PAT-1006"], dept_objs["Cardiology"], 1, "Waiting", "Dr. Vikram Seth", "Blood pressure checkup"),
        ]
        for pat, dept, tok_num, status, doc, notes in tokens_data:
            OPDToken.objects.get_or_create(
                department=dept,
                date=today,
                token_number=tok_num,
                defaults={
                    "patient": pat,
                    "status": status,
                    "doctor_name": doc,
                    "notes": notes,
                }
            )

        # 6. Admissions (match occupied beds)
        now = timezone.now()
        # Active: GEN-103 -> Amitabh Sen
        if not Admission.objects.filter(bed=bed_objs["GEN-103"], status="Admitted").exists():
            Admission.objects.create(
                patient=patient_objs["PAT-1003"],
                bed=bed_objs["GEN-103"],
                reason="Severe pneumonia, requires IV antibiotics and observation",
                status="Admitted",
            )
        # Active: ICU-01 -> Sunita Devi
        if not Admission.objects.filter(bed=bed_objs["ICU-01"], status="Admitted").exists():
            Admission.objects.create(
                patient=patient_objs["PAT-1004"],
                bed=bed_objs["ICU-01"],
                reason="Acute respiratory distress syndrome, continuous oxygen support",
                status="Admitted",
            )
        # Active: PVT-202 -> Meera Nair
        if not Admission.objects.filter(bed=bed_objs["PVT-202"], status="Admitted").exists():
            Admission.objects.create(
                patient=patient_objs["PAT-1006"],
                bed=bed_objs["PVT-202"],
                reason="Post-operative observation following elective laparoscopic surgery",
                status="Admitted",
            )
        # Past Discharged Admission: GEN-101 -> Rahul Sharma
        if not Admission.objects.filter(patient=patient_objs["PAT-1001"], status="Discharged").exists():
            adm = Admission.objects.create(
                patient=patient_objs["PAT-1001"],
                bed=bed_objs["GEN-101"],
                reason="Viral gastroenteritis dehydration",
                status="Discharged",
                discharge_date=now - timedelta(days=5),
            )
            # make sure GEN-101 stays Available
            bed_objs["GEN-101"].status = "Available"
            bed_objs["GEN-101"].save()

        # 7. Medicines (mix of normal and low stock)
        medicines_data = [
            ("Paracetamol 500mg", "Tablet", 120, Decimal("2.50"), today + timedelta(days=365), 25),
            ("Amoxicillin 500mg", "Capsule", 85, Decimal("8.00"), today + timedelta(days=280), 20),
            ("Azithromycin 250mg", "Tablet", 12, Decimal("15.00"), today + timedelta(days=190), 15), # Low stock
            ("Cetirizine 10mg", "Tablet", 9, Decimal("3.00"), today + timedelta(days=400), 20),      # Low stock
            ("Cough Syrup 100ml", "Syrup", 40, Decimal("65.00"), today + timedelta(days=210), 10),
            ("Insulin Glargine 100IU", "Injection", 4, Decimal("450.00"), today + timedelta(days=120), 10), # Low stock
            ("Pantoprazole 40mg", "Tablet", 150, Decimal("7.50"), today + timedelta(days=500), 30),
            ("Oral Rehydration Salts (ORS)", "Sachet", 80, Decimal("18.00"), today + timedelta(days=300), 25),
        ]
        med_objs = {}
        for name, cat, qty, price, exp, min_stk in medicines_data:
            med, _ = Medicine.objects.get_or_create(
                name=name,
                defaults={
                    "category": cat,
                    "quantity": qty,
                    "price": price,
                    "expiry_date": exp,
                    "minimum_stock": min_stk,
                }
            )
            med_objs[name] = med

        # 8. Dispensing log
        if not Dispensing.objects.exists():
            Dispensing.objects.create(
                medicine=med_objs["Paracetamol 500mg"],
                patient=patient_objs["PAT-1001"],
                quantity=10,
                dispensed_by=staff_user,
                notes="1 tablet thrice daily after food for fever",
            )
            Dispensing.objects.create(
                medicine=med_objs["Cough Syrup 100ml"],
                patient=patient_objs["PAT-1005"],
                quantity=1,
                dispensed_by=staff_user,
                notes="5ml twice daily for pediatric cough",
            )

        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully!"))
