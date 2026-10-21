"""Controller providing endpoints for diversity curves, collocation scatter, and reports."""

from flask import Blueprint, jsonify, request

from SPA.services.collocation_viz_service import CollocationVizService
from SPA.services.diversity_viz_service import DiversityVizService
from SPA.services.reporter_preview_service import ReporterPreviewService

lexicon_viz_bp = Blueprint("lexicon_viz", __name__, url_prefix="/api/v1/lexicon")
_div_service = DiversityVizService()
_colloc_service = CollocationVizService()
_rep_service = ReporterPreviewService()


@lexicon_viz_bp.route("/diversity/sensitivity", methods=["POST"])
def get_diversity_sensitivity():
    code = request.get_json(silent=True).get("code", "IR-IA") if request.get_json(silent=True) else "IR-IA"
    return jsonify(_div_service.get_length_sensitivity(code=code))


@lexicon_viz_bp.route("/diversity/compare", methods=["GET"])
def get_diversity_comparisons():
    return jsonify(_div_service.get_token_vs_lemma_and_punct())


@lexicon_viz_bp.route("/diversity/radar", methods=["POST"])
def get_diversity_radar():
    codes = request.get_json(silent=True).get("codes") if request.get_json(silent=True) else None
    return jsonify(_div_service.get_radar_zscores(codes=codes))


@lexicon_viz_bp.route("/diversity/mattr-trajectories", methods=["POST"])
def get_diversity_trajectories():
    codes = request.get_json(silent=True).get("codes") if request.get_json(silent=True) else None
    w = request.get_json(silent=True).get("window", 500) if request.get_json(silent=True) else 500
    return jsonify(_div_service.get_mattr_trajectories(codes=codes, window=w))


@lexicon_viz_bp.route("/diversity/zipf-curves", methods=["POST"])
def get_diversity_zipf():
    codes = request.get_json(silent=True).get("codes") if request.get_json(silent=True) else None
    return jsonify(_div_service.get_zipf_curves(codes=codes))


@lexicon_viz_bp.route("/collocation/scatter", methods=["POST"])
def get_collocation_scatter():
    data = request.get_json(silent=True) or {}
    code = data.get("code", "BR-SM")
    node = data.get("node", "robot")
    return jsonify(_colloc_service.get_graphcoll_scatter(code=code, node=node))


@lexicon_viz_bp.route("/collocation/sensitivity", methods=["POST"])
def get_collocation_sensitivity():
    data = request.get_json(silent=True) or {}
    code = data.get("code", "BR-SM")
    node = data.get("node", "robot")
    return jsonify(_colloc_service.get_measure_and_window_sensitivity(code=code, node=node))


@lexicon_viz_bp.route("/collocation/nltk", methods=["POST"])
def get_collocation_nltk():
    code = request.get_json(silent=True).get("code", "BR-SM") if request.get_json(silent=True) else "BR-SM"
    return jsonify(_colloc_service.get_nltk_bigrams(code=code))


@lexicon_viz_bp.route("/report/preview", methods=["GET"])
def get_report_preview():
    return jsonify(_rep_service.get_live_markdown_and_summary())
