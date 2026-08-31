#!/usr/bin/env python3
"""
CareBridge Hospital Management System
Flask Web Application
"""

from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = 'carebridge-2026-secret'

# ============================================================
# Constants
# ============================================================

BASE_FEE = 100.0
LAB_RATE = 10.0
DISCOUNT = 0.30
MIN_DAYS = 7

# ============================================================
# In-memory storage
# ============================================================

patients = []
appointments = []


# ============================================================
# Home / Dashboard
# ============================================================

@app.route('/')
def index():
    return render_template(
        'index.html',
        patient_count=len(patients),
        appt_count=len(appointments),
        patients=patients,
        appointments=appointments
    )


# ============================================================
# Patient Registration
# ============================================================

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        name = request.form.get('name', '').strip().title()
        age_str = request.form.get('age', '').strip()
        pid = request.form.get('patient_id', '').strip().upper()

        errors = []

        # Validate name
        if not name:
            errors.append('Name cannot be blank.')

        # Validate age
        try:
            age = int(age_str)

            if age < 0 or age > 120:
                errors.append('Age must be between 0 and 120.')

        except ValueError:
            errors.append('Age must be a whole number.')

        # Validate Patient ID
        if not pid:
            errors.append('Patient ID cannot be blank.')

        elif any(patient['id'] == pid for patient in patients):
            errors.append(
                'Patient ID already exists. Please use a different ID.'
            )

        # Show errors
        if errors:

            for error in errors:
                flash(error, 'danger')

            return render_template(
                'register.html',
                name=name,
                age=age_str,
                pid=pid
            )

        # Register patient
        patients.append({
            'name': name,
            'age': age,
            'id': pid,
            'registered': datetime.now().strftime(
                '%d %b %Y, %H:%M'
            )
        })

        flash(
            f'Patient "{name}" registered successfully!',
            'success'
        )

        return redirect(url_for('register'))

    return render_template('register.html')


# ============================================================
# Appointment Booking
# ============================================================

@app.route('/appointment', methods=['GET', 'POST'])
def appointment():

    min_date = (
        datetime.now() + timedelta(days=MIN_DAYS)
    ).strftime('%Y-%m-%d')

    if request.method == 'POST':

        pid = request.form.get(
            'patient_id', ''
        ).strip().upper()

        dept = request.form.get(
            'department', ''
        ).strip().upper()

        date_str = request.form.get(
            'appt_date', ''
        ).strip()

        errors = []

        # Validate Patient ID
        if not pid:
            errors.append('Patient ID cannot be blank.')

        elif not any(
            patient['id'] == pid
            for patient in patients
        ):
            errors.append(
                'Patient ID does not exist. '
                'Please register the patient first.'
            )

        # Validate department
        if dept not in ['GP', 'SPECIALIST']:
            errors.append(
                'Invalid department. '
                'Choose GP or Specialist.'
            )

        # Validate date
        try:

            appt_date = datetime.strptime(
                date_str,
                '%Y-%m-%d'
            )

            cutoff = (
                datetime.now()
                + timedelta(days=MIN_DAYS)
            )

            if appt_date.date() <= cutoff.date():
                errors.append(
                    f'Date must be more than '
                    f'{MIN_DAYS} days from today.'
                )

        except ValueError:

            errors.append(
                'Invalid date format. '
                'Use YYYY-MM-DD.'
            )

        # Prevent duplicate appointment
        if any(
            appt['patient_id'] == pid
            and appt['date'] == date_str
            for appt in appointments
        ):
            errors.append(
                'This patient already has '
                'an appointment on this date.'
            )

        # Show errors
        if errors:

            for error in errors:
                flash(error, 'danger')

            return render_template(
                'appointment.html',
                min_date=min_date,
                pid=pid,
                dept=dept,
                date_str=date_str
            )

        # Book appointment
        appointments.append({
            'patient_id': pid,
            'department': dept,
            'date': date_str,
            'booked': datetime.now().strftime(
                '%d %b %Y, %H:%M'
            )
        })

        flash(
            f'Appointment booked for {dept} '
            f'on {date_str}.',
            'success'
        )

        return redirect(url_for('appointment'))

    return render_template(
        'appointment.html',
        min_date=min_date
    )


# ============================================================
# Billing
# ============================================================

@app.route('/bill', methods=['GET', 'POST'])
def bill():

    result = None

    if request.method == 'POST':

        ptype = request.form.get(
            'patient_type', ''
        ).strip().capitalize()

        tests_str = request.form.get(
            'num_tests', ''
        ).strip()

        errors = []

        # Validate patient type
        if ptype not in [
            'Subsidised',
            'Private'
        ]:
            errors.append(
                'Invalid type. '
                'Choose Subsidised or Private.'
            )

        # Validate number of tests
        try:

            num_tests = int(tests_str)

            if num_tests < 0 or num_tests > 50:
                errors.append(
                    'Number of tests must be '
                    'between 0 and 50.'
                )

        except ValueError:

            errors.append(
                'Number of tests must '
                'be a whole number.'
            )

        # Show errors
        if errors:

            for error in errors:
                flash(error, 'danger')

        else:

            # Calculate bill
            lab_cost = num_tests * LAB_RATE
            subtotal = BASE_FEE + lab_cost

            if ptype == 'Subsidised':

                discount_amt = subtotal * DISCOUNT
                total = subtotal - discount_amt

            else:

                discount_amt = 0.0
                total = subtotal

            # Store result
            result = {
                'type': ptype,
                'tests': num_tests,
                'base': round(BASE_FEE, 2),
                'lab_cost': round(lab_cost, 2),
                'subtotal': round(subtotal, 2),
                'discount': round(discount_amt, 2),
                'total': round(total, 2)
            }

    return render_template(
        'bill.html',
        result=result
    )


# ============================================================
# Triage
# ============================================================

@app.route('/triage', methods=['GET', 'POST'])
def triage():

    result = None

    if request.method == 'POST':

        sev_str = request.form.get(
            'severity', ''
        ).strip()

        errors = []

        # Validate severity
        try:

            severity = int(sev_str)

            if severity < 1 or severity > 10:
                errors.append(
                    'Severity must be between 1 and 10.'
                )

        except ValueError:

            errors.append(
                'Severity must be a whole number '
                'between 1 and 10.'
            )

        # Show errors
        if errors:

            for error in errors:
                flash(error, 'danger')

        else:

            # Triage decision
            if 1 <= severity <= 4:

                room = 'Waiting Room'
                priority = 'Low'
                color = '#28a745'

            elif 5 <= severity <= 7:

                room = 'Room 1'
                priority = 'Medium'
                color = '#fd7e14'

            else:

                room = 'Room 2'
                priority = 'High'
                color = '#dc3545'

            result = {
    'severity': severity,
    'room': room,
    'priority': priority,
    'color': color,
    'assessed_at': datetime.now().strftime('%d %b %Y, %H:%M')
}

    return render_template(
        'triage.html',
        result=result
    )


# ============================================================
# Run Application
# ============================================================

if __name__ == '__main__':

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
