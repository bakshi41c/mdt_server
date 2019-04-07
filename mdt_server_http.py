import uuid
import log as logpy
from flask import Flask, request, jsonify
from flask_cors import CORS
from db import Database
import config
from authentication import Auth
import authorization
import jwt
import time

app = Flask(__name__)
CORS(app)
jwt_exp = 21600 # 6 hours to cover a MDT meeting - Future: Expire every 15 minutes, let client refresh
config = config.get_config()
db = Database(config["database"]["db_name"], config["database"]["ip"], config["database"]["port"])

log = logpy.get_logger('mdt_server_http.log')
auth = Auth(config)
jwt_secret = '8Co855M83e' # Only for development, generate new and keep it secret when deployed


def authenticate(deeid_login_sig_signed):
    uid = deeid_login_sig_signed['uID']
    dee_id = deeid_login_sig_signed['deeID']
    expiry = deeid_login_sig_signed['expirytime']
    data = deeid_login_sig_signed['data']
    sig=  deeid_login_sig_signed['signature']
    msg = uid + dee_id + expiry + data

    addr = auth.get_sig_address_from_signature(msg=msg, signature=sig)

    # TODO: Check with DeeId server if the deeidloginsigsined object is valid or not
    return auth.ethkey_in_deeid_contract(addr, dee_id)


def get_staff_from_auth_header(auth_header):
    if auth_header == '':
        return None
    jwt_token = auth_header.replace('Bearer ', '')
    claim = jwt.decode(jwt_token, jwt_secret)
    return db.get_staff(claim["staff_id"])


@app.route('/login', methods=['POST'])
def login():
    deeid_login_sig_signed = request.get_json(silent=True)
    authenticated = authenticate(deeid_login_sig_signed)
    if authenticated:
        # Generate JWT token
        token = jwt.encode({
            "staff_id" : deeid_login_sig_signed["deeID"],
            "exp" : int(time.time()) + jwt_exp
        }, jwt_secret).decode('utf-8')
        return jsonify({
            "token" : token
        })
    else:
        return "Unable to authenticate signature", 403


@app.route('/meetings')
def get_meetings():
    auth_header =request.headers.get('Authorization', '')
    print('Auth Header: ' + auth_header)
    staff = get_staff_from_auth_header(auth_header)
    if staff is None:
        return "Unable to authenticate, Check JWT", 403

    all_meetings = db.get_all_meetings()
    return jsonify(all_meetings)


@app.route('/meeting', methods=['POST'])
def create_meeting():
    # TODO: validate using JSON schema (Using Mongo validator)
    staff = get_staff_from_auth_header(request.headers.get('Authorization', ''))
    if staff is None:
        return "Unable to authenticate, Check JWT", 403

    meeting_data = request.get_json(silent=True)
    if meeting_data is None:
        return 404, "No Json Found"

    new_meeting_id = str(uuid.uuid4())
    meeting_data["_id"] = new_meeting_id
    res = db.insert_meeting(meeting_data)
    log.info("Inserted a new meeting: " + new_meeting_id)
    # TODO: Error handling

    for patient_id in meeting_data["patients"]:
        db.insert_patient_meeting_data(new_meeting_id, patient_id, {})

    return jsonify({"_id": new_meeting_id})


@app.route('/meeting/<meeting_id>')
def get_meeting(meeting_id):
    staff = get_staff_from_auth_header(request.headers.get('Authorization', ''))
    if staff is None:
        return "Unable to authenticate, Check JWT", 403

    meeting = db.get_meeting(meeting_id)
    if meeting is None:
        return "No meeting found" , 404

    roles = authorization.get_role(staff, meeting)

    if len(roles) == 0:
        return "Unauthorized" , 403

    return jsonify(meeting)


@app.route('/meeting/<meeting_id>', methods=['PUT'])
def update_meeting(meeting_id):
    meeting_data = request.get_json(silent=True)

    if meeting_data is None:
        return "No meeting data found in body"

    staff = get_staff_from_auth_header(request.headers.get('Authorization', ''))
    if staff is None:
        return "Unable to authenticate, Check JWT", 403

    meeting = db.get_meeting(meeting_id)
    if meeting is None:
        return "No meeting found", 404

    roles = authorization.get_role(staff, meeting)

    if authorization.Role.HOST not in roles:
        return "Unauthorized" , 403

    done = db.update_meeting(meeting_id, meeting_data)
    print(done)
    log.info("Updated meeting data: " + str(meeting_id))
    # TODO: Error handling

    return jsonify({"status": "updated"})


