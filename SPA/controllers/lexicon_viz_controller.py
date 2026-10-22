"""Controller providing endpoints for diversity curves, collocation scatter, and reports."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from SPA.services.collocation_viz_service import CollocationVizService
from SPA.services.diversity_viz_service import DiversityVizService
from SPA.services.reporter_preview_service import ReporterPreviewService


def create_lexicon_viz_blueprint(
    div_service: DiversityVizService,
    colloc_service: CollocationVizService,
    rep_service: ReporterPreviewService,
) -> Blueprint:
    """Factory to create lexicon visualization blueprint with injected services."""
    lexicon_viz_bp = Blueprint("lexicon_viz", __name__, url_prefix="/api/v1/lexicon")

    @lexicon_viz_bp.route("/diversity/sensitivity", methods=["POST"])
    def get_diversity_sensitivity():
        body = request.get_json(silent=True) or {}
        code = body.get("code", "IR-IA")
        return jsonify(div_service.get_length_sensitivity(code=code))

    @lexicon_viz_bp.route("/diversity/compare", methods=["GET"])
    def get_diversity_comparisons():
        return jsonify(div_service.get_token_vs_lemma_and_punct())

    @lexicon_viz_bp.route("/diversity/radar", methods=["POST"])
    def get_diversity_radar():
        body = request.get_json(silent=True) or {}
        codes = body.get("codes")
        return jsonify(div_service.get_radar_zscores(codes=codes))

    @lexicon_viz_bp.route("/diversity/mattr-trajectories", methods=["POST"])
    def get_diversity_trajectories():
        body = request.get_json(silent=True) or {}
        codes = body.get("codes")
        w = int(body.get("window", 500))
        return jsonify(div_service.get_mattr_trajectories(codes=codes, window=w))

    @lexicon_viz_bp.route("/diversity/zipf-curves", methods=["POST"])
    def get_diversity_zipf():
        body = request.get_json(silent=True) or {}
        codes = body.get("codes")
        return jsonify(div_service.get_zipf_curves(codes=codes))

    @lexicon_viz_bp.route("/collocation/scatter", methods=["POST"])
    def get_collocation_scatter():
        data = request.get_json(silent=True) or {}
        code = data.get("code", "BR-SM")
        node = data.get("node", "robot")
        return jsonify(colloc_service.get_graphcoll_scatter(code=code, node=node))

    @lexicon_viz_bp.route("/collocation/sensitivity", methods=["POST"])
    def get_collocation_sensitivity():
        data = request.get_json(silent=True) or {}
        code = data.get("code", "BR-SM")
        node = data.get("node", "robot")
        return jsonify(colloc_service.get_measure_and_window_sensitivity(code=code, node=node))

    @lexicon_viz_bp.route("/collocation/nltk", methods=["POST"])
    def get_collocation_nltk():
        body = request.get_json(silent=True) or {}
        code = body.get("code", "BR-SM")
        return jsonify(colloc_service.get_nltk_bigrams(code=code))

    @lexicon_viz_bp.route("/report/preview", methods=["GET"])
    def get_report_preview():
        return jsonify(rep_service.get_live_markdown_and_summary())

    return lexicon_viz_bp

