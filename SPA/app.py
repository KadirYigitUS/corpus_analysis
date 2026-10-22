"""Corpus Analysis SPA WSGI application factory."""

from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, render_template

from SPA.controllers.alignment_controller import create_alignment_blueprint
from SPA.controllers.alignment_viz_controller import create_alignment_viz_blueprint
from SPA.controllers.concordance_controller import create_concordance_blueprint
from SPA.controllers.concordance_viz_controller import create_concordance_viz_blueprint
from SPA.controllers.config_controller import create_config_blueprint
from SPA.controllers.corpus_controller import create_corpus_blueprint
from SPA.controllers.corpus_viz_controller import create_corpus_viz_blueprint
from SPA.controllers.export_controller import create_export_blueprint
from SPA.controllers.lexicon_controller import create_lexicon_blueprint
from SPA.controllers.lexicon_viz_controller import create_lexicon_viz_blueprint
from SPA.controllers.syntax_controller import create_syntax_blueprint
from SPA.controllers.syntax_viz_controller import create_syntax_viz_blueprint
from SPA.repositories.config_repository import ConfigRepository
from SPA.repositories.corpus_repository import CorpusRepository
from SPA.repositories.export_repository import ExportRepository
from SPA.repositories.nda_cache_repository import NdaCacheRepository
from SPA.services.alignment_delta_service import AlignmentDeltaService
from SPA.services.alignment_ner_service import AlignmentNerService
from SPA.services.alignment_stats_service import AlignmentStatsService
from SPA.services.alignment_structure_service import AlignmentStructureService
from SPA.services.batch_dispersion_service import BatchDispersionService
from SPA.services.collocation_service import CollocationService
from SPA.services.collocation_viz_service import CollocationVizService
from SPA.services.config_metadata_service import ConfigMetadataService
from SPA.services.depviz_service import DepvizService
from SPA.services.dispersion_matrix_service import DispersionMatrixService
from SPA.services.diversity_service import DiversityService
from SPA.services.diversity_viz_service import DiversityVizService
from SPA.services.inventory_memory_service import InventoryMemoryService
from SPA.services.inventory_tables_service import InventoryTablesService
from SPA.services.nda_parallel_service import NdaParallelService
from SPA.services.pos_comparison_service import PosComparisonService
from SPA.services.pos_matrix_service import PosMatrixService
from SPA.services.pos_service import PosService
from SPA.services.reporter_bundle_service import ReporterBundleService
from SPA.services.reporter_preview_service import ReporterPreviewService
from SPA.services.search_kwic_service import SearchKwicService
from SPA.services.search_summary_service import SearchSummaryService
from SPA.services.tfidf_service import TfidfService


def create_app(data_root: str | None = None) -> Flask:
    """Create and configure the Corpus Analysis SPA Flask application."""
    os.environ.setdefault("CORPUS_CACHE_POLICY", "keep")
    base_dir = Path(__file__).resolve().parent
    template_dir = base_dir / "views" / "templates"
    static_dir = base_dir / "views" / "static"

    app = Flask(
        __name__,
        template_folder=str(template_dir),
        static_folder=str(static_dir),
        static_url_path="/static",
    )

    # 1. Repositories (Single shared CorpusRepository & CorpusLoader)
    config_repo = ConfigRepository()
    paths = config_repo.get_paths()
    corpus_repo = CorpusRepository(data_root=data_root)
    nda_repo = NdaCacheRepository(corpus_repo.loader, path_config=paths)
    export_repo = ExportRepository(paths)

    # 2. Services (All 20 corpus services share corpus_repo)
    config_svc = ConfigMetadataService(config_repo)
    inv_svc = InventoryMemoryService(corpus_repo)
    inv_tables_svc = InventoryTablesService(corpus_repo)
    stats_svc = AlignmentStatsService(corpus_repo)
    ner_svc = AlignmentNerService(corpus_repo, nda_repo)
    delta_svc = AlignmentDeltaService(corpus_repo, stats_service=stats_svc, ner_service=ner_svc)
    align_struct_svc = AlignmentStructureService(corpus_repo)
    nda_svc = NdaParallelService(corpus_repo, nda_repo)
    pos_comp_svc = PosComparisonService(corpus_repo)
    pos_svc = PosService(corpus_repo, comp_service=pos_comp_svc)
    pos_matrix_svc = PosMatrixService(corpus_repo)
    dep_svc = DepvizService(corpus_repo)
    search_svc = SearchKwicService(corpus_repo)
    search_sum_svc = SearchSummaryService(corpus_repo)
    disp_svc = BatchDispersionService(corpus_repo)
    disp_matrix_svc = DispersionMatrixService(corpus_repo)
    div_svc = DiversityService(corpus_repo)
    div_viz_svc = DiversityVizService(corpus_repo)
    colloc_svc = CollocationService(corpus_repo)
    colloc_viz_svc = CollocationVizService(corpus_repo)
    tfidf_svc = TfidfService(corpus_repo)
    rep_preview_svc = ReporterPreviewService(corpus_repo)
    bundle_svc = ReporterBundleService(corpus_repo, export_repo)

    app.extensions["corpus_repo"] = corpus_repo
    app.extensions["services"] = {
        "inv": inv_svc,
        "inv_tables": inv_tables_svc,
        "stats": stats_svc,
        "ner": ner_svc,
        "delta": delta_svc,
        "align_struct": align_struct_svc,
        "nda": nda_svc,
        "pos_comp": pos_comp_svc,
        "pos": pos_svc,
        "pos_matrix": pos_matrix_svc,
        "dep": dep_svc,
        "search": search_svc,
        "search_sum": search_sum_svc,
        "disp": disp_svc,
        "disp_matrix": disp_matrix_svc,
        "div": div_svc,
        "div_viz": div_viz_svc,
        "colloc": colloc_svc,
        "colloc_viz": colloc_viz_svc,
        "tfidf": tfidf_svc,
        "rep_preview": rep_preview_svc,
        "bundle": bundle_svc,
    }

    # 3. Blueprints
    app.register_blueprint(create_config_blueprint(config_svc))
    app.register_blueprint(create_corpus_blueprint(inv_svc))
    app.register_blueprint(create_alignment_blueprint(delta_svc, nda_svc, stats_svc))
    app.register_blueprint(create_syntax_blueprint(pos_svc, dep_svc))
    app.register_blueprint(create_concordance_blueprint(search_svc, disp_svc))
    app.register_blueprint(create_lexicon_blueprint(div_svc, colloc_svc, tfidf_svc))
    app.register_blueprint(create_export_blueprint(bundle_svc, inv_svc))
    app.register_blueprint(create_corpus_viz_blueprint(inv_tables_svc))
    app.register_blueprint(create_alignment_viz_blueprint(align_struct_svc))
    app.register_blueprint(create_syntax_viz_blueprint(pos_matrix_svc))
    app.register_blueprint(create_concordance_viz_blueprint(search_sum_svc, disp_matrix_svc))
    app.register_blueprint(create_lexicon_viz_blueprint(div_viz_svc, colloc_viz_svc, rep_preview_svc))

    # 4. Root View Route & Favicon
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/favicon.ico")
    def favicon():
        return ("", 204)


    # 5. Security Headers (CSP Middleware)
    @app.after_request
    def set_security_headers(response):
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self' data:;"
        )
        response.headers["Content-Security-Policy"] = csp
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        return response

    return app
