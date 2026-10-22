# 15 · Mathematical Formulas, `drop` vs `mask` Algebra & Sub-Component Specifications

## 1. Algorithmic Distinction: `mode='drop'` vs `mode='mask'`

The global `TokenView` matrix exposes four orthogonal switches:
$$V_{\text{matrix}} = \{\text{tok}, \text{lem}\} \times \{\text{False}, \text{True}\} \times \{\text{drop}, \text{mask}\} \times \{\text{drop}, \text{keep}, \text{strip}, \text{split}\}$$

When `filter_function_words=True`, closed-class UPOS tags (`ADP`, `AUX`, `CCONJ`, `DET`, `NUM`, `PART`, `PRON`, `SCONJ`, `PUNCT`, `SYM`, `X`) and Turkish Oflazer morphological function heads (`Postp`, `Conj`, `Det`, `Pron`, `Ques`, `Interj`, `Punc`) are marked ineligible (`eligible[i] = False`):

1. **Bag-of-Words / Type-Token / Frequency Estimators** (`InventoryMemoryService`, `InventoryTablesService`, `PosService`, `PosMatrixService`, `DiversityService` global metrics, `TfidfService`):
   - Always iterate over `view.analysed()`, which strips `None` placeholders in both `mode='drop'` and `mode='mask'`.
   - Consequently, `N`, `V`, `TTR`, `Guiraud_R`, `Yule_K`, `Simpson_D`, `MTLD`, and `HD_D` are invariant to `drop` vs `mask` and never count `None` as a lexical type.
2. **Positional / Sliding-Window / Span Estimators** (`DiversityService.masked_mattr_series`, `MATTR_50`, `MATTR_100`, `MATTR_500`, `CollocationService`, `ConcordanceService`):
   - Under `mode='drop'`, ineligible tokens are physically removed before windowing, compacting content words into adjacent positions:
     $$S_{\text{drop}} = [w_i \mid \text{eligible}(w_i) = \text{True}]$$
   - Under `mode='mask'`, ineligible tokens remain at their original running-word positions as `None` placeholders:
     $$S_{\text{mask}}[i] = \begin{cases} w_i & \text{if } \text{eligible}(w_i) = \text{True} \\ \text{None} & \text{otherwise} \end{cases}$$
   - For sliding-window $\text{MATTR}_W$, each positional window of span $W$ computes the local type-token ratio over non-null content words inside that span:
     $$\text{MATTR}_{W,\text{mask}} = \frac{1}{N_{\text{raw}} - W + 1} \sum_{j=0}^{N_{\text{raw}} - W} \frac{|\{x \in S_{\text{mask}}[j : j+W] \mid x \neq \text{None}\}|}{|\{i \in [j, j+W) \mid S_{\text{mask}}[i] \neq \text{None}\}|}$$
   - For Union-Slot collocations (`collocation.py`), window spans $\pm k$ are measured in original running-word token offsets around each node occurrence while skipping `None` placeholders as candidate collocates.

---

## 2. Tab-by-Tab Mathematical Reference Catalog

