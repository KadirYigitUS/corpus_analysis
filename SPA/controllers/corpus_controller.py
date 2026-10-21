"""Blueprint for corpus inventory, source tables, schema inspection, and telemetry."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from SPA.services.inventory_memory_service import InventoryMemoryService

corpus_bp = Blueprint("corpus", __name__, url_prefix="/api/v1/corpus")


def create_corpus_blueprint(service: InventoryMemoryService) -> Blueprint:
    """Factory to create corpus blueprint with injected service."""

    @corpus_bp.route("/inventory", methods=["GET"])
    def get_inventory():
        summary = service.get_summary_stats()
        return jsonify(summary), 200

    @corpus_bp.route("/source-tables", methods=["GET"])
    def get_source_tables():
        category = request.args.get("category")
        tables = service.get_source_tables(category_filter=category)
        return jsonify(tables), 200

    @corpus_bp.route("/distribution-figure1", methods=["GET"])
    def get_distribution_figure():
        data = service.get_token_distribution_figure1()
        return jsonify(data), 200

    @corpus_bp.route("/schema/<text_code>", methods=["GET"])
    def get_schema(text_code: str):
        try:
            schema = service.get_schema_inspector(text_code)
            return jsonify(schema), 200
        except Exception as exc:
            return jsonify({"error": str(exc)}), 404

    @corpus_bp.route("/telemetry", methods=["GET"])
    def get_telemetry():
        stats = service.get_summary_stats()
        return jsonify({
            "rss_mb": stats["rss_mb"],
            "cache_info": stats["cache_info"],
            "total_texts": stats["total_texts"],
        }), 200

    @corpus_bp.route("/cache/evict", methods=["POST"])
    def evict_cache():
        data = request.get_json() or {}
        keep_n = int(data.get("keep_latest_n", 0))
        evicted = service._repo.evict_cache(keep_latest_n=keep_n)
        return jsonify({"evicted_count": evicted}), 200

    return corpus_bp
