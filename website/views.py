from flask import Blueprint
from flask import render_template, jsonify, request
from flask_login import login_required, current_user
from .models import User
import mysql.connector
from mysql.connector import errors
from datetime import datetime


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
    if(current_user.role=='superuser'):
        username = request.form.get("selectedUser")
    else:
        username = current_user.username
    
    print(request.form.get("imgurl"))
    if meter_reading:
        today=datetime.today().strftime('%Y-%m-%d')
        msg=''
        try:
            query = "INSERT INTO readings (meter_reading,date, image, username) VALUES ('{}','{}','{}','{}')".format(
                meter_reading,today, image, username
            )
            cursor.execute(query)
            con.commit()
            msg="Meter reading Submitted Sucessfully!!"
        except errors.IntegrityError as e:
            msg="Meter reading Submission Failed,\n As Todays Meter reading is already Submitted !!"
        return render_template("dashboard.html", msg=msg)
    return render_template("dashboard.html")
