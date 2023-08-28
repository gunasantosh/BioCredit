from flask import Blueprint
from flask import render_template, jsonify, request
from flask_login import login_required, current_user
from .models import User
import mysql.connector

views = Blueprint("views", __name__)

con = mysql.connector.connect(
    host="localhost", user="root", password="mypassword", database="dapp"
)
cursor = con.cursor(buffered=True)


@views.route("/")
@views.route("/home")
def home():
    return render_template("index.html")


@views.route("/dashboard")
@login_required
def dashboard():
    role = current_user.role
    user_list = User.query.filter_by(role="user").all()
    return render_template("dashboard.html", role=role, user_list=user_list)


# @views.route('/save', methods=['POST'])
# def save():
#     image_data = request.json.get('image_data')
#     if image_data:

#         query = "INSERT INTO captured_image (image) VALUES ('{}')".format(image_data)
#         cursor.execute(query)
#         con.commit()
#         return jsonify({'status': 'success'})
#     else:
#         return jsonify({'status': 'error'})


@views.route("/process_form", methods=["POST"])
@login_required
def process_form():
    meter_reading = request.form.get("reading")
    image = request.form.get("imgurl")
    username = request.form.get("selectedUser")
    print(request.form.get("imgurl"))
    if meter_reading:
        query = "INSERT INTO captured_image (meter_reading, image, username) VALUES ('{}','{}','{}')".format(
            meter_reading, image, username
        )
        cursor.execute(query)
        con.commit()
        return render_template("dashboard.html", msg="Meter reading Submitted !!")
    return render_template("dashboard.html")
