from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime, timedelta
import calendar

app = Flask(__name__)
app.secret_key = 'carebridge-secret-key-2025'

# ============ CONSTANTS ============
BASE_CONSULTATION_FEE = 100.00
LAB_TEST_RATE = 10.00
SUBSIDISED_DISCOUNT = 0.30
MIN_APPOINTMENT_DAYS = 7

TIME_SLOTS = [
    "09:00 AM", "09:30 AM", "10:00 AM", "10:30 AM", "11:00 AM",
    "02:00 PM", "02:30 PM", "03:00 PM", "03:30 PM", "04:00 PM"
]

# In-memory storage
patients = []
appointments = []

# ============ CALENDAR HELPER ============
def generate_calendar(year, month):
    """Generate calendar grid data for the booking page."""
    cal = calendar.Calendar()
    weeks = []
    today = datetime.now().date()
    min_date = today + timedelta(days=MIN_APPOINTMENT_DAYS)

    for week in cal.monthdayscalendar(year, month):
        week_data = []
        for day_num in week:
            if day_num == 0:
                week_data.append(None)
                continue

            date_obj = datetime(year, month, day_num).date()
            date_iso = date_obj.strftime('%Y-%m-%d')
            date_display = date_obj.strftime('%d/%m/%Y')

            # Check bookings for this date
            booked_slots = [a['time_slot'] for a in appointments if a['date_iso'] == date_iso]
            available_slots = [s for s in TIME_SLOTS if s not in booked_slots]

            week_data.append({
                'day': day_num,
                'date_iso': date_iso,
                'date_display': date_display,
                'is_valid': date_obj > min_date,
                'is_today': date_obj == today,
                'is_past': date_obj <= today,
                'available_slots': available_slots,
                'booked_slots': booked_slots,
                'is_full': len(available_slots) == 0
            })
        weeks.append(week_data)

    # Calculate prev/next month for navigation
    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1

    if month == 12:
        next_year, next_month = year + 1, 1
    else:
        next_year, next_month = year, month + 1

    return {
        'weeks': weeks,
        'month_name': calendar.month_name[month],
        'year': year,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year
    }

# ============ HOME / DASHBOARD ============
@app.route('/')
def home():
    # Count unique patients with appointments
    booked_patient_ids = set(a['patient_id'] for a in appointments)
    return render_template('index.html', 
                         patient_count=len(patients), 
                         appt_count=len(appointments),
                         booked_patients=len(booked_patient_ids))

# ============ VIEW PATIENTS ============
@app.route('/patients')
def view_patients():
    return render_template('patients.html', patients=patients)

# ============ REGISTER PATIENT ============
@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    success = None

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        age_str = request.form.get('age', '').strip()
        patient_id = request.form.get('patient_id', '').strip()

        if not name:
            error = "Name cannot be blank."
        elif not age_str:
            error = "Age cannot be blank."
        else:
            try:
                age = int(age_str)
                if age <= 0:
                    error = "Age must be a positive number."
            except ValueError:
                error = "Age must be a whole number."

        if not error and not patient_id:
            error = "Patient ID cannot be blank."

        # Check for duplicate patient ID
        if not error:
            for p in patients:
                if p['patient_id'] == patient_id:
                    error = f"Patient ID '{patient_id}' already exists."
                    break

        if not error:
            patients.append({
                'name': name, 
                'age': int(age_str), 
                'patient_id': patient_id,
                'registered_at': datetime.now().strftime('%d/%m/%Y %H:%M')
            })
            success = f"Patient '{name}' (ID: {patient_id}) registered successfully!"

    return render_template('register.html', error=error, success=success)

