import json
import copy
import event_schema_validator

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


def test_validate_general_event():
    event = copy.deepcopy(general_event_dict)
    ok, err = event_schema_validator.validate(event)
    assert ok


def test_validate_general_event_fail_timestamp():
    event = copy.deepcopy(general_event_dict)
    event['timestamp'] = "4640564060"
    ok, err = event_schema_validator.validate(event)
    assert not ok


def test_validate_general_event_fail_missing_by():
    event = copy.deepcopy(general_event_dict)
    event.pop("by")
    ok, err = event_schema_validator.validate(event)
    assert not ok


def test_validate_general_event_fail_missing_id():
    event = copy.deepcopy(general_event_dict)
    event.pop("_id")
    ok, err = event_schema_validator.validate(event)
    assert not ok


def test_validate_general_event_fail_missing_meeting_id():
    event = copy.deepcopy(general_event_dict)
    event.pop("meetingId")
    ok, err = event_schema_validator.validate(event)
    assert not ok


def test_validate_general_event_fail_missing_timestamp():
    event = copy.deepcopy(general_event_dict)
    event.pop("timestamp")
    ok, err = event_schema_validator.validate(event)
    assert not ok


def test_validate_general_event_fail_missing_type():
    event = copy.deepcopy(general_event_dict)
    event.pop("type")
    ok, err = event_schema_validator.validate(event)
    assert not ok


def test_validate_general_event_fail_invalid_type():
    event = copy.deepcopy(general_event_dict)
    event['type'] = "l33t"
    ok, err = event_schema_validator.validate(event)
    assert not ok


def test_validate_comment_event():
    event = copy.deepcopy(comment_event_dict)
    ok, err = event_schema_validator.validate(event)
    assert ok


def test_validate_comment_event_fail_missing_content():
    event = copy.deepcopy(comment_event_dict)
    event.pop("content")
    ok, err = event_schema_validator.validate(event)
    assert not ok


def test_validate_comment_event_fail_missing_comment():
    event = copy.deepcopy(comment_event_dict)
    event["content"].pop("comment")
    ok, err = event_schema_validator.validate(event)
    assert not ok


def test_validate_discussion_event():
    event = copy.deepcopy(discussion_event_dict)
    ok, err = event_schema_validator.validate(event)
    assert ok


def test_validate_discussion_event_fail_missing_content():
    event = copy.deepcopy(discussion_event_dict)
    event.pop("content")
    ok, err = event_schema_validator.validate(event)
    assert not ok


def test_validate_discussion_event_fail_missing_patient():
    event = copy.deepcopy(discussion_event_dict)
    event["content"].pop("patient")
    ok, err = event_schema_validator.validate(event)
    assert not ok


def test_validate_reply_event():
    event = copy.deepcopy(reply_event_dict)
    ok, err = event_schema_validator.validate(event)
    assert ok


def test_validate_reply_event_fail_missing_content():
    event = copy.deepcopy(reply_event_dict)
    event.pop("content")
    ok, err = event_schema_validator.validate(event)
    assert not ok


def test_validate_reply_event_fail_missing_reply():
    event = copy.deepcopy(reply_event_dict)
    event["content"].pop("reply")
    ok, err = event_schema_validator.validate(event)
    assert not ok


def test_validate_join_event():
    event = copy.deepcopy(join_event_dict)
    ok, err = event_schema_validator.validate(event)
    assert ok


def test_validate_join_event_fail_missing_content():
    event = copy.deepcopy(join_event_dict)
    event.pop("content")
    ok, err = event_schema_validator.validate(event)
    assert not ok


def test_validate_join_event_fail_missing_otp():
    event = copy.deepcopy(join_event_dict)
    event["content"].pop("otp")
    ok, err = event_schema_validator.validate(event)
    assert not ok


def test_validate_poll_event():
    event = copy.deepcopy(poll_event_dict)
    ok, err = event_schema_validator.validate(event)
    assert ok


def test_validate_poll_event_fail_missing_content():
    event = copy.deepcopy(poll_event_dict)
    event.pop("content")
    ok, err = event_schema_validator.validate(event)
    assert not ok


def test_validate_poll_event_fail_missing_question():
    event = copy.deepcopy(poll_event_dict)
    event["content"].pop("question")
    ok, err = event_schema_validator.validate(event)
    assert not ok


def test_validate_poll_event_fail_missing_options():
    event = copy.deepcopy(poll_event_dict)
    event["content"].pop("options")
    ok, err = event_schema_validator.validate(event)
    assert not ok


def test_validate_poll_event_fail_no_options():
    event = copy.deepcopy(poll_event_dict)
    event["content"]["options"] = []
    ok, err = event_schema_validator.validate(event)
    assert not ok


def test_validate_poll_event_fail_one_option():
    event = copy.deepcopy(poll_event_dict)
    event["content"]["options"] = ["yes"]
    ok, err = event_schema_validator.validate(event)
    assert not ok


def test_validate_poll_event_three_option():
    event = copy.deepcopy(poll_event_dict)
    event["content"]["options"] = ["yes", "no", "maybe"]
    ok, err = event_schema_validator.validate(event)
    assert ok


def test_validate_start_event():
    event = copy.deepcopy(start_event_dict)
    ok, err = event_schema_validator.validate(event)
    assert ok


def test_validate_start_event_fail_missing_content():
    event = copy.deepcopy(start_event_dict)
    event.pop("content")
    ok, err = event_schema_validator.validate(event)
    assert not ok


def test_validate_start_event_fail_missing_otp():
    event = copy.deepcopy(start_event_dict)
    event["content"].pop("otp")
    ok, err = event_schema_validator.validate(event)
    assert not ok


def test_validate_start_event_fail_missing_meeting():
    event = copy.deepcopy(start_event_dict)
    event["content"].pop("meeting")
    ok, err = event_schema_validator.validate(event)
    assert not ok


def test_validate_start_event_fail_invalid_otp_type():
    event = copy.deepcopy(start_event_dict)
    event["content"]["otp"] = 4320
    ok, err = event_schema_validator.validate(event)
    assert not ok


def test_validate_vote_event():
    event = copy.deepcopy(vote_event_dict)
    ok, err = event_schema_validator.validate(event)
    assert ok


def test_validate_vote_event_fail_missing_content():
    event = copy.deepcopy(vote_event_dict)
    event.pop("content")
    ok, err = event_schema_validator.validate(event)
    assert not ok


def test_validate_vote_event_fail_missing_otp():
    event = copy.deepcopy(vote_event_dict)
    event["content"].pop("vote")
    ok, err = event_schema_validator.validate(event)
    assert not ok
