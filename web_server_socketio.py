import json
import time

from flask_socketio import send as send_ws, close_room
from flask_socketio import emit as emit_ws
from flask_socketio import join_room, leave_room
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from enum import Enum
from db import Database
import config
from authorization import Role, get_role
import authentication as auth
import copy
from meeting_event import ack_event_template, MeetingEventType
import event_schema_validator
import log

app = Flask(__name__)

app.config['SECRET_KEY'] = 'TVBam9S&W7IbTC8W'

socketio = SocketIO(app)
CORS(app)

config = config.get_config()
db = Database(config["database"]["db_name"], config["database"]["ip"], config["database"]["port"])
log = log.get_logger('web_server_socketio.py')

timestamp_tolerance = 10  # seconds

ongoing_meetings = {}


def start(event, staff, meeting, roles) -> (bool, dict):
    # Check if the user is allowed to start
    if Role.HOST not in roles:
        return False, get_ack(event["eventId"], event["meetingId"],
                              content={"details": {"errorCode": EventStreamError.UNAUTHORISED.value}},
                              ack_type=MeetingEventType.ACK_ERR.value)

    # Check if meeting has already started, if it has send the otp, in case the host has forgotten
    started, _ = validate_meeting_started(event, meeting)
    if started:
        otp = ongoing_meetings[meeting["_id"]]["otp"]
        return False, get_ack(event["eventId"], event["meetingId"],
                              content={"details": {"otp": otp,
                                                   "errorCode": EventStreamError.UNAUTHORISED.value}},
                              ack_type=MeetingEventType.ACK_ERR.value)

    # Create the meeting details
    ongoing_meetings[meeting["_id"]] = {
        "otp": event["content"]["otp"],
        "host": staff["_id"],
        "joined_participants": [staff["_id"]],
        "start_event": event,
        "events": {
            event["eventId"] : event
        },
        "polls": {},
        "unref_events": {}  # Events that havent been referenced, needed for when the meeting ends
    }

    # ACK
    ack = get_ack(event["eventId"], event["meetingId"])
    return True, ack


def join(event, staff, meeting, roles) -> (bool, dict):
    # Check if the user is allowed to join
    if Role.PARTICIPANT not in roles:
        return False, get_ack(event["eventId"], event["meetingId"],
                              content={"details": {"errorCode": EventStreamError.UNAUTHORISED.value}},
                              ack_type=MeetingEventType.ACK_ERR.value)

    # Check if meeting has started
    ok, err_ack = validate_meeting_started(event, meeting)
    if not ok:
        return False, err_ack

    meeting_session_details = ongoing_meetings.get(meeting["_id"], None)

    # Check OTP
    if not event["content"]["otp"] == meeting_session_details["otp"]:
        return False, get_ack(event["eventId"], event["meetingId"],
                              content={"details": {"errorCode": EventStreamError.BAD_OTP.value}},
                              ack_type=MeetingEventType.ACK_ERR.value)

    # Add user to the participants who have joined
    if staff["_id"] not in meeting_session_details["joined_participants"]:
        meeting_session_details["joined_participants"].append(staff["_id"])

    # Join the socketio room using the sessison_id
    join_room(meeting["_id"])

    start_event = ongoing_meetings[meeting["_id"]]["start_event"]
    # ACK
    ack = get_ack(event["eventId"], event["meetingId"], content={
        "details": {
            "startEvent": json.dumps(start_event)
        }
    }, ack_type=MeetingEventType.ACK_JOIN.value)
    return True, ack


