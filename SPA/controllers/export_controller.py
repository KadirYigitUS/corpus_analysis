"""Blueprint for research bundle generation and quick search console execution."""

from __future__ import annotations

import io

from flask import Blueprint, jsonify, request, send_file

from SPA.models.stats_dto import ExportBundleDTO
from SPA.models.view_params_dto import TokenViewParamsDTO
from SPA.services.inventory_memory_service import InventoryMemoryService
from SPA.services.reporter_bundle_service import ReporterBundleService


def create_export_blueprint(
    bundle_service: ReporterBundleService,
    inventory_service: InventoryMemoryService,
) -> Blueprint:
    """Factory to create export blueprint with injected services."""
    export_bp = Blueprint("export", __name__, url_prefix="/api/v1/export")

    @export_bp.route("/quick-search", methods=["POST"])
    def quick_search_endpoint():
        data = request.get_json() or {}
        term = str(data.get("term", "")).strip()
        if not term:
            return jsonify({"error": "Missing search term"}), 400

        view_params = TokenViewParamsDTO.from_dict(data.get("view_params", {}))
        max_conc = int(data.get("max_concordance", 5))

        res = bundle_service.execute_quick_search(
            term=term,
            view_params=view_params,
            max_concordance=max_conc,
        )
        return jsonify(res), 200

    @export_bp.route("/bundle", methods=["POST"])
    def export_bundle():
        data = request.get_json() or {}
        bundle_dto = ExportBundleDTO.from_dict(data.get("bundle", {}))
        active_tables = data.get("tables", {})

        summary_stats = inventory_service.get_summary_stats()
        zip_bytes = bundle_service.generate_research_bundle(
            bundle_dto=bundle_dto,
            summary_stats=summary_stats,
            active_tables=active_tables,
        )

        return send_file(
            io.BytesIO(zip_bytes),
            mimetype="application/zip",
            as_attachment=True,
            download_name=f"{bundle_dto.bundle_name}.zip",
        )

    return export_bp
