import streamlit as st
import os
import json
from pymongo import MongoClient
# Corrected import: InvalidId is now in bson.errors
from bson.objectid import ObjectId
from pymongo.errors import ConnectionFailure
from bson.errors import InvalidId # Corrected import path for InvalidId
from dotenv import load_dotenv # Import load_dotenv

# Load environment variables from .env file at the start
load_dotenv()

# --- MongoDB Connection ---
# This function will establish and return the MongoDB database client and db object.
# It uses Streamlit's st.session_state to cache the connection and avoid reconnecting on every rerun.
def _get_mongo_db():
    if 'mongo_client' not in st.session_state or st.session_state.mongo_client is None:
        try:
            # Retrieve MongoDB URI from environment variables
            mongo_uri = "mongodb+srv://ram:9345269165@inventory.1qnvb22.mongodb.net/?retryWrites=true&w=majority&appName=inventory"
            if not mongo_uri:
                st.error("MongoDB URI not found in .env file. Please add MONGO_URI to your .env.")
                st.stop() # Stop app execution if essential config is missing

            client = MongoClient(mongo_uri)
            # The database name is typically part of the URI, or you can specify it here.
            db = client.get_database("inventory") # Gets database specified in URI, or default if none.
            
            # Ping the database to check connection
            client.admin.command('ping')
            st.session_state.mongo_client = client
            st.session_state.mongo_db = db
            print("MongoDB connection successful!")
        except ConnectionFailure as e:
            st.error(f"Could not connect to MongoDB: {e}. Please check your MONGO_URI and network connection.")
            st.stop() # Stop app execution if DB connection fails
        except Exception as e:
            st.error(f"An unexpected error occurred during MongoDB connection: {e}")
            st.stop()
    return st.session_state.mongo_db

def _to_object_id(id_str):
    """Converts a string ID to ObjectId, returns None if invalid."""
    try:
        return ObjectId(id_str)
    except InvalidId:
        return None

# --- User Operations ---
def load_users():
    """Loads all users from the MongoDB 'users' collection."""
    db = _get_mongo_db()
    users_collection = db.users
    users = []
    for user_doc in users_collection.find():
        user_doc['id'] = str(user_doc['_id']) # Convert ObjectId to string for Streamlit
        users.append(user_doc)
    return users

def add_user(user_data):
    """Adds a new user to the MongoDB 'users' collection."""
    db = _get_mongo_db()
    users_collection = db.users
    result = users_collection.insert_one(user_data)
    return str(result.inserted_id) # Return the string representation of the new user's ID

def find_user_by_username(username):
    """Finds a user by username in the MongoDB 'users' collection."""
    db = _get_mongo_db()
    users_collection = db.users
    user_doc = users_collection.find_one({'username': username})
    if user_doc:
        user_doc['id'] = str(user_doc['_id']) # Convert ObjectId to string
    return user_doc

def find_user_by_id(user_id):
    """Finds a user by their string ID in the MongoDB 'users' collection."""
    db = _get_mongo_db()
    users_collection = db.users
    obj_id = _to_object_id(user_id)
    if not obj_id:
        return None
    user_doc = users_collection.find_one({'_id': obj_id})
    if user_doc:
        user_doc['id'] = str(user_doc['_id'])
    return user_doc

def update_user(user_id, updates):
    """Updates an existing user in the MongoDB 'users' collection."""
    db = _get_mongo_db()
    users_collection = db.users
    obj_id = _to_object_id(user_id)
    if not obj_id:
        return False
    
    # Ensure '_id' is not in updates, as it's immutable
    if '_id' in updates:
        del updates['_id']
    if 'id' in updates: # Also remove the string 'id' if present
        del updates['id']

    result = users_collection.update_one({'_id': obj_id}, {'$set': updates})
    return result.modified_count > 0

def delete_user(user_id):
    """Deletes a user from the MongoDB 'users' collection."""
    db = _get_mongo_db()
    users_collection = db.users
    obj_id = _to_object_id(user_id)
    if not obj_id:
        return False
    result = users_collection.delete_one({'_id': obj_id})
    return result.deleted_count > 0

# --- Inventory Operations ---
def get_all_inventory_items():
    """Retrieves all inventory items from the MongoDB 'inventory' collection."""
    db = _get_mongo_db()
    inventory_collection = db.inventory
    items = []
    for item_doc in inventory_collection.find():
        item_doc['id'] = str(item_doc['_id']) # Convert ObjectId to string
        items.append(item_doc)
    return items

