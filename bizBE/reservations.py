"""Customer accounts and atomic, per-listing free reservations."""
import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from functools import wraps

import jwt
from bson import ObjectId
from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db, listings

reservations_bp = Blueprint("reservations", __name__)
# Separate from the legacy admin API key. Persist via this environment variable for deployments.
CUSTOMER_SECRET = os.environ.get("CUSTOMER_JWT_SECRET") or os.urandom(32)


def customer_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        try:
            token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
            claims = jwt.decode(token, CUSTOMER_SECRET, algorithms=["HS256"])
            request.customer = claims["sub"]
        except (jwt.InvalidTokenError, KeyError):
            return jsonify(error="Please sign in again."), 401
        return view(*args, **kwargs)
    return wrapped


def deadline(value):
    if isinstance(value, datetime):
        date = value
    elif isinstance(value, str):
        try:
            date = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            date = parsedate_to_datetime(value)
    else:
        raise ValueError("Missing collection deadline")
    return date.replace(tzinfo=timezone.utc) if date.tzinfo is None else date


@reservations_bp.post("/api/v1.0/customers/register")
def register():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    name = str(data.get("name", "")).strip()
    password = data.get("password", "")
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email) or not name or not isinstance(password, str) or len(password) < 8:
        return jsonify(error="Enter a name, valid email and password of at least 8 characters."), 400
    from pymongo.errors import DuplicateKeyError
    try:
        db.customers.insert_one({"_id": email, "name": name[:100], "password": generate_password_hash(password, method="pbkdf2:sha256:1000000")})
    except DuplicateKeyError:
        return jsonify(error="An account already exists for this email."), 409
    return jsonify(message="Account created. You can now sign in."), 201


@reservations_bp.post("/api/v1.0/customers/login")
def sign_in():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    user = db.customers.find_one({"_id": email})
    password = data.get("password", "")
    if not user or not isinstance(password, str) or not check_password_hash(user["password"], password):
        return jsonify(error="Email or password is incorrect."), 401
    token = jwt.encode({"sub": email, "exp": datetime.now(timezone.utc) + timedelta(hours=8)}, CUSTOMER_SECRET, algorithm="HS256")
    return jsonify(token=token, name=user["name"])


@reservations_bp.post("/api/v1.0/reservations")
@customer_required
def reserve():
    data = request.get_json(silent=True) or {}
    listing_id = data.get("listing_id", "")
    quantity = data.get("quantity")
    key = data.get("request_id", "")
    if not ObjectId.is_valid(listing_id) or type(quantity) is not int or quantity < 1 or quantity > 10 or not isinstance(key, str) or not re.fullmatch(r"[a-f0-9]{32}", key):
        return jsonify(error="Choose 1–10 portions and a valid food listing."), 400
    oid = ObjectId(listing_id)
    item = listings.find_one({"_id": oid})
    if not item:
        return jsonify(error="Food listing no longer exists."), 404
    existing = item.get("reservations", {}).get(key)
    if existing:
        if existing["customer"] != request.customer:
            return jsonify(error="Reservation reference already used."), 409
        return jsonify(existing)
    try:
        available = int(re.match(r"^\d+", str(item.get("quantity_available", "")))[0])
        end = deadline(item.get("pickup_deadline"))
    except (TypeError, ValueError, IndexError):
        return jsonify(error="Provider must update the quantity and collection deadline."), 409
    if item.get("listing_status", "").lower() != "available" or end <= datetime.now(timezone.utc) or available < quantity:
        return jsonify(error="This food is no longer available for the selected quantity."), 409
    order = {"id": key, "customer": request.customer, "food_name": item["food_name"], "listing_id": listing_id,
             "quantity": quantity, "status": "confirmed", "collection_code": uuid.uuid4().hex[:10].upper(),
             "pickup_location": item.get("pickup_location"), "pickup_deadline": end.isoformat(),
             "created_at": datetime.now(timezone.utc).isoformat()}
    # Stock and reservation live in one document and change atomically.
    result = listings.update_one(
        {"_id": oid, "quantity_available": item["quantity_available"],
         "listing_status": item["listing_status"], "pickup_deadline": item["pickup_deadline"],
         "reservations." + key: {"$exists": False}},
        {"$set": {"quantity_available": available - quantity, "reservations." + key: order}})
    if not result.modified_count:
        latest = listings.find_one({"_id": oid})
        existing = (latest or {}).get("reservations", {}).get(key)
        if existing and existing["customer"] == request.customer:
            return jsonify(existing)
        return jsonify(error="Stock changed. Refresh the listing and try again."), 409
    return jsonify(order), 201


@reservations_bp.get("/api/v1.0/reservations")
@customer_required
def orders():
    rows = []
    for item in listings.find({"reservations": {"$exists": True}}, {"reservations": 1}):
        rows.extend(order for order in item["reservations"].values() if order["customer"] == request.customer)
    return jsonify(sorted(rows, key=lambda row: row["created_at"], reverse=True))


@reservations_bp.post("/api/v1.0/reservations/<order_id>/cancel")
@customer_required
def cancel(order_id):
    if not re.fullmatch(r"[a-f0-9]{32}", order_id):
        return jsonify(error="Invalid reservation."), 400
    path = "reservations." + order_id
    item = listings.find_one({path + ".customer": request.customer})
    if not item:
        return jsonify(error="Reservation not found."), 404
    order = item["reservations"][order_id]
    if order["status"] == "cancelled":
        return jsonify(message="Reservation cancelled.")
    if order["status"] != "confirmed":
        return jsonify(error="This reservation cannot be cancelled."), 409
    result = listings.update_one(
        {"_id": item["_id"], path + ".customer": request.customer, path + ".status": "confirmed"},
        {"$set": {path + ".status": "cancelled"}, "$inc": {"quantity_available": order["quantity"]}})
    if not result.modified_count:
        return jsonify(error="Reservation changed. Refresh your orders."), 409
    return jsonify(message="Reservation cancelled. Portions returned to stock.")
