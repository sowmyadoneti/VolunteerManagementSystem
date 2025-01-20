from app import mongo
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId, errors 

class Event:
    collection = mongo.db.events

    @classmethod
    def create(cls, data):  
        return cls.collection.insert_one(data)
    

    @classmethod
    def update(cls, event_id, data):
        try:
            cls.collection.update_one({"_id": ObjectId(event_id)}, data)
        except Exception as e:
            print(f"Update failed: {e}")

    @classmethod
    def update_e(cls, event_id, update_data):
        """
        Perform an update operation on an event document.
        """
        cls.collection.update_one({"_id": ObjectId(event_id)}, update_data)

    @classmethod
    def find_by_id(cls, id):
        return cls.collection.find_one({"_id": ObjectId(id)})
    

    @classmethod
    def get_by_id(cls, id):
        return cls.collection.find_one({"_id": ObjectId(id)})
    

    @classmethod
    def find_by_organizer_id(cls, organizer_id):
        return list(cls.collection.find({"organizer_id": organizer_id}))
    

    @classmethod
    def delete_by_id(cls, event_id):
        print(event_id)
        return cls.collection.delete_one({"_id": ObjectId(event_id)})
    

    @classmethod
    def delete(cls, data):

        return cls.collection.delete_one(data)
    
    @classmethod
    def find_all(cls, query={}):
        return list(cls.collection.find(query))
    
    @classmethod
    def find_all_ongoing(cls):
        return cls.collection.find({"status": "ongoing"})
    

    @classmethod
    def delete_one(cls, data):
        return cls.collection.delete_one(data)
    @classmethod
    def update_one(cls, data, new_data):
        return cls.collection.update_one(data, new_data)
        