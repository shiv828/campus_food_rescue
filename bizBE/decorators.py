from functools import wraps

import jwt
from flask import current_app, jsonify, make_response, request


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
                    current_app.config['SECRET_KEY'],
                    algorithms="HS256")
        except:
            return make_response(jsonify({"message":"Token is invalid"}), 401)

        request.user = data
        return func(*args, **kwargs)

    return jwt_required_wrapper
