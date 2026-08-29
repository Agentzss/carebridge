#!/usr/bin/env python3
"""
CareBridge Hospital Management System
Flask Web Application
"""

from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'carebridge-2025-secret'

# Constants
BASE_FEE = 100.0
LAB_RATE = 10.0
DISCOUNT = 0.30
MIN_DAYS = 7

# In-memory storage
patients = []
appointments = []


@app.route('/')
def index():
    return render_template('index.html',
                           patient_count=len(patients),
                           appt_count=len(appointments))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        age_str = request.form.get('age', '').strip()
        pid = request.form.get('patient_id', '').strip()

        errors = []
        if not name:
            errors.append('Name cannot be blank.')
        try:
            age = int(age_str)
            if age <= 0:
                errors.append('Age must be a positive number.')
        except ValueError:
            errors.append('Age must be a whole number.')
        if not pid:
            errors.append('Patient ID cannot be blank.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('register.html', name=name, age=age_str, pid=pid)

        patients.append({
            'name': name,
            'age': age,
            'id': pid,
            'registered': datetime.now().strftime('%d %b %Y, %H:%M')
        })
        flash(f'Patient "{name}" registered successfully!', 'success')
        return redirect(url_for('register'))

    return render_template('register.html')


@app.route('/appointment', methods=['GET', 'POST'])
def appointment():
    min_date = (datetime.now() + timedelta(days=MIN_DAYS)).strftime('%Y-%m-%d')

    if request.method == 'POST':
        dept = request.form.get('department', '').strip().upper()
        date_str = request.form.get('appt_date', '').strip()

        errors = []
        if dept not in ['GP', 'SPECIALIST']:
            errors.append('Invalid department. Choose GP or Specialist.')

        try:
            appt_date = datetime.strptime(date_str, '%Y-%m-%d')
            cutoff = datetime.now() + timedelta(days=MIN_DAYS)
            if appt_date.date() <= cutoff.date():
                errors.append(f'Date must be more than {MIN_DAYS} days from today.')
        except ValueError:
            errors.append('Invalid date format. Use YYYY-MM-DD.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('appointment.html', min_date=min_date,
                                   dept=dept, date_str=date_str)

        appointments.append({
            'department': dept,
            'date': date_str,
            'booked': datetime.now().strftime('%d %b %Y, %H:%M')
        })
        flash(f'Appointment booked for {dept} on {date_str}.', 'success')
        return redirect(url_for('appointment'))

    return render_template('appointment.html', min_date=min_date)


@app.route('/bill', methods=['GET', 'POST'])
def bill():
    result = None
    if request.method == 'POST':
        ptype = request.form.get('patient_type', '').strip().capitalize()
        tests_str = request.form.get('num_tests', '').strip()

        errors = []
        if ptype not in ['Subsidised', 'Private']:
            errors.append('Invalid type. Choose Subsidised or Private.')
        try:
            num_tests = int(tests_str)
            if num_tests < 0:
                errors.append('Number of tests cannot be negative.')
        except ValueError:
            errors.append('Number of tests must be a whole number.')

        if errors:
            for e in errors:
                flash(e, 'danger')
        else:
            subtotal = BASE_FEE + (num_tests * LAB_RATE)
            if ptype == 'Subsidised':
                total = subtotal * (1 - DISCOUNT)
                discount_amt = subtotal * DISCOUNT
            else:
                total = subtotal
                discount_amt = 0

            result = {
                'type': ptype,
                'tests': num_tests,
                'base': BASE_FEE,
                'lab_cost': num_tests * LAB_RATE,
                'subtotal': subtotal,
                'discount': discount_amt,
                'total': total
            }

    return render_template('bill.html', result=result)


@app.route('/triage', methods=['GET', 'POST'])
def triage():
    result = None
    if request.method == 'POST':
        sev_str = request.form.get('severity', '').strip()

        errors = []
        try:
            severity = int(sev_str)
            if severity < 1 or severity > 10:
                errors.append('Severity must be between 1 and 10.')
        except ValueError:
            errors.append('Severity must be a whole number between 1 and 10.')

        if errors:
            for e in errors:
                flash(e, 'danger')
        else:
            if 1 <= severity <= 4:
                room, priority, color = 'Waiting Room', 'Low', '#28a745'
            elif 5 <= severity <= 7:
                room, priority, color = 'Room 1', 'Medium', '#fd7e14'
            else:
                room, priority, color = 'Room 2', 'High', '#dc3545'

            result = {
                'severity': severity,
                'room': room,
                'priority': priority,
                'color': color
            }

    return render_template('triage.html', result=result)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
