import config
from authorization import get_role, Role
from db import Database
from gen_sample import Sample
from model import Meeting, Staff

c = config.get_test_config()
s = Sample(c)
db = Database(c["database"]["db_name"], c["database"]["ip"], c["database"]["port"])

for i in range(50):
    s.gen_staff_data()

for i in range(50):
    s.gen_patient_data()

mid = s.gen_meeting_data()


def test_get_role_host():
    meeting = Meeting.parse(db.get_meeting(mid))
    staff = Staff.parse(db.get_staff(meeting.host))
    roles = get_role(staff, meeting)
    assert (Role.HOST in roles) and (Role.PARTICIPANT in roles)


def test_get_role_participant():
    meeting = Meeting.parse(db.get_meeting(mid))
    staff = Staff.parse(db.get_staff(meeting.staff[1]))
    roles = get_role(staff, meeting)
    assert (Role.PARTICIPANT in roles)


def test_get_role_none():
    meeting = Meeting.parse(db.get_meeting(mid))
    all_staff_ids = set([staff["_id"] for staff in db.get_all_staff()])
    non_participants = all_staff_ids.difference(set(meeting.staff))
    staff = Staff.parse(db.get_staff(non_participants.pop()))
    roles = get_role(staff, meeting)
    assert (len(roles) == 0)
