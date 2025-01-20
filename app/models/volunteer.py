from app import mongo
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
class Volunteer:
    collection = mongo.db.volunteers 

    @classmethod
    def get_by_email(cls, email):
        volunteer = cls.collection.find_one({"email": email})
        return volunteer
    


    
    @classmethod
    def exists_by_email(cls, email):
        return cls.collection.find_one({"email": email}) is not None
    
    @classmethod
    def find_all(cls):
        volunteers = list(cls.collection.find())
        return volunteers
    
    @classmethod
    def find_by_id(cls, volunteer_id):
        volunteer = cls.collection.find_one({"_id": ObjectId(volunteer_id)}) 
        return volunteer
    
    @classmethod
    def create(cls, data):
        return cls.collection.insert_one(data)

    @classmethod
    def count_all(cls):
        return cls.collection.count_documents({})

    @classmethod
    def delete(cls, volunteer_id):
        cls.collection.delete_one({"_id": ObjectId(volunteer_id)})


    @classmethod
    def update(cls, volunteer_id, data):
        cls.collection.update_one({"_id": ObjectId(volunteer_id)}, {"$set": data})


    @classmethod
    def find_by_volunteer_code(cls, volunteer_code):
        volunteer = cls.collection.find_one({"volunteer_code": volunteer_code})
        return volunteer
    
    @classmethod
    def check_password(cls, user, password):
        return check_password_hash(user["password"], password)
    

    @classmethod
    def find_all_part_time(cls):
        volunteers = list(cls.collection.find({"volunteer_type": "Part-Time"}))
        return volunteers
    

    @classmethod
    def find_one(cls, query):
        return cls.collection.find_one(query)