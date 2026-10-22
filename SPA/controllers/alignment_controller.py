"""Blueprint for translation alignment, length deltas, and NDA parallel views."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from SPA.models.alignment_dto import AlignmentFilterDTO
from SPA.services.alignment_delta_service import AlignmentDeltaService
from SPA.services.alignment_stats_service import AlignmentStatsService
from SPA.services.nda_parallel_service import NdaParallelService


def create_alignment_blueprint(
    delta_service: AlignmentDeltaService,
    nda_service: NdaParallelService,
    stats_service: AlignmentStatsService | None = None,
) -> Blueprint:
    """Factory to create alignment blueprint with injected services."""
    alignment_bp = Blueprint("alignment", __name__, url_prefix="/api/v1/alignment")

    @alignment_bp.route("/kpis/<pair_code>", methods=["GET"])
    def get_kpis(pair_code: str):
        ch_raw = request.args.get("chapter_no")
        ch_no = int(ch_raw) if ch_raw and ch_raw not in ("all", "null", "") else None
        kpis = delta_service.get_alignment_kpis(pair_code, chapter_no=ch_no)
        if "error" in kpis:
            return jsonify(kpis), 404
        return jsonify(kpis), 200

    @alignment_bp.route("/stats/<pair_code>", methods=["GET"])
    def get_stats(pair_code: str):
        ch_raw = request.args.get("chapter_no")
        ch_no = int(ch_raw) if ch_raw and ch_raw not in ("all", "null", "") else None
        svc = stats_service or delta_service._stats
        res = svc.get_stats_and_series(pair_code, chapter_no=ch_no)
        if "error" in res:
            return jsonify(res), 404
        return jsonify(res), 200

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
        max_rows = int(request.args.get("max_rows", 15))
        mode = str(request.args.get("mode", "linked"))
        page = int(request.args.get("page", 1))
        ais_raw = request.args.get("ais", "").strip()
        hits_raw = request.args.get("hits", "").strip()
        ais = (
            [int(x.strip()) for x in ais_raw.split(",") if x.strip().isdigit()]
            if ais_raw
            else None
        )
        hits = (
            [x.strip() for x in hits_raw.split(",") if x.strip()]
            if hits_raw
            else None
        )
        payload = nda_service.get_parallel_payload(
            pair_code=pair_code,
            mode=mode,
            page=page,
            max_rows=max_rows,
            alignment_ids=ais,
            hits=hits,
        )
        return jsonify(payload), 200

    @alignment_bp.route("/nda/dictionary/<pair_code>", methods=["GET"])
    def get_nda_dict(pair_code: str):
        dictionary = nda_service.get_tripartite_dictionary(pair_code)
        return jsonify(dictionary), 200

    @alignment_bp.route("/nda/attributions/<pair_code>/<int:ai>", methods=["GET"])
    def get_row_attributions(pair_code: str, ai: int):
        attrs = nda_service.get_row_attribution_summary(pair_code, ai)
        return jsonify(attrs), 200

    return alignment_bp
