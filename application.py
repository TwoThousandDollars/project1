import os

from flask import Flask, session
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# export FLASK_APP=application.py
# export FLASK_DEBUG=1
# export DATABASE_URL=postgres://cpqpbvmoqzkulc:171fb91e294c916380d14afa19a54d00e8846543c6408e3e601efe27f847659e@ec2-54-204-18-53.compute-1.amazonaws.com:5432/d5s43bbs1sgg6d

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


@app.route("/")
def index():
    return "Project 1: TODO"
