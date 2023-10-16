from flask import Blueprint
from flask import render_template, jsonify, request, redirect,url_for
from flask_login import login_required, current_user
from .models import User
import mysql.connector
from mysql.connector import errors
from datetime import datetime,time,timedelta
from geopy.distance import geodesic
import segno
from cryptography.fernet import Fernet
import website.contract.contract as contract
from website import db_host,db_name,db_password,db_user,BASE_URL
from beaker import client, sandbox
from algosdk.v2client import algod,indexer
from algosdk import mnemonic
from dotenv import load_dotenv
import os,hashlib,requests,json
load_dotenv("../.env")

API_KEY=os.getenv('API_KEY')
PUBLIC_KEY=os.getenv('PUBLIC_KEY')
MNEMONIC=os.getenv('MNEMONIC')
PINATA_KEY=os.getenv('PINATA_KEY')
PINATA_SECRET_KEY=os.getenv('PINATA_SECRET_KEY')
APP_ID=433686116


views = Blueprint("views", __name__)
key = b"Jxb-gEda5CtPcq-z2oiCDbIYzUbe9C_ooa_CTl_QCEs="


def hashTuple(tup:tuple) -> str:
    tuple_str = str(tup)
    hash_object = hashlib.sha256()
    hash_object.update(tuple_str.encode('utf-8'))
    hash_hex = hash_object.hexdigest()
    return hash_hex

