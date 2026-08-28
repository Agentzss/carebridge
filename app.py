from flask import Flask, render_template, request
from datetime import datetime, timedelta
import calendar
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "carebridge-secret-key")

# ==================== SETTINGS ====================

CONSULTATION_FEE = 100.00
LAB_TEST_RATE = 10.00
SUBSIDISED_DISCOUNT = 0.30
MIN_APPOINTMENT_DAYS = 7

TIME_SLOTS = [
    "09:00 AM", "09:30 AM", "10:00 AM", "10:30 AM", "11:00 AM",
    "02:00 PM", "02:30 PM", "03:00 PM", "03:30 PM", "04:00 PM"
]

patients = []
appointments = []


# ==================== HELPERS ====================

def find_patient(patient_id):
    return next(
        (p for p in patients if p["patient_id"] == patient_id),
        None
    )


def get_available_slots(date_iso):
    booked = {
        a["time_slot"]
        for a in appointments
        if a["date_iso"] == date_iso
    }

    return [slot for slot in TIME_SLOTS if slot not in booked]


def generate_calendar(year, month):
    today = datetime.now().date()
    min_date = today + timedelta(days=MIN_APPOINTMENT_DAYS)

    weeks = []

    for week in calendar.Calendar().monthdayscalendar(year, month):
        week_data = []

        for day in week:
            if day == 0:
                week_data.append(None)
                continue

            date = datetime(year, month, day).date()
            date_iso = date.strftime("%Y-%m-%d")
            available = get_available_slots(date_iso)

            week_data.append({
                "day": day,
                "date_iso": date_iso,
                "date_display": date.strftime("%d/%m/%Y"),
                "is_valid": date >= min_date,
                "is_today": date == today,
                "is_past": date < today,
                "available_slots": available,
                "booked_slots": [
                    slot for slot in TIME_SLOTS
                    if slot not in available
                ],
                "is_full": not available
            })

        weeks.append(week_data)

    previous = datetime(year, month, 1) - timedelta(days=1)
    next_month = datetime(year, month, 28) + timedelta(days=4)

    return {
        "weeks": weeks,
        "month_name": calendar.month_name[month],
        "year": year,
        "prev_month": previous.month,
        "prev_year": previous.year,
        "next_month": next_month.month,
        "next_year": next_month.year
    }


# ==================== HOME ====================

@app.route("/")
def home():
    booked_patients = {a["patient_id"] for a in appointments}

    return render_template(
        "index.html",
        patient_count=len(patients),
        appt_count=len(appointments),
        booked_patients=len(booked_patients)
    )


# ==================== PATIENTS ====================

@app.route("/patients")
def view_patients():
    return render_template("patients.html", patients=patients)


# ==================== REGISTER ====================

@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    success = None

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        age = request.form.get("age", "").strip()
        patient_id = request.form.get("patient_id", "").strip()

        if not name:
            error = "Name cannot be blank."

        elif not age:
            error = "Age cannot be blank."

        else:
            try:
                age = int(age)

                if age <= 0:
                    error = "Age must be a positive number."

            except ValueError:
                error = "Age must be a whole number."

        if not error and not patient_id:
            error = "Patient ID cannot be blank."

        if not error and find_patient(patient_id):
            error = f"Patient ID '{patient_id}' already exists."

        if not error:
            patients.append({
                "name": name,
                "age": age,
                "patient_id": patient_id,
                "registered_at": datetime.now().strftime("%d/%m/%Y %H:%M")
            })

            success = f"Patient '{name}' registered successfully!"

    return render_template(
        "register.html",
        error=error,
        success=success
    )


# ==================== APPOINTMENTS ====================

