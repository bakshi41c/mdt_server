from enum import Enum

class Meeting:
    def __init__(self):
        self.id = ''
        self.title = ''
        self.description = ''
        self.started = False
        self.ended = False
        self.contract_id = False
        self.host = ''
        self.date = ''
        self.staff = []
        self.patients = []
        self.attended_staff = []
        self._json_key_map = {
            '_id': 'id',
            'title': 'title',
            'description': 'description',
            'started': 'started',
            'ended': 'ended',
            'contractId': 'contract_id',
            'host': 'host',
            'date': 'date',
            'staff': 'staff',
            'patients': 'patients',
            'attendedStaff': 'attended_staff',
        }

    @staticmethod
    def parse(d):
        m = Meeting()
        for json_key, attr in m._json_key_map.items():
            setattr(m, attr, d[json_key])

        return m


    def to_json_dict(self):
        m = dict()
        for json_key, attr in self._json_key_map.items():
            m[json_key] = self.__getattribute__(attr)
        return m

class Staff:
    def __init__(self):
        self.id = ''
        self.name = ''
        self.role = ''
        self._json_key_map = {
            '_id': 'id',
            'name': 'name',
            'role': 'role',
        }

    @staticmethod
    def parse(d):
        s = Staff()
        for json_key, attr in s._json_key_map.items():
            setattr(s, attr, d[json_key])

        return s

    def to_json_dict(self):
        s = dict()
        for json_key, attr in self._json_key_map.items():
            s[json_key] = self.__getattribute__(attr)
        return s


class Patient:
    def __init__(self):
        self.id = ''
        self.name = ''
        self.dob = ''
        self.hospital_number = 0
        self.info_flex_link = ''
        self._json_key_map = {
            '_id': 'id',
            'name': 'name',
            'dob': 'dob',
            'hospitalNumber': 'hospital_number',
            'infoflexLink': 'infoflex_link',
        }

    @staticmethod
    def parse(d):
        p = Patient()
        for json_key, attr in p._json_key_map.items():
            setattr(p, attr, d[json_key])

        return p

    def to_json_dict(self):
        p = dict()
        for json_key, attr in self._json_key_map.items():
            p[json_key] = self.__getattribute__(attr)
        return p


class Event:
    def __init__(self):
        self.by = ''
        self.id = ''
        self.ref_event = ''
        self.timestamp = 0
        self.meeting_id = ''
        self.type = ''  # type: MeetingEventType
        self.content = None
        self._json_key_map = {
            'by': 'by',
            '_id': 'id',
            'refEvent': 'ref_event',
            'timestamp': 'timestamp',
            'meetingId': 'meeting_id',
            'type': 'type',
            'content': 'content',
        }

    @staticmethod
    def parse(d):
        e = Event()
        for json_key, attr in e._json_key_map.items():
            if attr == 'type':
                setattr(e, attr, MeetingEventType(d[json_key]))
                continue

            setattr(e, attr, d[json_key])
        return e

    def to_json_dict(self):
        e = dict()
        for json_key, attr in self._json_key_map.items():
            if attr == 'type':
                e[json_key] = self.__getattribute__(attr).value
                continue
            elif attr == 'content' and type(self.__getattribute__(attr)) is not dict:  #  As we don't enforce content, it can be just a dict
                e[json_key] = self.__getattribute__(attr).to_json_dict()
                continue

            e[json_key] = self.__getattribute__(attr)
        return e


class StartContent:
    def __init__(self):
        self.otp = ''
        self.key = ''
        self.deeid_login_sig_signed = DeeIdLoginSigSigned()
        self._json_key_map = {
            'otp' : 'otp',
            'key' : 'key',
            'deeIDLoginSigSigned' : 'deeid_login_sig_signed',
            'meeting': 'meeting'
        }

    @staticmethod
    def parse(d):
        sc = StartContent()
        for json_key, attr in sc._json_key_map.items():
            setattr(sc, attr, d[json_key])

        return sc


class JoinContent:
    def __init__(self):
        self.otp = ''
        self.key = ''
        self.deeid_login_sig_signed = DeeIdLoginSigSigned()
        self.meeting = Meeting()
        self._json_key_map = {
            'otp': 'otp',
            'key': 'key',
            'deeIDLoginSigSigned': 'deeid_login_sig_signed',
        }

    @staticmethod
    def parse(d):
        jc = JoinContent()
        for json_key, attr in jc._json_key_map.items():
            setattr(jc, attr, d[json_key])

        return jc


class DeeIdLoginSigSigned:
    def __init__(self):
        self.uid = ''
        self.expiry_time = ''
        self.dee_id = ''
        self.data = ''
        self.msg = ''
        self.signature = ''
        self._json_key_map = {
            'uID': 'uid',
            'expirytime': 'expiry_time',
            'deeID': 'dee_id',
            'data': 'data',
            'msg': 'msg',
            'signature': 'signature'
        }


    @staticmethod
    def parse(d):
        dss = DeeIdLoginSigSigned()
        for json_key, attr in dss._json_key_map.items():
            setattr(dss, attr, d[json_key])

        return dss


