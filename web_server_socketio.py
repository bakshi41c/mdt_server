import json
import time
from flask_socketio import close_room
from flask_socketio import emit as emit_ws
from flask_socketio import join_room, leave_room
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
from enum import Enum
import traceback

import meeting_contract_helper
from db import Database
import config
from authorization import Role, get_role
import authentication
import copy
import event_schema_validator
import log as logger
import logging
from model import Event, Staff, Meeting, AckErrorContent, EventError, JoinContent, DeeIdLoginSigSigned, MeetingEventType, \
    StartContent, AckJoinContent, AckEndContent, PollContent, VoteContent, PDCContent, AckPollEndContent

app = Flask(__name__)

app.config['SECRET_KEY'] = 'TVBam9S&W7IbTC8W'

socketio = SocketIO(app)

CORS(app)

config = config.get_config()
db = Database(config["database"]["db_name"], config["database"]["ip"], config["database"]["port"])
log = logger.get_logger('web_server_socketio')
timestamp_tolerance = 10  # seconds
ongoing_meetings = {}
auth = authentication.Auth(config)
smart_contract = meeting_contract_helper.MeetingContractHelper(config)

class OngiongMeeting:
    def __init__(self):
        self.otp = ''
        self.host = ''
        self.start_event = None
        self.events = {} # type: dict[str, Event]
        self.polls = {} # type: dict[str, Poll]
        self.unref_events = {}  # type: dict[str, Event]
        self.session_keys = {} # type: dict[str, str]
        self.latest_join_events = {}  # type: dict[str, Event]


class Poll:
    def __init__(self):
        self.votes = {} # type: dict[str, Event]

def start(event, staff, meeting, roles) -> (bool, dict):
    log.debug("Processing Start event")
    # Check if the user is allowed to start
    if Role.HOST not in roles:
        return False, get_error_ack(event.id, event.meeting_id,
                                    content=AckErrorContent(error_code=EventError.UNAUTHORISED,
                                                      details=''))

    # Check if meeting has already started, if it has send the otp, in case the host has forgotten
    started, _ = validate_meeting_started(event, meeting)
    if started:
        otp = ongoing_meetings[meeting.id].otp
        return False, get_error_ack(event.id, event.meeting_id,
                                    content=AckErrorContent(error_code=EventError.MEETING_ALREADY_STARTED,
                                                      details='Meeting already started, otp : ' + otp))

    # Parse the content of event as StartContent
    try:
        sc = StartContent.parse(event.content)
        dee_id_login_sig = DeeIdLoginSigSigned.parse(sc.deeid_login_sig_signed)
        new_key = sc.key
        uid = dee_id_login_sig.uid
        expiry = dee_id_login_sig.expiry_time
        sig = dee_id_login_sig.signature
    except KeyError as ke:
        log.error(ke)
        traceback.print_tb(ke.__traceback__)
        return False, get_error_ack(event.id, event.meeting_id,
                                    content=AckErrorContent(error_code=EventError.MALFORMED_EVENT,
                                                      details="Content doesnt have sufficient values"))

    # Authenticate new key
    msg = uid + staff.id + expiry + new_key
    addr = auth.get_sig_address_from_signature(msg=msg, signature=sig)
    ok = auth.ethkey_in_deeid_contract(addr, staff.id)
    if not ok:
        return False, get_error_ack(event.id, event.meeting_id,
                                    content=AckErrorContent(error_code=EventError.UNAUTHORISED,
                                                      details="New pubKey cannot be authenticated"))
    print("OTP: ", sc.otp)
    #  Create new meeting session
    om = OngiongMeeting()
    om.otp = sc.otp
    om.host = staff.id
    om.start_event = event
    om.events = {event.id: event}
    om.polls = {}
    om.unref_events = {}
    om.session_keys = {
        staff.id : new_key
    }
    om.latest_join_events = []

    # Create smart contract for the meeting  - COSTS MONEY
    log.debug("Deploying Smart Contract...")
    try:
        meeting.contract_id = smart_contract.new_meeting_contract(meeting)
    except Exception as e:  # We catch all exceptions as there are too many
        log.error("FAILED deploying smart contract")
        log.error(e)
        traceback.print_tb(e.__traceback__)
        return False, get_error_ack(event.id, event.meeting_id,
                                content=AckErrorContent(error_code=EventError.INTERNAL_ERROR,
                                                        details='Smart Contract could not be deployed'))

    log.debug("Deployed smart contract!")
    log.debug(meeting.contract_id)
    ongoing_meetings[meeting.id] = om
    meeting.started = True # Set the meeting as started in the db
    db.update_meeting(meeting.id, meeting.to_json_dict())

    # ACK
    ack = get_ack(event.id, event.meeting_id)
    return True, ack


