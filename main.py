from flask import Flask, render_template, request, redirect, session, url_for, flash
from werkzeug.utils import secure_filename
import os
import time
import json

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "changeme")

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
PROJECTS_FILE = "projects.json"

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def load_projects():
    if os.path.exists(PROJECTS_FILE):
        with open(PROJECTS_FILE, "r") as f:
            return json.load(f)
    return []


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
        return redirect(url_for("index"))
    else:
        flash("Please fill out all fields.")
        return redirect(url_for("index"))


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
            flash("Incorrect password.")
    return render_template("login.html")


@app.route("/add-project", methods=["POST"])
def add_project():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    try:
        title = request.form.get("title")
        builder = request.form.get("builder")
        location = request.form.get("location")
        price_range = request.form.get("price_range")
        size_range = request.form.get("size_range")
        possession = request.form.get("possession")
        bhk_data = request.form.get("bhk")
        image = request.files.get("image")

        print("🧪 DEBUG:")
        print("Title:", title)
        print("Builder:", builder)
        print("Location:", location)
        print("Price Range:", price_range)
        print("Size Range:", size_range)
        print("Possession:", possession)
        print("BHK Data:", bhk_data)
        print("Image:", image.filename if image else "No image uploaded")

        if not all([title, builder, location, price_range, size_range, possession, bhk_data]):
            flash("All fields are required.", "error")
            return redirect(url_for("admin"))

        image_filename = ""
        if image and allowed_file(image.filename):
            timestamp = str(int(time.time()))
            filename = secure_filename(f"{title.lower().replace(' ', '_')}_{timestamp}.{image.filename.rsplit('.', 1)[1]}")
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_filename = f"static/uploads/{filename}"
        else:
            flash("Invalid or missing image. Must be jpg, png, jpeg, or gif.", "error")
            return redirect(url_for("admin"))

        configs = []
        lines = bhk_data.strip().split("\n")
        for line in lines:
            parts = line.strip().split(",")
            if len(parts) != 3:
                flash("Each BHK line must follow: Type, Size, Price", "error")
                return redirect(url_for("admin"))
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

        print("✅ Project saved successfully.")
        flash("Project added successfully!", "success")
        return redirect(url_for("admin"))

    except Exception as e:
        print("❌ Error occurred:", str(e))
        flash(f"Error adding project: {str(e)}", "error")
        return redirect(url_for("admin"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))
import json

LEADS_FILE = "leads.json"

def save_lead(lead):
    leads = []
    if os.path.exists(LEADS_FILE):
        with open(LEADS_FILE, "r") as f:
            leads = json.load(f)
    leads.append(lead)
    with open(LEADS_FILE, "w") as f:
        json.dump(leads, f, indent=2)

@app.route("/submit-lead", methods=["POST"])
def submit_lead():
    name = request.form.get("name")
    email = request.form.get("email")
    mobile = request.form.get("mobile")
    project_title = request.form.get("project_title")

    if name and email and mobile:
        save_lead({
            "name": name,
            "email": email,
            "mobile": mobile,
            "project": project_title
        })
        flash("Thanks for your interest!", "success")
    else:
        flash("All lead fields are required.", "error")

    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=81)
