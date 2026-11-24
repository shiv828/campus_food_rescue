#pip install pymongo
from pymongo import MongoClient


#Mongo connection
client = MongoClient("mongodb://localhost:27017")
db = client.listing
listings = db.food
