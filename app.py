from flask import Flask, make_response, jsonify, request
#pip install pymongo
from pymongo import MongoClient
from bson import ObjectId
from authentication import token_required

import jwt
import datetime
import hmac
import os

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ["FLASK_SECRET_KEY"]
LOGIN_USERNAME = os.environ["CAMPUS_RESCUE_USERNAME"]
LOGIN_PASSWORD = os.environ["CAMPUS_RESCUE_PASSWORD"]

#Mongo connection
client = MongoClient("mongodb://localhost:27017")
db = client.listing
listings = db.food

@app.route("/api/v1.0/login", methods=['GET'])
def login():
    auth = request.authorization

    if (
        auth
        and auth.username == LOGIN_USERNAME
        and auth.password is not None
        and hmac.compare_digest(auth.password, LOGIN_PASSWORD)
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


@app.route("/", methods=["GET"])
def index():
    return make_response("<h1>Welcome to campus food rescue</h1>", 200)


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


# fetch by ID
@app.route("/api/v1.0/listings/<string:biz_id>", methods=["GET"])
def show_one_listings(biz_id):
    business = listings.find_one({'_id':ObjectId(biz_id)})

    if business is not None:
        business['_id'] = str(business['_id'])

        #for review in business['reviews']:
            #review['_id'] = str(review['_id'])
        
        return make_response(jsonify(business), 200)

    else:
        return make_response(jsonify({"error":"Invalid business ID"}), 404)


@app.route("/api/v1.0/listings", methods=["POST"])
@token_required
def add_listings():
    if "name" in request.form and \
        "town" in request.form and "rating" in request.form:
        
        new_business = {
            "name": request.form["name"],
            "town": request.form["town"],
            "rating": request.form["rating"],
            "review": []
        }

        new_business_id = listings.insert_one(new_business)

        new_business_link = "http://127.0.0.1:5001/api/v1.0/listings/"\
            + str(new_business_id.inserted_id)
        
        return make_response(jsonify({"url": new_business_link}), 201)

    else:
        return make_response(jsonify({"url":"Missing form data"}), 404)


@app.route("/api/v1.0/listings/<string:biz_id>", methods=["PUT"])
@token_required
def edit_listings(biz_id):
    if "name" in request.form and "town" in request.form and "rating" in request.form:
        results = listings.update_one(
            {"_id":ObjectId(biz_id)}, {
                "$set": {
                    "name": request.form["name"],
                    "town": request.form["town"],
                    "rating": request.form["rating"],
                }
            }
        )
        if results.matched_count == 1:
            edited_link = "http://127.0.0.1:5001/api/v1.0/listings/" \
            + biz_id 
            return make_response(jsonify({"url": edited_link}), 200)
        else:
            return make_response(jsonify({"error": "Invalid business ID"}), 404)
    else:
        return make_response(jsonify({"error":"Missing form data"}), 404)


@app.route("/api/v1.0/listings/<string:biz_id>", methods=['DELETE'])
@token_required
def delete_listings(biz_id):
    result = listings.delete_one({"_id":ObjectId(biz_id)})

    if result.deleted_count == 1:
        return make_response(jsonify({"message":"Listing deleted!!!"}), 200)
    else:
        return make_response(jsonify({"error":"Invalid business ID"}), 404)


# ===================== REVIEWS ==============================

@app.route("/api/v1.0/listings/<int:biz_id>/reviews", methods=['GET'])
def get_all_reviews(biz_id):
    for business in listings:
        if business['id'] == biz_id:
            break

    return make_response(jsonify(business["reviews"]), 200)

#=======================================Reviews (Post method) =================================

@app.route("/api/v1.0/listings/<string:biz_id>/reviews", methods=['POST'])
@token_required
def add_new_review(biz_id): 
    new_review = {
        "_id": ObjectId(),
        "username": request.form['username'],
        "comments": request.form['comments'],
        "stars": request.form['stars']
        }
        
    listings.update_one({ "_id" : ObjectId(biz_id) },\
        {"$push": {"review":new_review}})

    new_review_link = "http://127.0.0.1:5001/api/v1.0/listings/"+ biz_id +"/reviews"\
        + str(new_review["_id"])
    
    return make_response(jsonify({"url": new_review_link}), 201)

@app.route("/api/v1.0/listings/<int:biz_id>/reviews/<int:rev_id>", methods=['GET'])
def fetch_one_review(biz_id, rev_id):
    for business in listings:
        if business["id"] == biz_id:
            for review in business["reviews"]:
                if review["id"] == rev_id:
                    break
            break
    
    return make_response(jsonify(review), 200)

@app.route("/api/v1.0/listings/<int:biz_id>/reviews/<int:rev_id>", methods=['PUT'])
@token_required
def update_review(biz_id, rev_id):
    for business in listings:
        if business["id"] == biz_id:
            for review in business["reviews"]:
                if review["id"] == rev_id:
                    review["username"] = request.form["username"]
                    review["comments"] = request.form["comments"]
                    review["stars"] = request.form["stars"]
                    break
            break
    
    return make_response(jsonify(review), 200)


@app.route("/api/v1.0/listings/<int:biz_id>/reviews/<int:rev_id>", methods=['DELETE'])
@token_required
def delete_review(biz_id, rev_id):
    for business in listings:
        if business["id"] == biz_id:
            for review in business["reviews"]:
                if review["id"] == rev_id:
                    business["review"].remove(review)
                    break
            break
    
    return make_response(jsonify({"Message":"Review Deleted successfully!!!"}), 200)

if __name__ == "__main__":
    app.run(debug=True, port=5001)