def leave(event, staff, meeting):
    # Check if meeting actually started
    ok, err_ack = validate_meeting_started(event, meeting)
    if not ok:
        return False, err_ack

    # Check if they have actually joined
    ok, err_ack = validate_join(event, staff, meeting)
    if not ok:
        return False, err_ack

    # Check of ref event is correct
    ok, err_ack = validate_ref_event(event, meeting)
    if not ok:
        return False, err_ack

    meeting_session_details = ongoing_meetings[meeting["_id"]]

    # Check if they are in the meeting, if so, remove them, otherwise its an error
    if staff["_id"] in meeting_session_details["joined_participants"]:
        meeting_session_details["joined_participants"].remove(staff["_id"])
    else:
        return False, get_ack(event["eventId"], event["meetingId"],
                              content={"details": {"errorCode": EventStreamError.MEETING_NOT_JOINED.value}},
                              ack_type=MeetingEventType.ACK_ERR.value)

    leave_room(meeting["_id"])

    # ACK
    ack = get_ack(event["eventId"], event["meetingId"])
    return True, ack


def end(event, staff, meeting, roles):
    # Check whether they should be allowed to end
    if Role.HOST not in roles:
        return False, get_ack(event["eventId"], event["meetingId"],
                              content={"details": {"errorCode": EventStreamError.UNAUTHORISED.value}},
                              ack_type=MeetingEventType.ACK_ERR.value)

    # Check if meeting actually started
    ok, err_ack = validate_meeting_started(event, meeting)
    if not ok:
        return False, err_ack

    # Check if they have actually joined
    ok, err_ack = validate_join(event, staff, meeting)
    if not ok:
        return False, err_ack

    # Check if ref event is correct
    ok, err_ack = validate_ref_event(event, meeting)
    if not ok:
        return False, err_ack

    meeting_session_details = ongoing_meetings[meeting["_id"]]

    # ACK
    ack = get_ack(event["eventId"], event["meetingId"], content=meeting_session_details["unref_events"].keys())

    return True, ack


def poll(event, staff, meeting, roles):
    # Check whether they should be allowed to start a poll
    if Role.HOST not in roles:
        return False, get_ack(event["eventId"], event["meetingId"],
                              content={"details": {"errorCode": EventStreamError.UNAUTHORISED.value}},
                              ack_type=MeetingEventType.ACK_ERR.value)

    # Check if meeting actually started
    ok, err_ack = validate_meeting_started(event, meeting)
    if not ok:
        return False, err_ack

    # Check if they have actually joined
    ok, err_ack = validate_join(event, staff, meeting)
    if not ok:
        return False, err_ack

    # Check of ref event is correct
    ok, err_ack = validate_ref_event(event, meeting)
    if not ok:
        return False, err_ack

    meeting_session_details = ongoing_meetings.get(meeting["_id"], None)
    meeting_session_details["polls"][event["eventId"]] = {
        "votes": {},
        "options": []
    }

    # ACK
    ack = get_ack(event["eventId"], event["meetingId"])
    return True, ack


def vote(event, staff, meeting, roles):
    # Check whether they should be allowed to vote
    if Role.PARTICIPANT not in roles:
        return False, get_ack(event["eventId"], event["meetingId"],
                              content={"details": {"errorCode": EventStreamError.UNAUTHORISED.value}},
                              ack_type=MeetingEventType.ACK_ERR.value)

    # Check if meeting actually started
    ok, err_ack = validate_meeting_started(event, meeting)
    if not ok:
        return False, err_ack

    # Check if they have actually joined
    ok, err_ack = validate_join(event, staff, meeting)
    if not ok:
        return False, err_ack

    meeting_session_details = ongoing_meetings.get(meeting["_id"], None)

    # Check if refEvent is a poll
    poll = meeting_session_details["polls"].get(event["refEvent"], None)
    if poll is None:
        return False, get_ack(event["eventId"], event["meetingId"],
                              content={"details": {"errorCode": EventStreamError.POLL_NOT_FOUND.value}},
                              ack_type=MeetingEventType.ACK_ERR.value)

    # Check if vote is one of the options
    user_vote = event["content"]["vote"]
    if user_vote not in poll["options"]:
        return False, get_ack(event["eventId"], event["meetingId"],
                              content={"details": {"errorCode": EventStreamError.INVALID_VOTE_OPTION.value}},
                              ack_type=MeetingEventType.ACK_ERR.value)

    # Check if already voted
    if event["by"] in poll["votes"].keys():
        return False, get_ack(event["eventId"], event["meetingId"],
                              content={"details": {"errorCode": EventStreamError.ALREADY_VOTED.value}},
                              ack_type=MeetingEventType.ACK_ERR.value)

    poll["votes"][event["by"]] = event

    # ACK
    ack = get_ack(event["eventId"], event["meetingId"])
    return True, ack


