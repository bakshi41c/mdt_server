import uuid

from flask import Flask, request, jsonify
from flask_cors import CORS
from random import randint

import pymongo

app = Flask(__name__)
CORS(app)
DB_NAME = "mdt_meetings"
DB_IP = "localhost"
DB_PORT = "27017"

mongo_client = pymongo.MongoClient("mongodb://" + DB_IP + ":" + DB_PORT + "/")
db = mongo_client[DB_NAME]
meeting_col = db["meeting"]
events_col = db["events"]
staff_col = db["staff"]
patient_col = db["patient"]
patient_meeting_data_col = db["patient_meeting_data"]


@app.route('/meetings')
def get_meetings():
    all_meetings = list(meeting_col.find())
    print(all_meetings)
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
    res = meeting_col.insert_one(meeting)
    log("Inserted a new meeting: " + new_meeting_id)
    # TODO: Error handling

    for patient_id in meeting["patients"]:
        patient_meeting_data_col.insert_one({
            "meeting_id": new_meeting_id,
            "patient_id": patient_id,
            "mdt_outcome": "",
            "mdt_question": "",
            "group": "",
            "lc": "",
            "investigation": "",
            "surgery": "",
        })

    return jsonify({"_id": new_meeting_id})


@app.route('/meeting/<meeting_id>')
def get_meeting(meeting_id):
    # TODO: Permission
    meeting = meeting_col.find_one({"_id": meeting_id})
    return jsonify(meeting)


@app.route('/meeting/<meeting_id>', methods=['PUT'])
def update_meeting(meeting_id):
    # TODO: Error handling
    meeting = request.get_json(silent=True)
    done = meeting_col.update_one({"_id": meeting_id}, {'$set': meeting})
    log("Updated meeting data: ", meeting_id)
    return "updated"


@app.route('/meeting/<meeting_id>', methods=['DELETE'])
def delete_meeting(meeting_id):
    # TODO: Error handling
    meeting = meeting_col.find_one({"_id": meeting_id})
    for patient_id in meeting["patients"]:  # Delete all meeting specific patient data
        patient_meeting_data_col.delete_one({"meeting_id": meeting_id, "patient_id": patient_id})
    meeting_col.delete_one({"_id": meeting_id})
    log("Deleted meeting: ", meeting_id)
    return "deleted"


@app.route('/meeting/<meeting_id>/start')
def join_meeting(meeting_id):
    # TODO: Permission
    otp_code = randint(1000, 9999)
    return jsonify({'otp': otp_code})


@app.route('/meeting/<meeting_id>/patient/<patient_id>')
def get_patient_meeting_data(meeting_id, patient_id):
    patient_meeting_data = patient_meeting_data_col.find_one({"meeting_id": meeting_id, "patient_id": patient_id})
    return jsonify(patient_meeting_data)


@app.route('/meeting/<meeting_id>/patient/<patient_id>', methods=['PUT'])
def update_patient_meeting_data(meeting_id, patient_id):
    # TODO: Error handling
    patient_meeting_data = request.get_json(silent=True)
    done = patient_meeting_data_col.update_one({"meeting_id": meeting_id, "patient_id": patient_id},
                                               {'$set': patient_meeting_data})
    log("Updated patient-meeting data: ", meeting_id, patient_id)
    return "updated"


@app.route('/events')  # FIXME: Remove during deployment
def __get_all_events__():
    all_events = list(events_col.find())

    return jsonify(all_events)


@app.route('/event/<event_id>')
def get_event(event_id):
    events = events_col.find_one({"_id": event_id})
    return jsonify(events)


@app.route('/event', methods=['POST'])
def create_event():
    event = request.get_json(silent=True)
    new_event_id = str(uuid.uuid4())
    event["_id"] = new_event_id
    res = events_col.insert_one(event)  # TODO: validate using JSON schema (Using Mongo validator)
    log("Inserted a new event: " + new_event_id)
    return jsonify({"_id": new_event_id})


@app.route('/event/<event_id>', methods=['PUT'])
def update_event(event_id):
    event = request.get_json(silent=True)
    done = events_col.update_one({"_id": event_id}, {'$set': event})
    log("Updated event: ", event_id)
    return "updated"


@app.route('/patients')
def get_all_patients():
    all_patients = list(patient_col.find())

    return jsonify(all_patients)


@app.route('/patient/<patient_id>')
def get_patient(patient_id):
    patient = patient_col.find_one({"_id": patient_id})
    return jsonify(patient)


@app.route('/staff')
def get_all_staff():
    all_staff = list(staff_col.find())
    return jsonify(all_staff)


@app.route('/staff/<staff_id>')
def get_staff(staff_id):
    staff = staff_col.find_one({"_id": staff_id})
    return jsonify(staff)


def log(*args, **kwargs):
    print(args, kwargs)


if __name__ == '__main__':
    app.run(port='51234')
