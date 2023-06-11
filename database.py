from flask_pymongo import PyMongo
from flask import current_app as app
from flask import g
from bson.objectid import ObjectId
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Manually load .env file
load_dotenv()

class Database:
    def __init__(self):
        self.client = MongoClient(os.getenv("MONGODB_URI"))
        self.db = self.client.ai_app_db

    def insert_one(self, collection_name, document):
        return self.db[collection_name].insert_one(document)

    def find(self, collection_name, query):
        return self.db[collection_name].find(query)

    def find_one(self, collection_name, query):
        return self.db[collection_name].find_one(query)

    def find_one_by_id(self, collection_name, item_id):
        return self.db[collection_name].find_one({'_id': ObjectId(item_id)})

    def update_one(self, collection_name, query, new_values):
        return self.db[collection_name].update_one(query, new_values)
    
    def insert_many(self, collection_name, data):
        collection = self.db[collection_name]
        collection.insert_many(data)


def get_db():
    if 'db' not in g:
        g.db = Database().db
    return g.db

db = Database()
