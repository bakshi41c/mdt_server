import json

import bencode

import config
from authentication import Auth

with open('tests/general_event.json') as f:
    event_dict = json.load(f)

c = config.get_test_config()


def test_sign_event():
    auth = Auth(c)
    signed_event = auth.sign_event(event_dict=event_dict)
    assert signed_event["_id"] == event_dict["_id"]


def test_get_sig_address_from_event():
    auth = Auth(c)
    addr = auth.get_sig_address_from_event(event_dict)
    assert addr == "0x1c0b2f7a73ecbf7ce694887020dbcbaaa2e126f7"
