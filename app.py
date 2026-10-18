from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api")
def api():
    return "Welcome to my first API!"

@app.route("/student")
def student():
    return jsonify({
        "id": "24-0087",
        "name": "Kc Jane Marie Ladoing",
        "program": "BSIT",
        "year": 3,
        "section": "B"
    })

@app.route("/hello")
def hello():
    name = request.args.get("name", "student")
    return jsonify({"message": f"hello {name}"})

if __name__ == "__main__":
    app.run(debug=True)