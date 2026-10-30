from flask import Flask, make_response, jsonify, request
from functools import wraps
#pip install pymongo
from pymongo import MongoClient
from bson import ObjectId

import jwt
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = ('mysecret')

#Mongo connection
client = MongoClient("mongodb://localhost:27017")
db = client.listing
listings = db.food


#JWT decorator
def jwt_required(func):
    @wraps(func)
    def jwt_required_wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        token = None
        
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip()

        if not token:
            return make_response(jsonify({"message": "Token is missing"}), 401)

        try:
            data = jwt.decode(token,
                    app.config['SECRET_KEY'],
                    algorithms="HS256")
        except:
            return make_response(jsonify({"message":"Token is invalid"}), 401)

        request.user = data
        return func(*args, **kwargs)

    return jwt_required_wrapper

@app.route("/api/v1.0/login", methods=['GET'])
def login():
    auth = request.authorization

    if (
        auth
    and auth.username == "admin"
    ):
        token = jwt.encode({
            'user' : auth.username,
            'exp' : datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=30)
        },
        app.config['SECRET_KEY'],
        algorithm="HS256")

        return make_response(jsonify({"token": token}), 200)
    
    return make_response("Could not verify", 401, \
        {'WWW-Authenticate': 'Basic realm = "Login required"'}) 


#====listings routes========================
@app.route("/", methods=["GET"])
def index():
    return make_response("<h1>Welcome to campus food rescue</h1>", 200)

#===============================Show all listings========================================
@app.route("/api/v1.0/listings", methods=["GET"])
def show_all_listings():
 
    page_num, page_size = 1, 3
    if request.args.get('pn'):
        page_num = int(request.args.get('pn'))
    if request.args.get('ps'):
        page_size = int(request.args.get('ps'))
    page_start = (page_size * (page_num - 1))

    data_to_return = []

    for business in listings.find().skip(page_start).limit(page_size):
        business['_id'] = str(business['_id'])

        #for review in business['reviews']:
            #review['_id'] = str(review['_id'])

        data_to_return.append(business)

    return make_response(jsonify(data_to_return), 200)


# ==============================Show one listings========================================
@app.route("/api/v1.0/listings/<string:listing_id>", methods=["GET"])
def show_one_listings(listing_id):
    business = listings.find_one({'_id':ObjectId(listing_id)})

    if business is not None:
        business['_id'] = str(business['_id'])

        #for review in business['reviews']:
            #review['_id'] = str(review['_id'])
        
        return make_response(jsonify(business), 200)

    else:
        return make_response(jsonify({"error":"Invalid business ID"}), 404)

#===============================Show listings by food name========================================
@app.route("/api/v1.0/listings/food_name/<string:food_name>", methods=["GET"])
def show_listings_by_food_name(food_name):
    data_to_return = []

    for business in listings.find({"food_name": food_name}):
        business['_id'] = str(business['_id'])

        #for review in business['reviews']:
            #review['_id'] = str(review['_id'])

        data_to_return.append(business)

    return make_response(jsonify(data_to_return), 200)

#===============================Show listings by provider id========================================
@app.route("/api/v1.0/listings/provider_id/<string:provider_id>", methods=["GET"])
def show_listings_by_provider_id(provider_id):
    data_to_return = []

    for business in listings.find({"provider_id": provider_id}):
        business['_id'] = str(business['_id'])

        #for review in business['reviews']:
            #review['_id'] = str(review['_id'])

        data_to_return.append(business)

    return make_response(jsonify(data_to_return), 200)

#===============================Show listings by listing status========================================
@app.route("/api/v1.0/listings/listing_status/<string:listing_status>", methods=["GET"])
def show_listings_by_listing_status(listing_status):
    data_to_return = []

    for business in listings.find({"listing_status": listing_status}):
        business['_id'] = str(business['_id'])

        #for review in business['reviews']:
            #review['_id'] = str(review['_id'])

        data_to_return.append(business)

    return make_response(jsonify(data_to_return), 200)  


#==============================Add listings========================================
@app.route("/api/v1.0/listings", methods=["POST"])
#@jwt_required
def add_listings():
    if "listing_id" in request.form and \
        "food_name" in request.form and "description" in request.form:
        
        new_listings = {
            "listing_id": request.form["listing_id"],
            "provider_id": request.form["provider_id"],
            "food_name": request.form["food_name"],
            "description": request.form["description"],
            "quantity_available": request.form["quantity_available"],
            "dietary_tags": request.form["dietary_tags"],
            "pickup_location": request.form["pickup_location"],
            "available_from": request.form["available_from"],
            "pickup_deadline": request.form["pickup_deadline"],
            "listing_status": request.form["listing_status"],
            "created_at": request.form["created_at"],
            "updated_at": request.form["updated_at"]
        }

        new_listings_id = listings.insert_one(new_listings)

        new_listings_link = "http://127.0.0.1:5001/api/v1.0/listings/"\
            + str(new_listings_id.inserted_id)
        
        return make_response(jsonify({"url": new_listings_link}), 201)

    else:
        return make_response(jsonify({"url":"Missing form data"}), 404)
    

#===============================Edit listings========================================
@app.route("/api/v1.0/listings/<string:listing_id>", methods=["PUT"])
@jwt_required
def edit_listings(listing_id):
    if "listing_id" in request.form and "provider_id" in request.form and "food_name" in request.form:
        results = listings.update_one(
            {"_id":ObjectId(listing_id)}, {
                "$set": {
                    "listing_id": request.form["listing_id"],
                    "provider_id": request.form["provider_id"],
                    "food_name": request.form["food_name"],
                    "description": request.form["description"],
                    "quantity_available": request.form["quantity_available"],
                    "dietary_tags": request.form["dietary_tags"],
                    "pickup_location": request.form["pickup_location"],
                    "available_from": request.form["available_from"],
                    "pickup_deadline": request.form["pickup_deadline"],
                    "listing_status": request.form["listing_status"],
                    "created_at": request.form["created_at"],
                    "updated_at": request.form["updated_at"]
                }
            }
        )
        if results.matched_count == 1:
            edited_link = "http://127.0.0.1:5001/api/v1.0/listings/" \
            + listing_id 
            return make_response(jsonify({"url": edited_link}), 200)
        else:
            return make_response(jsonify({"error": "Invalid business ID"}), 404)
    else:
        return make_response(jsonify({"error":"Missing form data"}), 404)


#===============================Delete listings========================================
@app.route("/api/v1.0/listings/<string:listing_id>", methods=['DELETE'])
@jwt_required
def delete_listings(listing_id):
    result = listings.delete_one({"_id":ObjectId(listing_id)})

    if result.deleted_count == 1:
        return make_response(jsonify({"message":"Listing deleted!!!"}), 200)
    else:
        return make_response(jsonify({"error":"Invalid business ID"}), 404)



if __name__ == "__main__":
    app.run(debug=True, port=5001)