def join(event, staff, meeting, roles) -> (bool, dict):
    log.debug("Processing Join event")
    # Check if the user is allowed to join
    if Role.PARTICIPANT not in roles:
        return False, get_error_ack(event.id, event.meeting_id,
                                    content=AckErrorContent(error_code=EventError.UNAUTHORISED,
                                                                    details=''))

    # Check if meeting has started
    ok, err_ack = validate_meeting_started(event, meeting)
    if not ok:
        return False, err_ack

    # Get Meeting session details
    meeting_session_details = ongoing_meetings.get(meeting.id, None)  # type: OngiongMeeting

    # Parse the content of event as JoinContent
    try:
        jc = JoinContent.parse(event.content)
        dee_id_login_sig = DeeIdLoginSigSigned.parse(jc.deeid_login_sig_signed)
        new_key = jc.key
        uid = dee_id_login_sig.uid
        expiry = dee_id_login_sig.expiry_time
        sig = dee_id_login_sig.signature
    except KeyError as ke:
        log.error(ke)
        traceback.print_tb(ke.__traceback__)
        return False, get_error_ack(event.id, event.meeting_id,
                                    content=AckErrorContent(error_code=EventError.MALFORMED_EVENT,
                                                                    details="Content doesnt have sufficient values"))

    # Check OTP
    if not jc.otp == meeting_session_details.otp:
        return False, get_error_ack(event.id, event.meeting_id,
                                    content=AckErrorContent(error_code=EventError.BAD_OTP,
                                                                    details=''))


    # Authenticate new key
    msg = uid + staff.id + expiry + new_key
    addr = auth.get_sig_address_from_signature(msg=msg, signature=sig)
    ok = auth.ethkey_in_deeid_contract(addr, staff.id)

    if not ok:
        return False, get_error_ack(event.id, event.meeting_id,
                                    content=AckErrorContent(error_code=EventError.UNAUTHORISED,
                                                                    details="New pubKey cannot be authenticated"))

    meeting_session_details.session_keys[staff.id] = new_key

    # Add them to the list of staff that have joined the meeting
    update_attended_staff(meeting, staff)

    # Join the socketio room using the sessison_id
    join_room(meeting.id)

    start_event = meeting_session_details.start_event
    latest_join_events = meeting_session_details.latest_join_events

    # ACK
    jac = AckJoinContent(start_event, latest_join_events)
    ack = get_ack(event.id, event.meeting_id, type=MeetingEventType.ACK_JOIN, content=jac)
    return True, ack


def leave(event, staff, meeting):
    log.debug("Processing Leave event")
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

    # Get Meeting session details
    # meeting_session_details = ongoing_meetings.get(meeting.id, None)  # type: OngiongMeeting
    #
    # # Check if they are in the meeting, if so, remove them, otherwise its an error
    # if staff.id in meeting_session_details.joined_particpants:
    #     meeting_session_details.joined_particpants.remove(staff.id)
    # else:
    #     return False, get_error_ack(event.id, event.meeting_id,
    #                                 content=AckErrorContent(error_code=EventError.MEETING_NOT_JOINED,
    #                                                                 details=""))

    leave_room(meeting.id)

    # ACK
    ack = get_ack(event.id, event.meeting_id)
    return True, ack


