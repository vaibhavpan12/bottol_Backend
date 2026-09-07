import os

from pymongo import MongoClient
from dotenv import load_dotenv


load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
print("MONGO_URI:", MONGO_URI)

client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=10000
)

db = client["pivora"]

products_collection = db["products"]
orders_collection = db["orders"]
users_collection = db["users"]
carts_collection = db["carts"]
admin_collection = db["admins"]
carts_collection.create_index(
    "user_id",
    unique=True
)