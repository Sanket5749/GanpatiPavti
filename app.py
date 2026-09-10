from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client
import os

load_dotenv()  # Load variables from .env file

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-me-in-production")

# Credentials loaded from .env
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

# -----------------------------
# Supabase setup
# -----------------------------

SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# -----------------------------
# Auth helper
# -----------------------------

def is_logged_in():
    return session.get("logged_in") is True


# -----------------------------
# Amount to words
# -----------------------------

ones = [
    "", "एक", "दोन", "तीन", "चार", "पाच",
    "सहा", "सात", "आठ", "नऊ", "दहा",
    "अकरा", "बारा", "तेरा", "चौदा", "पंधरा",
    "सोळा", "सतरा", "अठरा", "एकोणीस"
]

tens = [
    "", "", "वीस", "तीस", "चाळीस",
    "पन्नास", "साठ", "सत्तर", "ऐंशी", "नव्वद"
]


def number_to_marathi_words(n):

    if n < 20:
        return ones[n]

    if n < 100:
        return tens[n // 10] + (
            " " + ones[n % 10] if n % 10 else ""
        )

    if n < 1000:
        return (
            ones[n // 100]
            + "शे"
            + (
                " " + number_to_marathi_words(n % 100)
                if n % 100 else ""
            )
        )

    if n < 100000:
        return (
            number_to_marathi_words(n // 1000)
            + " हजार "
            + (
                number_to_marathi_words(n % 1000)
                if n % 1000 else ""
            )
        )

    if n < 10000000:
        return (
            number_to_marathi_words(n // 100000)
            + " लाख "
            + (
                number_to_marathi_words(n % 100000)
                if n % 100000 else ""
            )
        )

    return str(n)


# -----------------------------
# Login / Logout
# -----------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if is_logged_in():
        return redirect(url_for("home"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("home"))
        else:
            error = "चुकीचे username किंवा password!"

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# -----------------------------
# Home
# -----------------------------

@app.route("/")
def home():
    if not is_logged_in():
        return redirect(url_for("login"))
    return render_template("form.html")


# -----------------------------
# Generate Pavti
# -----------------------------

@app.route("/generate", methods=["POST"])
def generate():
    if not is_logged_in():
        return redirect(url_for("login"))

    name     = request.form.get("name", "").strip()
    amount   = request.form.get("amount", "").strip()
    date_raw = request.form.get("date", "").strip()

    # Convert from HTML date format (YYYY-MM-DD) to DD-MM-YYYY
    try:
        date = datetime.strptime(date_raw, "%Y-%m-%d").strftime("%d-%m-%Y")
    except ValueError:
        date = date_raw  # fallback: use as-is if parsing fails

    if not name or not amount:
        return "Name and amount are required.", 400

    try:
        amount = int(amount)
    except ValueError:
        return "Invalid amount.", 400

    # Get next sequential receipt number (MAX id + 1)
    result = supabase.table("receipts").select("id").order("id", desc=True).limit(1).execute()
    if result.data:
        next_no = result.data[0]["id"] + 1
    else:
        next_no = 1

    receipt_no   = str(next_no)
    amount_words = number_to_marathi_words(amount)
    created_at   = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    # Save to Supabase
    supabase.table("receipts").insert({
        "receipt_no": receipt_no,
        "name":       name,
        "amount":     amount,
        "date":       date,
        "created_at": created_at,
    }).execute()

    return render_template(
        "pavti.html",
        name=name,
        amount=amount,
        amount_words=amount_words,
        date=date,
        receipt_no=receipt_no
    )


# -----------------------------
# Dashboard
# -----------------------------

@app.route("/dashboard")
def dashboard():
    if not is_logged_in():
        return redirect(url_for("login"))

    result = supabase.table("receipts").select("*").order("id", desc=True).execute()
    receipts = result.data or []

    total_amount = sum(r["amount"] for r in receipts)
    total_count  = len(receipts)

    return render_template(
        "dashboard.html",
        receipts=receipts,
        total_amount=total_amount,
        total_count=total_count
    )


# -----------------------------
# Delete Single Record
# -----------------------------

@app.route("/delete/<int:receipt_id>", methods=["POST"])
def delete_one(receipt_id):
    if not is_logged_in():
        return redirect(url_for("login"))

    supabase.table("receipts").delete().eq("id", receipt_id).execute()

    return redirect(url_for("dashboard"))


# -----------------------------
# Yadi (Public donor list)
# -----------------------------

@app.route("/yadi")
def yadi():
    result = supabase.table("receipts").select("*").order("amount", desc=False).order("id", desc=False).execute()
    receipts = result.data or []

    total_amount = sum(r["amount"] for r in receipts)
    total_count  = len(receipts)

    return render_template(
        "yadi.html",
        receipts=receipts,
        total_amount=total_amount,
        total_count=total_count
    )


if __name__ == "__main__":
    app.run(debug=True)