def end_poll(event, staff, meeting, roles):
    # Check whether they should be allowed to vote
    if Role.HOST not in roles:
        return False, get_ack(event["eventId"], event["meetingId"],
                              content={"details": {"errorCode": EventStreamError.UNAUTHORISED.value}},
                              ack_type=MeetingEventType.ACK_ERR.value)

    # Check if meeting actually started
    ok, err_ack = validate_meeting_started(event, meeting)
    if not ok:
        return False, err_ack

    # Check if they have actually joined
    ok, err_ack = validate_join(event, staff, meeting)
    if not ok:
        return False, err_ack

    meeting_session_details = ongoing_meetings.get(meeting["_id"], None)

    # Check if refEvent is a poll
    poll = meeting_session_details["polls"].get(event["refEvent"], None)
    if poll is None:
        return False, get_ack(event["eventId"], event["meetingId"],
                              content={"details": {"errorCode": EventStreamError.POLL_NOT_FOUND.value}},
                              ack_type=MeetingEventType.ACK_ERR.value)

    # ACK
    ack = get_ack(event["eventId"], event["meetingId"],
                  content={"details": {"votes": json.dumps(list(poll["votes"].values()))}},
                  ack_type=MeetingEventType.ACK_POLL_END.value)

    # Delete poll
    del meeting_session_details["polls"][event["refEvent"]]

    return True, ack


def comment_reply_disagreement(event, staff, meeting, roles):
    # Check whether they should be allowed to vote
    if Role.PARTICIPANT not in roles:
        return False, get_ack(event["eventId"], event["meetingId"],
                              content={"details": {"errorCode": EventStreamError.UNAUTHORISED.value}},
                              ack_type=MeetingEventType.ACK_ERR.value)

    # Check if meeting actually started
    ok, err_ack = validate_meeting_started(event, meeting)
    if not ok:
        return False, err_ack

    # Check if they have actually joined
    ok, err_ack = validate_join(event, staff, meeting)
    if not ok:
        return False, err_ack

    # Check of ref event is correct
    ok, err_ack = validate_ref_event(event, meeting)
    if not ok:
        return False, err_ack

    # ACK
    ack = get_ack(event["eventId"], event["meetingId"])
    return True, ack


def discussion(event, staff, meeting, roles):
    # Check whether they should be allowed to start discussion
    if Role.HOST not in roles:
        return False, get_ack(event["eventId"], event["meetingId"],
                              content={"details": {"errorCode": EventStreamError.UNAUTHORISED.value}},
                              ack_type=MeetingEventType.ACK_ERR.value)

    # Check if meeting actually started
    ok, err_ack = validate_meeting_started(event, meeting)
    if not ok:
        return False, err_ack

    # Check if they have actually joined
    ok, err_ack = validate_join(event, staff, meeting)
    if not ok:
        return False, err_ack

    # Check of ref event is correct
    ok, err_ack = validate_ref_event(event, meeting)
    if not ok:
        return False, err_ack

    # ACK
    ack = get_ack(event["eventId"], event["meetingId"])
    return True, ack