### 2.1 Tab 1: Corpus Inventory & Lexical Volume
- **Scope Token Sum**: $N_{\text{scope}} = \sum_{t \in \text{Scope}} |\text{view}_t.\text{analysed}()|$
- **Turkish Lemma Apostrophe Remediation (`clean_lemma`)**: Strips Turkish inflectional suffixes after apostrophe variants (`'`, `’`, `‘`, `` ` ``, `´`, `ʼ`, `ʻ`) while preserving internal compound hyphens (`bilim-kurgu'nun` $\to$ `bilim-kurgu`).

### 2.2 Tab 2: Translation Alignment & Length-Delta Metrics
- **Sentence Ratio**: $R_{\text{sent}} = \frac{S_{\text{TR}}}{S_{\text{EN}}}$
- **Token Expansion Ratio**: $\bar{r}_{\text{exp}} = \frac{1}{M} \sum_{i=1}^{M} \frac{L_{\text{TR},i}}{L_{\text{EN},i}}$ across $M$ non-empty aligned groups.
- **1:1 Cardinality Share**: $P_{1:1} = \frac{|\{i \mid S_{\text{EN},i} = 1 \land S_{\text{TR},i} = 1\}|}{M} \times 100\%$
- **OLS 1:1 Length Slope (`Şekil 1B`)**: $\hat{\beta}_1 = \frac{\sum_{i \in \Omega_{1:1}} w_{\text{EN},i} w_{\text{TR},i}}{\sum_{i \in \Omega_{1:1}} w_{\text{EN},i}^2}$

### 2.3 Tab 3: NDA Parallel Corpora & Layer Hierarchy
- **Layer Precedence**: Top-Layer `IRREALIA` (`SCIFI_*`) annotations supersede Layer 0 `REALIA` (`NER_*`) spans when rendering token pills.
- **Tripartite Dictionary State Machine**: Tracks `[G: ±, P: ±]` across `linked` bilingual pairs, `single_eng` source irrealia, and `single_tur` target coinages.

### 2.4 Tab 4: Comparative POS & Morphosyntactic Homogeneity
- **Relative UPOS Share & Divergence**:
  $$p_u = \frac{c_u}{N} \times 100\%, \quad \Delta\text{pp}_u = p_{\text{TR},u} - p_{\text{EN},u}$$
- **Lexical Density & Noun/Verb Ratio**:
  $$\text{LD} = \frac{c_{\text{NOUN}} + c_{\text{VERB}} + c_{\text{ADJ}} + c_{\text{ADV}}}{N} \times 100\%, \quad \text{N/V} = \frac{c_{\text{NOUN}}}{c_{\text{VERB}}}$$
- **Pearson's $\chi^2$ & Cramér's $V$**:
  $$\chi^2 = \sum_{i=1}^{R} \sum_{j=1}^{C} \frac{(O_{ij} - E_{ij})^2}{E_{ij}}, \quad V = \sqrt{\frac{\chi^2}{N \cdot \min(R-1, C-1)}}$$

### 2.5 Tab 5: Universal Dependencies Directed Arcs
- **Syntactic Dependency Graph**: $G = (V_{\text{tokens}}, E_{\text{arcs}})$ with directed edges $e = (w_{\text{head}} \xrightarrow{\text{deprel}} w_{\text{dep}})$ and optional function-word dimming (`opacity: 0.4`).

### 2.6 Tab 6: 5-View KWIC Concordance
- **Relative Frequency per 10,000 Words**: $\text{Rate}_{10\text{k}} = \frac{f_q}{N} \times 10{,}000$
- **Punctuation Sensitivity Range**: $\Delta_{\max-\min} = \max_{p \in \{\text{drop,keep,strip,split}\}} f_q(p) - \min_{p} f_q(p)$

### 2.7 Tab 7: Batch Dispersion & Correlation Matrix
- **Juilland's $D$**:
  $$D = 1 - \frac{\text{CV}}{\sqrt{k - 1}}, \quad \text{CV} = \frac{\sigma_v}{\mu_v}, \quad \sigma_v = \sqrt{\frac{1}{k}\sum_{j=1}^{k}(v_j - \mu_v)^2}$$
- **Benjamini–Hochberg FDR $q$-value**:
  $$q_{(i)} = \min_{j \ge i} \left(1.0,\; \frac{m \cdot p_{(j)}}{j}\right)$$

### 2.8 Tab 8: 22 LancsBox-X Lexical Diversity Metrics
- **Algebraic Transformations**:
  $$\text{TTR} = \frac{V}{N}, \quad R_{\text{Guiraud}} = \frac{V}{\sqrt{N}}, \quad \text{CTTR} = \frac{V}{\sqrt{2N}}, \quad C_{\text{Herdan}} = \frac{\ln V}{\ln N}, \quad a^2_{\text{Maas}} = \frac{\ln N - \ln V}{(\ln N)^2}, \quad U_{\text{Dugast}} = \frac{1}{a^2_{\text{Maas}}}$$
- **Frequency Spectrum Estimators**:
  $$K_{\text{Yule}} = 10^4 \frac{\sum_i i^2 V_i - N}{N^2}, \quad D_{\text{Simpson}} = \sum_i \frac{V_i \cdot i(i-1)}{N(N-1)}, \quad R_{\text{Honoré}} = \frac{100 \ln N}{1 - V_1/V}, \quad S_{\text{Sichel}} = \frac{V_2}{V}, \quad M_{\text{Michéa}} = \frac{V}{V_2}$$
- **Information & Sequential Estimators**: Shannon $H = -\sum_{w} p_w \log_2 p_w$, $\text{STTR}_{1000}$, $\text{MATTR}_{50/100/500}$, bidirectional $\text{MTLD}_{0.72}$, $\text{HD-D}_{42}$, and Zipf OLS $\log_{10} f = \alpha + \beta \log_{10} r$.

### 2.9 Tab 9: Union-Slot Collocation Contingency & 6 Association Measures
- **Union-Slot Contingency**: $R_1 = |\bigcup_{i} W_{\pm k}(\text{node}_i)|$, $E_{11} = \frac{R_1 C_1}{N}$, $O_{12} = R_1 - O_{11}$, $O_{21} = C_1 - O_{11}$, $O_{22} = N - R_1 - C_1 + O_{11}$.
- **Association Scores**:
  $$\text{LogDice} = 14 + \log_2 \frac{2 O_{11}}{R_1 + C_1}, \quad \text{MI}^k = \log_2 \frac{O_{11}^k}{E_{11}} \; (k \in \{1,2,3\}), \quad T = \frac{O_{11} - E_{11}}{\sqrt{O_{11}}}, \quad G^2 = \operatorname{sgn}(O_{11} - E_{11}) \cdot 2 \sum_{i,j} O_{ij} \ln \frac{O_{ij}}{E_{ij}}$$

### 2.10 Tab 10: Sublinear TF-IDF & Structured Corpus Reporter
- **Sublinear TF & Smooth IDF**:
  $$\text{tf}'(t,d) = 1 + \ln(\text{tf}(t,d)), \quad \text{idf}(t) = \ln\left(\frac{1 + n_{\text{docs}}}{1 + \text{df}(t)}\right) + 1, \quad w_{t,d} = \frac{\text{tf}'(t,d)\,\text{idf}(t)}{\sqrt{\sum_{k} (\text{tf}'(k,d)\,\text{idf}(k))^2}}$$
