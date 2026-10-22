"""Blueprint for lexical diversity, Union-Slot collocations, and TF-IDF keyness."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from SPA.models.stats_dto import CollocationParamsDTO, TfidfParamsDTO
from SPA.models.view_params_dto import CorpusScopeDTO, TokenViewParamsDTO
from SPA.services.collocation_service import CollocationService
from SPA.services.diversity_service import DiversityService
from SPA.services.tfidf_service import TfidfService


def create_lexicon_blueprint(
    diversity_service: DiversityService,
    collocation_service: CollocationService,
    tfidf_service: TfidfService,
) -> Blueprint:
    """Factory to create lexicon blueprint with injected services."""
    lexicon_bp = Blueprint("lexicon", __name__, url_prefix="/api/v1/lexicon")

    @lexicon_bp.route("/diversity/table", methods=["POST"])
    def get_diversity_table():
        data = request.get_json() or {}
        view_params = TokenViewParamsDTO.from_dict(data.get("view_params", {}))
        scope_dto = CorpusScopeDTO.from_dict(data.get("scope", {}))
        table = diversity_service.get_diversity_table(view_params, scope_dto)
        return jsonify({"items": table}), 200

    @lexicon_bp.route("/diversity/mattr", methods=["POST"])
    def get_mattr():
        data = request.get_json() or {}
        text_code = str(data.get("text_code", ""))
        view_params = TokenViewParamsDTO.from_dict(data.get("view_params", {}))
        window = int(data.get("window", 500))
        result = diversity_service.get_mattr_trajectory(
            text_code=text_code, view_params=view_params, window=window
        )
        return jsonify(result), 200

    @lexicon_bp.route("/diversity/zipf", methods=["POST"])
    def get_zipf():
        data = request.get_json() or {}
        text_code = str(data.get("text_code", ""))
        view_params = TokenViewParamsDTO.from_dict(data.get("view_params", {}))
        max_ranks = int(data.get("max_ranks", 500))
        result = diversity_service.get_zipf_rank_frequency(
            text_code=text_code, view_params=view_params, max_ranks=max_ranks
        )
        return jsonify(result), 200

    @lexicon_bp.route("/collocation/table", methods=["POST"])
    def get_collocations():
        data = request.get_json() or {}
        colloc_params = CollocationParamsDTO.from_dict(data)
        view_params = TokenViewParamsDTO.from_dict(data.get("view_params", {}))
        result = collocation_service.get_collocations(colloc_params, view_params)
        return jsonify(result), 200

    @lexicon_bp.route("/tfidf/keywords", methods=["POST"])
    def get_tfidf_keywords():
        data = request.get_json() or {}
        tfidf_params = TfidfParamsDTO.from_dict(data)
        view_params = TokenViewParamsDTO.from_dict(data.get("view_params", {}))
        scope_dto = CorpusScopeDTO.from_dict(data.get("scope", {}))
        result = tfidf_service.get_top_keywords_per_text(
            tfidf_params=tfidf_params,
            view_params=view_params,
            scope_dto=scope_dto,
        )
        return jsonify(result), 200

    @lexicon_bp.route("/tfidf/dense", methods=["POST"])
    def get_tfidf_dense():
        data = request.get_json() or {}
        tfidf_params = TfidfParamsDTO.from_dict(data)
        view_params = TokenViewParamsDTO.from_dict(data.get("view_params", {}))
        scope_dto = CorpusScopeDTO.from_dict(data.get("scope", {}))
        result = tfidf_service.get_dense_matrix(
            tfidf_params=tfidf_params,
            view_params=view_params,
            scope_dto=scope_dto,
        )
        return jsonify(result), 200

    return lexicon_bp
