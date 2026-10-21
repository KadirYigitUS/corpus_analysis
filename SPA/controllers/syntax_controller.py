"""Blueprint for POS profiling, morphosyntactic comparisons, and dependency trees."""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from SPA.models.view_params_dto import CorpusScopeDTO
from SPA.services.depviz_service import DepvizService
from SPA.services.pos_service import PosService

syntax_bp = Blueprint("syntax", __name__, url_prefix="/api/v1/syntax")


def create_syntax_blueprint(
    pos_service: PosService,
    depviz_service: DepvizService,
) -> Blueprint:
    """Factory to create syntax blueprint with injected services."""

    @syntax_bp.route("/pos/profiles", methods=["POST"])
    def get_pos_profiles():
        data = request.get_json() or {}
        scope_dto = CorpusScopeDTO.from_dict(data)
        content_only = bool(data.get("content_only", False))
        table = pos_service.get_pos_profile_table(scope_dto, content_only=content_only)
        return jsonify({"items": table}), 200

    @syntax_bp.route("/pos/pair-delta/<pair_code>", methods=["GET"])
    def get_pair_delta(pair_code: str):
        content_only = request.args.get("content_only", "false").lower() == "true"
        delta = pos_service.get_pair_delta_pp(pair_code, content_only=content_only)
        return jsonify(delta), 200

    @syntax_bp.route("/pos/author-summary", methods=["GET"])
    def get_author_summary():
        content_only = request.args.get("content_only", "false").lower() == "true"
        rows = pos_service.get_author_summary_table(content_only=content_only)
        return jsonify({"items": rows}), 200

    @syntax_bp.route("/pos/group-comparison", methods=["POST"])
    def get_group_comparison():
        data = request.get_json() or {}
        comp = pos_service.get_group_comparison_figure2c(
            group_a_scope=str(data.get("group_a", "trans_tr")),
            group_b_scope=str(data.get("group_b", "indig_tr")),
            comparison_key=str(data.get("comparison_key", "ALL")),
            content_only=bool(data.get("content_only", False)),
            n_bootstrap=int(data.get("n_bootstrap", 800)),
        )
        return jsonify(comp), 200

    @syntax_bp.route("/dep/conll", methods=["POST"])
    def get_dep_conll():
        data = request.get_json() or {}
        try:
            conll = depviz_service.get_sentence_conll_table(
                text_code=str(data.get("text_code", "")),
                chapter_no=int(data.get("chapter_no", 1)),
                paragraph_no=int(data.get("paragraph_no", 1)),
                sentence_no=int(data.get("sentence_no", 1)),
            )
            return jsonify({"tokens": conll}), 200
        except Exception as exc:
            return jsonify({"error": str(exc)}), 404

    @syntax_bp.route("/dep/tree-svg", methods=["POST"])
    def get_dep_svg():
        data = request.get_json() or {}
        try:
            svg = depviz_service.get_sentence_tree_svg(
                text_code=str(data.get("text_code", "")),
                chapter_no=int(data.get("chapter_no", 1)),
                paragraph_no=int(data.get("paragraph_no", 1)),
                sentence_no=int(data.get("sentence_no", 1)),
                dim_function_words=bool(data.get("dim_function_words", True)),
                compact=bool(data.get("compact", False)),
            )
            return jsonify({"svg": svg}), 200
        except Exception as exc:
            return jsonify({"error": str(exc)}), 404

    @syntax_bp.route("/dep/aligned/<pair_code>/<int:ai>", methods=["GET"])
    def get_aligned_tree(pair_code: str, ai: int):
        pair_trees = depviz_service.get_aligned_tree_pair(pair_code, ai)
        return jsonify(pair_trees), 200

    return syntax_bp
