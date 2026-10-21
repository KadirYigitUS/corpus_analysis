"""Controller extending syntax endpoints with UPOS matrix heatmap and aligned tree options."""

from flask import Blueprint, jsonify, request

from SPA.services.pos_matrix_service import PosMatrixService

syntax_viz_bp = Blueprint("syntax_viz", __name__, url_prefix="/api/v1/syntax")
_matrix_service = PosMatrixService()


@syntax_viz_bp.route("/pos/matrix", methods=["GET"])
def get_pos_matrix():
    """Return 13x17 UPOS heatmap matrix payload."""
    content_only = request.args.get("content_only", "false").lower() == "true"
    return jsonify(_matrix_service.get_upos_heatmap_matrix(content_only=content_only))
