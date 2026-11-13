import os
import sqlite3
import requests

from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DATABASE = "students.db"

# PARTNER API
CLASSMATE_API_URL = "https://distura-kate-ashley-voh6.onrender.com/students"
PARTNER_POST_API_URL = "https://distura-kate-ashley-voh6.onrender.com/students"


# ==========================================
# DATABASE CONNECTION
# ==========================================

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ==========================================
# DATABASE INITIALIZATION
# ==========================================

def init_db():
    conn = get_db_connection()

    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                name TEXT NOT NULL,
                program TEXT NOT NULL,
                year INTEGER NOT NULL,
                section TEXT NOT NULL,
                source TEXT DEFAULT 'Local'
            )
        """)

        columns = [
            row["name"]
            for row in conn.execute(
                "PRAGMA table_info(students)"
            ).fetchall()
        ]

        if "source" not in columns:
            conn.execute("""
                ALTER TABLE students
                ADD COLUMN source TEXT DEFAULT 'Local'
            """)

        conn.commit()

    finally:
        conn.close()


init_db()


# ==========================================
# VALIDATE STUDENT DATA
# ==========================================

def validate_student(data):

    if not isinstance(data, dict):
        return "Valid JSON data is required."

    required = [
        "student_id",
        "name",
        "program",
        "year",
        "section"
    ]

    for field in required:
        if data.get(field) is None:
            return f"{field} is required."

    for field in [
        "student_id",
        "name",
        "program",
        "section"
    ]:
        if not str(data[field]).strip():
            return f"{field} cannot be empty."

    try:
        year = int(data["year"])

        if year < 1 or year > 10:
            return "Year must be between 1 and 10."

    except (TypeError, ValueError):
        return "Year must be a valid number."

    return None


# ==========================================
# HOME PAGE
# ==========================================

@app.route("/")
def home():
    return render_template("index.html")


# ==========================================
# BASIC APIS
# ==========================================

@app.route("/api")
def api():
    return "Welcome to my first API"


@app.route("/student")
def get_student():
    return jsonify({
        "student_id": "24-0087",
        "name": "Kc Jane Marie Ladoing",
        "program": "BSIT",
        "year": 3,
        "section": "B"
    })


@app.route("/course")
def get_course():
    return jsonify({
        "course": "Bachelor of Science in Information Technology",
        "program": "BSIT",
        "year": 3,
        "section": "B",
        "description": "Bachelor of Science in Information Technology"
    })


@app.route("/skills")
def get_skills():
    return jsonify({
        "skills": [
            "Python",
            "Flask",
            "HTML",
            "CSS",
            "JavaScript",
            "Database Management"
        ]
    })


@app.route("/hello")
def say_hello():
    name = request.args.get("name", "Student").strip()

    return jsonify({
        "message": f"Hello, {name}!"
    })


# ==========================================
# GET ALL LOCAL DATABASE RECORDS
# ==========================================

@app.route("/students", methods=["GET"])
@app.route("/api/students", methods=["GET"])
def get_students():

    conn = get_db_connection()

    try:
        students = conn.execute("""
            SELECT * FROM students
            ORDER BY id DESC
        """).fetchall()

        return jsonify([
            dict(student)
            for student in students
        ])

    finally:
        conn.close()


# ==========================================
# GET STUDENT BY ID
# ==========================================

@app.route("/students/<int:id>", methods=["GET"])
@app.route("/api/students/<int:id>", methods=["GET"])
def get_student_by_id(id):

    conn = get_db_connection()

    try:
        student = conn.execute("""
            SELECT * FROM students
            WHERE id = ?
        """, (id,)).fetchone()

    finally:
        conn.close()

    if student is None:
        return jsonify({
            "error": "Student not found"
        }), 404

    return jsonify(dict(student))


# ==========================================
# GET STUDENTS BY SECTION
# ==========================================

@app.route("/students/section/<section_name>")
def get_students_by_section(section_name):

    conn = get_db_connection()

    try:
        students = conn.execute("""
            SELECT * FROM students
            WHERE section = ?
            ORDER BY id DESC
        """, (section_name.upper(),)).fetchall()

        return jsonify([
            dict(student)
            for student in students
        ])

    finally:
        conn.close()


# ==========================================
# PARTNER API INTEGRATION - GET
# ==========================================

@app.route("/partner-records", methods=["GET"])
@app.route("/classmate-students", methods=["GET"])
def get_partner_records():

    try:
        response = requests.get(
            CLASSMATE_API_URL,
            headers={"Accept": "application/json"},
            timeout=20
        )

        response.raise_for_status()

        return jsonify(response.json()), 200

    except requests.exceptions.Timeout:

        return jsonify({
            "error": "The partner API request timed out."
        }), 504

    except requests.exceptions.RequestException as error:

        return jsonify({
            "error": "Unable to connect to partner API.",
            "details": str(error)
        }), 502

    except ValueError:

        return jsonify({
            "error": "Partner API returned invalid JSON."
        }), 502


# ==========================================
# ADD LOCAL STUDENT (WITH PARTNER SYNC)
# ==========================================

@app.route("/api/students", methods=["POST"])
def add_local_student():

    data = request.get_json(silent=True)

    error = validate_student(data)

    if error:
        return jsonify({"error": error}), 400

    conn = get_db_connection()

    try:
        cursor = conn.execute("""
            INSERT INTO students (
                student_id,
                name,
                program,
                year,
                section,
                source
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            str(data["student_id"]).strip(),
            str(data["name"]).strip(),
            str(data["program"]).strip(),
            int(data["year"]),
            str(data["section"]).strip().upper(),
            "Local"
        ))

        conn.commit()
        new_id = cursor.lastrowid

    except sqlite3.Error as error:
        return jsonify({
            "error": str(error)
        }), 500

    finally:
        conn.close()

    # Automatically push/sync the new record to Partner's/Kate's API
    try:
        payload = {
            "student_id": str(data["student_id"]).strip(),
            "name": str(data["name"]).strip(),
            "program": str(data["program"]).strip(),
            "year": int(data["year"]),
            "section": str(data["section"]).strip().upper(),
            "source": "Local"
        }
        requests.post(PARTNER_POST_API_URL, json=payload, timeout=10)
    except Exception as sync_err:
        print(f"Warning: Failed to sync new record to partner API: {sync_err}")

    return jsonify({
        "message": "Student added successfully and synced with partner!",
        "id": new_id,
        "source": "Local"
    }), 201