def end(event, staff, meeting, roles):
    log.debug("Processing End event")
    # Check whether they should be allowed to end
    if Role.HOST not in roles:
        return False, get_error_ack(event.id, event.meeting_id,
                                    content=AckErrorContent(error_code=EventError.UNAUTHORISED,
                                                                    details=''))

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

    # Get Meeting session details
    meeting_session_details = ongoing_meetings.get(meeting.id, None)  # type: OngiongMeeting

    # ACK  -- WE get ACK early as we need the signature for smart contract later, and there could be errors with that
    eac = AckEndContent(list(meeting_session_details.unref_events.keys()))
    ack = get_ack(event.id, event.meeting_id, type=MeetingEventType.ACK_END, content=eac)
    return True, ack


def poll(event, staff, meeting, roles):
    log.debug("Processing Poll event")
    # Check whether they should be allowed to start a poll
    if Role.HOST not in roles:
        return False, get_error_ack(event.id, event.meeting_id,
                                    content=AckErrorContent(error_code=EventError.UNAUTHORISED,
                                                             details=''))

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

    # Get Meeting session details
    meeting_session_details = ongoing_meetings.get(meeting.id, None)  # type: OngiongMeeting

    # Parsing content as PollContent
    try:
        pc = PollContent.parse(event.content)
    except KeyError as ke:
        log.error(ke)
        traceback.print_tb(ke.__traceback__)
        return False, get_error_ack(event.id, event.meeting_id,
                                    content=AckErrorContent(error_code=EventError.MALFORMED_EVENT,
                                                                    details="Content doesnt have sufficient values"))

    new_poll = Poll()
    poll.votes = {}

    meeting_session_details.polls[event.id] = new_poll

    # ACK
    ack = get_ack(event.id, event.meeting_id)
    return True, ack


def vote(event, staff, meeting, roles):
    log.debug("Processing Vote Event")
    # Check whether they should be allowed to vote
    if Role.PARTICIPANT not in roles:
        return False, get_error_ack(event.id, event.meeting_id,
                                    content=AckErrorContent(error_code=EventError.UNAUTHORISED,
                                                                    details=''))

    # Check if meeting actually started
    ok, err_ack = validate_meeting_started(event, meeting)
    if not ok:
        return False, err_ack

    # Check if they have actually joined
    ok, err_ack = validate_join(event, staff, meeting)
    if not ok:
        return False, err_ack

    # Get Meeting session details
    meeting_session_details = ongoing_meetings.get(meeting.id, None)  # type: OngiongMeeting

    # Check if refEvent is a poll
    poll = meeting_session_details.polls.get(event.ref_event, None)
    if poll is None:
        return False, get_error_ack(event.id, event.meeting_id,
                                    content=AckErrorContent(error_code=EventError.POLL_NOT_FOUND,
                                                                    details=''))

    # Parsing content as VoteContent
    try:
        vc = VoteContent.parse(event.content)
    except KeyError as ke:
        traceback.print_tb(ke.__traceback__)
        log.error(ke)
        return False, get_error_ack(event.id, event.meeting_id,
                                    content=AckErrorContent(error_code=EventError.MALFORMED_EVENT,
                                                                    details="Content doesnt have sufficient values"))
    #
    # # Check if vote is one of the options
    # if vc.vote not in poll.options:
    #     return False, get_error_ack(event.id, event.meeting_id,
    #                                 content=AckErrorContent(error_code=EventError.INVALID_VOTE_OPTION,
    #                                                                 details='').to_json_dict())

    # Check if already voted
    if event.by in poll.votes:
        return False, get_error_ack(event.id, event.meeting_id,
                                    content=AckErrorContent(error_code=EventError.ALREADY_VOTED,
                                                                    details=''))

    log.debug("Adding the vote to votes")
    poll.votes[staff.id] = event

    # ACK
    ack = get_ack(event.id, event.meeting_id)
    return True, ack


