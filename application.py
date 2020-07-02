import os
import requests

from flask import Flask, session, render_template, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

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

x = 0


@app.route("/")
def index():

    alerts = []
    return render_template("index.html", alerts=alerts)


@app.route("/login", methods=["POST"])
def login():
    """Login to account"""
    global x

    # Get form information.
    username = request.form.get("username")
    password = request.form.get("password")

    # Make sure user exists.
    if db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).rowcount == 0:
        return render_template("index.html", alerts=[f"login failed: {username} not found"])
    if db.execute("SELECT * FROM users WHERE username = :username AND password = :password", {"username": username, "password": password}).rowcount == 0:
        return render_template("index.html", alerts=[f"login failed: incorrect password"])
    db.commit()

    session["username"] = db.execute(
        "SELECT * FROM users WHERE username = :username", {"username": username}).fetchone()
    x = session["username"].id
    # x = x+99
    return render_template("home.html", username=session["username"].username)


@app.route("/register", methods=["POST"])
def register():
    """register for account"""

    # Get form information.
    username = request.form.get("username")
    password = request.form.get("password")

    # # Make sure username doesn't exists.
    if db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).rowcount != 0:
        alerts = [
            f"The username: {username} already exists, please use a different one"]
        return render_template("index.html", alerts=alerts)

    db.execute("INSERT INTO users (username, password) VALUES (:username, :password)",
               {"username": username, "password": password})
    db.commit()
    alerts = [f"successfully registered {username}"]
    return render_template("index.html", alerts=alerts)


@app.route("/search", methods=["POST"])
def search():
    """register for account"""

    # Get form information.
    search_type = request.form.get("search_type")
    search_query = request.form.get("search_query")

    if search_type == "title":
        books = db.execute(
            "SELECT * FROM books WHERE lower(title) LIKE :title", {"title": f"%{search_query.lower()}%"}).fetchall()
        if books == []:
            return render_template("books.html", books=[], count=0)

    elif search_type == "author":
        books = db.execute(
            "SELECT * FROM books WHERE lower(author) LIKE :author", {"author": f"%{search_query.lower()}%"}).fetchall()
        if books == []:
            return render_template("books.html", books=[], count=0)

    elif search_type == "ISBN":
        books = db.execute(
            "SELECT * FROM books WHERE lower(isbn) LIKE :isbn", {"isbn": f"%{search_query.lower()}%"}).fetchall()
        if books == []:
            return render_template("books.html", books=[], count=0)

    return render_template("books.html", books=books, count=len(books))


@ app.route("/book/<string:isbn>")
def review(isbn):
    global x

    book = db.execute(
        "SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()

    res = requests.get("https://www.goodreads.com/book/review_counts.json",
                       params={"key": "YjxbSvi2f1v0KuKj7NTVZA", "isbns": isbn})
    goodreads = res.json()
    # return res.json()

    reviews = db.execute(
        "SELECT * FROM reviews WHERE isbn = :isbn", {"isbn": isbn}).fetchall()

    return render_template("book.html", book=book, goodreads=goodreads, reviews=reviews)


@ app.route("/book/<string:isbn>/post", methods=["POST"])
def post_review(isbn):
    userReview = request.form.get("userReview")
    userRating = request.form.get("userRating")
    global x
    user_id = x
    # return(f"{x}")

    book = db.execute(
        "SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()

    res = requests.get("https://www.goodreads.com/book/review_counts.json",
                       params={"key": "YjxbSvi2f1v0KuKj7NTVZA", "isbns": isbn})

    if res.status_code != 200:
        raise Exception("ERROR: API request unsuccessful.")

    goodreads = res.json()
    # return res.json()
    # print(session["username"])
    user = db.execute(
        "SELECT * FROM users WHERE id = :user_id", {"user_id": user_id}).fetchone()

    db.execute("INSERT INTO reviews (isbn, user_id, review, rating, username) VALUES (:isbn, :user_id, :review, :rating, :username)",
               {"isbn": isbn, "user_id": user_id, "review": userReview, "rating": userRating, "username": user.username})
    db.commit()
    reviews = db.execute(
        "SELECT * FROM reviews WHERE isbn = :isbn", {"isbn": isbn}).fetchall()

    return render_template("book.html", book=book, goodreads=goodreads, reviews=reviews)
