from flask import Flask, request, jsonify
import pymongo

app = Flask(__name__)
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


@app.route('/meetings')  # FIXME: Remove during deployment
def __get_meetings__():
    all_meetings = meeting_col.find()
    return jsonify(all_meetings)


@app.route('/meeting/<meeting_id>')
def get_meeting(meeting_id):
    # TODO: Permission
    meeting_col.find({"_id": meeting_id})


@app.route('/meeting', methods=['POST'])
def create_meeting():
    meeting = request.get_json(silent=True)
    mid = meeting_col.insert_one(meeting)  # TODO: validate using JSON schema (Using Mongo validator)
    log("Inserted a new meeting: " + mid)
    # TODO: Error handling
    # TODO: Think about meeting id - ?
    return mid


@app.route('/meeting/<meeting_id>', methods=['PUT'])
def update_meeting(meeting_id):
    # TODO: Error handling
    meeting = request.get_json(silent=True)
    done = meeting_col.update_one({"_id" : meeting_id}, meeting)
    log("Updated meeting data: ", meeting_id)
    return


@app.route('/meeting/<meeting_id>/patient/<patient_id>')
def get_patient_meeting_data(meeting_id, patient_id):
    patient_meeting_data = patient_meeting_data_col.find({"_id": patient_id, "meeting_id": meeting_id})
    return jsonify(patient_meeting_data)


@app.route('/meeting/<meeting_id>/patient/<patient_id>', methods=['PUT'])
def update_patient_meeting_data(meeting_id, patient_id):
    # TODO: Error handling
    patient_meeting_data = request.get_json(silent=True)
    done = patient_meeting_data_col.update_one({"meeting_id": meeting_id, "patient_id": patient_id}, patient_meeting_data)
    log("Updated patient-meeting data: ", meeting_id, patient_id)
    return


@app.route('/event/<event_id>')
def get_event(event_id):
    events = meeting_col.find({"_id": event_id})
    return jsonify(events)


@app.route('/event', methods=['POST'])
def create_event():
    event = request.get_json(silent=True)
    eid = events_col.insert_one(event)  # TODO: validate using JSON schema (Using Mongo validator)
    log("Inserted a new event: " + eid)


@app.route('/event/<event_id>', methods=['PUT'])
def update_event(event_id):
    event = request.get_json(silent=True)
    done = events_col.update_one({"_id": event_id}, event)
    log("Updated event: ", event_id)


@app.route('/staff/<staff_id>')
def get_patient(staff_id):
    staff = staff_col.find({"_id": staff_id})
    return jsonify(staff)


@app.route('/events')  # FIXME: Remove during deployment
def __get_all_events__():
    all_events = events_col.find()

    return jsonify(all_events)


@app.route('/patients')
def get_patients():
    all_patients = patient_col.find()

    return jsonify(all_patients)


@app.route('/staff')
def get_staff():
    all_staff = staff_col.find()

    return jsonify(all_staff)


def log(*args, **kwargs):
    print(args, kwargs)


if __name__ == '__main__':
    app.run()
