from app import mongo
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId

class Organization:
    collection = mongo.db.organizations 

    @classmethod
    def find_one(cls, data):
        return cls.collection.find_one(data)
    
    @classmethod
    def exists_by_email(cls, email):
        return cls.collection.find_one({"org_email": email}) is not None
    

    @classmethod
    def get_by_email(cls, email):
        return cls.collection.find_one({"org_email": email})

    @classmethod
    def create(cls, data):
        cls.collection.insert_one(data)

    @classmethod
    def find_by_id(cls, organization_id): 
        return cls.collection.find_one({"_id": ObjectId(organization_id)})

    @classmethod
    def find_all(cls):
        return list(cls.collection.find())
    
    @classmethod
    def count_all(cls):
        return cls.collection.count_documents({})

    @classmethod
    def exists_by_organization_id(cls, organization_id):
        return cls.collection.find_one({"_id": organization_id}) is not None
    


    @classmethod
    def delete(cls, organization_id): 
        cls.collection.delete_one({"_id": ObjectId(organization_id)})



    @classmethod
    def update(cls, organization_id, data):
        cls.collection.update_one({"_id": ObjectId(organization_id)}, {"$set": data})
        