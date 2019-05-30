import json
import sys
import time
from random import randint
import click
import socketio
import config
from authentication import Auth
from db import Database
from model import Staff, Event, MeetingEventType, StartContent, DeeIdLoginSigSigned, Meeting

sio = socketio.Client()
sio.connect('http://localhost:51235')
c = config.get_config()
db = Database(c["database"]["db_name"], c["database"]["ip"], c["database"]["port"])
auth = Auth(c)

public_key = ""
secret_key = ""
staff = ""
meeting_id = ""
ref_event = "genesis"


@sio.on('room-message')
def on_message(data):
    global ref_event
    event = json.loads(data)
    print("Message from Server!")
    print_event(event)

    ref_event = json.loads(data)["_id"]


def server_reply(data):
    event =  json.loads(data)
    print("Reply from Server!")
    print_event(event)


@click.command()
@click.argument('address')
@click.argument('secret')
def login(address, secret):
    global public_key, secret_key, staff
    public_key = address
    secret_key = secret
    staff_dict = db.get_staff(address)
    if staff_dict is None:
        print("Unknown Staff!")
    try:
        staff = Staff.parse(staff_dict)
    except Exception as e:
        print("Error parsing staff!", e)

    if staff is None:
        print("Unknown Staff!")

    print(
        "****************************************\n"
        "*       C-MEET CLI (FOR TESTING)       *\n"
        "****************************************"
    )
    print("Connected to Meeting Server!")
    print("You are logged in as ", staff.name, "!\n")
    menu()
    print("Bye!")
    sio.disconnect()


def menu():
    options = {"start", "join", "leave", "end", "poll", "vote", "end_poll", "discussion", "pdc", "comment", "reply", "exit"}
    menu_options = ''.join(["> " + option + "\n" for option in options])

    option = ""
    while True:
        option = click.prompt('Menu:\n' + menu_options, type=str)

        if option == "start":
            start()
        if option == "join":
            join()
        if option == "poll":
            poll()
        if option == "vote":
            vote()
        if option == "comment":
            comment()
        print(option)

        if option == "exit":
            break


def start():
    global meeting_id
    event = Event()
    event.type = MeetingEventType.START
    event.ref_event = "genesis"
    event.timestamp = int(time.time())
    event.by = public_key
    meeting_id = click.prompt("Meeting id?", type=str)

    event.meeting_id = meeting_id

    meeting_dict = db.get_meeting(meeting_id)

    if meeting_dict is None:
        print("Meeting not found")
        return

    otp = str(randint(1000, 9999))

    start_content = {
        'otp': otp,
        "deeIDLoginSigSigned": {
          "data": "",
          "deeID": "",
          "expirytime": "",
          "msg": "",
          "signature": "",
          "type": "",
          "uID": "2a7d1a6c-3d2c-45f2-b56f-54f10152289e"},
        "key": public_key,
        "meeting": meeting_dict
    }

    event.content = start_content
    print("Using OTP: ", otp)
    signed_event = auth.sign_event(event.to_json_dict())
    print("Sending!")
    print_event(signed_event)
    sio.emit('room-message', json.dumps(signed_event), callback=server_reply)


def join():
    global meeting_id
    event = Event()
    event.type = MeetingEventType.JOIN
    event.timestamp = int(time.time())
    event.by = public_key

    if meeting_id == "":
        meeting_id = click.prompt("Meeting id?", type=str)

    event.meeting_id = meeting_id

    meeting_dict = db.get_meeting(meeting_id)

    if meeting_dict is None:
        print("Meeting not found")
        return

    event.ref_event = meeting_dict["startEventId"]

    otp = click.prompt("otp?", type=str)

    join_content = {
        'otp': otp,
        "deeIDLoginSigSigned": {
            "data": "",
            "deeID": "",
            "expirytime": "",
            "msg": "",
            "signature": "",
            "type": "",
            "uID": "2a7d1a6c-3d2c-45f2-b56f-54f10152289e"},
        "key": public_key,
    }

    event.content = join_content

    signed_event = auth.sign_event(event.to_json_dict())
    print("Sending!")
    print_event(signed_event)
    sio.emit('room-message', json.dumps(signed_event), callback=server_reply)


def comment():
    event = Event()
    event.type = MeetingEventType.JOIN
    event.timestamp = int(time.time())
    event.by = public_key
    event.meeting_id = meeting_id
    event.ref_event = ref_event
    comment_str = click.prompt("comment?", type=str)
    event.content = {
        "comment": comment_str
    }

    signed_event = auth.sign_event(event.to_json_dict())
    sio.emit('room-message', json.dumps(signed_event), callback=server_reply)


def poll():
    event = Event()
    event.type = MeetingEventType.POLL
    event.timestamp = int(time.time())
    event.by = public_key
    event.meeting_id = meeting_id
    event.ref_event = ref_event
    patient = click.prompt("patient?", type=str)
    question = click.prompt("question?", type=str)
    no_of_options = click.prompt("no. of options?", type=int)
    options = []
    for i in range(0, no_of_options):
        option = click.prompt("option " + str(i+1) + "" , type=str)
        options.append(option)

    event.content = {
        "patient": patient,
        "question": question,
        "options": options
    }
    signed_event = auth.sign_event(event.to_json_dict())
    print("Sending!")
    print_event(signed_event)
    sio.emit('room-message', json.dumps(signed_event), callback=server_reply)


def vote():
    event = Event()
    event.type = MeetingEventType.VOTE
    event.timestamp = int(time.time())
    event.by = public_key
    event.meeting_id = meeting_id
    event.ref_event = click.prompt("Poll Event Id?", type=str)

    vote_str = click.prompt("vote?", type=str)

    event.content = {
        "vote": vote_str,
    }
    signed_event = auth.sign_event(event.to_json_dict())
    print("Sending!")
    print_event(signed_event)
    sio.emit('room-message', json.dumps(signed_event), callback=server_reply)


def print_event(event):
    print("===================")
    print(json.dumps(event, sort_keys=True, indent=4))
    print("===================\n")


if __name__ == '__main__':
    login()
    exit()
