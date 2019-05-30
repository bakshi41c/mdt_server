from web3.auto import w3

import config
from db import Database
from meeting_contract_helper import MeetingContractHelper
from model import Meeting

c = config.get_test_config()
db = Database(c["database"]["db_name"], c["database"]["ip"], c["database"]["port"])

# IMPORTANT: MAKE SURE ETHEREUM NODE (OR GANACHE) IS RUNNING AND CONFIGURED IN config.json !!


def test_meeting_contract_deployment():
    mch = MeetingContractHelper(c)
    meeting = Meeting.parse(db.get_all_meetings()[0])
    contract_addr = mch.new_meeting_contract(meeting)

    mdt_meeting = w3.eth.contract(
        address=contract_addr,
        abi=mch.contract_abi,
    )

    assert mdt_meeting.functions.getMeetingId().call() == meeting.id


def test_meeting_contract_set_hash():
    mch = MeetingContractHelper(c)
    meeting = Meeting.parse(db.get_all_meetings()[0])
    contract_addr = mch.new_meeting_contract(meeting)
    meeting.contract_id = contract_addr
    mch.set_event_hash(meeting, "start_event", "end_event")

    mdt_meeting = w3.eth.contract(
        address=contract_addr,
        abi=mch.contract_abi,
    )

    assert mdt_meeting.functions.getEvents().call() == ["start_event", "end_event"]
