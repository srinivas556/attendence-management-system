# Smart Attendance Management System

A role-based Flask + SQLite attendance management application with separate Faculty and Student modules.

## Features

### Faculty
- Faculty login
- Dashboard statistics
- Add/delete students
- Create/update daily attendance
- Attendance history
- Individual student attendance percentage

### Student
- Student login using roll number and password
- Personal dashboard
- Overall attendance percentage
- Present/absent counts
- Personal attendance history
- Students cannot modify attendance

## Tech Stack
Python, Flask, SQLite, HTML, CSS, JavaScript

## Demo Accounts

Faculty:
- Username: `admin`
- Password: `admin123`

Students:
- Roll Number: `CSE001`
- Password: `student123`

Other demo students: `CSE002`, `CSE003`, same password.

## Run on Windows CMD

```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`

## Important

This is an educational portfolio project. Passwords are intentionally simple for local demonstration; a production system should use password hashing, CSRF protection, stronger session configuration, and a proper authentication strategy.

## Render Deployment

Build command: `pip install -r requirements.txt`

Start command: `gunicorn app:app`
