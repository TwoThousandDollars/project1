import os

from flask import Flask, session, render_template, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

# export FLASK_APP=application.py
# export FLASK_DEBUG=1
# export DATABASE_URL=postgres://cpqpbvmoqzkulc:171fb91e294c916380d14afa19a54d00e8846543c6408e3e601efe27f847659e@ec2-54-204-18-53.compute-1.amazonaws.com:5432/d5s43bbs1sgg6d
#
# goodread info:
KEY = "JrtWojWMmtu1eVLQ2Jwgbw"
# secret: ZsdMuaz8QuIt8wJrr729SNPThf2F2aRjUGXlFj8


# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """ Allow users to register for brooksbooks.com """

    if request.method == "POST":
        user = request.form.get("username")
        pword = request.form.get("password")
        confirm = request.form.get("confirmation")

        # Ensures user provided all required fields
        if not user or not pword or not confirm:
            return render_template("apology.html")

        # Ensures password and confirmation match
        if not pword == confirm:
            return render_template("apology.html")

        # Generate a hash to be stored in database
        hash = generate_password_hash(pword)

        # Ensure user doesn't already exists
        test = db.execute("SELECT * FROM users WHERE username = :user",
                            {"user": user}).fetchall()

        if len(test) > 0:
            return render_template("apology.html")

        # Registers user
        db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)",
                    {"username": user, "hash": hash})

        # Grabs id to log user in
        rows = db.execute("SELECT id FROM users WHERE username = :username",
                            {"username": user})
        row = list(rows)

        session["user_id"] = row[0]["id"]

        return render_template("index.html", row=row, ses=session["user_id"])

    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    return render_template("login.html")


@app.route("/search", methods=["GET", "POST"])
def search():
    return render_template("search.html")


@app.route("/books", methods=["GET", "POST"])
def books():
    return render_template("books.html")
