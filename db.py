import pymongo


class Database:
    def __init__(self, db_name, db_ip, db_port):
        self.db_name = db_name
        self.db_ip = db_ip
        self.db_port = db_port

        self.client = pymongo.MongoClient("mongodb://" + self.db_ip + ":" + self.db_port + "/")
        self.db = self.client[self.db_name]
        self.meeting_col = self.db["meeting"]
        self.events_col = self.db["events"]
        self.staff_col = self.db["staff"]
        self.patient_col = self.db["patient"]
        self.patient_meeting_data_col = self.db["patient_meeting_data"]

    ############
    # MEETINGS #
    ############

    def insert_meeting(self, meeting):
        return self.meeting_col.insert_one(meeting)

    def get_meeting(self, meeting_id):
        return self.meeting_col.find_one({"_id": meeting_id})

    def update_meeting(self, meeting_id, data):
        return self.meeting_col.update_one({"_id": meeting_id}, {'$set': data})

    def delete_meeting(self, meeting_id):
        return self.meeting_col.delete_one({"_id": meeting_id})

    def get_all_meetings(self):
        return list(self.meeting_col.find())

    ###################
    # PATIENT-MEETING #
    ###################

    def insert_patient_meeting_data(self, meeting_id, patient_id,  meeting_patient_data):
        meeting_patient_data["meeting_id"] = meeting_id
        meeting_patient_data["patient_id"] = patient_id
        meeting_patient_data["mdt_outcome"] = meeting_patient_data.get("mdt_outcome", "")
        meeting_patient_data["mdt_question"] = meeting_patient_data.get("mdt_question", "")
        meeting_patient_data["group"] = meeting_patient_data.get("group", "")
        meeting_patient_data["lc"] = meeting_patient_data.get("lc", "")
        meeting_patient_data["investigation"] = meeting_patient_data.get("investigation", "")
        meeting_patient_data["surgery"] = meeting_patient_data.get("surgery", "")

        self.patient_meeting_data_col.insert_one(meeting_patient_data)

    def get_patient_meeting_data(self, meeting_id, patient_id):
        return self.patient_meeting_data_col.find_one({"meeting_id": meeting_id, "patient_id": patient_id})

    def update_patient_meeting_data(self, meeting_id, patient_id, data):
        return self.patient_meeting_data_col.update_one({"meeting_id": meeting_id, "patient_id": patient_id},
                                                   {'$set': data})

    def delete_patient_meeting_data(self, meeting_id, patient_id):
        return self.patient_meeting_data_col.delete_one({"meeting_id": meeting_id, "patient_id": patient_id})

    ############
    # PATIENTS #
    ############

    def get_patient(self, patient_id):
        return self.patient_col.find_one({"_id": patient_id})

    def get_all_patients(self):
        return list(self.patient_col.find())

    ##########
    # EVENTS #
    ##########

    def get_event(self, event_id):
        return self.events_col.find_one({"_id": event_id})

    def get_all_events_in_meeting(self, meeting_id):
        pass

    def get_all_events(self):
        return list(self.events_col.find())

    def insert_event(self, event):
        return self.events_col.insert_one(event)

    ##########
    # STAFF  #
    ##########

    def get_staff(self, staff_id):
        return self.staff_col.find_one({"_id": staff_id})

    def get_all_staff(self):
        return list(self.staff_col.find())

