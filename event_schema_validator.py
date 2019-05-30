import json
from model import MeetingEventType
from jsonschema import validate as validate_schema, ValidationError
import log as logger

log = logger.get_logger('event_schema_validator')

with open('schema/event_schema.json') as f:
    event_schema = json.load(f)

content_schemas_files = {
    MeetingEventType.START: "schema/event_content_start_schema.json",
    MeetingEventType.DISCUSSION: "schema/event_content_discussion_schema.json",
    MeetingEventType.COMMENT: "schema/event_content_comment_schema.json",
    MeetingEventType.REPLY: "schema/event_content_reply_schema.json",
    MeetingEventType.PATIENT_DATA_CHANGE: "schema/event_content_patientDataChange_schema.json",
    MeetingEventType.POLL: "schema/event_content_poll_schema.json",
    MeetingEventType.JOIN: "schema/event_content_join_schema.json",
    MeetingEventType.VOTE: "schema/event_content_vote_schema.json",
}


def validate(json_data) -> (bool, str):
    # Validate with the  event schema (without considering the content field)
    try:
        validate_schema(instance=json_data, schema=event_schema)
    except ValidationError as ve:
        log.debug(str(type(ve)) + ', ' + str(ve))
        return False, str(ve.message)

    # Get the event type
    try:
        event_type = MeetingEventType((json_data["type"]))
    except ValueError as ve:
        log.debug(str(type(ve)) + ', ' + str(ve))
        return False, "Unknown value in 'type'"

    # Return if the content is supposed to be empty/ignored
    if event_type not in content_schemas_files.keys():
        return True, None

    # Get the schema file for the content
    file = content_schemas_files.get(event_type, None)
    with open(file) as f:
        event_content_schema = json.load(f)

    # Validate with the right content schema
    try:
        validate_schema(instance=json_data.get("content", {}), schema=event_content_schema)
    except ValidationError as ve:
        log.debug(str(type(ve)) + ', ' + str(ve))
        return False, str(ve.message)

    return True, None


####################
#  CODE DUMP       #
# #
# pdc_event = {
#     "by": "publicKey [onlyHost]",
#     "_id": "signature(event)",
#     "meetingId": "",
#     "refEvent": "",
#     "timestamp": 0,
#     "type": "patientDataChange",
#
#     "content": {
#         "patient": "",
#         "from": "",
#         "to": ""
#     }
# }
#
# start_event = {
#     "by": "publicKey [onlyHost]",
#     "meetingId": "",
#     "_id": "signature(event)",
#     "timestamp": 0,
#     "type": "start",
#     "content": {
#         "otp": "4256"
#     }
# }
#
# join_event = {
#     "by": "publicKey",
#     "refEvent": "",
#     "_id": "signature(event)",
#     "meetingId": "",
#     "timestamp": 0,
#     "type": "join",
#     "content": {
#         "otp": "4256"
#     }
# }
#
# leave_event = {
#     "by": "publicKey [onlyHost]",
#     "_id": "signature(event)",
#     "refEvent": "",
#     "meetingId": "",
#     "timestamp": 0,
#     "type": "leave",
#     "content": {}
# }
#
# poll_event = {
#     "by": "publicKey",
#     "_id": "signature(event)",
#     "meetingId": "",
#     "refEvent": "",
#     "timestamp": 0,
#     "type": "poll",
#
#     "content": {
#         "patient": "",
#         "question": "",
#         "options": ["Yes", "No"]
#     }
# }
#
# vote_event = {
#     "by": "publicKey",
#     "_id": "signature(event)",
#     "refEvent": "",
#     "meetingId": "",
#     "timestamp": 0,
#     "type": "vote",
#
#     "content": {
#         "vote": ""
#     }
#
# }
#
# poll_end_event = {
#     "by": "publicKey [hostOnly]",
#     "_id": "signature(event)",
#     "refEvent": "",
#     "meetingId": "",
#     "timestamp": 0,
#     "type": "pollEnd",
#
#     "content": {}
# }
#
# comment_event = {
#     "by": "publicKey",
#     "_id": "signature(event)",
#     "refEvent": "",
#     "timestamp": 0,
#     "type": "comment",
#     "meetingId": "",#
#     "content": {
#         "patient": "",
#         "comment": ""
#     }
# }
#
# reply_event = {
#     "by": "publicKey",
#     "_id": "signature(event)",
#     "refEvent": "",
#     "timestamp": 0,
#     "meetingId": "",
#     "type": "reply",
#
#     "content": {
#         "reply": ""
#     }
# }
#
# discussion_event = {
#     "by": "publicKey [onlyHost]",
#     "_id": "signature(event)",
#     "refEvent": "",
#     "timestamp": 0,
#     "meetingId": "",
#     "type": "discussion",
#
#     "content": {
#         "patient": "patientPublicKey"
#     }
# }
#
# disagree_event = {
#     "by": "publicKey",
#     "_id": "signature(event)",
#     "refEvent": "",
#     "timestamp": 0,
#     "meetingId": "",
#     "type": "disagreement",
#     "content": {}
# }
#
# end_event = {
#     "by": "publicKey [onlyHost]",
#     "_id": "signature(event)",
#     "refEvent": "",
#     "timestamp": 0,
#     "meetingId": "",
#     "type": "end",
#     "content": {}
# }
#
# ack_event = {
#     "by": "publicKey [onlyServer]",
#     "_id": "signature(event)",
#     "refEvent": "",
#     "timestamp": 0,
#     "meetingId": "",
#     "type": "ack",
#     "content": {
#         "ha": "whatever"
#     }
# }
#
# print(validate(ack_event))
# print(validate(end_event))
# print(validate(disagree_event))
# print(validate(discussion_event))
# print(validate(reply_event))
# print(validate(comment_event))
# print(validate(poll_end_event))
# print(validate(vote_event))
# print(validate(poll_event))
# print(validate(leave_event))
# print(validate(join_event))
# print(validate(start_event))
# print(validate(pdc_event))
