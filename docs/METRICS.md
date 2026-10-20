# METRICS.md — formulas, conventions, edge cases

Notation: `N` running words (non-punctuation, eligible in the chosen view), `V` types (case-folded,
Turkish `I/İ` aware), `V_m` number of types with frequency `m`, `V₁` hapax legomena.

## 1 · Views
| name | definition |
|---|---|
| field `tok` / `lem` | surface form / lemma |
| `raw` | all non-punctuation tokens (under `punct='drop'`) |
| `content` | only NOUN, VERB, ADJ, ADV, PROPN, NUM, X (function words hidden). Turkish also hides tokens whose morphological head (`morph.split('+')[1]`) ∈ {Postp, Conj, Det, Pron, Ques, Interj, Punc}. English uses UPOS only. Source: `passim_analysis/services/upos_filter_service.py` |
| `drop` / `mask` | function words removed from the sequence / kept in the sequence but ineligible as node, collocate or type |
| `punct` | 4 punctuation regimes (`drop`, `keep`, `strip`, `split`); see below |

### Punctuation Handling Regimes (Passim-Aligned Methodology)
Turkish texts processed with VNLP retain punctuation within words (e.g. `Türkiye'nin`, `Fred'`, `robot-bilim`, `1882'de`), and this retention is also present in lemmatized datasets (e.g. `fred'`, `ay'da`, `1882'`, `adı-her-neyse`). The toolkit provides 4 explicit options for `TokenView`, search, KWIC, collocations, and diversity:

| `punct` mode | Standalone Punctuation | In-Token Punctuation | Example Form (`field='tok'`) | Example Form (`field='lem'`) | Use Case |
|---|---|---|---|---|---|
| `drop` (default) | Excluded (`fcl != PUNCT`) | Preserved as-is | `türkiye'nin`, `robot-bilim` | `türkiye'nin`, `robot-bilim` | Standard corpus analysis without punctuation inflation |
| `keep` | Included (`fcl == PUNCT` kept) | Preserved as-is | `türkiye'nin`, `?`, `.` | `türkiye'nin`, `?`, `.` | Studying punctuation syntax, dialogue marks, rhetorical questions |
| `strip` | Excluded | Collapsed / stripped (Passim `remove_punctuations`) | `türkiyenin`, `robotbilim`, `fred` | `türkiyenin`, `robotbilim`, `fred` | Search and vocabulary counts matching unpunctuated variants without word splitting |
| `split` | Excluded | Retokenized / decomposed (Passim `retokenizer`) | `['türkiye', 'nin']`, `['robot', 'bilim']` | `['türkiye', 'nin']`, `['robot', 'bilim']` | Stem matching, sub-component keyword retrieval (`robot`, `bilim`), decompounded lexical density |

The function-word share is **measured**, not assumed (see Chapter 4: ≈ 45–53 % English, ≈ 18–24 % Turkish).

## 2 · Normalised frequency and dispersion
* `per10k = 10 000 · hits / N`.
* Chunks: each text is split into `n = 10` equal position-slices; chunk rate = `10 000 · hits_k / N_k`.
* **Juilland's D** = `1 − V/√(n−1)`, `V = σ/μ` (population σ over the `n` counts); 1 = even, 0 = one chunk.
  Reported both *across texts* (rates per text) and *within text* (mean over texts with ≥ 1 hit).
* Pearson r (scipy), Spearman ρ (average ranks for ties), cosine = `x·y/(‖x‖‖y‖)` (0 if a vector is zero).
  Constant vectors → Pearson/Spearman = NaN.
* **Benjamini–Hochberg** q-values over all word pairs: `q_(i) = min_{j ≥ i} (m/j) p_(j)`, capped at 1.
* Bootstrap CI: percentile, 1 000–2 000 resamples, fixed seed 13.

## 3 · Collocation (window statistics)
* Slots: union of window positions around all node occurrences (node's own position excluded from its own
  window; sentence-clamped by default). `R1` = eligible slots, `O11` = collocate count in slots, `C1` =
  collocate frequency in the view, `E11 = R1·C1/N`. Table `[[O11, R1−O11],[C1−O11, N−R1−C1+O11]]`.
* `MI = log₂(O11/E11)`, `MI² = log₂(O11²/E11)`, `MI³ = log₂(O11³/E11)`,
  `T = (O11−E11)/√O11`,
  `G² = 2 Σ O_ij ln(O_ij/E_ij)` (0·ln0 = 0, signed negative when `O11 < E11`; p from χ²₁),
  `LogDice = 14 + log₂(2·O11/(f_node + C1))` (Rychlý 2008, raw frequencies).
