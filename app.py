from flask import Flask, render_template, request, redirect, url_for, current_app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.exc import StaleDataError
import time

# set up logging
import logging
logging.basicConfig(level=logging.DEBUG)

logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)
logging.getLogger('sqlalchemy.dialects').setLevel(logging.DEBUG)
logging.getLogger('sqlalchemy.pool').setLevel(logging.DEBUG)
logging.getLogger('sqlalchemy.orm').setLevel(logging.DEBUG)

# create the extension
db = SQLAlchemy()
# create the app
app = Flask(__name__)

# configure the postgres database
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:postgres@localhost:5432/todoapp"
# initialize the app with the extension
db.init_app(app)

# db models
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now(), server_onupdate=db.func.now())
    version_id = db.Column(db.Integer, nullable=False)

    __mapper_args__ = {
        "version_id_col": version_id
    }

    def __repr__(self):
        return f"User {self.username}"


app.before_request(lambda: logging.debug("\n\n\n--------------------====================---------------------"))

with app.app_context():
    db.create_all()

# web routes

@app.route("/")
@app.route("/users")
def user_index():
    users = db.session.execute(db.select(User).order_by(User.username)).scalars()
    return render_template("user/index.html", users=users)

@app.route("/users", methods=["POST"])
def user_create():
    user = User(
        username=request.form["username"],
        email=request.form["email"],
    )
    db.session.add(user)
    db.session.commit()
    return redirect(url_for("user_show", id=user.id))

@app.route("/user/<int:id>")
def user_show(id):
    user = db.get_or_404(User, id)
    return render_template("user/show.html", user=user)

@app.route("/user/<int:id>/delete", methods=["GET", "POST"])
def user_delete(id):
    user = db.get_or_404(User, id)

    if request.method == "POST":
        db.session.delete(user)
        db.session.commit()
        return redirect(url_for("user_index"))

    return render_template("user/delete.html", user=user)

@app.route("/user/<int:id>/edit")
def user_edit(id):
    user = db.get_or_404(User, id)
    return render_template("user/edit.html", user=user)

@app.route("/user/<int:id>", methods=["POST"])
def user_update(id):
    # open a database session and roll back in case of an exception
    try:
        user = db.session.get(User, id)
        user.username = request.form["username"]
        user.email = request.form["email"]
        db.session.add(user)
        # sleep for 5 seconds to simulate a long running request
        time.sleep(5)
        db.session.commit()
        return redirect(url_for("user_show", id=user.id))
    except StaleDataError as ex:
        # print exception information
        current_app.logger.exception(ex)
        # rollback the session
        db.session.rollback()
        # redirect to the edit page
        return "StaleDataError"
        #  return redirect(url_for("user_edit", id=id, error="The user has been updated by another user"))
