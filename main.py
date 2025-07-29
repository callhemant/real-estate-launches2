from flask import Flask, render_template, request, redirect, session, url_for, send_from_directory
from werkzeug.utils import secure_filename
import os
import time
import json

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "changeme")

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
PROJECTS_FILE = "projects.json"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def load_projects():
    if not os.path.exists(PROJECTS_FILE):
        return []
    with open(PROJECTS_FILE, "r") as f:
        return json.load(f)


def save_projects(projects):
    with open(PROJECTS_FILE, "w") as f:
        json.dump(projects, f, indent=2)


@app.route("/")
def index():
    projects = load_projects()
    return render_template("index.html", projects=projects)


@app.route("/subscribe", methods=["POST"])
def subscribe():
    firstname = request.form.get("firstname")
    email = request.form.get("email")

    if firstname and email:
        # You can optionally store subscribers in a separate JSON file
        return redirect(url_for("index"))
    else:
        return render_template("index.html", message="Please fill out all fields.")


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    projects = load_projects()
    return render_template("admin.html", projects=projects)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form.get("password")
        if password == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("admin"))
        else:
            return render_template("login.html", error="Incorrect password.")
    return render_template("login.html")


@app.route("/add-project", methods=["POST"])
def add_project():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    title = request.form.get("title")
    builder = request.form.get("builder")
    location = request.form.get("location")
    price_range = request.form.get("price_range")
    size_range = request.form.get("size_range")
    possession = request.form.get("possession")
    bhk_data = request.form.get("bhk")

    # Image upload
    image = request.files.get("image")
    image_filename = ""
    if image and allowed_file(image.filename):
        timestamp = str(int(time.time()))
        filename = secure_filename(f"{title.lower().replace(' ', '_')}-{timestamp}.{image.filename.rsplit('.', 1)[1]}")
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        image_filename = f"static/uploads/{filename}"

    configs = []
    if bhk_data:
        lines = bhk_data.strip().split("\n")
        for line in lines:
            parts = line.split(",")
            if len(parts) == 3:
                configs.append({
                    "type": parts[0].strip(),
                    "size": parts[1].strip(),
                    "price": parts[2].strip()
                })

    project = {
        "title": title,
        "builder": builder,
        "location": location,
        "price_range": price_range,
        "size_range": size_range,
        "possession": possession,
        "image": image_filename,
        "configs": configs
    }

    projects = load_projects()
    projects.append(project)
    save_projects(projects)

    return redirect(url_for("admin"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/static/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=81)
