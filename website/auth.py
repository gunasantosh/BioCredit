from flask import Blueprint
from flask import render_template,request,redirect,url_for,flash
from . import db
from .models import User
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

auth = Blueprint('auth', __name__)

@auth.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get("username")
        name = request.form.get("name")
        address = request.form.get("address")
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")
        role = request.form.get("user_role")
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")

        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            flash("Username already exists. Please choose a different username.", category="error")
        elif username and len(username.strip()) >= 4 and password1 and len(password1) >= 7 and password1 == password2 and username.isalnum():
            user = User(username=username, name=name, address=address, latitude=latitude, longitude=longitude,role=role,password=generate_password_hash(password1, method='sha256') )  
            db.session.add(user)
            db.session.commit()
            flash("Account created successfully!", category="success")
            return redirect(url_for('views.dashboard'))
        else:
            return render_template('register.html')

    return render_template("register.html")

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user:
            if check_password_hash(user.password, password):
                login_user(user, remember=True)
                return redirect(url_for('views.dashboard'))
            else:
                flash("Incorrect password, please try again.", category='error')
        else:
            flash("Username does not exist.", category='error')
    return render_template("login.html")

@auth.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

