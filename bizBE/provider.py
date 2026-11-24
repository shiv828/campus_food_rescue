from datetime import datetime, timezone
from functools import wraps

import click
from bson import ObjectId
from flask import Blueprint, jsonify, request

from extensions import db, listings
from reservations import customer_required

provider_bp = Blueprint("provider", __name__)


@provider_bp.cli.command("grant")
@click.argument("email")
@click.argument("provider_id")
def grant(email, provider_id):
    """Link an existing campus account to an approved provider."""
    provider_id = provider_id.strip()
    if not provider_id:
        raise click.ClickException("Enter a provider ID.")
    result = db.customers.update_one({"_id": email.strip().lower()},
                                     {"$set": {"provider_id": provider_id}})
    if not result.matched_count:
        raise click.ClickException("Register this account first.")


def provider_required(view):
    @wraps(view)
    @customer_required
    def wrapped(*args, **kwargs):
        account = db.customers.find_one({"_id": request.customer}, {"provider_id": 1})
        if not account or not account.get("provider_id"):
            return jsonify(error="This account has no approved provider access."), 403
        request.provider_id = account["provider_id"]
        return view(*args, **kwargs)
    return wrapped


@provider_bp.get("/api/v1.0/provider/listings")
@provider_required
def own_listings():
    rows = list(listings.find({"provider_id": request.provider_id},
                              {"food_name": 1, "listing_status": 1, "pickup_deadline": 1,
                               "quantity_available": 1}).sort("_id", -1))
    for row in rows:
        row["_id"] = str(row["_id"])
    return jsonify(rows)


@provider_bp.post("/api/v1.0/provider/listings")
@provider_required
def publish():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error="Enter the listing details."), 400
    fields = ("food_name", "description", "campus", "collection_point")
    if any(not isinstance(data.get(key), str) or not data[key].strip() for key in fields):
        return jsonify(error="Enter the food, description, campus and collection point."), 400
    quantity = data.get("quantity_available")
    if type(quantity) is not int or not 1 <= quantity <= 10000:
        return jsonify(error="Enter 1 to 10,000 portions."), 400
    try:
        start, end = [datetime.fromisoformat(data[key].replace("Z", "+00:00"))
                      for key in ("available_from", "pickup_deadline")]
        if start.tzinfo is None or end.tzinfo is None or end <= start or end <= datetime.now(timezone.utc):
            raise ValueError()
    except (KeyError, ValueError, TypeError, AttributeError):
        return jsonify(error="Choose a future deadline after the collection start."), 400
    tags = data.get("dietary_tags", "")
    if not isinstance(tags, str):
        return jsonify(error="Enter dietary tags as text."), 400
    oid = ObjectId()
    now = datetime.now(timezone.utc).isoformat()
    row = {"_id": oid, "listing_id": str(oid), "provider_id": request.provider_id,
           "food_name": data["food_name"].strip(), "description": data["description"].strip(),
           "pickup_location": {key: data[key].strip() for key in ("campus", "collection_point")},
           "quantity_available": quantity, "available_from": start.isoformat(),
           "pickup_deadline": end.isoformat(), "listing_status": "available",
           "dietary_tags": [tag.strip() for tag in tags.split(",") if tag.strip()],
           "created_at": now, "updated_at": now}
    listings.insert_one(row)
    return jsonify(_id=str(oid)), 201
