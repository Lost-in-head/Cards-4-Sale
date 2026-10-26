"""
Flask web application for the Cards-4-Sale listing pipeline.
"""

import importlib
import logging
import os
import tempfile

from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

from src.api.ebay_client import (
    build_listing_payload,
    publish_listing,
    search_ebay,
    suggest_price,
)
from src.api.openai_client import describe_image
from src.config import (
    ALLOWED_EXTENSIONS,
    HIGH_VALUE_THRESHOLD,
    MAX_CONTENT_LENGTH,
    UPLOAD_FOLDER,
    validate_config,
)
from src.database import (
    delete_listing,
    get_all_listings,
    get_listing,
    get_stats,
    init_db,
    record_publish_result,
    save_listing,
    update_listing_status,
)
from src.logging_config import configure_logging
from src.settings_store import apply_to_env, load_all, save_all
from src.validators import ImageValidator

logger = logging.getLogger(__name__)


def normalize_analysis_cards(image_analysis):
    """Normalize analysis to a list of item analyses."""
    if isinstance(image_analysis, dict) and isinstance(image_analysis.get("cards"), list):
        cards = [card for card in image_analysis["cards"] if isinstance(card, dict)]
        return cards or [image_analysis]
    return [image_analysis]


def build_search_query(analysis):
    """Construct an eBay query from the analyzed item."""
    base = [analysis.get("brand", ""), analysis.get("model", "")]
    category = (analysis.get("category") or "").lower()
    if "card" in category:
        for key in ("player_name", "set_name", "year", "card_number", "grade"):
            value = analysis.get(key)
            if value:
                base.append(str(value))
    query = " ".join(part for part in base if part).strip()
    return query or "collectible trading card"


def _build_listing_title(analysis):
    """Create an optimized eBay listing title."""
    brand = analysis.get("brand", "Item")
    model = analysis.get("model", "")
    category = (analysis.get("category") or "").lower()
    if "card" in category:
        player_name = analysis.get("player_name", "")
        if player_name and player_name.lower() not in model.lower():
            return f"{player_name} {brand} {model}".strip()
    return f"{brand} {model}".strip()


def format_description(analysis):
    """Format analysis into an eBay-ready description."""
    parts = []
    if analysis.get("category"):
        parts.append(f"**Category**: {analysis['category']}")
    if analysis.get("condition"):
        parts.append(f"**Condition**: {analysis['condition']}")

    for key, label in (
        ("player_name", "Player"),
        ("set_name", "Set"),
        ("year", "Year"),
        ("card_number", "Card Number"),
        ("grade", "Grade"),
    ):
        if analysis.get(key):
            parts.append(f"**{label}**: {analysis[key]}")

    if analysis.get("grading_notes"):
        notes = analysis["grading_notes"]
        if isinstance(notes, list):
            notes_text = "\n".join(f"• {n}" for n in notes)
        else:
            notes_text = str(notes)
        parts.append(f"**Grading Notes**:\n{notes_text}")

    if analysis.get("features"):
        features = analysis["features"]
        if isinstance(features, list):
            features_text = "\n".join(f"• {f}" for f in features)
        else:
            features_text = str(features)
        parts.append(f"**Features**:\n{features_text}")

    if analysis.get("brand"):
        parts.append(f"**Brand**: {analysis['brand']}")
    if analysis.get("model"):
        parts.append(f"**Model**: {analysis['model']}")

    return "\n\n".join(parts)


def generate_listing_from_analysis(analysis, filename):
    """Generate and persist one listing from one analyzed item."""
    search_query = build_search_query(analysis)
    listings = search_ebay(search_query, limit=8)
    suggested_price = suggest_price(listings)
    price_warning = suggested_price is None
    if suggested_price is None:
        suggested_price = 5.00

    title = _build_listing_title(analysis)
    payload = build_listing_payload(
        title=title,
        description=format_description(analysis),
        price=suggested_price,
        condition=analysis.get("condition", "Unknown"),
    )

    listing_id = save_listing(
        title=title,
        filename=filename,
        analysis=analysis,
        comparable_listings=listings,
        suggested_price=suggested_price,
        payload=payload,
    )

    if listing_id is None:
        raise RuntimeError("Failed to save listing to database")

    return {
        "listing_id": listing_id,
        "analysis": analysis,
        "comparable_listings": listings,
        "suggested_price": suggested_price,
        "price_warning": price_warning,
        "is_high_value": suggested_price >= HIGH_VALUE_THRESHOLD,
        "payload": payload,
    }