def patient_data_change(event, staff, meeting, roles):
    # Check whether they should be allowed to start discussion
    if Role.HOST not in roles:
        return False, get_ack(event["eventId"], event["meetingId"],
                              content={"details": {"errorCode": EventStreamError.UNAUTHORISED.value}},
                              ack_type=MeetingEventType.ACK_ERR.value)

    # Check if meeting actually started
    ok, err_ack = validate_meeting_started(event, meeting)
    if not ok:
        return False, err_ack

    # Check if they have actually joined
    ok, err_ack = validate_join(event, staff, meeting)
    if not ok:
        return False, err_ack

    # Check of ref event is correct
    ok, err_ack = validate_ref_event(event, meeting)
    if not ok:
        return False, err_ack

    # Check if patient actually exists
    patient_id = event["content"]["patient"]
    patient = db.get_patient(patient_id)
    if patient is None:
        return False, get_ack(event["eventId"], event["meetingId"],
                              content={"details": {"errorCode": EventStreamError.PATIENT_NOT_FOUND.value}},
                              ack_type=MeetingEventType.ACK_ERR.value)

    # ACK
    ack = get_ack(event["eventId"], event["meetingId"])
    return True, ack


def sign(event):
    return auth.sign_event(event)


def send(signed_event, broadcast_room=None):
    if broadcast_room is None:
        emit_ws('room-message', signed_event)
    else:
        emit_ws('room-message', signed_event, room=broadcast_room)


def record(event, meeting):
    log.debug("Storing: " + event["eventId"])
    log.debug(event)
    meeting_session_details = ongoing_meetings.get(meeting["_id"], None)
    meeting_session_details["events"][event["eventId"]] = event


def get_ack(ref_event, meeting_id, content=None, ack_type=MeetingEventType.ACK.value):
    valid_ack_types = [MeetingEventType.ACK.value, MeetingEventType.ACK_ERR.value, MeetingEventType.ACK_JOIN.value,
                       MeetingEventType.ACK_POLL_END]

    if ack_type not in valid_ack_types:
        log.warn("Ack type not a valid! Continuing anyway...   AckType: " + ack_type)

    if content is None:
        content = {}
    ack_event = copy.deepcopy(ack_event_template)
    ack_event["by"] = 'server'  # TODO: get_public_key_as_string
    ack_event["refEvent"] = ref_event
    ack_event["timestamp"] = int(time.time())
    ack_event["meetingId"] = meeting_id
    ack_event["content"] = content
    ack_event["type"] = ack_type
    return ack_event


def add_event_as_unref(meeting, event):
    ongoing_meetings[meeting["_id"]]["unref_events"][event["eventId"]] = None


def check_and_remove_ref_event(meeting, ref_event):
    ongoing_meetings[meeting["_id"]].pop(ref_event, None)


def validate_ref_event(event, meeting) -> (bool, dict):
    ref_valid = event["refEvent"] in ongoing_meetings[meeting["_id"]]["events"]

    if not ref_valid:
        err_ack = get_ack(event["eventId"], event["meetingId"],
                          content={"details": {"errorCode": EventStreamError.INVALID_REF_EVENT.value}},
                          ack_type=MeetingEventType.ACK_ERR.value)
        return False, err_ack
    return True, None


def validate_meeting_started(event, meeting) -> (bool, dict):
    meeting_started = meeting["_id"] in ongoing_meetings.keys()
    if not meeting_started:
        err_ack = get_ack(event["eventId"], event["meetingId"],
                          content={"details": {"errorCode": EventStreamError.MEETING_NOT_STARTED.value}},
                          ack_type=MeetingEventType.ACK_ERR.value)
        return False, err_ack

    return True, None


def validate_join(event, staff, meeting) -> (bool, dict):
    joined = staff["_id"] in ongoing_meetings[meeting["_id"]]["joined_participants"]
    if not joined:
        err_ack = get_ack(event["eventId"], event["meetingId"],
                          content={"details": {"errorCode": EventStreamError.MEETING_NOT_JOINED.value}},
                          ack_type=MeetingEventType.ACK_ERR.value)
        return False, err_ack

    return True, None


