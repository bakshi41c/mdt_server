from enum import Enum

ack_event_template = {
    "by": "",
    "eventId": "",
    "refEvent": "",
    "timestamp": "",
    "meetingId": "",
    "type": "ack",
    "content": {
    }
}


class MeetingEventType(Enum):
    START = "start"
    JOIN = "join"
    LEAVE = "leave"
    POLL = "poll"
    POLL_END = "pollEnd"
    VOTE = "vote"
    COMMENT = "comment"
    REPLY = "reply"
    DISCUSSION = "discussion"
    DISAGREEMENT = "disagreement"
    PATIENT_DATA_CHANGE = "patientDataChange"
    ACK = "ack"
    ACK_JOIN = "joinAck"
    ACK_POLL_END = "pollEndAck"
    ACK_ERR = "ackError"
    END = "end"
