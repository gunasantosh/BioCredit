from flask import Blueprint
from flask import render_template, jsonify, request
from flask_login import login_required, current_user
from .models import User
import mysql.connector
from mysql.connector import errors
from datetime import datetime
from geopy.distance import geodesic


views = Blueprint("views", __name__)

con = mysql.connector.connect(
    host="localhost", user="root", password="mypassword", database="dapp"
)
cursor = con.cursor(buffered=True)


@views.route("/")
@views.route("/home")
def home():
    return render_template("index.html")


@views.route("/dashboard",methods=['GET','POST'])
@login_required
def dashboard():
    msg=None
    if(request.method=='GET'):
        msg=request.args.get('msg')
    role = current_user.role
    user_list = User.query.filter_by(role="user").all()
    return render_template("dashboard.html", role=role, user_list=user_list,msg=msg)


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
    meter_reading = request.json["reading"]
    image = request.json["imgurl"]
    latitude=request.json['latitude']
    longitude=request.json['longitude']
    accuracy=request.json['accuracy']
    current_location=(latitude,longitude)
    user_latitude=current_user.latitude
    user_longitude=current_user.longitude
    user_location=(user_latitude,user_longitude)
    if(current_user.role=='superuser'):
        username = request.json["selectedUser"]
    else:
        username = current_user.username

    query = "SELECT * FROM user WHERE username='{}'".format(username)
    cursor.execute(query)
    res=cursor.fetchall()
    print(res)
    user_latitude=res[0][5]
    user_longitude=res[0][6]
    user_accuracy=res[0][7]
    user_location=(user_latitude,user_longitude)
    
    print(current_location)
    print(user_location)
    distance=geodesic(current_location,user_location).m
    print(distance)
    if(distance<=(float(accuracy)+float(user_accuracy)+200)):
        today=datetime.today().strftime('%Y-%m-%d')
        try:
            query = "INSERT INTO readings (meter_reading,date, image, username) VALUES ('{}','{}','{}','{}')".format(
                meter_reading,today, image, username
            )
            cursor.execute(query)
            con.commit()
            return jsonify({"statusCode":200,"msg":"Meter reading Submitted Sucessfully.!!"})
        except errors.IntegrityError as e:
            return jsonify({"statusCode":999,"msg":"Meter reading Submission Failed,\nAs Todays reading of {}'s Meter is already Submitted.!!".format(username)})
    else:
        return jsonify({"statusCode":999,"msg":"Please Submit the Form While Standing near the {}'s Meter.!!".format(username)})