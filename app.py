import sqlite3
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS  # Added for CORS support

app = Flask(__name__)
CORS(app)  # Enables CORS for all routes and origins


# Database Connection
def get_db_connection():
    conn = sqlite3.connect("students.db")
    conn.row_factory = sqlite3.Row
    return conn


# Home Page
@app.route("/")
def home():
    return render_template("index.html")


# API Endpoint
@app.route("/api")
def api():
    return "Welcome to my first API!"


# Student Information Endpoint
@app.route("/student")
def student():
    return jsonify({
        "id": "24-0087",
        "name": "Kc Jane Marie Ladoing",
        "program": "BSIT",
        "year": 3,
        "section": "B",
    })


# Greeting Endpoint
@app.route("/hello")
def hello():
    name = request.args.get("name", "student")
    return jsonify({"message": f"hello {name}"})


# Course Information Endpoint
@app.route("/course")
def course():
    return jsonify({
        "course": "Bachelor of Science in Information Technology",
        "program": "BSIT",
        "year": 3,
        "section": "B",
        "description": (
            "A program focused on information technology, programming, and"
            " computer systems."
        ),
    })


# Get All Students (Supports both /students and /api/students)
@app.route("/students")
@app.route("/api/students", methods=["GET"])
def students():
    conn = get_db_connection()
    try:
        students_data = conn.execute("SELECT * FROM students").fetchall()
        students_list = [dict(student) for student in students_data]
        return jsonify(students_list)
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


# CREATE: Add Student Endpoint (/api/students)
@app.route("/api/students", methods=["POST"])
def add_student():
    data = request.get_json()
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            """INSERT INTO students
            (student_id, name, program, year, section)
            VALUES (?, ?, ?, ?, ?)""",
            (
                data.get("student_id"),
                data.get("name"),
                data.get("program"),
                data.get("year"),
                data.get("section"),
            ),
        )
        conn.commit()
        new_id = cursor.lastrowid
        return jsonify({"message": "Student added", "id": new_id}), 201
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


# Get Student by ID (Database ID)
@app.route("/students/<int:id>")
@app.route("/api/students/<int:id>", methods=["GET"])
def get_student_by_id(id):
    conn = get_db_connection()
    try:
        student = conn.execute(
            "SELECT * FROM students WHERE id = ?", (id,)
        ).fetchone()
        if student is None:
            return jsonify({"error": "Student not found"}), 404
        return jsonify(dict(student))
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


# UPDATE: Update Student Endpoint
@app.route("/api/students/<int:id>", methods=["PUT"])
def update_student(id):
    data = request.get_json()
    conn = get_db_connection()
    try:
        conn.execute(
            """UPDATE students SET student_id=?, name=?, program=?,
            year=?, section=? WHERE id=?""",
            (
                data.get("student_id"),
                data.get("name"),
                data.get("program"),
                data.get("year"),
                data.get("section"),
                id,
            ),
        )
        conn.commit()
        return jsonify({"message": "Student updated"})
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


# DELETE: Delete Student Endpoint
@app.route("/api/students/<int:id>", methods=["DELETE"])
def delete_student(id):
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM students WHERE id = ?", (id,))
        conn.commit()
        return jsonify({"message": "Student deleted"})
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


# Get Students by Section (Additional Task Endpoint)
@app.route("/students/section/<section_name>")
def get_students_by_section(section_name):
    conn = get_db_connection()
    try:
        students_data = conn.execute(
            "SELECT * FROM students WHERE UPPER(section) = UPPER(?)",
            (section_name,),
        ).fetchall()
        students_list = [dict(student) for student in students_data]
        return jsonify({
            "section": section_name.upper(),
            "count": len(students_list),
            "students": students_list,
        })
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


# Run Flask Application
if __name__ == "__main__":
    app.run(debug=True)