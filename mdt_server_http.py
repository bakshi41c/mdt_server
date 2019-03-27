import uuid
import log as logpy
from flask import Flask, request, jsonify
from flask_cors import CORS
from db import Database
import config
import authorization

app = Flask(__name__)

CORS(app)

config = config.get_config()
db = Database(config["database"]["db_name"], config["database"]["ip"], config["database"]["port"])

log = logpy.get_logger('mdt_server_http.log')


@app.route('/meetings')
def get_meetings():
    all_meetings = db.get_all_meetings()
    return jsonify(all_meetings)


@app.route('/meeting', methods=['POST'])
def create_meeting():
    # TODO: validate using JSON schema (Using Mongo validator)
    meeting = request.get_json(silent=True)
    if meeting is None:
        return 404, "No Json Found"
    # TODO: Think about meeting id
    new_meeting_id = str(uuid.uuid4())
    meeting["_id"] = new_meeting_id
    res = db.insert_meeting(meeting)

    log.info("Inserted a new meeting: " + new_meeting_id)
    # TODO: Error handling

    for patient_id in meeting["patients"]:
        db.insert_patient_meeting_data(new_meeting_id, patient_id, {})

    return jsonify({"_id": new_meeting_id})


@app.route('/meeting/<meeting_id>')
def get_meeting(meeting_id):
    # authorization.get_role()
    meeting = db.get_meeting(meeting_id)
    if meeting is None:
        return "meeting not found", 404
    return jsonify(meeting)


@app.route('/meeting/<meeting_id>', methods=['PUT'])
def update_meeting(meeting_id):
    # TODO: Error handling
    meeting = request.get_json(silent=True)
    done = db.update_meeting(meeting_id, meeting)
    log.info("Updated meeting data: " + str(meeting_id))
    return jsonify({"status": "updated"})


@app.route('/meeting/<meeting_id>', methods=['DELETE'])
def delete_meeting(meeting_id):
    # TODO: Error handling
    meeting = db.get_meeting(meeting_id)
    for patient_id in meeting["patients"]:  # Delete all meeting specific patient data
        db.delete_patient_meeting_data(meeting_id, patient_id)
    db.delete_meeting(meeting_id)
    log.info("Deleted meeting: " + meeting_id)
    return jsonify({"status": "deleted"})


@app.route('/meeting/<meeting_id>/patient/<patient_id>')
def get_patient_meeting_data(meeting_id, patient_id):
    patient_meeting_data = db.get_patient_meeting_data(meeting_id, patient_id)
    if patient_meeting_data is None:
        return "patient_meeting_data not found", 404
    return jsonify(patient_meeting_data)


@app.route('/meeting/<meeting_id>/patient/<patient_id>', methods=['PUT'])
def update_patient_meeting_data(meeting_id, patient_id):
    # TODO: Error handling
    patient_meeting_data = request.get_json(silent=True)
    done = db.update_patient_meeting_data(meeting_id, update_meeting, patient_meeting_data)
    log.info("Updated patient-meeting data: M: " + meeting_id + ", P: " + patient_id)
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