def validate_timestamp(event) -> (bool, dict):
    current_time = int(time.time())
    if not (current_time - timestamp_tolerance <= event["timestamp"] <= current_time + timestamp_tolerance):
        err_event = get_ack(event["eventId"], event["meetingId"],
                            content={"details": {
                                "errorCode": EventStreamError.TIMESTAMP_NOT_SYNC.value,
                                "currentServerTime": str(current_time)}},
                            ack_type=MeetingEventType.ACK_ERR.value)

        return False, err_event

    return True, None


def validate_schema(event) -> (bool, dict):
    ok, err = event_schema_validator.validate(event)
    if not ok:
        event_id = event.get("eventId", "unknownEventId")
        meeting_id = event.get("meetingId", "unknownMeetingId")
        err_event = get_ack(event_id, meeting_id,
                            content={"details": {"errorCode": EventStreamError.MALFORMED_EVENT.value,
                                                 "errorDetails": err}},
                            ack_type=MeetingEventType.ACK_ERR.value)
        return False, err_event

    return True, None


def validate_signature(event) -> (bool, dict):
    # Check Signature of the participant
    ok = auth.verify_event(event)
    if not ok:
        event_id = event.get("eventId", "unknownEventId")
        meeting_id = event.get("meetingId", "unknownMeetingId")
        err_event = get_ack(event_id, meeting_id,
                            content={"details": {"errorCode": EventStreamError.BAD_SIGNATURE.value}})
        return False, err_event

    return True, None


def validate_preliminary_authority(event, roles) -> (bool, dict):
    if not roles:
        return False, get_ack(event["eventId"], event["meetingId"],
                              content={"details": {"errorCode": EventStreamError.UNAUTHORISED.value}},
                              ack_type=MeetingEventType.ACK_ERR.value)
    return True, None


def save_all_events_into_db(meeting):
    for eid, event in ongoing_meetings[meeting["_id"]]["events"].items():
        db.insert_event(event)


@socketio.on('room-message')
def room_message(event):
    try:
        event = json.loads(event)
    except ValueError as ve:
        log.error("Error Parsing room-message as JSON!")
        log.error(ve)
        return json.dumps(sign(get_ack(event["eventId"], event["meetingId"],
                                       content={"details": {"errorCode": EventStreamError.MALFORMED_EVENT.value}},
                                       ack_type=MeetingEventType.ACK_ERR.value)))

    # Validate JSON using schema
    ok, err_event = validate_schema(event)
    if not ok:
        log.error("Sending error msg")
        errormsg = json.dumps(sign(err_event))
        log.error("======== error_msg: " + errormsg)
        return errormsg

    # Check signature, before trusting anything it says
    # ok, err_event = validate_signature(event)
    # if not ok:
    #     return json.dumps(sign(err_event))
    #

    # Check timestamp
    ok, err_event = validate_timestamp(event)
    if not ok:
        return json.dumps(sign(err_event))

    # Get the staff
    staff = db.get_staff(event["by"])
    if staff is None:
        return json.dumps(sign(get_ack(event["eventId"], event["meetingId"],
                                       content={"details": {"errorCode": EventStreamError.STAFF_NOT_FOUND.value}},
                                       ack_type=MeetingEventType.ACK_ERR.value)))

    # Get the meeting
    meeting = db.get_meeting(event["meetingId"])
    if meeting is None:
        return json.dumps(sign(get_ack(event["eventId"], event["meetingId"],
                                       content={"details": {"errorCode": EventStreamError.MEETING_NOT_FOUND.value}},
                                       ack_type=MeetingEventType.ACK_ERR.value)))

    # Get the roles
    roles = get_role(staff, meeting)

    # A preliminary authority check to see if the user can make any statements about the meeting
    ok, err_event = validate_preliminary_authority(event, roles)
    if not ok:
        return json.dumps(sign(err_event))

    # Get the event type
    event_type = MeetingEventType((event["type"]))
    ack_event = None
    ok = False
    end_meeting = False

    if event_type == MeetingEventType.START:
        ok, ack_event = start(event, staff, meeting, roles)

    if event_type == MeetingEventType.JOIN:
        ok, ack_event = join(event, staff, meeting, roles)

    if event_type == MeetingEventType.LEAVE:
        ok, ack_event = leave(event, staff, meeting)

    if event_type == MeetingEventType.POLL:
        ok, ack_event = poll(event, staff, meeting, roles)

    if event_type == MeetingEventType.POLL_END:
        ok, ack_event = end_poll(event, staff, meeting, roles)

    if event_type == MeetingEventType.COMMENT or event_type == MeetingEventType.REPLY or event_type == MeetingEventType.DISAGREEMENT:
        ok, ack_event = comment_reply_disagreement(event, staff, meeting, roles)

    if event_type == MeetingEventType.DISCUSSION:
        ok, ack_event = discussion(event, staff, meeting, roles)

    if event_type == MeetingEventType.PATIENT_DATA_CHANGE:
        ok, ack_event = patient_data_change(event, staff, meeting, roles)

    if event_type == MeetingEventType.END:
        ok, ack_event = end(event, staff, meeting, roles)
        if ok:
            end_meeting = True

    if not ok:
        return json.dumps(sign(ack_event))
    else:
        # If an event has been referenced
        check_and_remove_ref_event(meeting, event.get("refEvent", ""))

        # Add ack and event to unreferenced events
        add_event_as_unref(meeting, event)
        add_event_as_unref(meeting, ack_event)

        # Sign the ack
        signed_ack_event = sign(ack_event)

        # Broadcast event
        send(json.dumps(event), broadcast_room=meeting["_id"])
        send(json.dumps(signed_ack_event), broadcast_room=meeting["_id"])

        record(event, meeting)
        record(signed_ack_event, meeting)

        if end_meeting:
            save_all_events_into_db(meeting)
            # write_to_smart_contract
            close_room(meeting["_id"])

        # Send the ack event to the user privately as well
        return json.dumps(signed_ack_event)


