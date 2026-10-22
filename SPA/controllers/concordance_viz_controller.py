"""Controller providing search summary rates, view comparison, and NLTK checks."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from SPA.models.view_params_dto import CorpusScopeDTO, TokenViewParamsDTO, parse_scope_and_view
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
        scope, view = parse_scope_and_view(request.args, data)
        has_vp = any(k in data or k in request.args for k in ("view_params", "field", "filter_function_words", "mode", "punct"))
        vp = view if has_vp else None
        term = str(data.get("term", data.get("query", "robot")))
        field = str(data.get("field", vp.field if vp else "lem"))
        match = str(data.get("match", data.get("match_mode", "exact")))
        return jsonify(
            summary_service.get_search_summary_and_bars(
                term, field=field, match=match, scope=scope, view_params=vp
            )
        )

    @concordance_viz_bp.route("/views-compare", methods=["POST"])
    def get_views_compare():
        """Return comparison table across raw vs content and drop vs mask."""
        data = request.get_json(silent=True) or {}
        has_sc = any(k in data or k in request.args for k in ("scope", "category", "author_filter", "text_code"))
        has_vp = any(k in data or k in request.args for k in ("view_params", "field", "filter_function_words", "mode", "punct"))
        scope, view = parse_scope_and_view(request.args, data)
        term = str(data.get("term", data.get("query", "robot")))
        match = str(data.get("match", data.get("match_mode", "exact")))
        return jsonify(
            summary_service.get_views_comparison(
                term,
                match=match,
                scope=scope if has_sc else CorpusScopeDTO(scope="all_tr"),
                view_params=view if has_vp else TokenViewParamsDTO(field="lem"),
            )
        )

    @concordance_viz_bp.route("/nltk", methods=["POST"])
    def get_nltk_crosscheck():
        """Return NLTK concordance lines and similar words."""
        data = request.get_json(silent=True) or {}
        _, view = parse_scope_and_view(request.args, data)
        has_vp = any(k in data or k in request.args for k in ("view_params", "field", "filter_function_words", "mode", "punct"))
        code = str(data.get("code", "IR-IA"))
        word = str(data.get("word", "robot"))
        return jsonify(
            summary_service.get_nltk_concordance_and_similar(
                code, word, view_params=view if has_vp else None
            )
        )

    @concordance_viz_bp.route("/batch-matrices", methods=["POST"])
    def get_batch_matrices():
        """Return full batch dispersion tables, heatmaps, and 10-chunk curves."""
        data = request.get_json(silent=True) or {}
        has_sc = any(k in data or k in request.args for k in ("scope", "category", "author_filter", "text_code"))
        has_vp = any(k in data or k in request.args for k in ("view_params", "field", "filter_function_words", "mode", "punct", "content_only"))
        scope, view = parse_scope_and_view(request.args, data)
        raw_input = str(data.get("raw_input", "robot, insan, dünya, uzay"))
        field = str(data.get("field", view.field if has_vp else "lem"))
        is_content = bool(data.get("content_only", view.filter_function_words if has_vp else False))
        return jsonify(
            dispersion_matrix_service.analyze_dispersion(
                raw_input,
                field=field,
                is_content=is_content,
                scope=scope if has_sc else CorpusScopeDTO(scope="all_tr"),
                view_params=view if has_vp else None,
            )
        )

    return concordance_viz_bp