# ============ BOOK APPOINTMENT (WITH CALENDAR) ============
@app.route('/book', methods=['GET', 'POST'])
def book():
    error = None
    success = None

    # Get month/year from query params or default to current
    try:
        year = int(request.args.get('year', datetime.now().year))
        month = int(request.args.get('month', datetime.now().month))
    except ValueError:
        year = datetime.now().year
        month = datetime.now().month

    # Ensure month is valid
    if month < 1 or month > 12:
        month = datetime.now().month

    cal_data = generate_calendar(year, month)

    if request.method == 'POST':
        patient_id = request.form.get('patient_id', '').strip()
        department = request.form.get('department', '').strip().upper()
        date_iso = request.form.get('date_iso', '').strip()
        time_slot = request.form.get('time_slot', '').strip()

        # Validation
        if not patient_id:
            error = "Please select a patient."
        elif not any(p['patient_id'] == patient_id for p in patients):
            error = "Selected patient not found."
        elif department not in ['GP', 'SPECIALIST']:
            error = "Please select a valid department."
        elif not date_iso:
            error = "Please select a date from the calendar."
        elif not time_slot:
            error = "Please select a time slot."
        elif time_slot not in TIME_SLOTS:
            error = "Invalid time slot selected."
        else:
            # Check if slot is already booked
            existing = [a for a in appointments if a['date_iso'] == date_iso and a['time_slot'] == time_slot]
            if existing:
                error = f"Sorry, {time_slot} on {datetime.strptime(date_iso, '%Y-%m-%d').strftime('%d/%m/%Y')} is already booked. Please choose another slot."
            else:
                patient = next(p for p in patients if p['patient_id'] == patient_id)
                appointments.append({
                    'patient_id': patient_id,
                    'patient_name': patient['name'],
                    'department': department,
                    'date_iso': date_iso,
                    'date_display': datetime.strptime(date_iso, '%Y-%m-%d').strftime('%d/%m/%Y'),
                    'time_slot': time_slot,
                    'booked_at': datetime.now().strftime('%d/%m/%Y %H:%M')
                })
                success = f"Appointment booked for {patient['name']} — {department} on {datetime.strptime(date_iso, '%Y-%m-%d').strftime('%d/%m/%Y')} at {time_slot}"

    return render_template('appointment.html', 
                         error=error, 
                         success=success, 
                         patients=patients,
                         time_slots=TIME_SLOTS,
                         **cal_data)

# ============ CALCULATE BILL ============
@app.route('/bill', methods=['GET', 'POST'])
def bill():
    error = None
    result = None

    if request.method == 'POST':
        patient_type = request.form.get('patient_type', '').strip().upper()
        tests_str = request.form.get('num_tests', '').strip()

        valid_types = ['SUBSIDISED', 'PRIVATE']

        if patient_type not in valid_types:
            error = "Invalid patient type. Choose Subsidised or Private."
        else:
            try:
                num_tests = int(tests_str)
                if num_tests < 0:
                    error = "Number of tests cannot be negative."
                else:
                    subtotal = BASE_CONSULTATION_FEE + (num_tests * LAB_TEST_RATE)
                    total = subtotal * (1 - SUBSIDISED_DISCOUNT) if patient_type == 'SUBSIDISED' else subtotal

                    result = {
                        'type': patient_type.title(),
                        'base_fee': BASE_CONSULTATION_FEE,
                        'lab_cost': num_tests * LAB_TEST_RATE,
                        'num_tests': num_tests,
                        'subtotal': subtotal,
                        'discount': subtotal * SUBSIDISED_DISCOUNT if patient_type == 'SUBSIDISED' else 0,
                        'total': total
                    }
            except ValueError:
                error = "Number of tests must be a whole number."

    return render_template('bill.html', error=error, result=result)

# ============ ASSIGN TRIAGE ROOM ============
@app.route('/triage', methods=['GET', 'POST'])
def triage():
    error = None
    result = None

    if request.method == 'POST':
        severity_str = request.form.get('severity', '').strip()

        try:
            severity = int(severity_str)
            if severity < 1 or severity > 10:
                error = "Severity must be between 1 and 10."
            else:
                if 1 <= severity <= 4:
                    room = "Waiting Room"
                    room_class = "waiting"
                    room_icon = "🛋️"
                    desc = "Non-urgent cases. Monitor and reassess as needed."
                elif 5 <= severity <= 7:
                    room = "Room 1"
                    room_class = "room1"
                    room_icon = "🚪"
                    desc = "Moderate urgency. Requires prompt medical attention."
                else:
                    room = "Room 2"
                    room_class = "room2"
                    room_icon = "🚨"
                    desc = "Critical condition. Immediate emergency care required."

                result = {
                    'severity': severity, 
                    'room': room,
                    'room_class': room_class,
                    'room_icon': room_icon,
                    'desc': desc
                }
        except ValueError:
            error = "Severity must be a whole number."

    return render_template('triage.html', error=error, result=result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
