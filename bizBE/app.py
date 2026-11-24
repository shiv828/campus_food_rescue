import os

from flask import Flask, make_response

from auth.auth import auth_bp
from businesses.businesses import businesses_bp

from provider import provider_bp
from reservations import reservations_bp
from flask_cors import CORS

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY') or os.urandom(32)
CORS(app)

# register blueprints
app.register_blueprint(provider_bp)
app.register_blueprint(reservations_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(businesses_bp)


@app.route("/", methods=["GET"])
def index():
    return make_response("<h1>Welcome to campus food rescue</h1>", 200)


if __name__ == "__main__":
    app.run(debug=True, port=5001)