class PollContent:
    def __init__(self):
        self.patient = ''
        self.question = ''
        self.options = []
        self.voting_key = ''
        self._json_key_map = {
            'patient': 'patient',
            'question': 'question',
            'options': 'options',
            'votingKey' : 'voting_key'
        }


    @staticmethod
    def parse(d):
        pc = PollContent()
        for json_key, attr in pc._json_key_map.items():
            setattr(pc, attr, d[json_key])

        return pc


class VoteContent:
    def __init__(self):
        self.vote = ''
        self._json_key_map = {
            'vote': 'vote',
        }

    @staticmethod
    def parse(d):
        vc = VoteContent()
        for json_key, attr in vc._json_key_map.items():
            setattr(vc, attr, d[json_key])

        return vc


class PollEndContent:
    def __init__(self):
        self.decrypt_key = ''
        self._json_key_map = {
            'decryptKey': 'decrypt_key',
        }

    @staticmethod
    def parse(d):
        vc = VoteContent()
        for json_key, attr in vc._json_key_map.items():
            setattr(vc, attr, d[json_key])

        return vc

class CommentContent:
    def __init__(self):
        self.comment = ''
        self.patient = ''
        self._json_key_map = {
            'comment': 'comment',
            'patient': 'patient',
        }

    @staticmethod
    def parse(d):
        cc = CommentContent()
        for json_key, attr in cc._json_key_map.items():
            setattr(cc, attr, d[json_key])

        return cc


class ReplyContent:
    def __init__(self):
        self.reply = ''
        self._json_key_map = {
            'reply': 'reply',
        }

    @staticmethod
    def parse(d):
        rc = ReplyContent()
        for json_key, attr in rc._json_key_map.items():
            setattr(rc, attr, d[json_key])

        return rc


class PDCContent:
    def __init__(self):
        self.from_data = ''
        self.to_data = ''
        self.patient = ''
        self._json_key_map = {
            'from': 'from_data',
            'to': 'to_data',
            'patient': 'patient',
        }

    @staticmethod
    def parse(d):
        pdc = PDCContent()
        for json_key, attr in pdc._json_key_map.items():
            setattr(pdc, attr, d[json_key])

        return pdc


class DiscussionContent:
    def __init__(self):
        self.patient = ''
        self._json_key_map = {
            'patient': 'patient',
        }

    @staticmethod
    def parse(d):
        dc = DiscussionContent()
        for json_key, attr in dc._json_key_map.items():
            setattr(dc, attr, d[json_key])

        return dc


class AckErrorContent:
    def __init__(self, error_code, details):
        self.error_code = error_code
        self.details = details
        self._json_key_map = {
            "errorCode": "error_code",
            "details": "details"
        }

    def to_json_dict(self):
        eac = dict()
        for json_key, attr in self._json_key_map.items():
            if attr == 'error_code':
                eac[json_key] = self.__getattribute__(attr).value
                continue
            eac[json_key] = self.__getattribute__(attr)
        return eac


# class AckStartContent:
#     def __init__(self):
#         self.details = []
#         self._json_key_map = {
#             "details": "details",
#         }
#
#     def to_json_dict(self):
#         sac = dict()
#         for json_key, attr in self._json_key_map.items():
#             sac[json_key] = self.__getattribute__(attr)
#         return sac


class AckJoinContent:
    def __init__(self, start_event, join_events):
        self.start_event = start_event
        self.join_events = join_events
        self._json_key_map = {
            "startEvent": "start_event",
            "joinEvents": "join_events",
        }

    def to_json_dict(self):
        jac = dict()
        for json_key, attr in self._json_key_map.items():
            if attr == 'start_event':
                jac[json_key] = self.__getattribute__(attr).to_json_dict()
            elif attr == 'join_events':
                e = self.__getattribute__(attr)
                e_json = {}
                for k, v in e:
                    e_json[k] = v.to_json_dict()
                jac[json_key] = e
        return jac


class AckPollEndContent:
    def __init__(self, votes):
        self.votes = votes
        self._json_key_map = {
            "votes": "votes",
        }

    def to_json_dict(self):
        aec = dict()
        for json_key, attr in self._json_key_map.items():
            aec[json_key] = self.__getattribute__(attr)
        return aec


class AckEndContent:
    def __init__(self, unrefed_event_ids):
        self.unrefed_event_ids = unrefed_event_ids
        self._json_key_map = {
            "unReferencedEventIds": "unrefed_event_ids",
        }

    def to_json_dict(self):
        aec = dict()
        for json_key, attr in self._json_key_map.items():
            aec[json_key] = self.__getattribute__(attr)
        return aec



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
    ACK_END = "ackEnd"
    END = "end"


class EventError(Enum):
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
    BAD_SESSION_KEY_SIGNATURE = "bad session key signature"
    SESSION_KEY_NOT_FOUND = "session key not found"
