import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "secret123"

# Config
UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ── Database Helper ──────────────────────────────────────────
def get_db():
    conn = sqlite3.connect("students.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            display_name TEXT NOT NULL,
            image_filename TEXT DEFAULT 'default.png'
        )
        """)
        # Insert a default user if table is empty
        existing = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if existing == 0:
            conn.execute("""
            INSERT INTO users (display_name, image_filename)
            VALUES ('Student User', 'default.png')
            """)
        conn.commit()

init_db()

# ── Helper: Check File Extension ─────────────────────────────
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ── Routes ───────────────────────────────────────────────────

# Dashboard — show current profile
@app.route("/")
def dashboard():
    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE id = 1").fetchone()
    return render_template("dashboard.html", user=user)

# Edit Profile — show form
@app.route("/edit", methods=["GET"])
def edit_profile():
    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE id = 1").fetchone()
    return render_template("edit_profile.html", user=user)

# Update Profile — handle form submission
@app.route("/update", methods=["POST"])
def update_profile():
    display_name = request.form.get("display_name", "").strip()
    file = request.files.get("profile_image")

    if not display_name:
        flash("❌ Display name cannot be empty.", "error")
        return redirect(url_for("edit_profile"))

    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE id = 1").fetchone()
        image_filename = user["image_filename"]

        # Handle image upload
        if file and file.filename != "":
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                image_filename = filename
            else:
                flash("❌ Invalid file type. Only JPG, JPEG, PNG allowed.", "error")
                return redirect(url_for("edit_profile"))

        # Update database
        conn.execute("""
        UPDATE users
        SET display_name = ?, image_filename = ?
        WHERE id = 1
        """, (display_name, image_filename))
        conn.commit()

    flash("✅ Profile updated successfully!", "success")
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.run(debug=True)