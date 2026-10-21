"""Controller providing structure summary and length relation scatter for alignment."""

from flask import Blueprint, jsonify, request

from SPA.services.alignment_structure_service import AlignmentStructureService

alignment_viz_bp = Blueprint("alignment_viz", __name__, url_prefix="/api/v1/alignment")
_service = AlignmentStructureService()


@alignment_viz_bp.route("/structure-summary", methods=["GET"])
def get_structure_summary():
    """Return summary table and stacked bar data for all translation pairs."""
    return jsonify(_service.get_structure_summary())


@alignment_viz_bp.route("/structure-scatter", methods=["POST"])
def get_structure_scatter():
    """Return downsampled 1:1 scatter points and OLS regression slopes."""
    data = request.get_json(silent=True) or {}
    selected_pairs = data.get("pairs")
    max_pts = data.get("max_points", 1500)
    return jsonify(_service.get_scatter_data(selected_pairs=selected_pairs, max_points=max_pts))
