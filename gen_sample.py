from random import randint
import random
import uuid
import math
from dateutil.relativedelta import relativedelta
import datetime
import pymongo
from web3.auto import w3, Web3

DB_NAME = "mdt_meetings"
DB_IP = "localhost"
DB_PORT = "27017"
no_of_samples = 50

mongo_client = pymongo.MongoClient("mongodb://" + DB_IP + ":" + DB_PORT + "/")
db = mongo_client[DB_NAME]
patient_col = db["patient"]
staff_col = db["staff"]

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


def gen_patient_data():
    pid = str(uuid.uuid4())
    return {
        "_id": pid,
        "name": first_name[randint(0, len(first_name) - 1)] + " " + last_name[randint(0, len(last_name) - 1)],

        # Get a random float from 0-20, then subtract that many years from now (in days)
        "dob": str(datetime.datetime.now() - relativedelta(days=math.floor(random.uniform(0, 20) * 365))),

        "hospitalNumber": randint(0, 50),
        "infoflexLink": "http://example.com/" + pid,

    }


def gen_staff_data():
    acct = w3.eth.account.create(str(uuid.uuid4()))
    return {
        "_id": acct.address,
        "name": first_name[randint(0, len(first_name) - 1)] + " " + last_name[randint(0, len(last_name) - 1)],
        "role": roles[randint(0, len(roles) - 1)],
    }


deeid_user_a = {  # The sample user in the DeeID app
    "_id": "0xa78e5bb6ff6a849e120985d32532e5067f262e19",
    "name": "Shubham Bakshi",
    "role": "Doctor",
}

if __name__ == '__main__':
    patients = []
    staff = []
    for i in range(no_of_samples):
        patients.append(gen_patient_data())
        staff.append(gen_staff_data())

    # print(patients)
    # print(staff)
    staff_col.insert(deeid_user_a)
    staff_col.insert_many(staff)
    patient_col.insert_many(patients)



'''
meeting = [
    {
        "_id": "g2c1452",
        "date": "2019-01-22 16:20:133.546876",
        "title": "GOSH MDT Meeting 30th Jan",
        "staff": ["09j733z", "8m742b9", "5x82azx"],
        "patients": ["94f5qzg", "495s67s"],
        "events": ["djfc432", "53trnaj", "bz94r0l", "ds4w59t", "xh051eg", "uf48074", "pfy4n9f", "v6u973f", "fr1s36a"]
    },
]


patient = [
    {
        "_id" : "94f5qzg",
        "name" : "Shubham Bakshi",
        "dob": "1994-11-03",
        "hospital_number" : "",
        "infoflex_link": "",

    }
]

staff = [
    {
        "_id": "djfc432",
        "name": "Shubham Bakshi",
        "role": "Student",
    }
]

patient_meeting_data = [
    {
        "patient_id": "94f5qzg",
        "meeting_id": "g2c1452",
        "questions_for_mdt": "",
        "group": "",
        "main_opinion": "",
        "investigation": "",
        "surgery": "",
        "lc": "",
        "meeting_outcome": "",
        "events": ["djfc432"]
    }
]

'''