"""Complete formula, metric, and pane documentation catalog across Global Matrix and Tabs 1-11."""

from __future__ import annotations

from typing import Any


def _frac(num: str, den: str) -> str:
    return f'<span class="math-frac"><span class="math-num">{num}</span><span class="math-den">{den}</span></span>'


def _sqrt(rad: str) -> str:
    return f'<span class="math-sqrt">&radic;<span class="math-radicand">{rad}</span></span>'


def _entry(tab: str, name: str, formula: str, desc: str, guard: str, cite: str) -> dict[str, str]:
    return {
        "tab": tab,
        "name": name,
        "formula": formula,
        "formula_html": formula,
        "description": desc,
        "nan_guard": guard,
        "citation": cite,
    }


HELP_CATALOG: dict[str, list[dict[str, str]]] = {
    "Global Matrix": [
        _entry(
            "Global Matrix",
            "TokenView 32-Combination Matrix (field × filter_fw × mode × punct)",
            "V<sub>matrix</sub> = {tok, lem} &times; {All, Content} &times; {drop, mask} &times; {drop, keep, strip, split}",
            "Controls lexical projection across all tabs: field selects surface token vs clean_lemma; filter_function_words filters TR/EN stopword and closed-class UPOS sets.",
            "clean_lemma strips Turkish apostrophe inflections while preserving hyphenated compounds.",
            "Corpus Analysis Toolkit v3 (2026)",
        ),
        _entry(
            "Global Matrix",
            "Filter Mode: Drop vs Positional Mask (mode='drop' | 'mask')",
            "Drop: S' = [w<sub>i</sub> : elig(w<sub>i</sub>)] &nbsp;|&nbsp; Mask: S'[i] = w<sub>i</sub> if elig(w<sub>i</sub>) else &empty;",
            "mode='drop' compacts the sequence for bag-of-words metrics; mode='mask' replaces filtered function words with None so sliding windows preserve original token distances.",
            "Bag-of-words estimators iterate view.analysed(); positional window estimators use view.forms.",
            "Sinclair (1991); Covington & McFall (2010)",
        ),
    ],
    "Tab 1: Inventory": [
        _entry(
            "Tab 1",
            "Corpus Scope Taxonomy & Lexical Volume (8 Scopes)",
            "N<sub>scope</sub> = &sum;<sub>t &in; Scope</sub> N<sub>t</sub>, &nbsp; V<sub>lemma</sub> = |{lem(w) : w &in; view.analysed()}|",
            "Aggregates running tokens, sentence counts, and content lemma vocabularies across all, all_en, all_tr, trans_en, trans_tr, indig_tr, author_related, author_turkish, and single.",
            "Requires valid Parquet cache v3-2026-04-20; RSS memory ceiling < 1500 MB.",
            "Even-Zohar (1990); Toury (2012)",
        ),
    ],
    "Tab 2: Alignment": [
        _entry(
            "Tab 2",
            "Token Expansion Ratio & Sentence Delta",
            f"r&#772;<sub>exp</sub> = {_frac('1', 'M')} &sum;<sub>i=1</sub><sup>M</sup> {_frac('L<sub>TR,i</sub>', 'L<sub>EN,i</sub>')}, &nbsp; &Delta;S<sub>i</sub> = S<sub>TR,i</sub> &minus; S<sub>EN,i</sub>",
            "Measures target-to-source morphological and syntactic expansion, sentence ratio (R_sent), and 1:1 alignment cardinality percentage across chapter and book spans.",
            "L_EN,i > 0 for ratio rows; 0:1 and 1:0 rows classified as additions/omissions.",
            "Gale & Church (1993); Baker (1996)",
        ),
    ],
    "Tab 3: NDA Parallel": [
        _entry(
            "Tab 3",
            "NDA Layer Precedence & [G: , P: ] Tripartite State Machine",
            "Layer 0: REALIA (NER_*) &prec; Top-Layer: IRREALIA (SCIFI_*) &nbsp;|&nbsp; State: [G: &plusmn;, P: &plusmn;]",
            "Renders side-by-side EN-TR aligned tokens with stepped SVG connectors linking first EN to first TR span tokens and tripartite dictionary drawers (Linked, EN-Only, TR-Only).",
            "Unpickled strictly via _NdaSafeUnpickler whitelist to prevent arbitrary code execution.",
            "Suvin (1979); Loponen (2009)",
        ),
    ],
    "Tab 4: POS & Morphology": [
        _entry(
            "Tab 4",
            "Relative UPOS Share, Pair Divergence & Lexical Density",
            f"p<sub>u</sub> = {_frac('c<sub>u</sub>', 'N')} &times; 100%, &nbsp; &Delta;pp<sub>u</sub> = p<sub>TR,u</sub> &minus; p<sub>EN,u</sub>, &nbsp; LD = {_frac('N<sub>NOUN+VERB+ADJ+ADV</sub>', 'N')}",
            "Computes 17-tag Universal POS proportions, translation pair percentage-point shifts, noun-to-verb ratios (N/V), and lexical density across texts and author cohorts.",
            "N > 0; VERB > 0 for N/V ratio.",
            "Ure (1971); Halliday (1985); Nivre et al. (2020)",
        ),
        _entry(
            "Tab 4",
            "Pearson Chi-Square, Cramér's V & 95% Bootstrap CIs",
            f"&chi;<sup>2</sup> = &sum; {_frac('(O<sub>ij</sub> &minus; E<sub>ij</sub>)<sup>2</sup>', 'E<sub>ij</sub>')}, &nbsp; V = {_sqrt(_frac('&chi;<sup>2</sup>', 'N &middot; min(R&minus;1, C&minus;1)'))}",
            "Evaluates morphosyntactic homogeneity between Translated TR and Indigenous TR over 500-token chunks with 1,000-iteration permutation p-values, BH-FDR q-values, and bootstrap CIs.",
            "E_ij > 0; chunk count >= 2 per comparison group.",
            "Cramér (1946); Efron & Tibshirani (1993)",
        ),
    ],
    "Tab 5: Dependency": [
        _entry(
            "Tab 5",
            "Universal Dependencies Directed Arc Graph & Bilingual Tree Alignment",
            "G = (V<sub>tokens</sub>, E<sub>arcs</sub>), &nbsp; e = (w<sub>head</sub> &rarr;<sup>deprel</sup> w<sub>dep</sub>)",
            "Projects CoNLL-U syntactic tuples (idx, word, lemma, upos, head, deprel) into directed SVG arc diagrams with optional UD label normalization and function-word dimming.",
            "Root tokens have head = 0; cyclic arcs guarded.",
            "Tesnière (1959); de Marneffe et al. (2021)",
        ),
    ],
    "Tab 6: Concordance & KWIC": [
        _entry(
            "Tab 6",
            "5-View KWIC Concordance & 4-Regime Punctuation Sensitivity",
            f"KWIC(q, &pm;k) = (L<sub>k</sub>&hellip;L<sub>1</sub>, w<sub>node</sub>, R<sub>1</sub>&hellip;R<sub>k</sub>), &nbsp; Rate<sub>10k</sub> = {_frac('f<sub>q</sub>', 'N')} &times; 10,000",
            "Supports Exact, Glob, and Regex queries with Turkish İ/I case-folding, multi-level positional sorting (position, node, L1, R1), and drop/keep/strip/split punctuation comparisons.",
            "Invalid regex syntax returns HTTP 400 diagnostic card without server failure.",
            "Sinclair (1991); Wynne (2008)",
        ),
    ],
    "Tab 7: Batch Dispersion": [
        _entry(
            "Tab 7",
            "Juilland's D Dispersion & Benjamini-Hochberg FDR Correlation Matrix",
            f"D = 1 &minus; {_frac('CV', _sqrt('k &minus; 1'))}, &nbsp; CV = {_frac('&sigma;<sub>v</sub>', '&mu;<sub>v</sub>')}, &nbsp; q<sub>(i)</sub> = min<sub>j &ge; i</sub> {_frac('m &middot; p<sub>(j)</sub>', 'j')}",
            "Quantifies uniformity of lexical distribution across k=10 narrative chunks and across corpus texts, paired with Pearson r, Spearman rho, and BH-FDR multiple-testing correction.",
            "Returns D = 0 when total frequency is 0 or concentrated in a single part; k > 1.",
            "Juilland & Chang-Rodríguez (1964); Benjamini & Hochberg (1995)",
        ),
    ],
    "Tab 8: Lexical Diversity": [
        _entry(
            "Tab 8",
            "Classical & Algebraic Transformations (TTR, Guiraud R, CTTR, Herdan C, Dugast U, Maas a²)",
            f"TTR = {_frac('V', 'N')}, &nbsp; R = {_frac('V', _sqrt('N'))}, &nbsp; CTTR = {_frac('V', _sqrt('2N'))}, &nbsp; C = {_frac('ln V', 'ln N')}, &nbsp; a<sup>2</sup> = {_frac('ln N &minus; ln V', '(ln N)<sup>2</sup>')}",
            "Computes core type-token ratios and logarithmic transformations (Dugast U = 1/a²) across active TokenView tokens or lemmas.",
            "N > 1 and V > 0; Dugast U guarded when V == N.",
            "Guiraud (1954); Carroll (1964); Herdan (1960); Maas (1972)",
        ),
        _entry(
            "Tab 8",
            "Frequency Spectrum & Repeat-Rate Estimators (Yule K, Simpson D, Honoré R, Sichel S, Michéa M, H)",
            f"K = 10<sup>4</sup> {_frac('&sum; i<sup>2</sup>V<sub>i</sub> &minus; N', 'N<sup>2</sup>')}, &nbsp; D = &sum; {_frac('V<sub>i</sub> i(i&minus;1)', 'N(N&minus;1)')}, &nbsp; R<sub>H</sub> = {_frac('100 ln N', '1 &minus; V<sub>1</sub>/V')}, &nbsp; H = &minus;&sum; p<sub>i</sub> log<sub>2</sub> p<sub>i</sub>",
            "Captures vocabulary concentration, hapax legomena (V1) richness, dislegomena (V2) ratios (Sichel S = V2/V, Michéa M = V/V2), and Shannon information entropy.",
            "N > 1; Honoré R guarded when V1 == V; Michéa M guarded when V2 == 0.",
            "Yule (1944); Simpson (1949); Honoré (1979); Sichel (1975)",
        ),
        _entry(
            "Tab 8",
            "Windowed, Sequential & Hypergeometric Richness (STTR, MATTR_W, MTLD_0.72, HD-D_42, Zipf OLS)",
            f"MATTR<sub>W</sub> = {_frac('1', 'N&minus;W+1')} &sum;<sub>j=1</sub><sup>N&minus;W+1</sup> {_frac('V<sub>j,W</sub>', 'N<sub>j,W</sub>')}, &nbsp; log<sub>10</sub> f = &alpha; + &beta; log<sub>10</sub> r",
            "Computes STTR_1000, sliding-window MATTR (W=50, 100, 500; preserving positional slots under mode='mask'), bidirectional MTLD (0.72 threshold), HD-D (sample=42), and Zipf OLS slope/R².",
            "N >= W for full windows; falls back to single window when N < W.",
            "McCarthy & Jarvis (2010); Covington & McFall (2010); Zipf (1949)",
        ),
    ],
    "Tab 9: Collocation": [
        _entry(
            "Tab 9",
            "Union-Slot 2×2 Contingency Table & Expected Frequency (O11, O12, O21, O22, E11)",
            f"R<sub>1</sub> = |&cup;<sub>i</sub> W<sub>&pm;k</sub>(node<sub>i</sub>)|, &nbsp; E<sub>11</sub> = {_frac('R<sub>1</sub> &middot; C<sub>1</sub>', 'N')}, &nbsp; O<sub>12</sub> = R<sub>1</sub> &minus; O<sub>11</sub>, &nbsp; O<sub>21</sub> = C<sub>1</sub> &minus; O<sub>11</sub>",
            "Constructs a strict union of ±k window slots around all node occurrences (clamped to sentence boundaries) so overlapping windows never inflate O11 above C1 or R1.",
            "0 <= O11 <= min(R1, C1); mode='mask' retains slot offsets while skipping None collocates.",
            "Evert (2008); Brezina et al. (2015)",
        ),
        _entry(
            "Tab 9",
            "6 Collocation Association Measures (LogDice, MI, MI², MI³, T-Score, Signed G²)",
            f"LogDice = 14 + log<sub>2</sub> {_frac('2 &middot; O<sub>11</sub>', 'R<sub>1</sub> + C<sub>1</sub>')}, &nbsp; MI<sup>k</sup> = log<sub>2</sub> {_frac('O<sub>11</sub><sup>k</sup>', 'E<sub>11</sub>')}, &nbsp; T = {_frac('O<sub>11</sub> &minus; E<sub>11</sub>', _sqrt('O<sub>11</sub>'))}, &nbsp; G<sup>2</sup> = &pm;2 &sum; O<sub>ij</sub> ln {_frac('O<sub>ij</sub>', 'E<sub>ij</sub>')}",
            "Ranks collocates across heuristic scale-free LogDice, information-theoretic MI/MI2/MI3, hypothesis-testing T-score, and Dunning's signed log-likelihood G² with GraphColl radial layouts.",
            "O11 >= min_freq and E11 > 0; 0 * ln(0) terms evaluate to 0.",
            "Church & Hanks (1990); Dunning (1993); Rychlý (2008)",
        ),
    ],
    "Tab 10: TF-IDF & Reporter": [
        _entry(
            "Tab 10",
            "Sublinear TF, Smooth IDF, L2 Normalization & Corpus Evidence Reporter",
            f"tf' = 1 + ln(tf), &nbsp; idf = ln({_frac('1 + n<sub>docs</sub>', '1 + df')}) + 1, &nbsp; w<sub>t,d</sub> = {_frac('tf&#39; &middot; idf', _sqrt('&sum;<sub>k</sub> (tf&#39;<sub>k</sub> &middot; idf<sub>k</sub>)<sup>2</sup>'))}",
            "Extracts distinctive document keywords with optional PROPN exclusion and generates structured Data-Evidence Contract summary cards and multi-table ZIP research bundles.",
            "tf > 0; L2 norm > 0.",
            "Spärck Jones (1972); Salton & Buckley (1988)",
        ),
    ],
    "Tab 11: Explorer": [
        _entry(
            "Tab 11",
            "Programmatic CorpusLoader & TokenView Reproducibility Contract",
            "view = TokenView(text, field, filter_function_words, mode, punct) &rarr; quick_search(loader, term)",
            "Executes live corpus-wide quick searches and synthesizes a deterministic Python script reflecting the active global scope, secondary filter, and 32-combination TokenView state.",
            "Evict All RAM clears both CorpusLoader tables and global_payload_cache.",
            "Peng (2011); Corpus Analysis Toolkit v3 (2026)",
        ),
    ],
}


def get_help_catalog() -> dict[str, Any]:
    return HELP_CATALOG
