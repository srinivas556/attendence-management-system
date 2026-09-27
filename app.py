from flask import Flask, render_template, request, redirect, url_for, session, flash
from database import init_db, get_db
from functools import wraps
from datetime import date

app = Flask(__name__)
app.secret_key = "change-this-secret-key"
init_db()

def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("login"))
            if role and session.get("role") != role:
                flash("You do not have permission to access that page.", "error")
                return redirect(url_for("dashboard"))
            return f(*args, **kwargs)
        return wrapped
    return decorator

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login_id = request.form["login_id"].strip()
        password = request.form["password"].strip()
        role = request.form["role"]
        db = get_db()
        if role == "Faculty":
            user = db.execute(
                "SELECT id, username, role FROM users WHERE username=? AND password=?",
                (login_id, password)
            ).fetchone()
            if user:
                session.update(user_id=user["id"], username=user["username"], role="Faculty")
                db.close()
                return redirect(url_for("dashboard"))
        else:
            student = db.execute(
                "SELECT id, name, roll_number FROM students WHERE roll_number=? AND password=?",
                (login_id, password)
            ).fetchone()
            if student:
                session.update(user_id=student["id"], username=student["roll_number"],
                               role="Student", student_id=student["id"], student_name=student["name"])
                db.close()
                return redirect(url_for("student_dashboard"))
        db.close()
        flash("Invalid credentials.", "error")
    return render_template("login.html")

@app.route("/dashboard")
@login_required("Faculty")
def dashboard():
    db = get_db()
    total_students = db.execute("SELECT COUNT(*) c FROM students").fetchone()["c"]
    today_present = db.execute("SELECT COUNT(*) c FROM attendance WHERE date=? AND status='Present'", (str(date.today()),)).fetchone()["c"]
    today_absent = db.execute("SELECT COUNT(*) c FROM attendance WHERE date=? AND status='Absent'", (str(date.today()),)).fetchone()["c"]
    total_records = db.execute("SELECT COUNT(*) c FROM attendance").fetchone()["c"]
    present_records = db.execute("SELECT COUNT(*) c FROM attendance WHERE status='Present'").fetchone()["c"]
    overall = round(present_records / total_records * 100, 1) if total_records else 0
    recent = db.execute("""SELECT a.date,s.roll_number,s.name,a.status FROM attendance a
                           JOIN students s ON s.id=a.student_id
                           ORDER BY a.date DESC,a.id DESC LIMIT 8""").fetchall()
    db.close()
    return render_template("dashboard.html", total_students=total_students,
                           today_present=today_present, today_absent=today_absent,
                           overall=overall, recent=recent)

@app.route("/students", methods=["GET", "POST"])
@login_required("Faculty")
def students():
    db = get_db()
    if request.method == "POST":
        name=request.form["name"].strip()
        roll=request.form["roll_number"].strip()
        email=request.form["email"].strip()
        department=request.form["department"].strip()
        password=request.form["password"].strip()
        if not name or not roll or not password:
            flash("Name, roll number and password are required.", "error")
        else:
            try:
                db.execute("""INSERT INTO students(name,roll_number,email,department,password)
                              VALUES(?,?,?,?,?)""",(name,roll,email,department,password))
                db.commit()
                flash("Student added successfully.", "success")
            except Exception:
                flash("Roll number already exists.", "error")
    students=db.execute("SELECT id,name,roll_number,email,department FROM students ORDER BY roll_number").fetchall()
    db.close()
    return render_template("students.html", students=students)

@app.post("/students/delete/<int:student_id>")
@login_required("Faculty")
def delete_student(student_id):
    db=get_db()
    db.execute("DELETE FROM attendance WHERE student_id=?",(student_id,))
    db.execute("DELETE FROM students WHERE id=?",(student_id,))
    db.commit(); db.close()
    flash("Student deleted.","success")
    return redirect(url_for("students"))

@app.route("/attendance", methods=["GET","POST"])
@login_required("Faculty")
def attendance():
    db=get_db()
    selected_date=request.form.get("date") or request.args.get("date") or str(date.today())
    students=db.execute("SELECT * FROM students ORDER BY roll_number").fetchall()
    if request.method=="POST" and request.form.get("action")=="save":
        for student in students:
            status=request.form.get(f"status_{student['id']}","Absent")
            existing=db.execute("SELECT id FROM attendance WHERE student_id=? AND date=?",
                                (student["id"],selected_date)).fetchone()
            if existing:
                db.execute("UPDATE attendance SET status=? WHERE id=?",(status,existing["id"]))
            else:
                db.execute("INSERT INTO attendance(student_id,date,status) VALUES(?,?,?)",
                           (student["id"],selected_date,status))
        db.commit(); db.close()
        flash("Attendance saved successfully.","success")
        return redirect(url_for("attendance",date=selected_date))
    existing=db.execute("SELECT student_id,status FROM attendance WHERE date=?",(selected_date,)).fetchall()
    status_map={r["student_id"]:r["status"] for r in existing}
    db.close()
    return render_template("attendance.html",students=students,selected_date=selected_date,status_map=status_map)

@app.route("/history")
@login_required("Faculty")
def history():
    db=get_db()
    records=db.execute("""SELECT a.date,s.roll_number,s.name,s.department,a.status
                          FROM attendance a JOIN students s ON s.id=a.student_id
                          ORDER BY a.date DESC,s.roll_number""").fetchall()
    db.close()
    return render_template("history.html",records=records)

@app.route("/student/<int:student_id>")
@login_required("Faculty")
def student_detail(student_id):
    db=get_db()
    student=db.execute("SELECT id,name,roll_number,email,department FROM students WHERE id=?",(student_id,)).fetchone()
    records=db.execute("SELECT date,status FROM attendance WHERE student_id=? ORDER BY date DESC",(student_id,)).fetchall()
    db.close()
    if not student: return "Student not found",404
    total=len(records); present=sum(1 for r in records if r["status"]=="Present")
    percentage=round(present/total*100,1) if total else 0
    return render_template("student_detail.html",student=student,records=records,
                           percentage=percentage,present=present,total=total)

@app.route("/student-dashboard")
@login_required("Student")
def student_dashboard():
    sid=session["student_id"]; db=get_db()
    student=db.execute("SELECT id,name,roll_number,email,department FROM students WHERE id=?",(sid,)).fetchone()
    records=db.execute("SELECT date,status FROM attendance WHERE student_id=? ORDER BY date DESC",(sid,)).fetchall()
    db.close()
    total=len(records); present=sum(1 for r in records if r["status"]=="Present")
    absent=total-present
    percentage=round(present/total*100,1) if total else 0
    return render_template("student_dashboard.html",student=student,records=records,
                           total=total,present=present,absent=absent,percentage=percentage)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__=="__main__":
    app.run(debug=True)