def add_inventory_item(item_data):
    """Adds a new inventory item to the MongoDB 'inventory' collection."""
    db = _get_mongo_db()
    inventory_collection = db.inventory
    result = inventory_collection.insert_one(item_data)
    return str(result.inserted_id) # Return the string representation of the new item's ID

def update_inventory_item(item_id, updates):
    """Updates an existing inventory item in the MongoDB 'inventory' collection."""
    db = _get_mongo_db()
    inventory_collection = db.inventory
    obj_id = _to_object_id(item_id)
    if not obj_id:
        return False
    
    if '_id' in updates:
        del updates['_id']
    if 'id' in updates:
        del updates['id']

    result = inventory_collection.update_one({'_id': obj_id}, {'$set': updates})
    return result.modified_count > 0

def delete_inventory_item(item_id):
    """Deletes an inventory item from the MongoDB 'inventory' collection."""
    db = _get_mongo_db()
    inventory_collection = db.inventory
    obj_id = _to_object_id(item_id)
    if not obj_id:
        return False
    result = inventory_collection.delete_one({'_id': obj_id})
    return result.deleted_count > 0

def find_inventory_item_by_id(item_id):
    """Finds an inventory item by its string ID in the MongoDB 'inventory' collection."""
    db = _get_mongo_db()
    inventory_collection = db.inventory
    obj_id = _to_object_id(item_id)
    if not obj_id:
        return None
    item_doc = inventory_collection.find_one({'_id': obj_id})
    if item_doc:
        item_doc['id'] = str(item_doc['_id'])
    return item_doc

# --- Supplier Operations ---
def get_all_suppliers():
    """Retrieves all suppliers from the MongoDB 'suppliers' collection."""
    db = _get_mongo_db()
    suppliers_collection = db.suppliers
    suppliers = []
    for supplier_doc in suppliers_collection.find():
        supplier_doc['id'] = str(supplier_doc['_id']) # Convert ObjectId to string
        suppliers.append(supplier_doc)
    return suppliers

def add_supplier(supplier_data):
    """Adds a new supplier to the MongoDB 'suppliers' collection."""
    db = _get_mongo_db()
    suppliers_collection = db.suppliers
    result = suppliers_collection.insert_one(supplier_data)
    return str(result.inserted_id) # Return the string representation of the new supplier's ID

def update_supplier(supplier_id, updates):
    """Updates an existing supplier in the MongoDB 'suppliers' collection."""
    db = _get_mongo_db()
    suppliers_collection = db.suppliers
    obj_id = _to_object_id(supplier_id)
    if not obj_id:
        return False
    
    if '_id' in updates:
        del updates['_id']
    if 'id' in updates:
        del updates['id']

    result = suppliers_collection.update_one({'_id': obj_id}, {'$set': updates})
    return result.modified_count > 0

def delete_supplier(supplier_id):
    """Deletes a supplier from the MongoDB 'suppliers' collection."""
    db = _get_mongo_db()
    suppliers_collection = db.suppliers
    obj_id = _to_object_id(supplier_id)
    if not obj_id:
        return False
    result = suppliers_collection.delete_one({'_id': obj_id})
    return result.deleted_count > 0

def find_supplier_by_id(supplier_id):
    """Finds a supplier by their string ID in the MongoDB 'suppliers' collection."""
    db = _get_mongo_db()
    suppliers_collection = db.suppliers
    obj_id = _to_object_id(supplier_id)
    if not obj_id:
        return None
    supplier_doc = suppliers_collection.find_one({'_id': obj_id})
    if supplier_doc:
        supplier_doc['id'] = str(supplier_doc['_id'])
    return supplier_doc

def find_suppliers_by_category(category_name):
    """
    Finds suppliers who supply a given category from the MongoDB 'suppliers' collection.
    Returns a list of supplier documents.
    """
    db = _get_mongo_db()
    suppliers_collection = db.suppliers
    # Find suppliers where the 'categories' array contains the given category_name
    suppliers = []
    for supplier_doc in suppliers_collection.find({'categories': category_name}):
        supplier_doc['id'] = str(supplier_doc['_id'])
        suppliers.append(supplier_doc)
    return suppliers
