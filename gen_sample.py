from random import randint
import random
import uuid
import math
from dateutil.relativedelta import relativedelta
import datetime
from web3.auto import w3, Web3

from db import Database
import config

first_name = [
    "Rigoberto",
    "Tess",
    "Hilton",
    "Martin",
    "Adan",
    "Glendora",
    "Leroy",
    "Harold",
    "Glynis",
    "Bernita",
    "Shubham",
    "Sirvan"
]

last_name = [
    "Oliver",
    "Suarez",
    "Shepard",
    "Morris",
    "Huerta",
    "Cantrell",
    "Smith",
    "Pugh",
    "Knox",
    "Hines",
    "Bakshi",
    "Almasi"
]

roles = [
    "Student",
    "Nurse",
    "Doctor",
    "Admin"
]

deeid_user_a = {  # The sample user in the DeeID test app
    "_id": "0xa78e5bb6ff6a849e120985d32532e5067f262e19",
    "name": "Shubham Bakshi",
    "role": "Doctor",
}


class Sample:
    def __init__(self, config):
        self.config = config
        self.db = Database(config["database"]["db_name"], config["database"]["ip"], config["database"]["port"])

    def gen_patient_data(self):
        pid = str(uuid.uuid4())
        data = {
            "_id": pid,
            "name": first_name[randint(0, len(first_name) - 1)] + " " + last_name[randint(0, len(last_name) - 1)],

            # Get a random float from 0-20, then subtract that many years from now (in days)
            "dob": str(datetime.datetime.now() - relativedelta(days=math.floor(random.uniform(0, 20) * 365))),

            "hospitalNumber": randint(0, 50),
            "infoflexLink": "http://example.com/" + pid,

        }
        self.db.insert_patient(data)
        return pid

    def gen_staff_data(self):
        acct = w3.eth.account.create(str(uuid.uuid4()))
        # [pub, private]
        print([acct.address, acct.privateKey.hex()])

        data = {
            "_id": acct.address,
            "name": first_name[randint(0, len(first_name) - 1)] + " " + last_name[randint(0, len(last_name) - 1)],
            "role": roles[randint(0, len(roles) - 1)],
        }

        self.db.insert_staff(data)
        return acct.address

    def gen_meeting_data(self):
        mid = str(uuid.uuid4())
        patient_ids = [patient["_id"] for patient in self.db.get_all_patients()]
        staff_ids = [staff["_id"] for staff in self.db.get_all_staff()]
        patients = patient_ids[:randint(1, len(patient_ids))]
        staff = staff_ids[:randint(1, len(staff_ids))]

        data = {"_id": mid,
                "patients": patients,
                "staff": staff,
                "title": "MDT meeting",
                "description": "No description",
                "contractId": "",
                "startEventId": "",
                "host": staff[randint(0, len(staff) - 1)],
                "started": False,
                "ended": False,
                "attendedStaff": [],
                "date": "2019-04-23T02:56:22.000Z"}

        self.db.insert_meeting(data)
        return mid

    def delete_all(self, ):
        self.db.staff_col.drop()
        self.db.patient_col.drop()
        self.db.events_col.drop()
        self.db.meeting_col.drop()
        self.db.patient_meeting_data_col.drop()


if __name__ == '__main__':
    c = config.get_config()
    s = Sample(c)
    for i in range(50):
        s.gen_patient_data()

    print("[public, private]")
    for i in range(50):
        s.gen_staff_data()

    s.gen_meeting_data()
    s.gen_meeting_data()

