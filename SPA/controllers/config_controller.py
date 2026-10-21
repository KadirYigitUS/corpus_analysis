"""Blueprint for configuration paths, metadata registries, asset uploads, and help formulas."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from SPA.models.config_dto import AuthorMetadataDTO, BookMetadataDTO, PathConfigDTO
from SPA.services.config_metadata_service import ConfigMetadataService

config_bp = Blueprint("config", __name__, url_prefix="/api/v1")


def create_config_blueprint(service: ConfigMetadataService) -> Blueprint:
    """Factory to create config blueprint with injected service."""

    @config_bp.route("/config/paths", methods=["GET"])
    def get_paths():
        paths = service.get_paths()
        return jsonify({"paths": paths.to_dict()["paths"]}), 200

    @config_bp.route("/config/paths", methods=["POST"])
    def update_paths():
        data = request.get_json() or {}
        new_paths = PathConfigDTO.from_dict(data)
        result = service.update_paths(new_paths)
        return jsonify(result), 200

    @config_bp.route("/config/books", methods=["GET"])
    def get_books():
        author = request.args.get("author")
        books = service.get_books(author_code=author)
        return jsonify({"books": books}), 200

    @config_bp.route("/config/books", methods=["POST"])
    def update_book():
        data = request.get_json() or {}
        if "code" not in data:
            return jsonify({"error": "Missing book code"}), 400
        book_dto = BookMetadataDTO.from_dict(data)
        service.update_book(book_dto)
        return jsonify({"saved": True, "book": book_dto.to_dict()}), 200

    @config_bp.route("/config/authors", methods=["GET"])
    def get_authors():
        authors = service.get_authors()
        return jsonify({"authors": authors}), 200

    @config_bp.route("/config/authors", methods=["POST"])
    def update_author():
        data = request.get_json() or {}
        if "code" not in data:
            return jsonify({"error": "Missing author code"}), 400
        author_dto = AuthorMetadataDTO.from_dict(data)
        service.update_author(author_dto)
        return jsonify({"saved": True, "author": author_dto.to_dict()}), 200

    @config_bp.route("/config/upload-image", methods=["POST"])
    def upload_image():
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        file = request.files["file"]
        category = request.form.get("category", "book")
        if not file.filename:
            return jsonify({"error": "Empty filename"}), 400
        content = file.read()
        saved_url = service.upload_image(category, file.filename, content)
        return jsonify({"saved": True, "url": saved_url}), 200

    @config_bp.route("/help/formulas", methods=["GET"])
    def get_formulas():
        formulas = service.get_formula_registry()
        return jsonify(formulas), 200

    return config_bp
