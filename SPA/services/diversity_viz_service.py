"""Service computing lexical diversity sensitivity, comparisons, radar z-scores, and trajectories."""

from typing import Any

import numpy as np
import pandas as pd

from corpus_toolkit import TokenView, analysis, diversity
from SPA.repositories.corpus_repository import CorpusRepository
from SPA.services.payload_utils import df_to_table_payload, downsample_even, downsample_logrank


class DiversityVizService:
    def __init__(self, corpus_repo: CorpusRepository | None = None) -> None:
        self._repo = corpus_repo or CorpusRepository()
        self.repo = self._repo

    def get_length_sensitivity(self, code: str = "IR-IA") -> dict[str, Any]:
        text = self.repo.loader.load_text(code)
        try:
            forms = TokenView(text, "lem", False).analysed()
            sizes = np.unique(np.linspace(500, len(forms), 14).astype(int))
            rows = []
            for n in sizes:
                sub = forms[:n]
                rows.append({
                    "N": int(n),
                    "TTR": round(float(diversity.ttr(sub)), 3),
                    "MATTR_100": round(float(diversity.mattr(sub, 100)), 3),
                    "MTLD": round(float(diversity.mtld(sub)), 1),
                })
            df = pd.DataFrame(rows)
            return {
                "table": df_to_table_payload(df, title=f"Metin Boyu Duyarlılık Tablosu ({code})"),
                "series": [
                    {"name": "TTR (çöker)", "x": [r["N"] for r in rows], "y": [r["TTR"] for r in rows], "color": "#ef4444"},
                    {"name": "MATTR_100 (dirençli)", "x": [r["N"] for r in rows], "y": [r["MATTR_100"] for r in rows], "color": "#06b6d4"},
                ],
            }
        finally:
            text.evict()

    def get_token_vs_lemma_and_punct(self) -> dict[str, Any]:
        loader = self.repo.loader
        turkish = list(loader.load_all_turkish())
        div_raw = analysis.diversity_for(loader, turkish, field="lem", filter_function_words=False)
        div_tok = analysis.diversity_for(loader, turkish, field="tok")

        tok_lem_df = pd.DataFrame({
            "text": div_tok.index,
            "MATTR_100_tokens": div_tok["MATTR_100"].round(3),
            "MATTR_100_lemmas": div_raw["MATTR_100"].round(3),
            "V_tokens": div_tok["V"],
            "V_lemmas": div_raw["V"],
        })

        t_samples = [loader.load_text("BR-SM"), loader.load_text("KT-OK")]
        div_drop = analysis.diversity_for(loader, t_samples, field="tok", punct="drop")
        div_strip = analysis.diversity_for(loader, t_samples, field="tok", punct="strip")
        div_split = analysis.diversity_for(loader, t_samples, field="tok", punct="split")
        for s in t_samples:
            s.evict()

        punct_df = pd.DataFrame({
            "text": div_drop.index,
            "N_drop": div_drop["N"], "V_drop": div_drop["V"],
            "N_strip": div_strip["N"], "V_strip": div_strip["V"],
            "N_split": div_split["N"], "V_split": div_split["V"],
        })

        return {
            "token_vs_lemma": df_to_table_payload(tok_lem_df, title="Sözcük (Token) vs Kök (Lemma) Karşılaştırması"),
            "punct_regimes": df_to_table_payload(punct_df, title="Noktalama Kiplerinin Çeşitliliğe Etkisi"),
        }

    def get_radar_zscores(self, codes: list[str] | None = None) -> dict[str, Any]:
        loader = self.repo.loader
        div_raw = analysis.diversity_for(loader, loader.load_all(), field="lem", filter_function_words=False)
        metrics = list(diversity.RADAR_METRICS)

        z = (div_raw[metrics] - div_raw[metrics].mean()) / div_raw[metrics].std(ddof=0)
        z = z.fillna(0.0)

        target_codes = codes or ["IR-IA", "BR-SM", "OBI-SM", "ASD-PKD", "KT-OK", "SCS-OK"]
        series_list = []
        for name, row in z.iterrows():
            code = str(name).split(" · ")[0]
            if code in target_codes:
                series_list.append({
                    "name": str(name)[:20],
                    "z": [round(float(v), 2) for v in row[metrics]],
                })

        return {
            "axes": [diversity.METRIC_INFO[m].label.split(" (")[0] for m in metrics],
            "series": series_list,
        }

    def get_mattr_trajectories(self, codes: list[str] | None = None, window: int = 500) -> dict[str, Any]:
        loader = self.repo.loader
        target_codes = codes or ["IR-IA", "BR-SM", "OBI-SM"]
        texts = [loader.load_text(c) for c in target_codes]
        try:
            traj_map = analysis.mattr_trajectories_for(texts, window=window)
            series_list = []
            for label, arr in traj_map.items():
                if len(arr) == 0:
                    continue
                sub_arr = downsample_even(arr, 300)
                series_list.append({
                    "name": label[:22],
                    "x": [round(float(v), 1) for v in np.linspace(0, 100, len(sub_arr))],
                    "y": [round(float(v), 3) for v in sub_arr],
                })
            return {"series": series_list}
        finally:
            for t in texts:
                t.evict()

    def get_zipf_curves(self, codes: list[str] | None = None) -> dict[str, Any]:
        loader = self.repo.loader
        target_codes = codes or ["IR-IA", "BR-SM", "OBI-SM"]
        texts = [loader.load_text(c) for c in target_codes]
        try:
            zipf_map = analysis.zipf_for(texts)
            series_list = []
            for label, df in zipf_map.items():
                sampled = downsample_logrank(df, 200)
                series_list.append({
                    "name": label[:22],
                    "x": [int(r) for r in sampled["rank"]],
                    "y": [int(f) for f in sampled["freq"]],
                })
            return {"series": series_list}
        finally:
            for t in texts:
                t.evict()
