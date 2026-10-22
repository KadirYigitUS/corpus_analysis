"""Controller providing endpoints for corpus sizes, verification, and previews."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from SPA.models.view_params_dto import parse_scope_and_view
from SPA.services.inventory_tables_service import InventoryTablesService


def create_corpus_viz_blueprint(service: InventoryTablesService) -> Blueprint:
    """Factory to create corpus visualization blueprint with injected service."""
    corpus_viz_bp = Blueprint("corpus_viz", __name__, url_prefix="/api/v1/corpus")

    @corpus_viz_bp.route("/sizes-chart", methods=["GET"])
    def get_sizes_chart():
        """Return text sizes distribution bar chart data colored by focal_code."""
        scope, view = parse_scope_and_view(request.args)
        return jsonify(service.get_sizes_chart_data(scope=scope, view=view))

    @corpus_viz_bp.route("/verify-files", methods=["GET"])
    def get_verify_files():
        """Return disk pickle verification table."""
        scope, view = parse_scope_and_view(request.args)
        return jsonify(service.get_verify_files_table(scope=scope, view=view))

    @corpus_viz_bp.route("/size-summary", methods=["GET"])
    def get_size_summary():
        """Return summary table of non-punctuation tokens, sentences and words."""
        scope, view = parse_scope_and_view(request.args)
        return jsonify(service.get_size_summary_table(scope=scope, view=view))

    @corpus_viz_bp.route("/memory-report", methods=["GET"])
    def get_memory_report():
        """Return live memory allocation report across loaded texts."""
        return jsonify(service.get_memory_report_table())

    @corpus_viz_bp.route("/content-lemmas", methods=["GET"])
    def get_content_lemmas():
        """Return content lemmas count per text using iter_evicting."""
        scope, view = parse_scope_and_view(request.args)
        val_view = view if any(k in request.args for k in ("field", "filter_function_words", "mode", "punct")) else None
        return jsonify(service.get_content_lemmas_summary(scope=scope, view=val_view))

    @corpus_viz_bp.route("/preview/<string:code>", methods=["GET"])
    def get_text_preview(code: str):
        """Return 8-row previews of tokens and sentences tables."""
        n = request.args.get("n", default=8, type=int)
        return jsonify(service.get_head_preview(code, n=n))

    return corpus_viz_bp