def end_poll(event, staff, meeting, roles):
    log.debug("Processing End Poll event")
    # Check whether they should be allowed to end poll
    if Role.HOST not in roles:
        return False, get_error_ack(event.id, event.meeting_id,
                                    content=AckErrorContent(error_code=EventError.UNAUTHORISED,
                                                                    details=''))

    # Check if meeting actually started
    ok, err_ack = validate_meeting_started(event, meeting)
    if not ok:
        return False, err_ack

    # Check if they have actually joined
    ok, err_ack = validate_join(event, staff, meeting)
    if not ok:
        return False, err_ack

    # Get Meeting session details
    meeting_session_details = ongoing_meetings.get(meeting.id, None)  # type: OngiongMeeting

    #  Check if refEvent is a poll
    poll = meeting_session_details.polls.get(event.ref_event, None)
    if poll is None:
        return False, get_error_ack(event.id, event.meeting_id,
                                    content=AckErrorContent(error_code=EventError.POLL_NOT_FOUND,
                                                                    details=''))

    vote_event_ids = [event.id for event in list(poll.votes.values())]
    poll_end_ack_event = AckPollEndContent(votes=vote_event_ids)

    # ACK
    ack = get_ack(event.id, meeting.id,
                    type=MeetingEventType.ACK_POLL_END, content=poll_end_ack_event)

    # Delete poll
    meeting_session_details.polls.pop(event.ref_event)

    return True, ack


def comment_reply_disagreement(event, staff, meeting, roles):
    log.debug("Processing Comment/Reply/Disagreement event")
    # Check whether they should be allowed to vote
    if Role.PARTICIPANT not in roles:
        return False, get_error_ack(event.id, event.meeting_id,
                                    content=AckErrorContent(error_code=EventError.UNAUTHORISED,
                                                                    details=''))

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
    ack = get_ack(event.id, meeting.id)
    return True, ack


def discussion(event, staff, meeting, roles):
    log.debug("Processing Discussion event")
    # Check whether they should be allowed to start discussion
    if Role.HOST not in roles:
        return False, get_error_ack(event.id, event.meeting_id,
                                    content=AckErrorContent(error_code=EventError.UNAUTHORISED,
                                                                    details=''))

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
    ack = get_ack(event.id, meeting.id)
    return True, ack


def patient_data_change(event, staff, meeting, roles):
    log.debug("Processing PDC event")
    # Check whether they should be allowed to start discussion
    if Role.HOST not in roles:
        return False, get_error_ack(event.id, event.meeting_id,
                                    content=AckErrorContent(error_code=EventError.UNAUTHORISED,
                                                                    details=''))

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

    # Parsing content as VoteContent
    try:
        pdc = PDCContent.parse(event.content)
    except KeyError as ke:
        traceback.print_tb(ke.__traceback__)
        log.error(ke)
        return False, get_error_ack(event.id, event.meeting_id,
                                    content=AckErrorContent(error_code=EventError.MALFORMED_EVENT,
                                                                    details="Content doesnt have sufficient values"))

    # Check if patient actually exists
    patient_id = pdc.patient
    patient = db.get_patient(patient_id)
    if patient is None:
        return False, get_error_ack(event.id, event.meeting_id,
                                    content=AckErrorContent(error_code=EventError.PATIENT_NOT_FOUND,
                                                                    details=''))

    # ACK
    ack = get_ack(event.id, meeting.id)
    return True, ack


def sign(event : Event):
    signed_event = auth.sign_event(event.to_json_dict())
    return Event.parse(signed_event)


def send(signed_event, broadcast_room=None):
    if broadcast_room is None:
        emit_ws('room-message', signed_event)
    else:
        emit_ws('room-message', signed_event, room=broadcast_room)


