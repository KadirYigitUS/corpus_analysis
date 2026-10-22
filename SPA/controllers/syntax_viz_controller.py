"""Controller extending syntax endpoints with UPOS matrix heatmap and aligned tree options."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from SPA.models.view_params_dto import parse_scope_and_view
from SPA.services.pos_matrix_service import PosMatrixService


def create_syntax_viz_blueprint(matrix_service: PosMatrixService) -> Blueprint:
    """Factory to create syntax visualization blueprint with injected service."""
    syntax_viz_bp = Blueprint("syntax_viz", __name__, url_prefix="/api/v1/syntax")

    @syntax_viz_bp.route("/pos/matrix", methods=["GET"])
    def get_pos_matrix():
        """Return 13x17 UPOS heatmap matrix payload."""
        scope, view = parse_scope_and_view(request.args)
        content_only = (
            request.args.get("content_only", "false").lower() == "true"
            or view.filter_function_words
        )
        return jsonify(
            matrix_service.get_upos_heatmap_matrix(
                content_only=content_only, scope=scope, view=view
            )
        )

    return syntax_viz_bp


