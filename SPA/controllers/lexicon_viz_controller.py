"""Controller providing endpoints for diversity curves, collocation scatter, and reports."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from SPA.models.view_params_dto import CorpusScopeDTO, TokenViewParamsDTO, parse_scope_and_view
from SPA.services.collocation_viz_service import CollocationVizService
from SPA.services.diversity_viz_service import DiversityVizService
from SPA.services.reporter_preview_service import ReporterPreviewService


def _extract_sc_vp(
    body: dict,
    default_scope: str = "all",
    default_field: str = "lem",
    default_fw: bool = False,
) -> tuple[CorpusScopeDTO, TokenViewParamsDTO]:
    has_sc = any(k in body or k in request.args for k in ("scope", "category", "author_filter", "text_code"))
    has_vp = any(k in body or k in request.args for k in ("view_params", "field", "filter_function_words", "mode", "punct"))
    scope, view = parse_scope_and_view(request.args, body)
    sc = scope if has_sc else CorpusScopeDTO(scope=default_scope)
    vp = view if has_vp else TokenViewParamsDTO(field=default_field, filter_function_words=default_fw)
    return sc, vp


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
        _, vp = _extract_sc_vp(body)
        code = body.get("code", body.get("text_code", "IR-IA"))
        return jsonify(div_service.get_length_sensitivity(code=code, view_params=vp))

    @lexicon_viz_bp.route("/diversity/compare", methods=["GET", "POST"])
    def get_diversity_comparisons():
        body = request.get_json(silent=True) or {}
        sc, vp = _extract_sc_vp(body, default_scope="all_tr")
        return jsonify(div_service.get_token_vs_lemma_and_punct(scope=sc, view_params=vp))

    @lexicon_viz_bp.route("/diversity/radar", methods=["POST"])
    def get_diversity_radar():
        body = request.get_json(silent=True) or {}
        sc, vp = _extract_sc_vp(body)
        codes = body.get("codes")
        return jsonify(div_service.get_radar_zscores(codes=codes, scope=sc, view_params=vp))

    @lexicon_viz_bp.route("/diversity/mattr-trajectories", methods=["POST"])
    def get_diversity_trajectories():
        body = request.get_json(silent=True) or {}
        sc, vp = _extract_sc_vp(body)
        codes = body.get("codes")
        w = int(body.get("window", 500))
        return jsonify(div_service.get_mattr_trajectories(codes=codes, window=w, scope=sc, view_params=vp))

    @lexicon_viz_bp.route("/diversity/zipf-curves", methods=["POST"])
    def get_diversity_zipf():
        body = request.get_json(silent=True) or {}
        sc, vp = _extract_sc_vp(body)
        codes = body.get("codes")
        return jsonify(div_service.get_zipf_curves(codes=codes, scope=sc, view_params=vp))

    @lexicon_viz_bp.route("/collocation/scatter", methods=["POST"])
    def get_collocation_scatter():
        data = request.get_json(silent=True) or {}
        _, vp = _extract_sc_vp(data)
        code = data.get("code", data.get("text_code", "BR-SM"))
        node = data.get("node", data.get("node_query", "robot"))
        left = int(data.get("left_span", data.get("left", 5)))
        right = int(data.get("right_span", data.get("right", 5)))
        min_f = int(data.get("min_freq", 3))
        return jsonify(colloc_service.get_graphcoll_scatter(code=code, node=node, view_params=vp, left=left, right=right, min_freq=min_f))

    @lexicon_viz_bp.route("/collocation/sensitivity", methods=["POST"])
    def get_collocation_sensitivity():
        data = request.get_json(silent=True) or {}
        _, vp = _extract_sc_vp(data)
        code = data.get("code", data.get("text_code", "BR-SM"))
        node = data.get("node", data.get("node_query", "robot"))
        min_f = int(data.get("min_freq", 3))
        return jsonify(colloc_service.get_measure_and_window_sensitivity(code=code, node=node, view_params=vp, min_freq=min_f))

    @lexicon_viz_bp.route("/collocation/nltk", methods=["POST"])
    def get_collocation_nltk():
        body = request.get_json(silent=True) or {}
        _, vp = _extract_sc_vp(body, default_fw=True)
        code = body.get("code", body.get("text_code", "BR-SM"))
        return jsonify(colloc_service.get_nltk_bigrams(code=code, view_params=vp))

    @lexicon_viz_bp.route("/report/preview", methods=["GET", "POST"])
    def get_report_preview():
        body = request.get_json(silent=True) or {}
        sc, vp = _extract_sc_vp(body)
        return jsonify(rep_service.get_live_markdown_and_summary(scope=sc, view_params=vp))

    return lexicon_viz_bp


