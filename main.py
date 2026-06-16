import sqlite3
from flask import Flask, render_template, request, redirect, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = "student_management_secret_key"


# ---------------- LOGIN REQUIRED ----------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


# ---------------- HOME PAGE ----------------
@app.route("/")
@login_required
def home():
    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM students")
    total_students = cursor.fetchone()[0]

    cursor.execute("SELECT AVG(age) FROM students")
    avg_age = round(cursor.fetchone()[0] or 0)

    cursor.execute("SELECT MIN(age) FROM students")
    youngest = cursor.fetchone()[0] or 0

    cursor.execute("SELECT MAX(age) FROM students")
    oldest = cursor.fetchone()[0] or 0

    cursor.execute("SELECT age, COUNT(*) FROM students GROUP BY age")
    age_data = cursor.fetchall()

    cursor.execute("SELECT * FROM students ORDER BY id DESC LIMIT 5")
    recent_students = cursor.fetchall()

    conn.close()

    return render_template(
        "home.html",
        total_students=total_students,
        avg_age=avg_age,
        youngest=youngest,
        oldest=oldest,
        age_data=age_data,
        recent_students=recent_students
    )


# ---------------- ADD STUDENT ----------------
@app.route("/add_students", methods=["GET", "POST"])
@login_required
def add_students():
    if request.method == "POST":
        name = request.form["name"].strip()
        age = request.form["age"]

        conn = sqlite3.connect("students.db")
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO students (name, age) VALUES (?, ?)",
            (name, age)
        )

        conn.commit()
        conn.close()

        flash("Student Added Successfully!", "success")
        return redirect("/add_students")

    return render_template("add_students.html")


# ---------------- VIEW STUDENTS ----------------
@app.route("/view_students", methods=["GET", "POST"])
@login_required
def view_students():
    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()

    if request.method == "POST":
        keyword = request.form["keyword"]
        cursor.execute(
            "SELECT * FROM students WHERE name LIKE ?",
            ('%' + keyword + '%',)
        )
    else:
        cursor.execute("SELECT * FROM students")

    students = cursor.fetchall()
    conn.close()

    return render_template("view_students.html", students=students)


# ---------------- INIT DB ----------------
def init_db():
    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            age INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT
        )
    """)

    conn.commit()
    conn.close()


init_db()


# ---------------- EDIT STUDENT ----------------
@app.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_student(id):
    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students WHERE id = ?", (id,))
    student = cursor.fetchone()

    if request.method == "POST":
        name = request.form["name"]
        age = request.form["age"]

        cursor.execute("""
            UPDATE students
            SET name = ?, age = ?
            WHERE id = ?
        """, (name, age, id))

        conn.commit()
        conn.close()

        flash("Student Updated Successfully!", "warning")
        return redirect("/view_students")

    conn.close()
    return render_template("edit_student.html", student=student)


# ---------------- DELETE STUDENT ----------------
@app.route("/delete/<int:id>")
@login_required
def delete_student(id):
    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM students WHERE id = ?", (id,))

    conn.commit()
    conn.close()

    flash("Student Deleted Successfully!", "danger")
    return redirect("/view_students")


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("students.db")
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session["user"] = username
            return redirect("/")

        return "Invalid Credentials"

    return render_template("login.html")


# ---------------- SIGNUP ----------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        hashed_password = generate_password_hash(password)

        conn = sqlite3.connect("students.db")
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hashed_password)
        )

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("signup.html")


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")


# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run(debug=True)