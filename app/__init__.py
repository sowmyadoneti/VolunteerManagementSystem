from flask import Flask
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager
import os
import certifi

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/volunter"

app.secret_key = 'volunteer'
ca = certifi.where()

mongo = PyMongo(app)

