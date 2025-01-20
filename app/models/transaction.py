from app import mongo
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
from pymongo import ReturnDocument
class Transaction:
    collection = mongo.db.transactions 


    @classmethod
    def create(cls, transaction_data):
        return cls.collection.insert_one(transaction_data)

    @classmethod   
    def get_total_hours_worked(cls, volunteer_id):
        transactions = list(cls.collection.find({'user_id': ObjectId(volunteer_id)}))
        total_hours = 0
        for transaction in transactions:
            total_hours += transaction['hours_worked']
        return total_hours

    @classmethod
    def insert_one(cls, log):
        return cls.collection.insert_one(log)
    
    @classmethod
    def find_one(cls, query):
        print("==============================")
        print(f"Query: {query}")
        result = cls.collection.find_one(query)
        print(f"Result: {result}")
        return result
        
    @classmethod
    def find_all_by_user_id(cls, user_id):
        return list(cls.collection.find({"user_id": ObjectId(user_id)}))



    @classmethod
    def     find_by_user_id(cls, user_id):
        return cls.collection.find_one({"user_id": ObjectId(user_id)})

    @classmethod
    def find(cls, query):
        return cls.collection.find(query)
    
    @classmethod
    def update_one(cls, query, new_values):
        return cls.collection.update_one(query, new_values)
    

    @classmethod
    def find_one_and_update(cls, query, new_values, sort=None, return_document=ReturnDocument.BEFORE):
        options = {}
        if sort:
            options['sort'] = sort
        options['return_document'] = return_document
        return cls.collection.find_one_and_update(query, new_values, **options)
