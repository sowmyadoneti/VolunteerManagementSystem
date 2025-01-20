from app import mongo
from werkzeug.security import generate_password_hash, check_password_hash

class Certification:
    collection = mongo.db.certifications

    
    @classmethod
    def find_one(cls, query):
        print(query)
        return cls.collection.find_one(query)

    @classmethod
    def find(cls, query):
        return cls.collection.find(query)
    
    @classmethod
    def count_all(cls):
        return cls.collection.count_documents({})

    @classmethod
    def insert(cls, data):
        return cls.collection.insert_one(data)

    @classmethod
    def update(cls, query, data):
        return cls.collection.update_one(query, data)

    @classmethod
    def create(cls, data):
        return cls.collection.insert_one(data)


