import click
import config
from authentication import Auth
from db import Database
from meeting_contract_helper import MeetingContractHelper
from model import Meeting
from web3.auto import Web3

c = config.get_config()
db = Database(c["database"]["db_name"], c["database"]["ip"], c["database"]["port"])
auth = Auth(c)

mch = MeetingContractHelper(c)
w3 = Web3(Web3.HTTPProvider(c["smart_contract"]["bc_provider_url"]))

meeting = None # type: Meeting


@click.command()
@click.argument('meeting_id')
def entry(meeting_id):
    global meeting
    print(
        "****************************************\n"
        "*       CONTRACT CLI (FOR TESTING)     *\n"
        "****************************************"
    )

    meeting = Meeting.parse(db.get_meeting(meeting_id))
    menu()
    print("Bye!")


def menu():
    options = ["1. Deploy contract", "2. Get Event Hashes", "3. Exit"]
    menu_options = ''.join(["> " + option + "\n" for option in options])

    option = ""
    while True:
        option = click.prompt('Menu:\n' + menu_options, type=str)
        if option == "1":
            deploy_contract()
        if option == "2":
            get_event_hash()
        if option == "3" or option == "exit":
            break


def deploy_contract():
    global meeting

    print("Deploying Contract...")
    if meeting is None:
        print("Error Meeting does not exist")

    try:
        contract_addr = mch.new_meeting_contract(meeting)
        print("Contract Successfully Deployed!")
        print("Contract ID: ", contract_addr)
    except Exception as e:
        print(e)
        return


def get_event_hash():
    contract_addr = get_or_ask_contract_id()
    print("")
    print("Contract ID: ", contract_addr)
    mdt_meeting = w3.eth.contract(
        address=contract_addr,
        abi=mch.contract_abi,
    )

    try:
        hashes = mdt_meeting.functions.getEvents().call()
    except Exception as e:
        print(e)
        return

    if len(hashes) < 2:
        print("Error parsing hash events!")
        print(hashes)
        return

    print("DB: ")
    print("START: ", meeting.start_event_id)
    print("END_ACK: ", find_end_ack_event_id())
    print("--")
    print("Smart Contract: ")
    print("START: ", hashes[0])
    print("END_ACK: ", hashes[1])
    print("")


def get_or_ask_contract_id():
    if meeting.contract_id == '' or meeting.contract_id is None:
        print("Could not automatically fetch Contract ID from database!")
        return click.prompt("Contract ID?")

    return meeting.contract_id


def find_end_ack_event_id():
    events = db.get_all_events_in_meeting(meeting.id)

    for event in events:
        if event["type"] == "ackEnd":
            return event["_id"]


if __name__ == '__main__':
    entry()
    exit()