def update_attended_staff(meeting : Meeting, staff : Staff):
    if staff.id not in meeting.attended_staff:
        meeting.attended_staff.append(staff.id)
        db.update_meeting(meeting.id, meeting.to_json_dict())

def record(event: Event, meeting : Meeting):
    log.debug("Storing: " + event.id)
    log.debug(event)
    meeting_session_details = ongoing_meetings.get(meeting.id, None)  # type: OngiongMeeting
    meeting_session_details.events[event.id] = event
    db.insert_event(event.to_json_dict())


def get_error_ack(ref_event, meeting_id, content=None):
    ack_event = Event()
    ack_event.type = MeetingEventType.ACK_ERR
    ack_event.meeting_id = meeting_id
    ack_event.ref_event = ref_event
    ack_event.timestamp = int(time.time())

    if content is None:
        content = {}
    ack_event.content = content
    return ack_event


def get_ack(ref_event, meeting_id, type=MeetingEventType.ACK, content=None):
    ack_event = Event()
    ack_event.type = type
    ack_event.meeting_id = meeting_id
    ack_event.ref_event = ref_event
    ack_event.timestamp = int(time.time())

    if content is None:
        content = {}
    ack_event.content = content
    return ack_event

def add_event_as_unref(meeting : Meeting, event : Event):
    meeting_session_details = ongoing_meetings.get(meeting.id, None)  # type: OngiongMeeting
    meeting_session_details.unref_events[event.id] = None


def check_and_remove_ref_event(meeting, ref_event):
    meeting_session_details = ongoing_meetings.get(meeting.id, None)  # type: OngiongMeeting
    meeting_session_details.unref_events.pop(ref_event, None)


def validate_ref_event(event, meeting) -> (bool, dict):
    meeting_session_details = ongoing_meetings.get(meeting.id, None)  # type: OngiongMeeting
    ref_valid = event.ref_event in meeting_session_details.events

    if not ref_valid:
        err_ack = get_error_ack(event.id, event.meeting_id,
                                content=AckErrorContent(error_code=EventError.INVALID_REF_EVENT,
                                                                    details=''))
        return False, err_ack
    return True, None


def validate_meeting_started(event : Event, meeting : Meeting) -> (bool, dict):
    meeting_started = meeting.id in ongoing_meetings
    if not meeting_started:
        err_ack = get_error_ack(event.id, event.meeting_id,
                                content=AckErrorContent(error_code=EventError.MEETING_NOT_STARTED,
                                                                    details=''))
        return False, err_ack

    return True, None


def validate_join(event, staff, meeting) -> (bool, dict):
    joined = staff.id in meeting.attended_staff
    if not joined:
        err_ack = get_error_ack(event.id, event.meeting_id,
                                content=AckErrorContent(error_code=EventError.MEETING_NOT_JOINED,
                                                                    details=''))
        return False, err_ack

    return True, None


def validate_timestamp(event) -> (bool, dict):
    current_time = int(time.time())
    if not (current_time - timestamp_tolerance <= event.timestamp <= current_time + timestamp_tolerance):
        err_event = get_error_ack(event.id, event.meeting_id,
                                  content=AckErrorContent(error_code=EventError.TIMESTAMP_NOT_SYNC,
                                                                    details='Server Timestamp : ' + str(current_time)))


        return False, err_event

    return True, None


def validate_schema(event_dict) -> (bool, dict):
    ok, err = event_schema_validator.validate(event_dict)
    if not ok:
        err_event = get_error_ack("unknown", "unknown",
                                  content=AckErrorContent(error_code=EventError.MALFORMED_EVENT,
                                                      details=err))

        return False, err_event

    return True, None


