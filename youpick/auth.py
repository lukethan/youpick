import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from .db import db
from .models import User
from sqlalchemy import text

bp = Blueprint('auth', __name__, url_prefix='/auth')
#Sets up the prefix auth for all routes in this module

#Used the tutorial from flask documentation for the auth setup
@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirmation = request.form['confirmation']
        error = None

        if not username.strip():
            error = 'Please enter a username'
        elif not password.strip():
            error = 'Please enter a password'
        elif not confirmation.strip():
            error = 'Please confirm your password'
        elif password.strip() != confirmation.strip():
            error = 'Confirmation password entered incorrectly'

        if error is None:
            try:
                sql = text("INSERT INTO users (username, password) VALUES (:username, :password)")
                params = {'username': username, 'password': (generate_password_hash(password))}
                db.session.execute(sql, params)
                db.session.commit()
            #I like this integrity error, because I was querying the db and then comparing it to request.form
            except IntegrityError:
                error = f"User {username} is already registered."
                db.session.rollback()
            else:
                return redirect(url_for("auth.login"))

        flash(error)
        #I like how the error is set by the conditional but it doesnt return until the end
        #I structure my code by returning render template after each flash which is inefficient

    return render_template('auth/register.html')



#Used the tutorital from flask documentation for the auth setup
@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None
        user = User.query.filter_by(username=username).first()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user.password, password):
            error = 'Incorrect password.'
        else:
            # Successful login logic
            flash('Login successful!')
            return redirect(url_for('picks.index'))  # Redirect to a successful login page

        flash(error)
    return render_template('auth/login.html')

# class User(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(100), unique=True, nullable=False)
#     password = db.Column(db.String(200), nullable=False)

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = User.query.get(user_id)

#  @bp.before_app_request
# def load_logged_in_user():
#     user_id = session.get('user_id')

#     if user_id is None:
#         g.user = None
#     else:
#         g.user = get_db().execute(
#             'SELECT * FROM users WHERE id = ?', (user_id,)
#         ).fetchone()
#         #I like the g variable being used here if there is a session

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))
    #Identical to finance assignment

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view
#This is cool because it is basically taking whatever function the decorator is affixed to
#And passing it as an argument to this function. the **kwargs allows for any number of 
#key word arguments because we don't know how many we will need for each function that we decorate