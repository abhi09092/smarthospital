# Smart Hospital Queue & Resource Management System

A lightweight, clean, and fully functional MVP built with **Django, SQLite, HTML5, CSS3, JavaScript, and Bootstrap 5**. Designed specifically for academic presentations and BTech project demonstrations.

---

## 🚀 Key Features

1. **Role-Based Authentication & Dashboard**:
   - Built-in Django authentication with two roles: **Admin** and **Staff**.
   - Real-time KPI summary cards: Total Patients, Today's OPD count, Available Beds, Occupied Beds, Total Medicines, Low-Stock Warnings.
   - Quick action shortcuts and live OPD/admission widgets.

2. **Patient Management**:
   - Register new patients with automatic Patient ID generation (`PAT-1001`, `PAT-1002`, ...).
   - Search patients by name, phone number, or patient ID.
   - Filter by gender.
   - Patient Profile view showing comprehensive medical history: past OPD visits, bed admissions, and dispensed medications.
   - Full CRUD support (Add, View, Edit, Delete).

3. **OPD Queue Management**:
   - Register patients for OPD consultations across departments (General Medicine, Cardiology, Orthopedics, Pediatrics, etc.).
   - Automatic daily sequential token numbers per department (`#1`, `#2`, ... resets daily).
   - Real-time queue tracker with statuses: `Waiting`, `In Progress`, `Completed`, `Cancelled`.
   - Fast one-click status transitions (Call Patient In & Mark Consultation Completed).

4. **Bed Availability & Admission**:
   - Visual ward layout with color coding (**Green** for Available, **Red** for Occupied).
   - Categories: `General`, `ICU`, `Emergency`, `Private`.
   - Prevents double-booking: occupied beds cannot be assigned to another patient.
   - Automatic bed status updates:
     - Admitting a patient marks the bed as `Occupied`.
     - Discharging a patient automatically sets the discharge timestamp and returns the bed to `Available`.

5. **Medicine & Basic Inventory**:
   - Inventory tracking: Name, Category, Stock Quantity, Price, Expiry Date, Minimum Stock Threshold.
   - Search by medicine name or category.
   - Filter by low-stock warnings (**Orange** alert badge when `quantity <= minimum_stock`).
   - Dispensing system: automatically deducts stock, prevents over-dispensing (cannot dispense more than available), and triggers immediate low-stock notifications.

---

## 🛠️ Technology Stack

- **Backend**: Python 3, Django 4.2 LTS
- **Database**: SQLite3 (`db.sqlite3`)
- **Frontend**: HTML5, CSS3, Bootstrap 5.3, Bootstrap Icons, Vanilla JavaScript
- **Security**: Django CSRF protection, `@login_required` route guards, input validation

---

## 👥 Demo User Credentials

| Role | Username | Password | Access Level |
|---|---|---|---|
| **Admin** | `admin` | `admin123` | Full administrative & clinical access |
| **Staff** | `staff` | `staff123` | Clinical & operational access |

---

## 📁 Project Directory Structure

```text
hospital_project/
├── manage.py
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── hospital/
│   ├── models.py          # Patient, Department, OPDToken, Bed, Admission, Medicine, Dispensing
│   ├── views.py           # Dashboard, Patient, OPD, Bed, Admission, Medicine views
│   ├── urls.py            # Route mappings
│   ├── forms.py           # Form definitions with validation
│   ├── admin.py           # Django Admin integration
│   ├── tests.py           # Unit tests
│   └── management/
│       └── commands/
│           └── seed_data.py # Demo data populator
├── templates/
│   ├── base.html          # Responsive base layout with navy sidebar & topbar
│   ├── login.html         # Login interface
│   ├── dashboard.html     # Real-time analytics & KPIs
│   ├── patients/          # list, form, detail, delete_confirm
│   ├── opd/               # queue, register
│   ├── beds/              # list, form
│   ├── admissions/        # list, admit, discharge_confirm
│   └── medicines/         # list, form, dispense, delete_confirm
├── static/
│   ├── css/custom.css     # Clean medical theme styling
│   └── js/main.js         # Interactive helpers
└── db.sqlite3             # Pre-seeded SQLite database
```

---

## 🏃 Running the Application

1. Open your terminal in the project directory:
   ```bash
   cd hospital_project
   ```

2. Run the development server (using your python environment):
   ```bash
   python3 manage.py runserver 8000
   ```
   *(Or using the project venv: `../.venv/bin/python manage.py runserver 8000`)*

3. Open your browser and navigate to:
   ```
   http://127.0.0.1:8000/
   ```

4. Log in using `admin` / `admin123` or `staff` / `staff123`.

---

## 🧪 Running Unit Tests

To run the automated test suite verifying all 11 core functional requirements:
```bash
python manage.py test
```