class EventStreamError(Enum):
    UNAUTHORISED = "unauthorized"
    MEETING_NOT_FOUND = "meeting not found"
    BAD_SIGNATURE = "bad signature"
    BAD_OTP = "bad otp"
    MALFORMED_EVENT = "malformed event"
    TIMESTAMP_NOT_SYNC = "time stamp not in sync"
    INTERNAL_ERROR = "internal error"
    INVALID_REF_EVENT = "invalid ref event"
    UNKNOWN_ERROR = "unknown error"
    STAFF_NOT_FOUND = "staff nor found"
    MEETING_NOT_STARTED = "meeting not started"
    MEETING_NOT_JOINED = "meeting not joined"
    POLL_NOT_FOUND = "poll not found"
    INVALID_VOTE_OPTION = "invalid vote option"
    PATIENT_NOT_FOUND = "patient not found"
    MEETING_ALREADY_STARTED = "meeting already started"
    ALREADY_VOTED = "already voted"


if __name__ == '__main__':
    socketio.run(app, host="localhost", port=51235)

# def validate_room(event, meeting) -> (bool, dict):
#     room = event.get("room", None)
#     # check if event contains a room
#     if room is None:
#         err_ack = get_ack(event["eventId"], event["meetingId"], content={"details" : { "errorCode": EventStreamError.MALFORMED_EVENT,
#                                                                          "errorDetails": "Missing field: 'room'"},
#                           ack_type=MeetingEventType.ACK_ERR.value)
#         return False, err_ack
#
#     # check if the room is correct
#     if ongoing_meetings[meeting["_id"]]["room"] != room:
#         err_ack = get_ack(event["eventId"], event["meetingId"], content={"details" : { "errorCode": EventStreamError.INVALID_ROOM},
#                           ack_type=MeetingEventType.ACK_ERR.value)
#         return False, err_ack
#
#     return True, None
#
# Check if th

# Check if it has room, as its not a mandatory field and not required for every OP, its not part of JSON schema
# TODO: Think about putting this somewhere else
