import sqlite3
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)


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
        "section": "B"
    })


# Greeting Endpoint
@app.route("/hello")
def hello():
    name = request.args.get("name", "student")

    return jsonify({
        "message": f"hello {name}"
    })


# Course Information Endpoint
@app.route("/course")
def course():
    return jsonify({
        "course": "Bachelor of Science in Information Technology",
        "program": "BSIT",
        "year": 3,
        "section": "B",
        "description": (
            "A program focused on information technology, "
            "programming, and computer systems."
        )
    })


# Get All Students
@app.route("/students")
def students():
    conn = get_db_connection()

    try:
        students_data = conn.execute(
            "SELECT * FROM students"
        ).fetchall()

        students_list = [
            dict(student) for student in students_data
        ]

        return jsonify(students_list)

    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500

    finally:
        conn.close()


# Get Student by ID
@app.route("/students/<int:id>")
def get_student_by_id(id):
    conn = get_db_connection()

    try:
        student = conn.execute(
            "SELECT * FROM students WHERE id = ?",
            (id,)
        ).fetchone()

        if student is None:
            return jsonify({
                "error": "Student not found"
            }), 404

        return jsonify(dict(student))

    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500

    finally:
        conn.close()


# Run Flask Application
if __name__ == "__main__":
    app.run(debug=True)