"""Controller providing search summary rates, view comparison, and NLTK checks."""

from flask import Blueprint, jsonify, request

from SPA.services.search_summary_service import SearchSummaryService

concordance_viz_bp = Blueprint("concordance_viz", __name__, url_prefix="/api/v1/concordance")
_service = SearchSummaryService()


@concordance_viz_bp.route("/summary", methods=["POST"])
def get_search_summary():
    """Return per-text hits, running words, and per10k rate bars."""
    data = request.get_json(silent=True) or {}
    term = str(data.get("term", "robot"))
    field = str(data.get("field", "lem"))
    match = str(data.get("match", "exact"))
    return jsonify(_service.get_search_summary_and_bars(term, field=field, match=match))


@concordance_viz_bp.route("/views-compare", methods=["POST"])
def get_views_compare():
    """Return comparison table across raw vs content and drop vs mask."""
    data = request.get_json(silent=True) or {}
    term = str(data.get("term", "robot"))
    return jsonify(_service.get_views_comparison(term))


@concordance_viz_bp.route("/nltk", methods=["POST"])
def get_nltk_crosscheck():
    """Return NLTK concordance lines and similar words."""
    data = request.get_json(silent=True) or {}
    code = str(data.get("code", "IR-IA"))
    word = str(data.get("word", "robot"))
    return jsonify(_service.get_nltk_concordance_and_similar(code, word))


@concordance_viz_bp.route("/batch-matrices", methods=["POST"])
def get_batch_matrices():
    """Return full batch dispersion tables, heatmaps, and 10-chunk curves."""
    from SPA.services.dispersion_matrix_service import DispersionMatrixService
    data = request.get_json(silent=True) or {}
    raw_input = str(data.get("raw_input", "robot, insan, dünya, uzay"))
    field = str(data.get("field", "lem"))
    is_content = bool(data.get("content_only", False))
    disp_service = DispersionMatrixService()
    return jsonify(disp_service.analyze_dispersion(raw_input, field=field, is_content=is_content))

