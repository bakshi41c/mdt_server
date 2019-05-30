import copy
import json

import pytest

import config
from authorization import Role
from db import Database
from gen_sample import Sample
from model import Meeting, Staff, Patient, Event, MeetingEventType

with open('tests/general_event.json') as f:
    general_event_dict = json.load(f)

with open('tests/comment_event.json') as f:
    comment_event_dict = json.load(f)

with open('tests/discussion_event.json') as f:
    discussion_event_dict = json.load(f)

with open('tests/reply_event.json') as f:
    reply_event_dict = json.load(f)

with open('tests/join_event.json') as f:
    join_event_dict = json.load(f)

with open('tests/poll_event.json') as f:
    poll_event_dict = json.load(f)

with open('tests/start_event.json') as f:
    start_event_dict = json.load(f)

with open('tests/vote_event.json') as f:
    vote_event_dict = json.load(f)


c = config.get_test_config()
s = Sample(c)
db = Database(c["database"]["db_name"], c["database"]["ip"], c["database"]["port"])


def test_parse_and_convert_meeting():
    original_dict = db.get_all_meetings()[0]
    parsed_object = Meeting.parse(original_dict)
    generated_dict = parsed_object.to_json_dict()
    assert original_dict == generated_dict


def test_parse_and_convert_modified_meeting():
    original_dict = db.get_all_meetings()[0]
    parsed_object = Meeting.parse(original_dict)  # Type: Meeting
    parsed_object.started = not parsed_object.started
    original_dict["started"] = not original_dict["started"]
    parsed_dict = parsed_object.to_json_dict()
    assert original_dict == parsed_dict


def test_parse_and_convert_bad_meeting():
    original_dict = db.get_all_meetings()[0]
    print(original_dict)
    original_dict.pop("title")
    with pytest.raises(KeyError) as e:
        parsed_dict = Meeting.parse(original_dict)


def test_parse_and_convert_staff():
    original_dict = db.get_all_staff()[0]
    parsed_object = Staff.parse(original_dict)
    generated_dict = parsed_object.to_json_dict()
    assert original_dict == generated_dict


def test_parse_and_convert_modified_staff():
    original_dict = db.get_all_staff()[0]
    parsed_object = Staff.parse(original_dict)  # Type: Meeting
    parsed_object.name = "AASNvlaSNv aknsv laksnvlakvn"
    original_dict["name"] = "AASNvlaSNv aknsv laksnvlakvn"
    parsed_dict = parsed_object.to_json_dict()
    assert original_dict == parsed_dict


def test_parse_and_convert_bad_staff():
    original_dict = db.get_all_staff()[0]
    print(original_dict)
    original_dict.pop("name")
    with pytest.raises(KeyError) as e:
        parsed_dict = Meeting.parse(original_dict)


def test_parse_and_convert_patient():
    original_dict = db.get_all_patients()[0]
    parsed_object = Patient.parse(original_dict)
    generated_dict = parsed_object.to_json_dict()
    assert original_dict == generated_dict


def test_parse_and_convert_modified_patient():
    original_dict = db.get_all_patients()[0]
    parsed_object = Patient.parse(original_dict)  # Type: Meeting
    parsed_object.name = "AASNvlaSNv aknsv laksnvlakvn"
    original_dict["name"] = "AASNvlaSNv aknsv laksnvlakvn"
    parsed_dict = parsed_object.to_json_dict()
    assert original_dict == parsed_dict


def test_parse_and_convert_bad_patient():
    original_dict = db.get_all_patients()[0]
    print(original_dict)
    original_dict.pop("name")
    with pytest.raises(KeyError) as e:
        parsed_dict = Meeting.parse(original_dict)


def test_parse_and_convert_event():
    original_dict = copy.deepcopy(general_event_dict)
    parsed_object = Event.parse(original_dict)
    generated_dict = parsed_object.to_json_dict()
    assert original_dict == generated_dict


def test_parse_event_type():
    original_dict = copy.deepcopy(general_event_dict)
    original_dict["type"] = "join"
    parsed_object = Event.parse(original_dict)  # Type: Meeting
    assert parsed_object.type == MeetingEventType.JOIN


def test_parse_and_convert_modified_event():
    original_dict = copy.deepcopy(general_event_dict)
    parsed_object = Event.parse(original_dict)  # Type: Meeting
    parsed_object.type = MeetingEventType.START
    original_dict["type"] = "start"
    parsed_dict = parsed_object.to_json_dict()
    assert original_dict == parsed_dict


def test_parse_and_convert_bad_event():
    original_dict = copy.deepcopy(general_event_dict)
    print(original_dict)
    original_dict.pop("meetingId")
    with pytest.raises(KeyError) as e:
        parsed_dict = Meeting.parse(original_dict)