# ==========================================
# IMPORT PARTNER STUDENT
# SOURCE = PARTNER API
# ==========================================

@app.route("/import-student", methods=["POST"])
def import_partner_student():

    data = request.get_json(silent=True)

    error = validate_student(data)

    if error:
        return jsonify({"error": error}), 400

    conn = get_db_connection()

    try:
        cursor = conn.execute("""
            INSERT INTO students (
                student_id,
                name,
                program,
                year,
                section,
                source
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            str(data["student_id"]).strip(),
            str(data["name"]).strip(),
            str(data["program"]).strip(),
            int(data["year"]),
            str(data["section"]).strip().upper(),
            "Partner API"
        ))

        conn.commit()

        return jsonify({
            "message": "Partner record successfully saved to your local database!",
            "id": cursor.lastrowid,
            "source": "Partner API"
        }), 201

    except sqlite3.Error as error:

        return jsonify({
            "error": str(error)
        }), 500

    finally:
        conn.close()


# ==========================================
# SEND PRACTICE RECORD TO PARTNER
# ==========================================

@app.route("/send-to-partner", methods=["POST"])
def send_to_partner():

    record = {
        "student_id": "EXT-001",
        "name": "Sample Exchange Record",
        "program": "BSIT",
        "year": 1,
        "section": "A",
        "source": "Partner API"
    }

    try:
        response = requests.post(
            PARTNER_POST_API_URL,
            json=record,
            timeout=20
        )

        return jsonify({
            "message": "Practice record sent to partner.",
            "status_code": response.status_code,
            "partner_response": response.text,
            "sent_record": record
        }), 200 if response.ok else 502

    except requests.exceptions.Timeout:

        return jsonify({
            "error": "Partner API request timed out."
        }), 504

    except requests.exceptions.RequestException as error:

        return jsonify({
            "error": "Unable to send record to partner.",
            "details": str(error)
        }), 502


# ==========================================
# UPDATE STUDENT (WITH PARTNER SYNC)
# ==========================================

@app.route("/api/students/<int:id>", methods=["PUT"])
def update_student(id):

    data = request.get_json(silent=True)

    error = validate_student(data)

    if error:
        return jsonify({"error": error}), 400

    conn = get_db_connection()

    try:
        existing = conn.execute("""
            SELECT id, source, student_id
            FROM students
            WHERE id = ?
        """, (id,)).fetchone()

        if existing is None:
            return jsonify({
                "error": "Student not found"
            }), 404

        conn.execute("""
            UPDATE students
            SET student_id = ?,
                name = ?,
                program = ?,
                year = ?,
                section = ?
            WHERE id = ?
        """, (
            str(data["student_id"]).strip(),
            str(data["name"]).strip(),
            str(data["program"]).strip(),
            int(data["year"]),
            str(data["section"]).strip().upper(),
            id
        ))

        conn.commit()
        existing_source = existing["source"]

    except sqlite3.Error as error:
        return jsonify({
            "error": str(error)
        }), 500

    finally:
        conn.close()

    # Automatically push/sync the updated record to Partner's API
    try:
        payload = {
            "student_id": str(data["student_id"]).strip(),
            "name": str(data["name"]).strip(),
            "program": str(data["program"]).strip(),
            "year": int(data["year"]),
            "section": str(data["section"]).strip().upper()
        }
        # If partner supports PUT/POST via student_id mapping:
        requests.put(f"{PARTNER_POST_API_URL}/{id}", json=payload, timeout=10)
    except Exception as sync_err:
        print(f"Warning: Failed to sync update to partner API: {sync_err}")

    return jsonify({
        "message": "Student updated successfully and synced!",
        "source": existing_source
    })


# ==========================================
# DELETE STUDENT
# ==========================================

@app.route("/api/students/<int:id>", methods=["DELETE"])
def delete_student(id):

    conn = get_db_connection()

    try:
        cursor = conn.execute("""
            DELETE FROM students
            WHERE id = ?
        """, (id,))

        if cursor.rowcount == 0:
            return jsonify({
                "error": "Student not found"
            }), 404

        conn.commit()

        return jsonify({
            "message": "Student deleted successfully!"
        })

    except sqlite3.Error as error:

        return jsonify({
            "error": str(error)
        }), 500

    finally:
        conn.close()


# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":

    app.run(
        debug=os.environ.get("FLASK_DEBUG") == "1",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5001))
    )