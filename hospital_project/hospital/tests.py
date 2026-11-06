from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
from decimal import Decimal

from .models import Patient, Department, OPDToken, Bed, Admission, Medicine, Dispensing


class PatientTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='teststaff', password='password123')
        self.client = Client()
        self.client.login(username='teststaff', password='password123')

    def test_patient_creation_and_auto_id(self):
        patient = Patient.objects.create(
            name="John Doe",
            age=30,
            gender="Male",
            phone="1234567890",
            address="123 Elm St"
        )
        self.assertTrue(patient.patient_id.startswith("PAT-"))
        self.assertEqual(patient.name, "John Doe")

    def test_patient_search_and_filter(self):
        p1 = Patient.objects.create(name="Alice Walker", age=25, gender="Female", phone="9991112222", address="City A")
        p2 = Patient.objects.create(name="Bob Smith", age=40, gender="Male", phone="8882223333", address="City B")

        response = self.client.get(reverse('patient_list'), {'q': 'Alice'})
        self.assertContains(response, "Alice Walker")
        self.assertNotContains(response, "Bob Smith")

        response = self.client.get(reverse('patient_list'), {'gender': 'Male'})
        self.assertContains(response, "Bob Smith")


class OPDTokenTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='teststaff', password='password123')
        self.client = Client()
        self.client.login(username='teststaff', password='password123')

        self.patient1 = Patient.objects.create(name="P1", age=20, gender="Male", phone="111", address="Addr1")
        self.patient2 = Patient.objects.create(name="P2", age=25, gender="Female", phone="222", address="Addr2")
        self.dept1 = Department.objects.create(name="Cardiology")
        self.dept2 = Department.objects.create(name="Pediatrics")

    def test_daily_token_generation_per_department(self):
        today = timezone.localdate()
        token1 = OPDToken.objects.create(patient=self.patient1, department=self.dept1, date=today)
        self.assertEqual(token1.token_number, 1)

        token2 = OPDToken.objects.create(patient=self.patient2, department=self.dept1, date=today)
        self.assertEqual(token2.token_number, 2)

        # Different department should start at token 1
        token_dept2 = OPDToken.objects.create(patient=self.patient1, department=self.dept2, date=today)
        self.assertEqual(token_dept2.token_number, 1)

    def test_token_status_update(self):
        token = OPDToken.objects.create(patient=self.patient1, department=self.dept1)
        self.assertEqual(token.status, 'Waiting')

        response = self.client.post(reverse('opd_update_status', args=[token.pk]), {'status': 'In Progress'})
        token.refresh_from_db()
        self.assertEqual(token.status, 'In Progress')

        response = self.client.post(reverse('opd_update_status', args=[token.pk]), {'status': 'Completed'})
        token.refresh_from_db()
        self.assertEqual(token.status, 'Completed')


class BedAndAdmissionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='teststaff', password='password123')
        self.client = Client()
        self.client.login(username='teststaff', password='password123')

        self.patient1 = Patient.objects.create(name="Admit P1", age=50, gender="Male", phone="555", address="Addr")
        self.patient2 = Patient.objects.create(name="Admit P2", age=30, gender="Female", phone="666", address="Addr")
        self.bed1 = Bed.objects.create(bed_number="TEST-BED-01", category="General", status="Available")

    def test_admission_occupies_bed_and_prevents_double_booking(self):
        # Initial status
        self.assertEqual(self.bed1.status, 'Available')

        # Admit patient 1
        admission = Admission.objects.create(
            patient=self.patient1,
            bed=self.bed1,
            reason="High fever observation",
            status="Admitted"
        )
        self.bed1.refresh_from_db()
        self.assertEqual(self.bed1.status, 'Occupied')

        # Attempt to admit patient 2 to the same occupied bed
        with self.assertRaises(ValidationError):
            second_admission = Admission(
                patient=self.patient2,
                bed=self.bed1,
                reason="Fracture",
                status="Admitted"
            )
            second_admission.clean()

    def test_discharge_frees_bed(self):
        admission = Admission.objects.create(
            patient=self.patient1,
            bed=self.bed1,
            reason="Observation",
            status="Admitted"
        )
        self.bed1.refresh_from_db()
        self.assertEqual(self.bed1.status, 'Occupied')

        # Discharge via post view
        response = self.client.post(reverse('admission_discharge', args=[admission.pk]))
        admission.refresh_from_db()
        self.bed1.refresh_from_db()

        self.assertEqual(admission.status, 'Discharged')
        self.assertIsNotNone(admission.discharge_date)
        self.assertEqual(self.bed1.status, 'Available')


class MedicineAndDispensingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='teststaff', password='password123')
        self.client = Client()
        self.client.login(username='teststaff', password='password123')

        self.patient = Patient.objects.create(name="Pharmacy Patient", age=28, gender="Female", phone="777", address="X")
        self.med = Medicine.objects.create(
            name="Amoxicillin 250mg",
            category="Capsule",
            quantity=50,
            price=Decimal("5.00"),
            expiry_date=timezone.localdate() + timedelta(days=100),
            minimum_stock=10
        )

    def test_dispensing_reduces_stock(self):
        dispense = Dispensing.objects.create(
            medicine=self.med,
            patient=self.patient,
            quantity=15,
            dispensed_by=self.user
        )
        self.med.refresh_from_db()
        self.assertEqual(self.med.quantity, 35)

    def test_prevent_dispensing_more_than_stock(self):
        with self.assertRaises(ValidationError):
            dispense = Dispensing(
                medicine=self.med,
                patient=self.patient,
                quantity=100,  # exceeds available 50
                dispensed_by=self.user
            )
            dispense.clean()

    def test_low_stock_warning_trigger(self):
        self.assertFalse(self.med.is_low_stock)
        # Dispense enough to reach or drop below minimum_stock (10)
        Dispensing.objects.create(
            medicine=self.med,
            patient=self.patient,
            quantity=42,
            dispensed_by=self.user
        )
        self.med.refresh_from_db()
        self.assertEqual(self.med.quantity, 8)
        self.assertTrue(self.med.is_low_stock)


class AuthAndAccessTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_login_required_protection(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('login')))

    def test_admin_and_staff_login(self):
        admin = User.objects.create_superuser('adminuser', 'admin@hospital.test', 'adminpass')
        staff = User.objects.create_user('staffuser', 'staff@hospital.test', 'staffpass')

        # Test admin login
        resp = self.client.post(reverse('login'), {'username': 'adminuser', 'password': 'adminpass'})
        self.assertRedirects(resp, reverse('dashboard'))
        self.client.logout()

        # Test staff login
        resp = self.client.post(reverse('login'), {'username': 'staffuser', 'password': 'staffpass'})
        self.assertRedirects(resp, reverse('dashboard'))
