import datetime

import jwt
from flask import Blueprint, current_app, jsonify, make_response, request


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/api/v1.0/login", methods=['GET'])
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
        current_app.config['SECRET_KEY'],
        algorithm="HS256")

        return make_response(jsonify({"token": token}), 200)
    
    return make_response("Could not verify", 401, \
        {'WWW-Authenticate': 'Basic realm = "Login required"'}) 
