import os
import requests

from helpers import get_reviews, login_required

from flask import Flask, session, render_template, request, jsonify, redirect
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
    res_no_log = list(db.execute("SELECT * FROM reviews ORDER BY reviews DESC LIMIT 10"))

    return render_template("index.html", res=res_no_log)


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

        # Ensures user entered all required fields
        if not user or not pword:
            error = "Please enter all fields"
            return render_template("apology.html", error=error)

        check_user = list(db.execute("SELECT * FROM users WHERE username = :username",
                            {"username": user}))

        if check_password_hash(check_user[0]["hash"], pword) == False:
            error = "Incorrect credentials"
            return render_template("apology.html", error=error)

        # Logs user in
        session["user_id"] = check_user[0]["id"]

        return redirect("/")

    else:
        return render_template("login.html")

@app.route("/logout", methods=["GET", "POST"])
def logout():
    """ Log user out """

    # Log user out
    session.clear()

    # Return user to homepage
    return redirect("/")


@app.route("/search", methods=["GET", "POST"])
def search():
    """ Allow user to search for reviews about the books they like """

    if request.method == "POST":
        q = request.form.get("q").lower()

        res = list(db.execute("SELECT * FROM books WHERE isbn LIKE :q OR lower(title) LIKE :q OR lower(author) LIKE :q OR year LIKE :q LIMIT 10",
                            {"q": "%" + q + "%"}))

        # Ensures search exists in database
        if len(res) < 1:
            error = "Could not find any matching books."
            return render_template("apology.html", error=error)

        return render_template("results.html", res=res)

    else:
        return render_template("search.html")


@app.route("/books/<isbn>", methods=["GET", "POST"])
def books(isbn):
    """ Displays all information about book """

    book = list(db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}))

    if len(book) < 1:
        error = "Cannot find details on this book"
        return render_template("apology.html", error=error)

    res = {"isbn": book[0][0], "title": book[0][1], "author": book[0][2], "year": book[0][3]}
    gr = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": KEY, "isbns": isbn})
    g = gr.json()
    # if gr is None TODO

    if request.method == "POST":
        if session["user_id"] is None:
            error = "You must be logged in to leave a review"
            return render_template("apology.html", error=error)

        res = list(db.execute("SELECT * FROM reviews WHERE user_id = :user_id", {"user_id": session["user_id"]}))
        if len(res) > 1:
            error = "Users may only leave one review per book"
            return render_template("apology.html", error=error)

        score = int(request.form.get("score"))
        review = request.form.get("review")

        # Submit review
        db.execute("INSERT INTO reviews (score, isbn, user_id, review) VALUES (:score, :isbn, :user_id, :review)",
                    {"score": score, "isbn": isbn, "user_id": session["user_id"], "review": review})
        db.commit()

        # Gather reviews to display on page
        reviews = get_reviews(db, isbn)

        return render_template("books.html", res=res, reviews=reviews, gr=g["books"])

    else:
        reviews = get_reviews(db, isbn)
        return render_template("books.html", res=res, reviews=reviews, gr=g["books"])





@app.route("/api/<isbn>", methods=["GET", "POST"])
def api(isbn):
    """ Api access to information about the books in books table, as well as information about the book's reviews """

    res = list(db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}))
    stats = list(db.execute("SELECT AVG(score), COUNT(score) FROM reviews WHERE isbn = :isbn", {"isbn": isbn}))

    # Add review_cound & average_score to api access

    if len(res) != 1:
        return jsonify(res)
    else:
        return jsonify(isbn=res[0]["isbn"],
        title=res[0]["title"],
        author=res[0]["author"],
        year=res[0]["year"],
        review_count=stats[0][1],
        average_score=float(stats[0][0]))
