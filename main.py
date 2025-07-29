from flask import Flask, render_template, request, redirect, session, url_for, send_from_directory
from werkzeug.utils import secure_filename
from replit import db
import os
import time

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "changeme")

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and filename.rsplit(
        '.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    projects = [db[key] for key in db.keys() if key.startswith("project:")]
    return render_template("index.html", projects=projects)


@app.route("/subscribe", methods=["POST"])
def subscribe():
    firstname = request.form.get("firstname")
    email = request.form.get("email")

    if firstname and email:
        db[email] = {"firstname": firstname, "email": email}
        return redirect(url_for("index"))
    else:
        return render_template("index.html",
                               message="Please fill out all fields.")


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    submissions = [v for k, v in db.items() if "@" in k]
    projects = [db[key] for key in db.keys() if key.startswith("project:")]
    return render_template("admin.html",
                           submissions=submissions,
                           projects=projects)


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
        filename = secure_filename(
            f"{title.lower().replace(' ', '_')}-{timestamp}.{image.filename.rsplit('.', 1)[1]}"
        )
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

    key = f"project:{title.lower().replace(' ', '_')}"
    db[key] = {
        "title": title,
        "builder": builder,
        "location": location,
        "price_range": price_range,
        "size_range": size_range,
        "possession": possession,
        "image": image_filename,
        "configs": configs
    }
    return redirect(url_for("admin"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=81)
