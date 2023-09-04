from flask import Blueprint
from flask import render_template, jsonify, request
from flask_login import login_required, current_user
from .models import User
import mysql.connector
from mysql.connector import errors
from datetime import datetime
from geopy.distance import geodesic
import segno
from cryptography.fernet import Fernet


views = Blueprint("views", __name__)
key=b'Jxb-gEda5CtPcq-z2oiCDbIYzUbe9C_ooa_CTl_QCEs='



@views.route("/")
@views.route("/home")
def home():
    return render_template("index.html")


@views.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    fernet = Fernet(key)
    encMessage = fernet.encrypt(current_user.username.encode())
    qrcode=segno.make('http://127.0.0.1:5000/qr_redirect?secret={}'.format(encMessage))
    return render_template("dashboard.html",current_user=current_user,qrcode=qrcode)


@views.route("/capture_readings", methods=["POST", "GET"])
def capture_readings():
    con = mysql.connector.connect(
    host="localhost", user="root", password="", database="dapp"
)
    cursor = con.cursor(buffered=False,dictionary=True)
    msg = None
    if request.method == "GET":
        msg = request.args.get("msg")
    role = current_user.role
    user_list=None
    flag=True
    today = datetime.today().strftime("%Y-%m-%d")
    if(role=='superuser'):
        q="SELECT * FROM user WHERE role='user' AND 0 IN (SELECT COUNT(*) FROM readings WHERE readings.username=user.username AND timestamp>='{} 00:00:00' AND timestamp<='{} 23:59:59')".format(today,today)
        cursor.execute(q)
        ress=cursor.fetchall()
        print(ress)
        if(len(ress)>0):
            user_list=ress
        else:
            user_list=[]
            flag=False
    else:
        q="SELECT * FROM readings WHERE username='{}' AND timestamp>='{} 00:00:00' AND timestamp<='{} 23:59:59'".format(current_user.username,today,today)
        cursor.execute(q)
        ress=cursor.fetchall()
        if(len(ress)>0):
            flag=False


    
    return render_template(
        "capture_readings.html", role=role, user_list=user_list, msg=msg, flag=flag
    )


@views.route("/view_readings", methods=["POST", "GET"])
def view_readings():
    return render_template("view_readings.html")


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
    con = mysql.connector.connect(
    host="localhost", user="root", password="", database="dapp"
)
    cursor = con.cursor(buffered=False,dictionary=True)
    meter_reading = request.json["reading"]
    image = request.json["imgurl"]
    latitude = request.json["latitude"]
    longitude = request.json["longitude"]
    accuracy = request.json["accuracy"]
    current_location = (latitude, longitude)
    user_latitude = current_user.latitude
    user_longitude = current_user.longitude
    user_location = (user_latitude, user_longitude)
    if current_user.role == "superuser":
        username = request.json["selectedUser"]
    else:
        username = current_user.username

    query = "SELECT * FROM user WHERE username='{}'".format(username)
    cursor.execute(query)
    res = cursor.fetchall()
    if(len(res)>0):
        user_latitude = res[0]['latitude']
        user_longitude = res[0]['longitude']
        user_accuracy = res[0]['accuracy']
        user_location = (user_latitude, user_longitude)
    else:
        return jsonify(
            {
                "statusCode": 999,
                "msg": "Invalid Username Given"
            }
        )

    print(res)
    

    print(current_location)
    print(user_location)
    distance = geodesic(current_location, user_location).m
    print(distance)
    if distance <= (float(accuracy) + float(user_accuracy) + 200):
        today = datetime.today().strftime("%Y-%m-%d")
        try:
            query = "INSERT INTO readings (meter_reading,date, image, username,submitted_by) VALUES ('{}','{}','{}','{}','{}')".format(
                meter_reading, today, image, username, current_user.id
            )
            cursor.execute(query)
            con.commit()
            return jsonify(
                {"statusCode": 200, "msg": "Meter reading Submitted Sucessfully.!!"}
            )
        except errors.IntegrityError as e:
            return jsonify(
                {
                    "statusCode": 999,
                    "msg": "Meter reading Submission Failed,\nAs Todays reading of {}'s Meter is already Submitted.!!".format(
                        username
                    ),
                }
            )
    else:
        return jsonify(
            {
                "statusCode": 999,
                "msg": "Please Submit the Form While Standing near the {}'s Meter.!!".format(
                    username
                ),
            }
        )
