"""Blueprint for corpus search, KWIC concordancing, and batch dispersion."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from SPA.models.search_dto import SearchQueryDTO
from SPA.models.view_params_dto import CorpusScopeDTO, TokenViewParamsDTO
from SPA.services.batch_dispersion_service import BatchDispersionService
from SPA.services.search_kwic_service import SearchKwicService

concordance_bp = Blueprint("concordance", __name__, url_prefix="/api/v1/concordance")


def create_concordance_blueprint(
    search_service: SearchKwicService,
    dispersion_service: BatchDispersionService,
) -> Blueprint:
    """Factory to create concordance blueprint with injected services."""

    @concordance_bp.route("/search", methods=["POST"])
    def search_kwic():
        data = request.get_json() or {}
        query_dto = SearchQueryDTO.from_dict(data)
        view_params = TokenViewParamsDTO.from_dict(data.get("view_params", {}))
        scope_dto = CorpusScopeDTO.from_dict(data.get("scope", {}))
        sort_by = str(data.get("sort_by", "position"))

        try:
            result = search_service.search_kwic(
                query_dto=query_dto,
                view_params=view_params,
                scope_dto=scope_dto,
                sort_by=sort_by,
            )
            return jsonify(result), 200
        except Exception as exc:
            return jsonify({"error": f"Invalid search query: {exc}", "total_hits": 0, "lines": []}), 400

    @concordance_bp.route("/punct-compare", methods=["POST"])
    def compare_punct():
        data = request.get_json() or {}
        query_dto = SearchQueryDTO.from_dict(data)
        scope_dto = CorpusScopeDTO.from_dict(data.get("scope", {}))
        result = search_service.compare_punctuation_regimes(query_dto, scope_dto)
        return jsonify({"counts": result}), 200

    @concordance_bp.route("/batch-dispersion", methods=["POST"])
    def batch_dispersion():
        data = request.get_json() or {}
        terms = data.get("terms", [])
        if not terms and "terms_raw" in data:
            terms = [t.strip() for t in data["terms_raw"].split(",") if t.strip()]

        view_params = TokenViewParamsDTO.from_dict(data.get("view_params", {}))
        scope_dto = CorpusScopeDTO.from_dict(data.get("scope", {}))
        n_chunks = int(data.get("n_chunks", 10))

        result = dispersion_service.analyze_batch(
            terms=terms,
            view_params=view_params,
            scope_dto=scope_dto,
            n_chunks=n_chunks,
        )
        return jsonify(result), 200

    return concordance_bp
