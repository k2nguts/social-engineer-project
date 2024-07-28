import hashlib
import secrets
import string
from pymongo import MongoClient
from dynaconf import Dynaconf
import logging

logging.basicConfig(level=logging.INFO)

# Initialize Dynaconf with settings from settings.toml
try:
    settings = Dynaconf(settings_file="settings.toml")
except Exception as e:
    logging.error(f"Failed to load settings from settings.toml: {e}")
    raise

class MongoDB:
    def __init__(self):
        try:
            self.client = MongoClient(settings.database.uri)
            self.db = self.client[settings.database.database]
            self.victims_collection = self.db['victims']
            self.users_collection = self.db['users']
            logging.info("Connected to MongoDB")
        except Exception as e:
            logging.error(f"Failed to connect to MongoDB: {e}")
            raise

    def _generate_strong_token(self, length=24):
        # Generate a strong random token with specified length
        alphabet = string.ascii_letters + string.digits
        token = ''.join(secrets.choice(alphabet) for _ in range(length))
        return token

    def insert_victim_from_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    line = line.strip()
                    if line:
                        name, surname, email, department = line.split(',')
                        name, surname = name.strip().lower(), surname.strip().lower()
                        # Check if name_surname_hash already exists
                        name_surname_hash = self._hash_name_surname(name, surname)
                        existing_victim = self.victims_collection.find_one({"name_surname_hash": name_surname_hash})
                        if existing_victim:
                            logging.info(f"Victim {name} {surname} already exists, skipping insertion")
                            continue

                        # Generate strong random token
                        token = self._generate_strong_token()
                        
                        # Create victim data with token and other fields empty
                        victim_data = {
                            "name": name,
                            "surname": surname,
                            "email": email.strip(),
                            "department": department.strip(),
                            "token": token,
                            "status": "NOT-DELIVERED",
                            "num_of_opened":0,
                            "num_of_clicked":0,
                            "num_of_submitted":0,
                            "name_surname_hash": name_surname_hash,
                            "mail_opening_info":[],
                            "link_clicking_info":[],
                            "data_submitting_info":[]
                        }
                        
                        # Insert victim data into MongoDB
                        result = self.victims_collection.insert_one(victim_data)
                        if result.inserted_id:
                            logging.info(f"Victim {name} {surname} inserted successfully")
                        else:
                            logging.error(f"Failed to insert victim {name} {surname}")
        except Exception as e:
            logging.error(f"An error occurred while inserting victims from file: {e}")

    def _hash_name_surname(self, name, surname):
        # Combine name and surname and hash the result
        full_name = name + ' ' + surname
        hashed_name_surname = hashlib.sha256(full_name.encode()).hexdigest()
        return hashed_name_surname
    
    def get_victim_by_token(self, token):
        victim = self.victims_collection.find_one({"token": token})
        return victim    
    
    def update_victim_click_info(self, token, ip_address, user_agent, click_date):
        click_info = {
            "ip":ip_address,
            "user_agent":user_agent,
            "click_date":click_date
        }
        result = self.victims_collection.update_one(
            {"token":token},
            {
                "$inc":{"num_of_clicked":1},
                "$push":{"link_clicking_info":click_info}
            }
        )
        if result.modified_count > 0:
            return True
        else:
            return False
        
    def update_victim_submit_info(self, token, ip_address, user_agent, submit_date, submitted_username_password):
        submit_info = {
            "ip":ip_address,
            "user_agent":user_agent,
            "submit_date":submit_date,
            "submitted_username_password":submitted_username_password
        }
        result = self.victims_collection.update_one(
            {"token":token},
            {
                "$inc":{"num_of_submitted":1},
                "$push":{"data_submitting_info":submit_info}
            }
        )
        if result.modified_count > 0:
            return True
        else:
            return False
        
    def update_victim_open_info(self, token, opened_date):
        open_info = {
            "opened_date": opened_date
        }

        result = self.victims_collection.update_one(
            {"token": token},
            {
                "$inc": {"num_of_opened": 1},
                "$push": {"mail_opening_info": open_info}
            }
        )

        if result.modified_count > 0:
            return True
        else:
            return False
        
    def get_victims_summary(self):
        victims = self.victims_collection.find({}, {"_id": 0, "token": 1, "name": 1, "surname": 1, "email":1, "status": 1, "department": 1})
        return list(victims)
    
    def get_all_victims(self):
        try:
            victims = self.victims_collection.find({"_id":0})
            return list(victims)
        except Exception as e:
            logging.error(f"Error fetching all victims: {e}")
            return []

    def get_victim_by_token(self, token):
        try:
            victim = self.victims_collection.find_one({"token": token}, {"_id": 0})
            return victim
        except Exception as e:
            logging.error(f"Error getting victim by token: {e}")
            return None    


    def get_analytics_data(self):
        try:
            total_records = self.victims_collection.count_documents({})
            sent_records = self.victims_collection.count_documents({"status":"Delivered"})

             # Aggregate total number of opened, clicked, and submitted records
            num_of_opened = self.victims_collection.aggregate([{"$group": {"_id": None, "total": {"$sum": "$num_of_opened"}}}]).next().get("total", 0)
            num_of_clicked = self.victims_collection.aggregate([{"$group": {"_id": None, "total": {"$sum": "$num_of_clicked"}}}]).next().get("total", 0)
            num_of_submitted = self.victims_collection.aggregate([{"$group": {"_id": None, "total": {"$sum": "$num_of_submitted"}}}]).next().get("total", 0)
            
            return {
                "total_records": total_records,
                "sent_records": sent_records,
                "num_of_opened":num_of_opened,
                "num_of_clicked":num_of_clicked,
                "num_of_submitted":num_of_submitted
            }
        except Exception as e:
            logging.error(f"Failed to get analytics: {e}")
            return None