def validate_signature(event, staff, meeting, check_contract=False) -> (bool, dict):
    log.debug('Validating Signature...')

    sig_addr = str(auth.get_sig_address_from_event(event.to_json_dict()))

    #  Check session key, or if it doesnt exist, check with actual public key in smart contract
    ok = False
    if check_contract:
        log.debug('Checking DeeId Contract')
        ok = auth.ethkey_in_deeid_contract(sig_addr, staff.id)
        log.debug('Eth key in contract? ' + str(ok))
    else:
        # Get Meeting session details to get the session key
        meeting_session_details = ongoing_meetings.get(meeting.id, None)  # type: OngiongMeeting
        meeting_session_key = None
        if meeting_session_details is not None:
            meeting_session_key = meeting_session_details.session_keys.get(staff.id, None)

        if meeting_session_key is None:
            err_event = get_error_ack(event.id, event.meeting_id,
                                      content=AckErrorContent(error_code=EventError.BAD_SESSION_KEY_SIGNATURE,
                                                              details=''))
            return False, err_event

        ok = sig_addr.lower() == meeting_session_key.lower()
        log.debug('Sig Addr ' + sig_addr)
        log.debug('Session key ' + meeting_session_key)
        log.debug('Session key matches up? '+ str(ok))

    if not ok:
        err_event = get_error_ack(event.id, event.meeting_id,
                                  content=AckErrorContent(error_code=EventError.BAD_SIGNATURE,
                                                      details=''))

        return False, err_event

    return True, None


def validate_preliminary_authority(event, roles) -> (bool, dict):
    if not roles:
        err_event = get_error_ack(event.id, event.meeting_id,
                                  content=AckErrorContent(error_code=EventError.UNAUTHORISED,
                                                                  details=''))

        return False, err_event
    return True, None


def end_meeting_session(meeting, event, signed_ack_event):
    # Write the event hash of the meeting to smart contract  - COSTS MONEY
    meeting_session_details = ongoing_meetings.get(meeting.id, None)  # type: OngiongMeeting
    try:
        start_hash = meeting_session_details.start_event.id
        end_hash = signed_ack_event.id
        smart_contract.set_event_hash(meeting, start_hash, end_hash)
    except Exception as e:  # We catch all exceptions as there are too many
        log.error(e)
        traceback.print_tb(e.__traceback__)
        return False, get_error_ack(event.id, event.meeting_id,
                                    content=AckErrorContent(error_code=EventError.INTERNAL_ERROR,
                                                            details=''))

    # Mark meeting as ended
    meeting.ended = True
    db.update_meeting(meeting.id, meeting.to_json_dict())


    print('============= MEETING END =============')
    print(ongoing_meetings[meeting.id])
    print(signed_ack_event)
    ongoing_meetings.pop(meeting.id)
    close_room(meeting.id)