* **Deliberate deviation from the draft plan:** the plan's `N_span = N·S` cancelled `S` incorrectly; the
  standard `E11 = R1·C1/N` is used instead. Log-Dice uses raw frequencies, not window slots.

## 4 · Lexical diversity
| metric | formula | edge cases |
|---|---|---|
| TTR | V/N | |
| Guiraud R | V/√N | |
| CTTR | V/√(2N) | |
| Herdan C | ln V / ln N | NaN if N = 1 |
| Dugast U | ln²N / (ln N − ln V) | NaN if V = N |
| Maas a² | (ln N − ln V)/ln²N | NaN if N = 1 |
| Yule K | 10⁴ (Σ m² V_m − N)/N² | |
| Simpson D | Σ n(n−1) / (N(N−1)) | NaN if N ≤ 1 |
| Honoré R | 100 ln N / (1 − V₁/V) | NaN if V₁ = V |
| Hapax % (types / tokens) | 100 V₁/V, 100 V₁/N | |
| STTR | mean TTR of consecutive 1 000-token blocks; trailing partial block dropped | N < 1 000 → TTR + warning |
| MATTR(w) | mean TTR of every window of w tokens (O(N) sliding update); w ∈ {50,100,500} | N < w → TTR + warning |
| MTLD | per direction: N / factors, factor closes when running TTR ≤ 0.72; partial factor (1 − TTR)/(1 − 0.72); result = mean(forward, backward) | N < 2 → NaN |
| HD-D | McCarthy & Jarvis (2010): draw size 42; sum over types of `(1 - hypergeom.pmf(0, N, n_i, 42)) / 42` | N < 42 → NaN |

*Deviation from the plan:* MTLD is the standard McCarthy & Jarvis (2010) mean of the two directional values
(not `N/mean(F)`). Reference implementation for `#LancsBox`: Brezina, Weill-Tessier & McEnery (2021).

## 5 · Alignment
Cardinality = `(len(sentence_map_eng[ai]), len(sentence_map_tur[ai]))` → 1:1, 1:N, N:1, N:M, omission `(n,0)`,
addition `(0,m)`. `R_sent = Σ n_tur / Σ n_eng`; `word_ratio`, `char_ratio` from the alignment text
(whitespace words / characters).

## 6 · POS
Lexical density = `(NOUN+VERB+ADJ+ADV)/N_nonpunct · 100` (and a variant including PROPN); noun/verb ratio;
Turkish `deverbal_share` = tokens whose Oflazer analysis contains `+Inf` or `Part`. Group comparison:
per-UPOS mean difference with bootstrap CI over **texts**, pooled χ² with Cramér's V (descriptive for n = 3–5).

## 7 · TF-IDF
scikit-learn defaults reproduced by hand: `tf = 1 + ln(count)`, `idf = ln((1+n)/(1+df)) + 1`, L2 norm. English and
Turkish fitted separately; `exclude_pos={'PROPN'}` removes names; `n_chunks` splits texts into pseudo-documents.

## 8 · Dependency trees
`dir = 'left'` when the dependent is left of its head (displaCy convention). Heads that are 0, out of range or the
token itself produce no arc. English ClearNLP→UD *label* mapping only (`dobj→obj`, `nsubjpass→nsubj:pass`, `relcl→acl:relcl`, …).

## 9 · Cache
Key = `sha256([SCHEMA_VERSION, namespace, args…])[:20]`, with the source file's `size:mtime_ns` among the args.
Parquet for tables, JSON for small dicts, atomic `os.replace`, LRU eviction above 2 GB.

## 10 · References
Baker 1993 · Benjamini & Hochberg 1995 · Biber 1988 · Brezina, McEnery & Wattam 2015 · Brezina, Weill-Tessier &
McEnery 2021 · Carroll 1964 · Church & Hanks 1990 · Church et al. 1991 · Covington & McFall 2010 · Daille 1994 ·
Dugast 1979 · Dunning 1993 · Firth 1957 · Gries 2008 · Guiraud 1954 · Halliday 1985 · Herdan 1960 · Honoré 1979 ·
Juilland & Chang-Rodríguez 1964 · Luhn 1960 · Maas 1972 · McCarthy & Jarvis 2010 · Nivre et al. 2016 · Rychlý 2008 ·
Simeoni 1998 · Simpson 1949 · Sinclair 1991 · Spärck Jones 1972 · Tesnière 1959 · Toury 2012 · Ure 1971 · Yule 1944.
(Full list in the notebook; entries are unverified against Zotero until logged in the thesis truth table.)
