from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
from dotenv import load_dotenv
import sqlite3
import os

load_dotenv()  # Load variables from .env file

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-me-in-production")

DB_PATH = os.path.join(os.path.dirname(__file__), "receipts.db")

# Credentials loaded from .env
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")


# -----------------------------
# Database setup
# -----------------------------

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS receipts (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_no  TEXT NOT NULL UNIQUE,
                name        TEXT NOT NULL,
                amount      INTEGER NOT NULL,
                date        TEXT NOT NULL,
                created_at  TEXT NOT NULL
            )
        """)
        conn.commit()


init_db()


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

    name   = request.form.get("name", "").strip()
    amount = request.form.get("amount", "").strip()
    date   = request.form.get("date", "").strip()

    if not name or not amount:
        return "Name and amount are required.", 400

    try:
        amount = int(amount)
    except ValueError:
        return "Invalid amount.", 400

    # Sequential receipt number starting from 1
    with get_db() as conn:
        next_no = conn.execute(
            "SELECT COALESCE(MAX(id), 0) + 1 FROM receipts"
        ).fetchone()[0]

    receipt_no   = str(next_no)
    amount_words = number_to_marathi_words(amount)
    created_at   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Save to SQLite
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO receipts (receipt_no, name, amount, date, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (receipt_no, name, amount, date, created_at)
        )
        conn.commit()

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

    with get_db() as conn:

        receipts = conn.execute(
            "SELECT * FROM receipts ORDER BY id DESC"
        ).fetchall()

        total_amount = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM receipts"
        ).fetchone()[0]

        total_count = conn.execute(
            "SELECT COUNT(*) FROM receipts"
        ).fetchone()[0]

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

    with get_db() as conn:
        conn.execute("DELETE FROM receipts WHERE id = ?", (receipt_id,))
        conn.commit()

    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    app.run(debug=True)



# -----------------------------
# Database setup
# -----------------------------

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS receipts (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_no  TEXT NOT NULL UNIQUE,
                name        TEXT NOT NULL,
                amount      INTEGER NOT NULL,
                date        TEXT NOT NULL,
                created_at  TEXT NOT NULL
            )
        """)
        conn.commit()


init_db()


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
# Home
# -----------------------------

@app.route("/")
def home():
    return render_template("form.html")


# -----------------------------
# Generate Pavti
# -----------------------------

@app.route("/generate", methods=["POST"])
def generate():

    name   = request.form.get("name", "").strip()
    amount = request.form.get("amount", "").strip()
    date   = request.form.get("date", "").strip()

    if not name or not amount:
        return "Name and amount are required.", 400

    try:
        amount = int(amount)
    except ValueError:
        return "Invalid amount.", 400

    # Sequential receipt number starting from 1
    with get_db() as conn:
        next_no = conn.execute(
            "SELECT COALESCE(MAX(id), 0) + 1 FROM receipts"
        ).fetchone()[0]

    receipt_no   = str(next_no)
    amount_words = number_to_marathi_words(amount)
    created_at   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Save to SQLite
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO receipts (receipt_no, name, amount, date, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (receipt_no, name, amount, date, created_at)
        )
        conn.commit()

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

    with get_db() as conn:

        receipts = conn.execute(
            "SELECT * FROM receipts ORDER BY id DESC"
        ).fetchall()

        total_amount = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM receipts"
        ).fetchone()[0]

        total_count = conn.execute(
            "SELECT COUNT(*) FROM receipts"
        ).fetchone()[0]

    return render_template(
        "dashboard.html",
        receipts=receipts,
        total_amount=total_amount,
        total_count=total_count
    )


if __name__ == "__main__":
    app.run(debug=True)