@socketio.on('room-message')
def room_message(event_string):

    # Parse json as dict
    try:
        event_json = json.loads(event_string)
    except ValueError as ve:
        log.error("Error Parsing room-message as JSON!")
        log.error(ve)
        traceback.print_tb(ve.__traceback__)
        return json.dumps(sign(get_error_ack("unknown", "unknown",
                                  content=AckErrorContent(error_code=EventError.MALFORMED_EVENT,
                                                      details='Cant parse message as JSON'))).to_json_dict())


    # Validate JSON dict using schema
    ok, err_event = validate_schema(event_json)
    if not ok:
        log.error("Sending error msg")
        errormsg = json.dumps(sign(err_event).to_json_dict())
        log.error("======== error_msg: " + errormsg)
        return errormsg


    # Parse dict as event object
    try:
        event = Event.parse(event_json)
    except KeyError as ve:
        log.error("Error Parsing room-message!")
        log.error(ve)
        traceback.print_tb(ve.__traceback__)
        return json.dumps(sign(get_error_ack("unknown", "unknown",
                                  content=AckErrorContent(error_code=EventError.MALFORMED_EVENT,
                                                      details='Cant parse message as Event'))).to_json_dict())

    # Check timestamp
    ok, err_event = validate_timestamp(event)
    if not ok:
        return json.dumps(sign(err_event).to_json_dict())

    # Get the staff
    try:
        staff = Staff.parse(db.get_staff(event.by))
    except KeyError as ke:
        log.error(ke)
        traceback.print_tb(ke.__traceback__)
        return json.dumps(sign(get_error_ack(event.id, event.meeting_id,
                                  content=AckErrorContent(error_code=EventError.STAFF_NOT_FOUND,
                                                      details=''))).to_json_dict())
    except TypeError as te:
        log.error(te)
        traceback.print_tb(te.__traceback__)
        return json.dumps(sign(get_error_ack(event.id, event.meeting_id,
                                  content=AckErrorContent(error_code=EventError.STAFF_NOT_FOUND,
                                                      details=''))).to_json_dict())

    # Get the meeting
    try:
        meeting = Meeting.parse(db.get_meeting(event.meeting_id))
    except KeyError as ke:
        log.error(ke)
        traceback.print_tb(ke.__traceback__)
        return json.dumps(sign(get_error_ack(event.id, event.meeting_id,
                                  content=AckErrorContent(error_code=EventError.MEETING_NOT_FOUND,
                                                      details=''))).to_json_dict())

    except TypeError as te:
        log.error(te)
        traceback.print_tb(te.__traceback__)
        return json.dumps(sign(get_error_ack(event.id, event.meeting_id,
                                  content=AckErrorContent(error_code=EventError.MEETING_NOT_FOUND,
                                                      details=''))).to_json_dict())

    # Check signature, before trusting anything it says

    if event.type in [MeetingEventType.JOIN, MeetingEventType.START]:  # We check contract for join and start
        ok, err_event = validate_signature(event, staff, meeting, check_contract=True)
        if not ok:
            return json.dumps(sign(err_event).to_json_dict())
    else:
        ok, err_event = validate_signature(event, staff, meeting)
        if not ok:
            return json.dumps(sign(err_event).to_json_dict())

    # Get the roles
    roles = get_role(staff, meeting)

    # A preliminary authority check to see if the user can make any statements about the meeting
    ok, err_event = validate_preliminary_authority(event, roles)
    if not ok:
        return json.dumps(sign(err_event).to_json_dict())


    # Get the event type
    event_type = MeetingEventType(event.type)
    ack_event = None
    ok = False
    end_meeting = False
    send_privately = False

    if event_type == MeetingEventType.START:
        ok, ack_event = start(event, staff, meeting, roles)

    if event_type == MeetingEventType.JOIN:
        ok, ack_event = join(event, staff, meeting, roles)

    if event_type == MeetingEventType.LEAVE:
        ok, ack_event = leave(event, staff, meeting)

    if event_type == MeetingEventType.POLL:
        ok, ack_event = poll(event, staff, meeting, roles)

    if event_type == MeetingEventType.VOTE:
        ok, ack_event = vote(event, staff, meeting, roles)

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

    if not ok: # If not ok we send the error ack event privately
        return json.dumps(sign(ack_event).to_json_dict())
    else:
        # If an event has been referenced
        check_and_remove_ref_event(meeting, event.ref_event)

        # Add ack and event to unreferenced events
        add_event_as_unref(meeting, event)
        add_event_as_unref(meeting, ack_event)

        # Sign the ack
        signed_ack_event = sign(ack_event)

        if not send_privately:  # Only Broadcast if the send_privately is set to False
            # Broadcast event
            send(json.dumps(event.to_json_dict()), broadcast_room=meeting.id)
            send(json.dumps(signed_ack_event.to_json_dict()), broadcast_room=meeting.id)

        record(event, meeting)
        record(signed_ack_event, meeting)

        if end_meeting:
            end_meeting_session(meeting, event, signed_ack_event)

        # Send the ack event to the user privately as well
        return json.dumps(signed_ack_event.to_json_dict())


if __name__ == '__main__':
    socketio.run(app, host="localhost", port=51235)
