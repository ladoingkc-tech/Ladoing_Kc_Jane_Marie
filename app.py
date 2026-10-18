
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)


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


if __name__ == "__main__":
    app.run(debug=True)
