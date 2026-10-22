"""Service computing lexical diversity sensitivity, comparisons, radar z-scores, and trajectories."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from corpus_toolkit import analysis, diversity
from SPA.models.view_params_dto import CorpusScopeDTO, TokenViewParamsDTO
from SPA.repositories.corpus_repository import CorpusRepository
from SPA.services.diversity_service import masked_mattr_series
from SPA.services.payload_cache import global_payload_cache
from SPA.services.payload_utils import df_to_table_payload, downsample_even, downsample_logrank


class DiversityVizService:
    def __init__(self, corpus_repo: CorpusRepository | None = None) -> None:
        self._repo = corpus_repo or CorpusRepository()
        self.repo = self._repo

    def get_length_sensitivity(
        self, code: str = "IR-IA", view_params: TokenViewParamsDTO | None = None
    ) -> dict[str, Any]:
        vp = view_params or TokenViewParamsDTO(field="lem", filter_function_words=False)
        cache_key = global_payload_cache.build_key("div:sens", view=vp, code=code)
        if cached := global_payload_cache.get(cache_key):
            return cached

        text = self.repo.get_text_by_code(code) or self.repo.loader.load_text(code)
        try:
            view = self.repo.get_token_view(text, vp)
            forms = [str(x) for x in view.analysed()]
            is_masked = bool(vp.filter_function_words and vp.mode == "mask")
            m_seq = [str(f) if el else None for f, el in zip(view.forms, view.eligible)] if is_masked else []
            sizes = np.unique(np.linspace(min(500, max(10, len(forms))), len(forms), 14).astype(int))
            rows = []
            for n in sizes:
                sub = forms[:n]
                if is_masked:
                    s_m = masked_mattr_series(m_seq[: min(len(m_seq), int(n * 1.8))], 100)
                    valid_s = s_m[~np.isnan(s_m)]
                    m_val = float(valid_s.mean()) if len(valid_s) else float(diversity.mattr(sub, 100))
                else:
                    m_val = float(diversity.mattr(sub, 100))
                rows.append({"N": int(n), "TTR": round(float(diversity.ttr(sub)), 3), "MATTR_100": round(m_val, 3), "MTLD": round(float(diversity.mtld(sub)), 1)})
            payload = {
                "table": df_to_table_payload(pd.DataFrame(rows), title=f"Metin Boyu Duyarlılık Tablosu ({code})"),
                "series": [
                    {"name": "TTR (çöker)", "x": [r["N"] for r in rows], "y": [r["TTR"] for r in rows], "color": "#ef4444"},
                    {"name": "MATTR_100 (dirençli)", "x": [r["N"] for r in rows], "y": [r["MATTR_100"] for r in rows], "color": "#06b6d4"},
                ],
            }
            global_payload_cache.put(cache_key, payload)
            return payload
        finally:
            text.evict()

    def get_token_vs_lemma_and_punct(
        self, scope: CorpusScopeDTO | None = None, view_params: TokenViewParamsDTO | None = None
    ) -> dict[str, Any]:
        sc = scope or CorpusScopeDTO(scope="all_tr")
        vp = view_params or TokenViewParamsDTO(field="lem", filter_function_words=False)
        cache_key = global_payload_cache.build_key("div:compare", scope=sc, view=vp)
        if cached := global_payload_cache.get(cache_key):
            return cached

        loader = self.repo.loader
        texts = self.repo.get_texts_by_scope(sc) or list(loader.load_all_turkish())
        div_lem = analysis.diversity_for(loader, texts, field="lem", filter_function_words=vp.filter_function_words, mode=vp.mode, punct=vp.punct)  # type: ignore[arg-type]
        div_tok = analysis.diversity_for(loader, texts, field="tok", filter_function_words=vp.filter_function_words, mode=vp.mode, punct=vp.punct)  # type: ignore[arg-type]

        tok_lem_df = pd.DataFrame({
            "text": div_tok.index, "MATTR_100_tokens": div_tok["MATTR_100"].round(3),
            "MATTR_100_lemmas": div_lem["MATTR_100"].round(3), "V_tokens": div_tok["V"], "V_lemmas": div_lem["V"],
        })
        t_samples = texts[:2] if len(texts) >= 2 else [loader.load_text("BR-SM"), loader.load_text("KT-OK")]
        d_dr = analysis.diversity_for(loader, t_samples, field=vp.field, filter_function_words=vp.filter_function_words, mode=vp.mode, punct="drop")  # type: ignore[arg-type]
        d_st = analysis.diversity_for(loader, t_samples, field=vp.field, filter_function_words=vp.filter_function_words, mode=vp.mode, punct="strip")  # type: ignore[arg-type]
        d_sp = analysis.diversity_for(loader, t_samples, field=vp.field, filter_function_words=vp.filter_function_words, mode=vp.mode, punct="split")  # type: ignore[arg-type]
        for s in t_samples:
            s.evict()

        punct_df = pd.DataFrame({
            "text": d_dr.index, "N_drop": d_dr["N"], "V_drop": d_dr["V"],
            "N_strip": d_st["N"], "V_strip": d_st["V"], "N_split": d_sp["N"], "V_split": d_sp["V"],
        })
        payload = {
            "token_vs_lemma": df_to_table_payload(tok_lem_df, title="Sözcük (Token) vs Kök (Lemma) Karşılaştırması"),
            "punct_regimes": df_to_table_payload(punct_df, title="Noktalama Kiplerinin Çeşitliliğe Etkisi"),
        }
        global_payload_cache.put(cache_key, payload)
        return payload

    def get_radar_zscores(
        self, codes: list[str] | None = None, scope: CorpusScopeDTO | None = None, view_params: TokenViewParamsDTO | None = None
    ) -> dict[str, Any]:
        sc = scope or CorpusScopeDTO(scope="all")
        vp = view_params or TokenViewParamsDTO(field="lem", filter_function_words=False)
        loader = self.repo.loader
        texts = self.repo.get_texts_by_scope(sc) or list(loader.load_all())
        div_raw = analysis.diversity_for(loader, texts, field=vp.field, filter_function_words=vp.filter_function_words, mode=vp.mode, punct=vp.punct)  # type: ignore[arg-type]
        metrics = list(diversity.RADAR_METRICS)
        std = div_raw[metrics].std(ddof=0).replace(0, 1.0)
        z = ((div_raw[metrics] - div_raw[metrics].mean()) / std).fillna(0.0)

        target_codes = set(codes) if codes else {t.record.code for t in texts[:6]}
        if "OBI-SM" in target_codes:
            target_codes.add("O-SM")
        if "TSP-JL" in target_codes:
            target_codes.add("SP-JL")
        series_list = [
            {"name": str(name)[:20], "z": [round(float(v), 2) for v in row[metrics]]}
            for name, row in z.iterrows()
            if str(name).split(" · ")[0] in target_codes or not codes
        ]
        return {"axes": [diversity.METRIC_INFO[m].label.split(" (")[0] for m in metrics], "series": series_list}

    def get_mattr_trajectories(
        self, codes: list[str] | None = None, window: int = 500, scope: CorpusScopeDTO | None = None, view_params: TokenViewParamsDTO | None = None
    ) -> dict[str, Any]:
        vp = view_params or TokenViewParamsDTO(field="lem", filter_function_words=False)
        texts = self._resolve_texts(codes, scope)
        try:
            series_list = []
            for t in texts:
                v = self.repo.get_token_view(t, vp)
                if vp.filter_function_words and vp.mode == "mask":
                    arr = masked_mattr_series([str(f) if el else None for f, el in zip(v.forms, v.eligible)], window=window)
                else:
                    arr = diversity.mattr_series([str(x) for x in v.analysed()], window=window)
                if len(arr) == 0:
                    continue
                sub_arr = downsample_even(arr, 300)
                series_list.append({
                    "name": t.record.code[:22],
                    "x": [round(float(val), 1) for val in np.linspace(0, 100, len(sub_arr))],
                    "y": [round(float(val), 3) if not np.isnan(val) else 0.0 for val in sub_arr],
                })
            return {"series": series_list}
        finally:
            for t in texts:
                t.evict()

    def get_zipf_curves(
        self, codes: list[str] | None = None, scope: CorpusScopeDTO | None = None, view_params: TokenViewParamsDTO | None = None
    ) -> dict[str, Any]:
        vp = view_params or TokenViewParamsDTO(field="lem", filter_function_words=False)
        texts = self._resolve_texts(codes, scope)
        try:
            series_list = []
            for t in texts:
                v = self.repo.get_token_view(t, vp)
                sampled = downsample_logrank(diversity.rank_frequency([str(x) for x in v.analysed()]), 200)
                series_list.append({"name": t.record.code[:22], "x": [int(r) for r in sampled["rank"]], "y": [int(f) for f in sampled["freq"]]})
            return {"series": series_list}
        finally:
            for t in texts:
                t.evict()

    def _resolve_texts(self, codes: list[str] | None, scope: CorpusScopeDTO | None) -> list[Any]:
        if codes:
            return [t for c in codes if (t := self.repo.get_text_by_code(c)) is not None]
        if scope and scope.scope != "all":
            return self.repo.get_texts_by_scope(scope)[:6]
        return [t for c in ("IR-IA", "BR-SM", "OBI-SM") if (t := self.repo.get_text_by_code(c)) is not None]