def pin_json(json_):
    url = "https://api.pinata.cloud/pinning/pinJSONToIPFS"
    res=dict()
    res['pinataContent']=json_
    payload = json.dumps(res)
    print('apikey',API_KEY)
    print(type(PINATA_KEY))
    headers = {
    'Content-Type': 'application/json',
    'pinata_api_key': PINATA_KEY,
    'pinata_secret_api_key': PINATA_SECRET_KEY 
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    return json.loads(response.text)


def is_time_between(start_time, end_time, check_time=None):
    # If check time is not given, default to current time
    check_time = check_time or datetime.now().time()
    if start_time < end_time:
        return start_time <= check_time <= end_time
    else:  # crosses midnight
        return check_time >= start_time or check_time <= end_time
    

# Explorer
@views.route("/explorer", methods=["GET", "POST"])
def explorer():
    now = datetime.now()
    one_day_ago = now - timedelta(days=1)
    twenty_eight_days_ago = now - timedelta(days=28)
    con = mysql.connector.connect(
            host=db_host , user=db_user, password=db_password, database=db_name
        )
    cursor = con.cursor(buffered=False, dictionary=True)
    print(one_day_ago.strftime('%Y-%m-%d %H:%M:%S'))
    one_q="SELECT COUNT(*) AS rowcount FROM readings WHERE timestamp>'{}'".format(one_day_ago.strftime('%Y-%m-%d %H:%M:%S'))
    twenty_q="SELECT COUNT(*) AS rowcount FROM readings WHERE timestamp>'{}'".format(twenty_eight_days_ago.strftime('%Y-%m-%d %H:%M:%S'))
    cursor.execute(one_q)
    one_r=cursor.fetchone()
    last_one_day_count=one_r['rowcount']
    cursor.execute(twenty_q)
    twenty_r=cursor.fetchone()
    last_twenty_eight_days_count=twenty_r['rowcount']
    one_day_avg_q = "SELECT date, COUNT(*) AS NumberOfRecords FROM readings GROUP BY date"
    cursor.execute(one_day_avg_q)
    one_day_avg_res=cursor.fetchall()
    total=0
    counter=0
    for row in one_day_avg_res:
        total+=row['NumberOfRecords']
        counter+=1
    one_day_avg=round(total/counter,2)
    month_avg_q = "SELECT EXTRACT(MONTH FROM date) AS Month, COUNT(*) AS NumberOfRecords FROM readings GROUP BY EXTRACT(MONTH FROM date)"
    cursor.execute(month_avg_q)
    month_avg_res = cursor.fetchall()
    total=0
    counter=0
    for row in month_avg_res:
        total+=row['NumberOfRecords']
        counter+=1
    month_avg = round(total/counter,2)
    latest_q="SELECT * FROM readings ORDER BY date DESC LIMIT 10"
    cursor.execute(latest_q)
    latest_readings=cursor.fetchall()
    acct=sandbox.SandboxAccount(address=os,private_key=mnemonic.to_private_key(MNEMONIC))
    algod_client = algod.AlgodClient('', 'https://testnet-algorand.api.purestake.io/ps2', {"X-API-Key": API_KEY})
    app_client = client.ApplicationClient(
                algod_client, contract.app, signer=acct.signer,app_id=APP_ID
            )
    indexer_client = indexer.IndexerClient('', 'https://testnet-algorand.api.purestake.io/idx2', {"X-API-Key": API_KEY})
    box_names=app_client.get_box_names()
    box_contents=[app_client.get_box_contents(name) for name in box_names]
    previous_hashes = dict()
    for i,val in enumerate(box_names):
        print(type(box_contents[i].decode('utf-8')))
        previous_hashes[val.decode('utf-8')]=json.loads(box_contents[i].decode('utf-8').replace('\'','"'))
    return render_template("explorer.html",last_one_day_count=last_one_day_count,last_twenty_eight_days_count=last_twenty_eight_days_count
                           ,one_day_avg=one_day_avg,month_avg=month_avg,latest_readings=latest_readings,previous_hashes=previous_hashes)

@views.route("/send_hash",methods=['GET'])
def send_hash():
    if(is_time_between(time(23,49), time(23,59))):
        con = mysql.connector.connect(
            host=db_host , user=db_user, password=db_password, database=db_name
        )
        cursor = con.cursor(buffered=False, dictionary=True)
        today=datetime.today().strftime("%Y-%m-%d")
        q="SELECT * FROM readings WHERE date='{}' ORDER BY timestamp ASC".format(today)
        cursor.execute(q)
        rows=cursor.fetchall()
        if(len(rows)>0):
            acct=sandbox.SandboxAccount(address=os,private_key=mnemonic.to_private_key(MNEMONIC))
            algod_client = algod.AlgodClient('', 'https://testnet-algorand.api.purestake.io/ps2', {"X-API-Key": API_KEY})
            app_client = client.ApplicationClient(
                algod_client, contract.app, signer=acct.signer,app_id=APP_ID
            )
            global_state=app_client.get_global_state()
            lastHash = global_state['lastHash']
            json={"date":today,"lastHash":lastHash,"entries":[]}
            overall_tup = [lastHash]
            for row in rows:
                tupl = tuple([row['username'],row['date'],row['timestamp'],row['meter_reading'],row['image'],row['submitted_by']])
                hassh = hashTuple(tupl)
                json['entries'].append({row['username']:hassh})
                overall_tup.append(hassh)
            overall_hash = hashTuple(tuple(overall_tup))
            json['overall_hash']=overall_hash
            pin_res=pin_json(json)
            if('IpfsHash' in pin_res.keys()):
                cid=pin_res['IpfsHash']
                boxes=[(app_client.app_id,today)]
                res = app_client.call(contract.add_dayhash,boxes=boxes,date=today,hash=overall_hash,cid=cid)
                if(res.return_value=="Updated Hash Successfully.!!"):
                    return jsonify({"statusCode":200,"msg":"Success, Hash Generated & Uploaded For {}.<br>Click Following Links For <a target='_blank' style='color:#01FE43;' href='https://testnet.algoexplorer.io/tx/{}'>Txn</a> & <a style='color:#01FE43;' target='_blank' href='https://ipfs.io/ipfs/{}'>Data Hashes</a>".format(datetime.today().strftime("%b %dth, %Y"),res.tx_id,cid)})
                else:
                    return jsonify({"statusCode":400,"msg":"Hash Already Updated For {}.".format(datetime.today().strftime("%b %dth, %Y"))})
            else:
                return jsonify({"statusCode":500,"msg":"Pinning Hashes To IPFS Failed.",'r':pin_res})
        else:
            return jsonify({"statusCode":202,"msg":"No Entries Available Today To Generate Hash."})
    else:
        return jsonify({"statusCode":400,"msg":"This API is accessible from 23:49 PM to 23:59 PM."})





@views.route("/")
@views.route("/home")
def home():
    return render_template("index.html")


@views.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    fernet = Fernet(key)
    encMessage = fernet.encrypt(current_user.username.encode()).decode()
    qrcode = segno.make(
        "{}qr_redirect?secret={}".format(BASE_URL,encMessage)
    )
    return render_template("dashboard.html", current_user=current_user, qrcode=qrcode)

@views.route('/qr_redirect',methods=["GET"])
def qr_redirect():
    con = mysql.connector.connect(
        host=db_host , user=db_user, password=db_password, database=db_name
    )
    cursor = con.cursor(buffered=False, dictionary=True)
    if(request.args['secret']!=None):
        secret = request.args['secret']
        fernet = Fernet(key)
        username = fernet.decrypt(secret).decode()
        qrcode = segno.make(
        "{}qr_redirect?secret={}".format(BASE_URL,secret)
    )
        user_data=cursor.execute("SELECT * FROM user WHERE username='{}'".format(username))
        user_data=cursor.fetchall()
        user_data=user_data[0]
        if user_data['role'] == "user":
            th = """<th>S.no</th>
                <th>Date</th>
                <th>Reading</th>
                <th>Taken By</th>
                <th>Actions</th>"""
        else:
            th = """<th>S.no</th>
                <th>Date</th>
                <th>Username</th>
                <th>Reading</th>
                <th>Actions</th>"""
        if(current_user.is_authenticated):
            if(current_user.role=='superuser'):
                return redirect(url_for('views.capture_readings',selected=username))
            else:
                return render_template("external_profile.html",base='base.html',current_user=user_data,qrcode=qrcode,th=th,role=user_data['role'])
        else:
            return render_template("external_profile.html",base='base.html',current_user=user_data,qrcode=qrcode,th=th,role=user_data['role'])


@views.route("/capture_readings", methods=["POST", "GET"])
def capture_readings():
    con = mysql.connector.connect(
        host=db_host , user=db_user, password=db_password, database=db_name
    )
    cursor = con.cursor(buffered=False, dictionary=True)
    msg = None
    if request.method == "GET":
        msg = request.args.get("msg")
    selected = request.args.get('selected')
    role = current_user.role
    user_list = None
    flag = True
    today = datetime.today().strftime("%Y-%m-%d")
    if role == "superuser":
        q = "SELECT * FROM user WHERE role='user' AND 0 IN (SELECT COUNT(*) FROM readings WHERE readings.username=user.username AND timestamp>='{} 00:00:00' AND timestamp<='{} 23:59:59')".format(
            today, today
        )
        cursor.execute(q)
        ress = cursor.fetchall()
        if len(ress) > 0:
            user_list = ress
        else:
            user_list = []
            flag = False
    else:
        q = "SELECT * FROM readings WHERE username='{}' AND timestamp>='{} 00:00:00' AND timestamp<='{} 23:59:59'".format(
            current_user.username, today, today
        )
        cursor.execute(q)
        ress = cursor.fetchall()
        if len(ress) > 0:
            flag = False

    return render_template(
        "capture_readings.html", role=role, user_list=user_list, msg=msg, flag=flag, selected=selected
    )


@views.route("/view_readings", methods=["POST", "GET"])
def view_readings():
    if current_user.role == "user":
        th = """<th>S.no</th>
                <th>Date</th>
                <th>Reading</th>
                <th>Taken By</th>
                <th>Actions</th>"""
    else:
        th = """<th>S.no</th>
                <th>Date</th>
                <th>Username</th>
                <th>Reading</th>
                <th>Actions</th>"""
    role = current_user.role
    username = current_user.username

    return render_template("view_readings.html", th=th, role=role, username=username)


@views.route("/view_mimage", methods=["GET"])
def view_mimage():
    if request.args["date"] not in ["", None] and request.args["username"] not in [
        "",
        None,
    ]:
        con = mysql.connector.connect(
        host=db_host , user=db_user, password=db_password, database=db_name
        )
        cursor = con.cursor(buffered=False, dictionary=True)
        q = "SELECT image FROM readings WHERE username='{}' AND date='{}'".format(
            request.args["username"], request.args["date"]
        )
        cursor.execute(q)
        res = cursor.fetchall()
        if len(res) > 0:
            return (
                "<body style='display:block;background-color:black;height:100%;margin:0;'><img style='margin:auto;display:block;cursor:zoom-in;-webkit-user-select: none;' src='"
                + res[0]["image"]
                + "'></img></body>"
            )
        else:
            return "Image not available"
    else:
        return "Parameters Required"


@views.route("/modReadings", methods=["POST", "GET"])
def modReadings():
    try:
        con = mysql.connector.connect(
        host=db_host , user=db_user, password=db_password, database=db_name
        )
        cursor = con.cursor(buffered=False, dictionary=True)
        if request.method == "GET":
            draw = request.args.get("draw")
            row = int(request.args["start"])
            rowperpage = int(request.args["length"])
            searchValue = request.args["search[value]"]
            username = request.args["username"]

            ## Total number of records without filtering
            cursor.execute(
                "select count(*) as allcount from readings r INNER JOIN user u ON u.id=r.submitted_by WHERE u.username='{}'".format(
                    username
                )
            )
            rsallcount = cursor.fetchone()
            totalRecords = rsallcount["allcount"]

            ## Total number of records with filtering
            if searchValue != "":
                likeString = "%" + searchValue + "%"
                cursor.execute(
                    "SELECT count(*) as allcount from readings r INNER JOIN user u ON u.id=r.submitted_by WHERE (r.timestamp LIKE '{}' OR r.username LIKE '{}' OR r.meter_reading LIKE '{}') AND u.username='{}'".format(
                        likeString, likeString, likeString, username
                    )
                )
                rsallcount = cursor.fetchone()
                totalRecordwithFilter = rsallcount["allcount"]
            else:
                totalRecordwithFilter = totalRecords

            ## Sorting values
            columns = ["", "timestamp", "username", "meter_reading", ""]
            sort_column = request.args["order[0][column]"]
            sort_mode = request.args["order[0][dir]"]
            ## Fetch records
            if searchValue == "":
                if columns[int(sort_column)] != "":
                    cursor.execute(
                        "SELECT r.* FROM readings r INNER JOIN user u ON u.id=r.submitted_by WHERE u.username='{}' ORDER BY r.{} {} limit {}, {};".format(
                            username,
                            columns[int(sort_column)],
                            sort_mode,
                            row,
                            rowperpage,
                        )
                    )
                    finallist = cursor.fetchall()
                else:
                    cursor.execute(
                        "SELECT r.* FROM readings r INNER JOIN user u ON u.id=r.submitted_by WHERE u.username='{}' limit {}, {};".format(
                            username, row, rowperpage
                        )
                    )
                    finallist = cursor.fetchall()
            else:
                if columns[int(sort_column)] != "":
                    cursor.execute(
                        "SELECT r.* FROM readings r INNER JOIN user u ON u.id=r.submitted_by WHERE (r.timestamp LIKE '{}' OR r.username LIKE '{}' OR r.meter_reading LIKE '{}') AND u.username='{}' ORDER BY r.{} {} limit {}, {};".format(
                            likeString,
                            likeString,
                            likeString,
                            username,
                            columns[int(sort_column)],
                            sort_mode,
                            row,
                            rowperpage,
                        )
                    )
                    finallist = cursor.fetchall()
                else:
                    cursor.execute(
                        "SELECT r.* FROM readings r INNER JOIN user u ON u.id=r.submitted_by WHERE (r.timestamp LIKE '{}' OR r.username LIKE '{}' OR r.meter_reading LIKE '{}') AND u.username='{}' limit {}, {};".format(
                            likeString,
                            likeString,
                            likeString,
                            username,
                            row,
                            rowperpage,
                        )
                    )
                    finallist = cursor.fetchall()

            data = []
            i = 0
            for row in finallist:
                i += 1
                data.append(
                    {
                        "sno": i,
                        "date": row["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                        "username": row["username"],
                        "reading": row["meter_reading"],
                        "action": row["date"].strftime("%Y-%m-%d"),
                    }
                )

            response = {
                "draw": int(draw),
                "recordsTotal": totalRecords,
                "recordsFiltered": totalRecordwithFilter,
                "data": data,
            }
            return jsonify(response)
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        con.close()


@views.route("/userReadings", methods=["POST", "GET"])
def userReadings():
    try:
        con = mysql.connector.connect(
        host=db_host , user=db_user, password=db_password, database=db_name
        )
        cursor = con.cursor(buffered=False, dictionary=True)
        if request.method == "GET":
            draw = request.args.get("draw")
            row = int(request.args["start"])
            rowperpage = int(request.args["length"])
            searchValue = request.args["search[value]"]
            username = request.args["username"]

            ## Total number of records without filtering
            cursor.execute(
                "select count(*) as allcount from readings r INNER JOIN user u ON u.id=r.submitted_by WHERE r.username='{}'".format(
                    username
                )
            )
            rsallcount = cursor.fetchone()
            totalRecords = rsallcount["allcount"]

            ## Total number of records with filtering
            if searchValue != "":
                likeString = "%" + searchValue + "%"
                cursor.execute(
                    "SELECT count(*) as allcount from readings r INNER JOIN user u ON u.id=r.submitted_by WHERE (r.timestamp LIKE '{}' OR u.username LIKE '{}' OR r.meter_reading LIKE '{}') AND r.username='{}'".format(
                        likeString, likeString, likeString, username
                    )
                )
                rsallcount = cursor.fetchone()
                totalRecordwithFilter = rsallcount["allcount"]
            else:
                totalRecordwithFilter = totalRecords

            ## Sorting values
            columns = ["", "r.timestamp", "r.meter_reading", "u.username", ""]
            sort_column = request.args["order[0][column]"]
            sort_mode = request.args["order[0][dir]"]
            ## Fetch records
            if searchValue == "":
                if columns[int(sort_column)] != "":
                    cursor.execute(
                        "SELECT * FROM readings r INNER JOIN user u ON u.id=r.submitted_by WHERE r.username='{}' ORDER BY {} {} limit {}, {};".format(
                            username,
                            columns[int(sort_column)],
                            sort_mode,
                            row,
                            rowperpage,
                        )
                    )
                    finallist = cursor.fetchall()
                else:
                    cursor.execute(
                        "SELECT * FROM readings r INNER JOIN user u ON u.id=r.submitted_by WHERE r.username='{}' limit {}, {};".format(
                            username, row, rowperpage
                        )
                    )
                    finallist = cursor.fetchall()
            else:
                if columns[int(sort_column)] != "":
                    cursor.execute(
                        "SELECT * FROM readings r INNER JOIN user u ON u.id=r.submitted_by WHERE (r.timestamp LIKE '{}' OR u.username LIKE '{}' OR r.meter_reading LIKE '{}') AND r.username='{}' ORDER BY {} {} limit {}, {};".format(
                            likeString,
                            likeString,
                            likeString,
                            username,
                            columns[int(sort_column)],
                            sort_mode,
                            row,
                            rowperpage,
                        )
                    )
                    finallist = cursor.fetchall()
                else:
                    cursor.execute(
                        "SELECT * FROM readings r INNER JOIN user u ON u.id=r.submitted_by WHERE (r.timestamp LIKE '{}' OR u.username LIKE '{}' OR r.meter_reading LIKE '{}') AND r.username='{}' limit {}, {};".format(
                            likeString,
                            likeString,
                            likeString,
                            username,
                            row,
                            rowperpage,
                        )
                    )
                    finallist = cursor.fetchall()

            data = []
            i = 0
            for row in finallist:
                i += 1
                data.append(
                    {
                        "sno": i,
                        "date": row["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                        "submitted_by": row["username"],
                        "reading": row["meter_reading"],
                        "action": row["date"].strftime("%Y-%m-%d"),
                    }
                )

            response = {
                "draw": int(draw),
                "recordsTotal": totalRecords,
                "recordsFiltered": totalRecordwithFilter,
                "data": data,
            }
            return jsonify(response)
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        con.close()


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
        host=db_host , user=db_user, password=db_password, database=db_name
    )
    cursor = con.cursor(buffered=False, dictionary=True)
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
    if len(res) > 0:
        user_latitude = res[0]["latitude"]
        user_longitude = res[0]["longitude"]
        user_accuracy = res[0]["accuracy"]
        user_location = (user_latitude, user_longitude)
    else:
        return jsonify({"statusCode": 999, "msg": "Invalid Username Given"})

    distance = geodesic(current_location, user_location).m
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



