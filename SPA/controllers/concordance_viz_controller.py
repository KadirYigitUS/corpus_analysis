"""Controller providing search summary rates, view comparison, and NLTK checks."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from SPA.services.dispersion_matrix_service import DispersionMatrixService
from SPA.services.search_summary_service import SearchSummaryService


def create_concordance_viz_blueprint(
    summary_service: SearchSummaryService,
    dispersion_matrix_service: DispersionMatrixService,
) -> Blueprint:
    """Factory to create concordance visualization blueprint with injected services."""
    concordance_viz_bp = Blueprint(
        "concordance_viz", __name__, url_prefix="/api/v1/concordance"
    )

    @concordance_viz_bp.route("/summary", methods=["POST"])
    def get_search_summary():
        """Return per-text hits, running words, and per10k rate bars."""
        data = request.get_json(silent=True) or {}
        term = str(data.get("term", "robot"))
        field = str(data.get("field", "lem"))
        match = str(data.get("match", "exact"))
        return jsonify(summary_service.get_search_summary_and_bars(term, field=field, match=match))

    @concordance_viz_bp.route("/views-compare", methods=["POST"])
    def get_views_compare():
        """Return comparison table across raw vs content and drop vs mask."""
        data = request.get_json(silent=True) or {}
        term = str(data.get("term", "robot"))
        return jsonify(summary_service.get_views_comparison(term))

    @concordance_viz_bp.route("/nltk", methods=["POST"])
    def get_nltk_crosscheck():
        """Return NLTK concordance lines and similar words."""
        data = request.get_json(silent=True) or {}
        code = str(data.get("code", "IR-IA"))
        word = str(data.get("word", "robot"))
        return jsonify(summary_service.get_nltk_concordance_and_similar(code, word))

    @concordance_viz_bp.route("/batch-matrices", methods=["POST"])
    def get_batch_matrices():
        """Return full batch dispersion tables, heatmaps, and 10-chunk curves."""
        data = request.get_json(silent=True) or {}
        raw_input = str(data.get("raw_input", "robot, insan, dünya, uzay"))
        field = str(data.get("field", "lem"))
        is_content = bool(data.get("content_only", False))
        return jsonify(
            dispersion_matrix_service.analyze_dispersion(
                raw_input, field=field, is_content=is_content
            )
        )

    return concordance_viz_bp