@app.route('/meeting/<meeting_id>', methods=['DELETE'])
def delete_meeting(meeting_id):
    staff = get_staff_from_auth_header(request.headers.get('Authorization', ''))
    if staff is None:
        return "Unable to authenticate, Check JWT", 403

    meeting = db.get_meeting(meeting_id)
    if meeting is None:
        return "No meeting found", 404

    roles = authorization.get_role(staff, meeting)

    if authorization.Role.HOST not in roles:
        return "Unauthorized", 403

    for patient_id in meeting["patients"]:  # Delete all meeting specific patient data
        db.delete_patient_meeting_data(meeting_id, patient_id)
    db.delete_meeting(meeting_id)
    log.info("Deleted meeting: " + meeting_id)
    # TODO: Error handling

    return jsonify({"status": "deleted"})


@app.route('/meeting/<meeting_id>/patient/<patient_id>')
def get_patient_meeting_data(meeting_id, patient_id):
    staff = get_staff_from_auth_header(request.headers.get('Authorization', ''))
    if staff is None:
        return "Unable to authenticate, Check JWT", 403

    meeting = db.get_meeting(meeting_id)
    if meeting is None:
        return "No meeting found", 404

    roles = authorization.get_role(staff, meeting)

    if len(roles) == 0:
        return "Unauthorized", 403

    patient_meeting_data = db.get_patient_meeting_data(meeting_id, patient_id)
    if patient_meeting_data is None:
        return "patient_meeting_data not found", 404

    return jsonify(patient_meeting_data)


@app.route('/meeting/<meeting_id>/patient/<patient_id>', methods=['PUT'])
def update_patient_meeting_data(meeting_id, patient_id):
    staff = get_staff_from_auth_header(request.headers.get('Authorization', ''))
    if staff is None:
        return "Unable to authenticate, Check JWT", 403

    meeting = db.get_meeting(meeting_id)
    if meeting is None:
        return "No meeting found", 404

    roles = authorization.get_role(staff, meeting)

    if authorization.Role.HOST not in roles:
        return "Unauthorized", 403

    patient_meeting_data = request.get_json(silent=True)
    if patient_meeting_data is None:
        return "No patient meeting data found in body", 404

    done = db.update_patient_meeting_data(meeting_id, update_meeting, patient_meeting_data)
    log.info("Updated patient-meeting data: M: " + meeting_id + ", P: " + patient_id)
    # TODO: Error handling

    return jsonify({"status": "updated"})


@app.route('/patients')
def get_all_patients():
    all_patients = db.get_all_patients()
    return jsonify(all_patients)


@app.route('/patient/<patient_id>')
def get_patient(patient_id):
    patient = db.get_patient(patient_id)
    if patient is None:
        return "patient not found", 404
    return jsonify(patient)


@app.route('/staff')
def get_all_staff():
    all_staff = db.get_all_staff()
    return jsonify(all_staff)


@app.route('/staff/<staff_id>')
def get_staff(staff_id):
    staff = db.get_staff(staff_id)
    if staff is None:
        return "staff not found", 404
    return jsonify(staff)


if __name__ == '__main__':
    app.run(host="localhost", port=51234)


##############################################
#               CODE DUMP                    #
##############################################

# @app.route('/event', methods=['POST'])
# def create_event():
#     event = request.get_json(silent=True)
#     new_event_id = str(uuid.uuid4())
#     event["_id"] = new_event_id
#     res = db.
#
#     # TODO: validate using JSON schema (Using Mongo validator)
#     log("Inserted a new event: " + new_event_id)
#     return jsonify({"_id": new_event_id})
#
#
# @app.route('/event/<event_id>', methods=['PUT'])
# def update_event(event_id):
#     event = request.get_json(silent=True)
#     done = events_col.update_one({"_id": event_id}, {'$set': event})
#     log("Updated event: ", event_id)
#     return "updated"
#
#
# @app.route('/events')  # FIXME: Remove during deployment
# def __get_all_events__():
#     all_events = db.get_all_events()
#     return jsonify(all_events)
#
#
# @app.route('/event/<event_id>')
# def get_event(event_id):
#     events = db.get_event(event_id)
#     return jsonify(events)
