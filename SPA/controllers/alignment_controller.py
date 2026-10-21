"""Blueprint for translation alignment, length deltas, and NDA parallel views."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from SPA.models.alignment_dto import AlignmentFilterDTO
from SPA.services.alignment_delta_service import AlignmentDeltaService
from SPA.services.nda_parallel_service import NdaParallelService

alignment_bp = Blueprint("alignment", __name__, url_prefix="/api/v1/alignment")


def create_alignment_blueprint(
    delta_service: AlignmentDeltaService,
    nda_service: NdaParallelService,
) -> Blueprint:
    """Factory to create alignment blueprint with injected services."""

    @alignment_bp.route("/kpis/<pair_code>", methods=["GET"])
    def get_kpis(pair_code: str):
        kpis = delta_service.get_alignment_kpis(pair_code)
        if "error" in kpis:
            return jsonify(kpis), 404
        return jsonify(kpis), 200


    @alignment_bp.route("/chapters/<pair_code>", methods=["GET"])
    def get_chapters(pair_code: str):
        chapters = delta_service.get_chapter_navigation(pair_code)
        return jsonify({"chapters": chapters}), 200

    @alignment_bp.route("/rows", methods=["POST"])
    def get_rows():
        data = request.get_json() or {}
        filter_dto = AlignmentFilterDTO.from_dict(data)
        result = delta_service.get_filtered_rows(filter_dto)
        return jsonify(result), 200

    @alignment_bp.route("/nda/html/<pair_code>", methods=["GET"])
    def get_nda_html(pair_code: str):
        max_rows = int(request.args.get("max_rows", 20))
        html_content = nda_service.get_parallel_html(pair_code, max_rows=max_rows)
        return jsonify({"pair_code": pair_code, "html": html_content}), 200

    @alignment_bp.route("/nda/dictionary/<pair_code>", methods=["GET"])
    def get_nda_dict(pair_code: str):
        dictionary = nda_service.get_tripartite_dictionary(pair_code)
        return jsonify(dictionary), 200

    @alignment_bp.route("/nda/attributions/<pair_code>/<int:ai>", methods=["GET"])
    def get_row_attributions(pair_code: str, ai: int):
        attrs = nda_service.get_row_attribution_summary(pair_code, ai)
        return jsonify(attrs), 200

    return alignment_bp