@app.route("/book", methods=["GET", "POST"])
def book():
    error = None
    success = None

    try:
        year = int(request.args.get("year", datetime.now().year))
        month = int(request.args.get("month", datetime.now().month))

        if month < 1 or month > 12:
            raise ValueError

    except ValueError:
        year = datetime.now().year
        month = datetime.now().month

    if request.method == "POST":
        patient_id = request.form.get("patient_id", "").strip()
        department = request.form.get("department", "").strip().upper()
        date_iso = request.form.get("date_iso", "").strip()
        time_slot = request.form.get("time_slot", "").strip()

        patient = find_patient(patient_id)

        if not patient:
            error = "Please select a valid patient."

        elif department not in ["GP", "SPECIALIST"]:
            error = "Please select a valid department."

        elif time_slot not in TIME_SLOTS:
            error = "Please select a valid time slot."

        else:
            try:
                appointment_date = datetime.strptime(
                    date_iso, "%Y-%m-%d"
                ).date()

                minimum_date = (
                    datetime.now().date()
                    + timedelta(days=MIN_APPOINTMENT_DAYS)
                )

                if appointment_date < minimum_date:
                    error = (
                        f"Appointments must be at least "
                        f"{MIN_APPOINTMENT_DAYS} days in advance."
                    )

            except ValueError:
                error = "Invalid appointment date."

        if not error:
            available_slots = get_available_slots(date_iso)

            if time_slot not in available_slots:
                error = "That time slot is already booked."

        if not error:
            appointments.append({
                "patient_id": patient_id,
                "patient_name": patient["name"],
                "department": department,
                "date_iso": date_iso,
                "date_display": appointment_date.strftime("%d/%m/%Y"),
                "time_slot": time_slot,
                "booked_at": datetime.now().strftime("%d/%m/%Y %H:%M")
            })

            success = (
                f"Appointment booked for {patient['name']} "
                f"on {appointment_date.strftime('%d/%m/%Y')} "
                f"at {time_slot}."
            )

    return render_template(
        "appointment.html",
        error=error,
        success=success,
        patients=patients,
        time_slots=TIME_SLOTS,
        **generate_calendar(year, month)
    )


# ==================== BILLING ====================

@app.route("/bill", methods=["GET", "POST"])
def bill():
    error = None
    result = None

    if request.method == "POST":
        patient_type = request.form.get(
            "patient_type", ""
        ).strip().upper()

        tests = request.form.get("num_tests", "").strip()

        if patient_type not in ["SUBSIDISED", "PRIVATE"]:
            error = "Please select a valid patient type."

        else:
            try:
                tests = int(tests)

                if tests < 0:
                    error = "Number of tests cannot be negative."

            except ValueError:
                error = "Number of tests must be a whole number."

        if not error:
            lab_cost = tests * LAB_TEST_RATE
            subtotal = CONSULTATION_FEE + lab_cost

            discount = (
                subtotal * SUBSIDISED_DISCOUNT
                if patient_type == "SUBSIDISED"
                else 0
            )

            total = subtotal - discount

            result = {
                "type": patient_type.title(),
                "base_fee": CONSULTATION_FEE,
                "lab_cost": lab_cost,
                "num_tests": tests,
                "subtotal": subtotal,
                "discount": discount,
                "total": total
            }

    return render_template(
        "bill.html",
        error=error,
        result=result
    )


# ==================== TRIAGE ====================

@app.route("/triage", methods=["GET", "POST"])
def triage():
    error = None
    result = None

    if request.method == "POST":
        try:
            severity = int(
                request.form.get("severity", "").strip()
            )

            if severity < 1 or severity > 10:
                error = "Severity must be between 1 and 10."

            elif severity <= 4:
                result = {
                    "severity": severity,
                    "room": "Waiting Room",
                    "room_class": "waiting",
                    "room_icon": "🛋️",
                    "desc": "Non-urgent case. Monitor and reassess as needed."
                }

            elif severity <= 7:
                result = {
                    "severity": severity,
                    "room": "Room 1",
                    "room_class": "room1",
                    "room_icon": "🚪",
                    "desc": "Moderate urgency. Requires prompt attention."
                }

            else:
                result = {
                    "severity": severity,
                    "room": "Room 2",
                    "room_class": "room2",
                    "room_icon": "🚨",
                    "desc": "Critical condition. Immediate emergency care required."
                }

        except ValueError:
            error = "Severity must be a whole number."

    return render_template(
        "triage.html",
        error=error,
        result=result
    )


# ==================== RUN ====================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