def process_listing(image_path, filename="unknown.jpg"):
    """Process one image through the full listing pipeline."""
    try:
        logger.info("Analyzing uploaded image...")
        image_analysis = describe_image(image_path)
        analyses = normalize_analysis_cards(image_analysis)

        if not analyses:
            return {
                "success": False,
                "listings": [],
                "count": 0,
                "high_value_threshold": HIGH_VALUE_THRESHOLD,
                "error": "No items detected in image",
                "message": "❌ Could not identify any items in the photo",
            }

        logger.info("Searching eBay for similar items...")
        results = [generate_listing_from_analysis(analysis, filename) for analysis in analyses]
        return {
            "success": True,
            "listings": results,
            "count": len(results),
            "high_value_threshold": HIGH_VALUE_THRESHOLD,
            "message": f"✅ Generated {len(results)} listing draft{'s' if len(results) != 1 else ''} from one photo.",
        }
    except Exception:
        logger.exception("Error processing listing for %s", filename)
        return {
            "success": False,
            "listings": [],
            "count": 0,
            "high_value_threshold": HIGH_VALUE_THRESHOLD,
            "error": "Failed to generate listing",
            "message": "❌ Failed to generate listing",
        }


def allowed_file(filename):
    """Check if the uploaded filename is allowed."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def create_app():
    """Create and configure the Flask app."""
    configure_logging()
    apply_to_env()
    validate_config()

    app = Flask(__name__, template_folder="templates", static_folder="static")
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
    app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
    app.config["JSON_SORT_KEYS"] = False

    init_db()
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    @app.route("/")
    def index():
        stats = get_stats()
        return render_template("index.html", stats=stats)

    @app.route("/api/listings", methods=["GET"])
    def get_listings():
        listings = get_all_listings()
        return jsonify(listings), 200

    @app.route("/api/listings/<int:listing_id>", methods=["GET"])
    def get_listing_detail(listing_id):
        listing = get_listing(listing_id)
        if not listing:
            return jsonify({"error": "Listing not found"}), 404
        return jsonify(listing), 200

    @app.route("/api/listings/<int:listing_id>/status", methods=["PATCH"])
    def update_status(listing_id):
        data = request.get_json(silent=True) or {}
        status = data.get("status", "draft")
        if status not in ["draft", "published", "archived"]:
            return jsonify({"error": "Invalid status"}), 400
        success = update_listing_status(listing_id, status)
        if success:
            return jsonify({"success": True}), 200
        return jsonify({"error": "Listing not found or update failed"}), 404

    @app.route("/api/listings/<int:listing_id>", methods=["DELETE"])
    def delete_listing_endpoint(listing_id):
        success = delete_listing(listing_id)
        if success:
            return jsonify({"success": True}), 200
        return jsonify({"error": "Listing not found or delete failed"}), 404

    @app.route("/api/listings/<int:listing_id>/publish", methods=["POST"])
    def publish_listing_endpoint(listing_id):
        listing = get_listing(listing_id)
        if not listing:
            return jsonify({"error": "Listing not found"}), 404
        if listing.get("status") == "published":
            return jsonify({"error": "Listing already published"}), 409

        try:
            result = publish_listing(listing["payload"])
            external_listing_id = result.get("external_listing_id")
            record_publish_result(
                listing_id,
                published=True,
                external_listing_id=external_listing_id,
            )
            updated_listing = get_listing(listing_id)
            return jsonify({
                "success": True,
                "listing_id": listing_id,
                "external_listing_id": external_listing_id,
                "status": updated_listing.get("status") if updated_listing else "published",
            }), 200
        except Exception as e:
            error_message = str(e)
            record_publish_result(listing_id, published=False, error_message=error_message)
            return jsonify({"error": f"Publish failed: {error_message}"}), 502

    @app.route("/api/upload", methods=["POST"])
    def upload_file():
        if "photo" not in request.files:
            return jsonify({"error": "No photo provided"}), 400

        file = request.files["photo"]
        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        original_filename = secure_filename(file.filename)
        try:
            file.stream.seek(0, os.SEEK_END)
            file_size = file.stream.tell()
            file.stream.seek(0)
        except (AttributeError, OSError):
            file_size = request.content_length if request.content_length is not None else 1

        is_valid, err_msg = ImageValidator.validate_upload(original_filename, file_size)
        if not is_valid:
            return jsonify({"error": err_msg}), 400

        suffix = os.path.splitext(original_filename)[1] or ".jpg"
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                suffix=suffix,
                dir=app.config["UPLOAD_FOLDER"],
                delete=False,
            ) as tmp:
                tmp_path = tmp.name
                file.save(tmp_path)
            result = process_listing(tmp_path, original_filename)
        except Exception:
            logger.exception("Upload pipeline failed for %s", original_filename)
            return jsonify({"error": "Processing failed. Please try again."}), 500
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)

        status_code = 200 if result.get("success") else 500
        return jsonify(result), status_code

    @app.route("/downloads/<filename>")
    def download_file(filename):
        try:
            return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)
        except FileNotFoundError:
            return jsonify({"error": "File not found"}), 404

    @app.route("/api/health")
    def health():
        return jsonify({"status": "ok", "version": "1.0.0"}), 200

    @app.route("/settings")
    def settings_page():
        return render_template("settings.html")

    @app.route("/api/settings", methods=["GET"])
    def get_settings():
        stored = load_all()

        def _mask(key):
            value = stored.get(key, "")
            if not value:
                return ""
            visible = value[:4]
            return visible + "*" * max(4, len(value) - 4)

        return jsonify({
            "openai_api_key_set": bool(stored.get("OPENAI_API_KEY")),
            "openai_api_key_preview": _mask("OPENAI_API_KEY"),
            "ebay_client_id_set": bool(stored.get("EBAY_CLIENT_ID")),
            "ebay_client_id_preview": _mask("EBAY_CLIENT_ID"),
            "ebay_client_secret_set": bool(stored.get("EBAY_CLIENT_SECRET")),
            "use_openai_mock": os.environ.get("USE_OPENAI_MOCK", "True").lower() == "true",
            "use_ebay_mock": os.environ.get("USE_EBAY_MOCK", "True").lower() == "true",
            "ebay_sandbox": os.environ.get("EBAY_SANDBOX", "True").lower() == "true",
        }), 200

    @app.route("/api/settings", methods=["POST"])
    def save_settings():
        data = request.get_json(silent=True) or {}
        to_save = {}
        for key in ("OPENAI_API_KEY", "EBAY_CLIENT_ID", "EBAY_CLIENT_SECRET"):
            if key in data:
                to_save[key] = data[key]
        for key in ("USE_OPENAI_MOCK", "USE_EBAY_MOCK", "EBAY_SANDBOX"):
            if key in data:
                to_save[key] = "True" if data[key] else "False"
        for key in (
            "EBAY_MARKETPLACE_ID",
            "EBAY_MERCHANT_LOCATION_KEY",
            "EBAY_FULFILLMENT_POLICY_ID",
            "EBAY_PAYMENT_POLICY_ID",
            "EBAY_RETURN_POLICY_ID",
            "EBAY_DEFAULT_CATEGORY_ID",
            "EBAY_DEFAULT_CURRENCY",
            "EBAY_DEFAULT_QUANTITY",
        ):
            if key in data:
                to_save[key] = data[key]
        save_all(to_save)

        for key, value in to_save.items():
            if value:
                os.environ[key] = str(value)
            else:
                os.environ.pop(key, None)

        apply_to_env()

        import src.config as config_mod
        import src.api.openai_client as openai_mod
        import src.api.ebay_client as ebay_mod
        importlib.reload(config_mod)
        importlib.reload(openai_mod)
        importlib.reload(ebay_mod)

        return jsonify({"success": True}), 200

    @app.errorhandler(413)
    def request_entity_too_large(_error):
        return jsonify({"error": f"File too large. Max {MAX_CONTENT_LENGTH // (1024 * 1024)}MB"}), 413

    return app


if __name__ == "__main__":
    from src.config import DEBUG

    app = create_app()
    app.run(debug=DEBUG, host="127.0.0.1", port=5000)
