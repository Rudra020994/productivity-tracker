from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
from models import db, WorkEntry
from sqlalchemy import func
import os

# ===================================================
# Flask configuration
# ===================================================

app = Flask(__name__)

# --- Absolute path to the same DB you already have ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "instance", "productivity.db")
os.makedirs(os.path.join(BASE_DIR, "instance"), exist_ok=True)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + DB_PATH
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

with app.app_context():
    db.create_all()

# ===================================================
# Routes
# ===================================================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/add", methods=["POST"])
def add_activity():
    """Insert a new work‑entry record."""
    try:
        name = request.form["name"].strip()
        module = request.form["module"].strip()
        description = request.form["description"].strip()
        date_str = request.form["date"]
        start_str = request.form["start_time"]
        end_str = request.form["end_time"]

        date = datetime.strptime(date_str, "%Y-%m-%d").date()
        start_time = datetime.strptime(start_str, "%H:%M").time()
        end_time = datetime.strptime(end_str, "%H:%M").time()

        entry = WorkEntry(
            name=name,
            module=module,
            description=description,
            date=date,
            start_time=start_time,
            end_time=end_time,
        )
        entry.calculate_duration()
        db.session.add(entry)
        db.session.commit()
    except Exception as e:
        print("Error saving activity:", e)

    return redirect(url_for("index"))


# ===================================================
# Helper for flexible date parsing
# ===================================================

def parse_flexible_date(text):
    """Handle browsers that send dd‑mm‑yyyy or yyyy‑mm‑dd."""
    text = text.strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text).date()
    except Exception:
        return None


# ===================================================
# Report route (table version)
# ===================================================

@app.route("/report", methods=["GET", "POST"])
def report():
    labels, hours, message = [], [], None

    if request.method == "POST":
        start_raw = request.form.get("start_date", "")
        end_raw = request.form.get("end_date", "")

        print("DEBUG start_date raw:", start_raw)
        print("DEBUG end_date raw:", end_raw)

        start_date = parse_flexible_date(start_raw)
        end_date = parse_flexible_date(end_raw)

        if not start_date or not end_date:
            message = f"Invalid date format: {start_raw} → {end_raw}"
        else:
            entries = (
                db.session.query(
                    WorkEntry.date,
                    func.sum(WorkEntry.duration).label("total_hours"),
                )
                .filter(func.date(WorkEntry.date).between(start_date, end_date))
                .group_by(WorkEntry.date)
                .order_by(WorkEntry.date)
                .limit(10)
                .all()
            )

            if entries:
                labels = [e.date.strftime("%Y-%m-%d") for e in entries]
                hours = [float(e.total_hours) for e in entries]
                for lab, hr in zip(labels, hours):
                    print("DEBUG ->", lab, hr)
            else:
                message = "No data found for this date range."

    # Prepare zipped rows for Jinja
    rows = list(zip(labels, hours))
    return render_template("report.html", rows=rows, message=message)


# ===================================================
# Run the app
# ===================================================

if __name__ == "__main__":
    app.run(debug=True)
