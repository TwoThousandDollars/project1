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
            error = "Please enter all fields"
            return render_template("apology.html", error=error)

        # Ensures password and confirmation match
        if not pword == confirm:
            error = "Passwords do not match"
            return render_template("apology.html", error=error)

        # Generate a hash to be stored in database
        hash = generate_password_hash(pword)

        # Ensure user doesn't already exists
        test = db.execute("SELECT * FROM users WHERE username = :user",
                            {"user": user}).fetchone()

        if test is not None:
            error = "User already exists"
            return render_template("apology.html", error=error)

        # Registers user
        db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)",
                    {"username": user, "hash": hash})
        db.commit()

        # Grabs id to log user in
        rows = list(db.execute("SELECT * FROM users WHERE username = :username",
                            {"username": user}))

        # Creates session for specific user
        session["user_id"] = rows[0]["id"]

        return redirect(url_for("index"))

    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """ Allow users to log in """

    if request.method == "POST":
        user = request.form.get("u")
        pword = request.form.get("p")

        if not user or not pword:
            error = "Please enter all fields"
            return render_template("apology.html", error=error)

        check_user = list(db.execute("SELECT * FROM users WHERE username = :username",
                            {"username": user}))

        if check_password_hash(check_user[0]["hash"], pword) == False:
            error = "Incorrect credentials"
            return render_template("apology.html", error=error)

        session["user_id"] = check_user[0]["id"]

        return render_template("index.html", check=check_user[0]["id"], user=user)

    else:
        return render_template("login.html")


@app.route("/search", methods=["GET", "POST"])
def search():
    return render_template("search.html")


@app.route("/books", methods=["GET", "POST"])
def books():
    return render_template("books.html")
