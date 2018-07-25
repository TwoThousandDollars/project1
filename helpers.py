from flask import Flask, redirect, render_template, request, session
from functools import wraps


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def get_reviews(db, isbn):
    r = list(db.execute("SELECT reviews.score, reviews.review, users.username FROM reviews JOIN users ON (reviews.user_id = users.id)  WHERE isbn = :isbn",
                        {"isbn": isbn}))
    if len(r) < 1:
        r = ""
    return r
