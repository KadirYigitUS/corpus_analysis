"""Bölüm 10–13 ve Kaynakça (Türkçe): Eşdizimlilik, TF-IDF, raporlayıcı, etkileşimli gezgin ve kaynakça."""

from nbcells_tr import (
    Cell,
    akademik_not,
    alistirmalar,
    bolum_basligi,
    code,
    komut_kilavuzu,
    md,
    tuzaklar,
)


def chapters() -> list[Cell]:
    c: list[Cell] = []

    # ----------------------------------------------------------------- Bölüm 10
    c += [bolum_basligi(10, "Eşdizimlilik ve Birlikte Geçiş Ölçütleri", 35,
                         ["Düğüm ve eşdizimli sözcük için 2×2'lik olasılık tablosunu (contingency table) oluşturabilme",
                          "MI, MI², MI³, T-skoru, olabilirlik oranı (G²) ve Log-Dice ölçütlerini elle hesaplayabilme",
                          "Çekim gücü ile istatistiksel kanıtı ayırt edebilme (GraphColl dağılım grafiği)",
                          "Birleşimli aralık yuva sayımı (union-slot) ile ikili birlikte geçiş farkını kavrama"],
                         "Bölüm 6–7", "Hangi sözcükler düğüm sözcükle tesadüfün ötesinde anlamlı bir sıklıkla bir araya gelmektedir?"),
          md("""
    ### 10.1 Kuramsal Çerçeve
    J. R. Firth'ün (1957) ünlü ilkesi: *“Bir sözcüğü, birlikte arkadaşlık ettiği sözcüklerden tanırsınız.”*
    Bir **düğüm sözcük (node)** ve bir aralık penceresi (sol $L$, sağ $R$) belirleyelim:

    - $N$: Metindeki / derlemdeki toplam akan sözcük sayısı,
    - $R_1$: Pencere **yuvaları** (düğüm pencerelerinin kapsadığı toplam konumlar, düğümün kendisi hariç).
      Araç setimizde çakışan pencereler her konumu **bir kez** sayar (birleşimli yuvalar / union slots).
      Bu yöntem iki yakın düğümün arasındaki sözcükleri çift saymaz ve $O_{11} \le R_1$ ile $O_{11} \le C_1$ güvencesi verir.
    - $C_1$: Aday eşdizimli sözcüğün tüm metindeki toplam sıklığı,
    - $O_{11}$: Aday sözcüğün düğüm penceresi yuvaları *içinde* gözlenen sıklığı ($O = \\text{observed}$),
    - $E_{11} = \\frac{R_1 \cdot C_1}{N}$: Bağımsız rastgele dağılım varsayımı altında beklenen birlikte geçiş sayısı ($E = \\text{expected}$),

    $2 \\times 2$ olasılık tablosu şu şekilde kurulur:

    | | Pencere İçinde ($W$) | Pencere Dışında ($\\neg W$) | Toplam |
    |---|---|---|---|
    | **Aday Sözcük ($C$)** | $O_{11}$ | $O_{12} = C_1 - O_{11}$ | $C_1$ |
    | **Diğer Sözcükler ($\\neg C$)** | $O_{21} = R_1 - O_{11}$ | $O_{22} = N - R_1 - C_1 + O_{11}$ | $N - C_1$ |
    | **Toplam** | $R_1$ | $N - R_1$ | $N$ |

    Standart eşdizim ve bağıntı ölçütleri:

    | Ölçüt | Formül | Özellikler ve Tercih Eğilimi |
    |---|---|---|
    | **MI** (Church & Hanks 1990) | $\log_2 \\frac{O_{11}}{E_{11}}$ | Birliktelik gücü (etki büyüklüğü); düşük sıklıklı nadir sözcüklere aşırı duyarlıdır |
    | **MI²** (Daille 1994) | $\log_2 \\frac{O_{11}^2}{E_{11}}$ | Düşük sıklık yanlılığını dengeler |
    | **MI³** (Daille 1994) | $\log_2 \\frac{O_{11}^3}{E_{11}}$ | Sık tekrarlanan güçlü kalıpları öne çıkarır |
    | **T-skoru** (Church vd. 1991) | $\\frac{O_{11} - E_{11}}{\sqrt{O_{11}}}$ | İstatistiksel kesinlik/kanıt; sık geçen dilbilgisel ortakları öne çıkarır |
    | **G²** (Dunning 1993) | $2 \sum_{i,j} O_{ij} \ln \\frac{O_{ij}}{E_{ij}}$ | İşaretli olabilirlik oranı testi; pozitif = çekim, negatif = itim |
    | **Log-Dice** (Rychlý 2008) | $14 + \log_2 \\frac{2 O_{11}}{f_{\\text{düğüm}} + C_1}$ | Derlem boyutundan bütünüyle bağımsızdır; kusursuz eşdizim için en çok 14 değerini alır |

    **Güç ile Kanıtın Ayrıştırılması (GraphColl Yaklaşımı, Brezina vd. 2015).**
    MI metriği *etki büyüklüğünü (gücü)* ölçerken, $G^2$ metriği *örneklem büyüklüğüne dayalı istatistiksel kanıtı*
    (kesinliği) ölçer. MI ve $G^2$ değerlerini iki eksende gösteren bir dağılım grafiği dört ana bölgeyi ortaya koyar:
    nadir özel birliktelikler (yüksek MI, düşük $G^2$), merkezi izleksel eşdizimler (yüksek MI, yüksek $G^2$),
    dilbilgisel rutinler (düşük MI, yüksek $G^2$) ve rastgele gürültü.

    ### 10.2 Elle Doğrulanabilir Oyuncak Örnek
    Verilenler: $N = 1000$, $R_1 = 100$, $C_1 = 20$, $O_{11} = 10$, $f_{\\text{düğüm}} = 50$:
    1. $E_{11} = \\frac{100 \\times 20}{1000} = 2.0$
    2. $\\text{MI} = \log_2(10 / 2) = \log_2(5) \\approx 2.322$
    3. $\\text{MI}^2 = \log_2(100 / 2) = \log_2(50) \\approx 5.644$
    4. $\\text{MI}^3 = \log_2(1000 / 2) = \log_2(500) \\approx 8.966$
    5. $\\text{T-skoru} = \\frac{10 - 2}{\sqrt{10}} = \\frac{8}{3.1623} \\approx 2.530$
    6. $\\text{Log-Dice} = 14 + \log_2 \left(\\frac{20}{50 + 20}\\right) = 14 + \log_2(0.2857) = 14 - 1.8074 \\approx 12.193$
    """),
          komut_kilavuzu("Eşdizim Komutları", [
              ("collocation.association_table([o11], [c1], r1, n, f_node)", "Verilen sayımlar için 6 temel eşdizim ölçütünü hesaplama", "collocation.association_table([10], [20], 100, 1000, 50)"),
              ("collocation.collocates(view, 'node', left=5, right=5, min_freq=5)", "G2/MI/LogDice değerlerine göre sıralanmış eşdizim tablosu çıkarma", "collocation.collocates(view, 'robot', 5, 5, min_freq=5, sort_by='G2')"),
              ("viz.collocation_scatter(tab, 'node', x='MI', y='G2')", "Güç (MI) ve kanıt (G2) dağılım grafiğini çizdirme", "viz.collocation_scatter(tab, 'robot')"),
              ("TokenView(text, 'lem', filter_function_words=True, mode='drop')", "İzleksel eşdizimler için içerik sözcüğü görünümü", "TokenView(text, 'lem', True, 'drop')"),
              ("nltk_adapter.nltk_collocations(view, n=10, min_freq=5)", "NLTK bigram eşdizim ölçütleriyle çapraz kontrol", "nltk_adapter.nltk_collocations(view)"),
          ]),
          code("""
    # Elle doğrulanan oyuncak örnek kontrolü
    toy = collocation.association_table([10], [20], r1=100, n=1000, f_node=50)
    display(toy.round(3))
    """),
          code("""
    # Selma Mine'nin Ben, Robot çevirisinde 'robot' sözcüğü için eşdizimleri çıkarma
    br = loader.load_text("BR-SM")
    print("İncelenen metin:", loader.registry.display(br))
    node_view = TokenView(br, "lem", False, "drop")
    tab = collocation.collocates(node_view, "robot", left=5, right=5, min_freq=5, sort_by="G2")
    print("Olasılık tablosu parametreleri:", tab.attrs)
    show_table(tab.round(3), page_size=20, title="'robot' Eşdizimlileri — Ben, Robot (20 satır/sayfa, sıralanabilir)")
    """),
          code("""
    # GraphColl tarzı güç (MI) vs kanıt (G2) dağılım grafiği
    fig = viz.collocation_scatter(tab, "robot", x="MI", y="G2")
    plt.show()

    # Farklı ölçütlere göre en üst sırada yer alan eşdizimli ortakları karşılaştırma
    for measure in ("MI", "T", "LogDice", "G2"):
        top_words = tab.sort_values(measure, ascending=False)["collocate"].head(8).tolist()
        print(f"{measure:8s} → {top_words}")
    """),
          md("""
    #### Pencere Genişliği, Sınır Kenetlenmesi ve İçerik Sözcüğü Görünümü
    Pencere aralığı doğrudan *araştırma sorusuna* bağlıdır:
    - Dar pencereler ($\pm 1, \pm 2$) **biçimsözdizimsel** yapıyı ve yakın yönetimi (ilgeçler, yardımcı eylemler, niteleyiciler) yakalar.
    - Geniş pencereler ($\pm 5, \pm 10$) **izleksel/söylemsel** birliktelikleri ortaya çıkarır.
    - İşlevsel sözcükler filtrelendiğinde **`drop`** mesafeyi *içerik sözcükleri* üzerinden ölçer; **`mask`** ise akan sözcük konumlarını korur.
    """),
          code("""
    def top_collocates(view, left, right, sort_by="G2"):
        res = collocation.collocates(view, "robot", left=left, right=right, min_freq=5, sort_by=sort_by)
        return res["collocate"].head(8).tolist()

    print("Ham pencere ±2    :", top_collocates(TokenView(br, "lem", False), 2, 2))
    print("Ham pencere ±10   :", top_collocates(TokenView(br, "lem", False), 10, 10))
    print("İçerik 'drop'     :", top_collocates(TokenView(br, "lem", True, "drop"), 5, 5))
    print("İçerik 'mask'     :", top_collocates(TokenView(br, "lem", True, "mask"), 5, 5))
    """),
          md("#### NLTK ile Çapraz Kontrol: Bitişik İkili (Bigram) Eşdizimleri"),
          code("""
    display(nltk_adapter.nltk_collocations(TokenView(br, "lem", True), n=10, min_freq=5, measure="likelihood_ratio"))
    display(nltk_adapter.top_ngrams(TokenView(br, "lem", True), n=2, top=8))
    br.evict()
    """),
          tuzaklar(["Karakter özel adları (*Susan Calvin*, *Mike Donovan*) ham eşdizim listelerini domine edebilir: izleksel sözvarlığını görmek için özel adları filtreleyin (`exclude_pos={'PROPN'}`).",
                    "Pencere yuvaları her konum için bir kez sayılır (union slots): bu kural çakışan pencerelerin aynı sözcüğü mükerrer saymasını önler ve $O_{11} \le C_1$ tutarlılığını sağlar.",
                    "$G^2$ istatistiği işaretlidir: negatif değerler itimi (sözcüklerin tesadüfen beklenenden *daha az* sıklıkla bir araya geldiğini) gösterir."]),
          alistirmalar([("Isaac Asimov'un *I, Robot* romanında `human` (insan) sözlükbirimi ile Log-Dice değerine göre en güçlü eşdizim oluşturan İngilizce sözcükler hangileridir (±4)?",
                         "```python\nir = loader.load_text('IR-IA')\nprint(loader.registry.display(ir))\nv = TokenView(ir, 'lem', True)\n"
                         "display(collocation.collocates(v, 'human', 4, 4, min_freq=3, sort_by='LogDice').head(10))\nir.evict()\n```")]),
          akademik_not("""
          **Firthçi Anlambilim ve Repertuar Modellemesi (Firth 1957; Sinclair 1991):**
          Çoğuldizge kuramında (Even-Zohar 1990), eşdizimsel profiller çeviri metinlerin yabancı sözcük
          öbeklerini (*kalklar*, örn. *pozitronik beyin*) erek edebiyata aktarıp aktarmadığını ya da yerli
          dilsel kalıplara uyarlayıp uyarlamadığını belgeler. Log-Dice (Rychlý 2008), toplam derlem
          boyutundan etkilenmediği için farklı uzunluktaki yazar-çevirmen yapıtlarını karşılaştırmak adına
          en güvenilir ölçüttür.
          """),
          ]

    # ----------------------------------------------------------------- Bölüm 11
    c += [bolum_basligi(11, "TF-IDF ve Ayırt Edici Sözvarlığı (Keyness)", 20,
                         ["TF-IDF ağırlıklarını elle hesaplayabilme ve scikit-learn ile birebir eşleştiğini doğrulayabilme",
                          "İngilizce ve Türkçe alt derlemleri kuramsal gereklilikle ayrı ayrı eğitebilme",
                          "Ayırt edicilik ısı haritalarını okuyabilme ve özel adları eleyerek tür sözvarlığını ortaya çıkarabilme"],
                         "Bölüm 0–2", "Derlemdeki her metni diğerlerinden en çok ayıran özgün sözcükler hangileridir?"),
          md("""
    ### 11.1 Kuramsal Çerçeve
    TF-IDF (Spärck Jones 1972), sözcükleri metin içi sıklıkları (**TF**) ile metinlerarası ayırt ediciliklerinin
    (**IDF**) çarpımıyla ağırlıklandırır. Scikit-learn kütüphanesiyle birebir eşleşen algoritmamız şu bileşenleri kullanır:

    - **Alt-doğrusal TF**: $\\text{count} > 0$ için $\\text{TF}(t, d) = 1 + \ln(\\text{count}(t, d))$ (tekrarların azalan marjinal etkisi).
    - **Düzeltilmiş (Smooth) IDF**: $\\text{IDF}(t) = \ln\left(\\frac{1 + N}{1 + \\text{DF}(t)}\\right) + 1$; burada $N$ toplam metin sayısı, $\\text{DF}(t)$ ise terimin geçtiği metin sayısıdır.
    - **L2 Normu**: $\\vec{v}_{\\text{norm}} = \\frac{\\vec{v}}{\|\\vec{v}\|_2}$ metin uzunluğunun anahtarlık ağırlıklarını çarpıtmasını önler.

    İngilizce ve Türkçe kökten farklı dilbilgisel ve biçimbilimsel yapılara sahip olduğundan, iki dil **ayrı alt derlemler**
    olarak modellenir.

    ### 11.2 Elle Doğrulanabilir Oyuncak Örnek — Elle Hesaplama vs scikit-learn
    Üç belge: $d_1 = [a, b, b]$, $d_2 = [a, c]$, $d_3 = [c, c, d]$ ($N = 3$).
    - $a$: $d_1, d_2$ belgelerinde geçer $\Rightarrow \\text{DF} = 2 \Rightarrow \\text{IDF} = \ln(4/3) + 1 \\approx 1.2877$
    - $b$: $d_1$ belgesinde geçer $\Rightarrow \\text{DF} = 1 \Rightarrow \\text{IDF} = \ln(4/2) + 1 = \ln(2) + 1 \\approx 1.6931$
    - $c$: $d_2, d_3$ belgelerinde geçer $\Rightarrow \\text{DF} = 2 \Rightarrow \\text{IDF} = \ln(4/3) + 1 \\approx 1.2877$
    - $d$: $d_3$ belgesinde geçer $\Rightarrow \\text{DF} = 1 \Rightarrow \\text{IDF} = \ln(4/2) + 1 = \ln(2) + 1 \\approx 1.6931$

    $d_1$ içinde: $\\text{tf}(a) = 1 + \ln(1) = 1.0$; $\\text{tf}(b) = 1 + \ln(2) \\approx 1.6931$.
    Norm öncesi ağırlıklar: $w(a) = 1.0 \\times 1.2877 = 1.2877$; $w(b) = 1.6931 \\times 1.6931 \\approx 2.8667$.
    L2 normu: $\sqrt{1.2877^2 + 2.8667^2} = \sqrt{1.6582 + 8.2180} = 3.1427$.
    Normalize $d_1$: $a \\approx 0.410$, $b \\approx 0.912$.
    """),
          komut_kilavuzu("TF-IDF Komutları", [
              ("tfidf.tfidf_manual(docs)", "Belge listelerinden alt-doğrusal düzeltilmiş TF-IDF tablosu üretme", "tfidf.tfidf_manual([['a', 'b'], ['b', 'c']])"),
              ("tfidf.TfidfAnalyzer()", "Derlem TF-IDF çözümleyicisini başlatma", "analyzer = tfidf.TfidfAnalyzer()"),
              ("analyzer.fit(texts, field='lem', filter_function_words=True)", "Alt derlemi eğiterek ayırt edicilik vektörlerini çıkarma", "res = analyzer.fit(texts, 'lem', True)"),
              ("res.top_terms(doc_id, n=10)", "Belirli bir metin için en ayırt edici n terimi listeleme", "res.top_terms('BR-SM', 10)"),
              ("res.dense_top(top_k=5)", "Tüm belgeler boyunca en üstün terimlerin yoğun matrisini üretme", "res.dense_top(5)"),
              ("viz.heatmap(df, title)", "Metinler arası anahtarlık ısı haritasını çizdirme", "viz.heatmap(matrix, 'Keyness')"),
          ]),
          code("""
    # Elle hesaplama ile scikit-learn çıktısının birebir eşleşme testi
    docs = [["a", "b", "b"], ["a", "c"], ["c", "c", "d"]]
    manual = tfidf.tfidf_manual(docs)
    display(manual.round(3))

    from sklearn.feature_extraction.text import TfidfVectorizer
    skl = TfidfVectorizer(analyzer=lambda x: x, sublinear_tf=True).fit_transform(docs).toarray()
    print("scikit-learn ile birebir esitlik:", np.allclose(skl, manual[sorted(manual.columns)].to_numpy()))
    """),
          code("""
    # İngilizce ve Türkçe alt derlemleri ayrı ayrı çözümleme
    T = tfidf.TfidfAnalyzer()
    en = T.fit(loader.load_all_english(), "lem", filter_function_words=True)
    tr = T.fit(loader.load_all_turkish(), "lem", filter_function_words=True)

    print("--- En Ayırt Edici İngilizce Sözlükbirimler ---")
    for d in en.doc_ids[:3]:
        full_title = loader.registry.title_of(d)
        print(f"{d} ({full_title}): {en.top_terms(d, 6)['term'].tolist()}")

    print()
    print("--- En Ayırt Edici Türkçe Sözlükbirimler ---")
    for d in tr.doc_ids[:3]:
        full_title = loader.registry.title_of(d)
        print(f"{d} ({full_title}): {tr.top_terms(d, 6)['term'].tolist()}")
    """),
          md("""
    Görüldüğü üzere metindeki **karakter özel adları** (*Powell*, *Donovan*, *Arctor*) listelerin başında yer alır.
    **İzleksel ve edebi sözvarlığını** ortaya çıkarmak için özel adlar elenir (`exclude_pos={'PROPN'}`):
    """),
          code("""
    tr_np = T.fit(loader.load_all_turkish(), "lem", filter_function_words=True, exclude_pos={"PROPN"})
    fig = viz.heatmap(tr_np.dense_top(5).T, "TF-IDF Ayırt Edici Sözvarlığı (Türkçe Bilimkurgu Metinleri, Özel Adlar Hariç)",
                      cmap="mako_r", fmt=".2f", annotate=False)
    plt.show()

    for d in tr_np.doc_ids:
        print(f"{d:8s} ({loader.registry.title_of(d)[:30]}...) → {tr_np.top_terms(d, 6)['term'].tolist()}")
    """),
          md("""
    Az sayıda belgeden oluşan derlemlerde (5 İngilizce / 8 Türkçe metin) IDF değerleri kaba kalabilir.
    Metinleri daha küçük parçalara dilimleyerek (`n_chunks=5`) daha geniş bir belge evreni benzetimi yapılabilir:
    """),
          code("""
    ch = T.fit(loader.load_all_turkish(), "lem", filter_function_words=True, n_chunks=5, exclude_pos={"PROPN"})
    print(f"Toplam {len(ch.doc_ids)} adet dilimlenmiş sanal belge üretildi.")
    print("BR-SM (Ben, Robot) ilk dilimi:", ch.top_terms("BR-SM#1", 6)["term"].tolist())
    """),
          tuzaklar(["Her belgede geçen sözcükler $\\text{IDF} \\approx 1.0$ alır ve neredeyse sıfır anahtarlık ağırlığına sahip olur — bu tasarımın doğal sonucudur.",
                    "TF-IDF keşifsel bir ağırlıklandırma yöntemidir, bir istatistiksel hipotez testi değildir: iki derlem arasında istatistiksel anlamlılık iddia ederken $G^2$ anahtarlık testini tercih edin."]),
          alistirmalar([("Philip K. Dick'in *A Scanner Darkly* yapıtında geçen en ayırt edici 8 İngilizce sözlükbirim hangileridir (özel adlar hariç)?",
                         "```python\nr = T.fit(loader.load_all_english(), 'lem', True, exclude_pos={'PROPN'})\ndisplay(r.top_terms('ASD-PKD', 8))\n```")]),
          akademik_not("""
          **Derlem Biçembiliminde Anahtar Sözcük Çözümlemesi (Spärck Jones 1972; Scott 1997):**
          Çeviribilimde anahtar sözcük profillemesi, yazarın biçemi ile çevirmenin alışkanlıklarını
          (*habitus*, Simeoni 1998) ayırt etmeye olanak tanır. Özel adların ayıklanması, çeviri yoluyla
          içe aktarılan *novum* (Suvin 1979) ve tekno-bilimsel sözvarlığını doğrudan gözler önüne serer.
          """),
          ]

    # ----------------------------------------------------------------- Bölüm 12
    c += [bolum_basligi(12, "Araştırma Raporlayıcısı ve Denetim İzi", 15,
                         ["Elde edilen tablo ve grafikleri tekrarlanabilir bir bilimsel raporda toplayabilme",
                          "`data/corpus_analysis/…` dizini altındaki çıktıları denetleyebilme",
                          "Üç-Düzeyli Kural (Three-Tier Rule) uyarınca verilere dayalı otomatik özetler üretebilme"],
                         "Bölüm 0–11", "Denetlenebilir ve yayına hazır araştırma raporları üretme."),
          md("""
    ### 12.1 Tekrarlanabilir Bilimsel Araştırma ve Çıktı Mimarisi
    Dijital beşeri bilimler alanındaki her ampirik iddia, bağımsız araştırmacılarca denetlenebilir
    bir veri akışına dayanmalıdır. `CorpusReporter`, tüm çıktıları sürüm kontrolü dışındaki özel dizinlerde
    otomatik olarak yapılandırır:

    ```
    data/corpus_analysis/
    ├── .cache/     Türetilmiş Parquet tabloları (atomik, sınırlı LRU önbellek)
    ├── reports/    <calisma_adi>_<zaman_damgasi>.md (+ biçimlendirilmiş Excel kitabı .xlsx)
    ├── tables/     Her analiz tablosu UTF-8 TSV olarak saklanır
    └── figures/    Her görselleştirme 300-DPI yüksek çözünürlüklü PNG olarak kaydedilir
    ```

    **Katı Veri-Kanıt Sözleşmesi (Data-Evidence Contract):** Raporlayıcının `top_bottom_summary`
    işlevi, en uç istatistiksel değerleri doğrudan DataFrame matrislerinden hesaplar; asla varsayımsal
    ya da dayanıksız yorumlar üretmez.
    """),
          komut_kilavuzu("CorpusReporter Komutları", [
              ("reporter.CorpusReporter(config, registry, run_name='...')", "Üstveri takipli rapor oturumu başlatma", "rep = reporter.CorpusReporter(loader.config, loader.registry, 'deneme')"),
              ("rep.note(key=value)", "Yöntemsel parametreleri günlüğe kaydetme (pencere, görünüm vb.)", "rep.note(field='lem', span='phrase')"),
              ("rep.add_section('Başlık', 'Açıklama')", "Açıklayıcı Markdown bölümü ekleme", "rep.add_section('POS Çözümlemesi', 'Genel bakış...')"),
              ("rep.add_table('ad', df, caption='...')", "TSV tablosu kaydetme ve rapora + Excel'e ekleme", "rep.add_table('diversity', df, caption='Tablo 1')"),
              ("rep.add_figure('ad', fig, caption='...')", "300-DPI PNG kaydetme ve rapora bağlama", "rep.add_figure('radar', fig, caption='Şekil 1')"),
              ("rep.add_summary(reporter.top_bottom_summary(df, col, id_col))", "Veriye dayalı matematiksel özet ekleme", "rep.add_summary(reporter.top_bottom_summary(df, 'MTLD', 'pair'))"),
              ("rep.finalize()", "Markdown raporu ve çok sayfalı Excel kitabını derleme", "rapor_yolu = rep.finalize()"),
              ("analysis.standard_report(loader, run_name='...')", "Tek satırda standart boru hattı raporu (Envanter, Hizalama, POS, Çeşitlilik)", "analysis.standard_report(loader, 'standart')"),
          ]),
          code("""
    # Kapsamlı bir ampirik araştırma raporu oluşturma
    rep = reporter.CorpusReporter(loader.config, loader.registry, run_name="not_defteri_ornek")
    rep.note(field="lem", function_words="filtered", span="sentence-clamped")

    # Tümce Hizalama Bölümü
    rep.add_section("Tümce Hizalama Yapısı", "5 paralel çeviri çiftinde iki dilli tümce eşleşme dağılımları.")
    rep.add_table("alignment_summary", summary.round(3), caption="Tümce hizalama sayıları ve oranları.")
    rep.add_figure("alignment_stacked", viz.alignment_stacked(summary), caption="Şekil 1: Hizalama kategorisi oranları.")
    rep.add_summary(reporter.top_bottom_summary(summary, "R_sent", "pair"))

    # Sözcüksel Çeşitlilik Bölümü
    rep.add_section("Sözcüksel Çeşitlilik Çözümlemesi", "Türkçe metinlerde 14 LancsBox-X metriği değerlendirmesi.")
    rep.add_table("diversity_raw", div_raw.round(3), caption="Türkçe derlem genelinde ham çeşitlilik metrikleri.", index=True)
    rep.add_summary(reporter.top_bottom_summary(div_raw.reset_index(), "MTLD", "index"))

    # Raporu derleme (Markdown, TSV, PNG ve Excel dosyalarını üretir)
    report_path = rep.finalize()
    print("Rapor oluşturuldu:", report_path)
    """),
          code("""
    # Oluşturulan Markdown raporunun önizlemesi
    content = report_path.read_text(encoding="utf-8")
    print(content[:1500])
    """),
          md("#### Tek Satırda Standart Rapor Üretimi (Envanter, Hizalama, POS, Çeşitlilik):"),
          code("""
    std_path = analysis.standard_report(loader, run_name="standart_calisma")
    print("Standart araştırma raporu üretildi:", std_path)
    """),
          tuzaklar(["Zaman damgası kullanmadan aynı çalışma adıyla rapor üretmek önceki çıktıların üzerine yazabilir: varsayılan zaman damgalamayı açık tutun.",
                    "Excel kitapları (.xlsx) bir ofis yazılımında açıkken tekrar `finalize()` çağrısı dosya kilitleme hatası verebilir; dosyayı kapatın."]),
          alistirmalar([("Üretilen Excel kitabındaki çalışma sayfalarının isimlerini pandas ile inceleyin.",
                         "```python\nimport pandas as pd\nxlsx_path = report_path.with_suffix('.xlsx')\nprint('Excel sayfalari:', pd.ExcelFile(xlsx_path).sheet_names)\n```")]),
          akademik_not("""
          **Hesaplamalı Tekrarlanabilirlik ve Denetim İzleri (Peng 2011):**
          Modern dijital beşeri bilimler, ortaya konan istatistiksel iddiaların sözcükbirim ve hizalama
          düzeyine kadar izlenebilir olmasını şart koşar. Ham tabloları TSV ve Excel formatlarında saklayıp
          yüksek çözünürlüklü grafiklerle eşleştiren raporlama mimarimiz, tez savunması ve hakemli yayın
          süreçleri için tam şeffaflık sağlar.
          """),
          ]

    # ----------------------------------------------------------------- Bölüm 13
    c += [bolum_basligi(13, "Etkileşimli Derlem Gezgini (GUI)", 15,
                         ["Arama, KWIC dizini ve eşdizimleri etkileşimli bir widget paneliyle yönetebilme",
                          "`quick_search` işlevini betik tabanlı eşdeğer olarak kullanabilme",
                          "Önbellekteki tabloları bilinçli olarak temizleyerek (`evict`) belleği boşaltabilme"],
                         "Bölüm 6–10", "Derlem yorumbilimi (hermeneutics) için birleşik etkileşimli keşif aracı."),
          md("""
    ### 13.1 Birleşik Etkileşimli Gezgin Paneli
    Etkileşimli ipywidgets arayüzü, araç setinin sunduğu tüm yetenekleri tek bir dinamik grafik
    arayüzde birleştirir. Paneldeki her denetim, önceki bölümlerde öğrendiğimiz işlevsel API parametrelerine
    doğrudan karşılık gelir:

    - **Derlem / Kategori**: Metinleri paralel çeviriler, yazar-çevirmen çiftleri ya da yerli romanlara göre filtreler.
    - **Yazar-Çevirmen**: Kapsamı tek bir yazar-çevirmenle sınırlar (`Selma MİNE`, `Zühtü BAYAR`, `Özlem KURDOĞLU`).
    - **Sözcükler**: Virgülle ayrılmış arama terimleri (birleşik tarama).
    - **Alan**: Sözlükbirim (`lem`) veya yüzey sözcük (`tok`).
    - **Eşleşme**: Tam eşleşme, joker karakter (`*`) ya da düzenli ifade (regex).
    - **İşlevsel Sözcük Filtresi**: İçerik sözcüğü çözümlemesini açar/kapatır (`drop` vs `mask`).
    - **Pencere Aralığı**: Öbek, tümce veya simetrik aralık ($\pm L / \pm R$).
    - **Görünüm**: KWIC dizini (`kwic`, `sentence`, `table`) ya da istatistiksel `summary`.
    """),
          komut_kilavuzu("Etkileşimli Gezgin Komutları", [
              ("explorer.CorpusExplorerUI(loader).show()", "Etkileşimli ipywidgets arama ve dizin panelini görüntüleme", "ui = explorer.CorpusExplorerUI(loader); ui.show()"),
              ("explorer.quick_search(loader, ['sözcük'], ...)", "ConcordanceResult döndüren (kendini görüntüler; DataFrame için .to_dataframe()) betik eşdeğeri", "quick_search(loader, ['robot'], author='Selma Mine')"),
              ("loader.evict_all()", "Yüklenmiş tüm metin tablolarını bellekten tahliye etme", "loader.evict_all()"),
          ]),
          code("""
    # Etkileşimli widget panelini başlatma (başsız testlerde sessizce uyarı verir)
    try:
        from corpus_toolkit import explorer
        ui = explorer.CorpusExplorerUI(loader)
        ui.show()
    except Exception as exc:
        print("Etkileşimli arayüz başsız kipte kullanılamıyor:", exc)
    """),
          md("### 13.2 Betik Tabanlı Eşdeğer: `quick_search`"),
          code("""
    # Selma Mine metinlerinde 'robot' adını arayan betik çağrısı (NDA yan yana paralel görünüm)
    from corpus_toolkit.explorer import quick_search
    qs_res = quick_search(loader, ["robot"], category="Author-translator related texts",
                          author="Selma Mine", field="lem", pos={"NOUN"},
                          span="phrase", view="parallel", max_lines=3)
    """),
          code("""
    # Açık bellek temizliği: Keşif sonrası tüm tabloları RAM'den tahliye etme
    loader.evict_all()
    print("Bellek temizlendi: Yüklenmiş tüm metin tabloları tahliye edildi.")
    """),
          tuzaklar(["Etkileşimli grafik arayüz, `ipywidgets` kütüphanesinin etkin olduğu canlı bir Jupyter ortamı gerektirir.",
                    "Gezginde art arda birçok metni açmak RAM kullanımını artırabilir: uzun oturumlar arasında `loader.evict_all()` çağrısı yapın."]),
          alistirmalar([("Tüm Türkçe çeviri metinlerinde `uzay` sözlükbirimi için hızlı arama yapın ve ilk 5 bulguyu listeleyin.",
                         "```python\nfrom corpus_toolkit.explorer import quick_search\n"
                         "res = quick_search(loader, ['uzay'], category='Turkish translations', field='lem', view='kwic', max_lines=5)\n```")]),
          akademik_not("""
          **Keşifsel Veri Çözümlemesi ve Yorumbilimsel Soruşturma (Tukey 1977; Rockwell & Sinclair 2016):**
          Dijital edebiyat araştırmalarında bilgisayar destekli okuma, yakın okumanın (close reading)
          yerini almaz; makro düzeydeki uzaktan okuma (distant reading) ile mikro düzeydeki metinsel
          derinlemesine okuma arasında diyalektik bir köprü kurar (*Hermeneutica*).
          """),
          md("""
    ---
    ## 📚 Kaynakça
    - Baker, M. (1993). Corpus linguistics and translation studies: Implications and applications. M. Baker, G. Francis, & E. Tognini-Bonelli (Ed.), *Text and Technology: In Honour of John Sinclair* (ss. 233–250). John Benjamins.
    - Benjamini, Y., & Hochberg, Y. (1995). Controlling the false discovery rate: A practical and powerful approach to multiple testing. *Journal of the Royal Statistical Society: Series B (Methodological)*, 57(1), 289–300.
    - Biber, D. (1988). *Variation across speech and writing*. Cambridge University Press.
    - Bourdieu, P. (1993). *The Field of Cultural Production: Essays on Art and Literature*. Columbia University Press.
    - Brezina, V., McEnery, T., & Wattam, S. (2015). Collocations in context: A new perspective on collocation networks. *International Journal of Corpus Linguistics*, 20(2), 139–173.
    - Brezina, V., Weill-Tessier, P., & McEnery, T. (2021). *#LancsBox v. 6.0* [Bilgisayar yazılımı]. Lancaster University.
    - Church, K. W., & Hanks, P. (1990). Word association norms, mutual information, and lexicography. *Computational Linguistics*, 16(1), 22–29.
    - Church, K. W., Gale, W., Hanks, P., & Hindle, D. (1991). Using statistics in lexical analysis. U. Zernik (Ed.), *Lexical Acquisition: Exploiting On-Line Resources to Build a Lexicon* (ss. 115–164). Lawrence Erlbaum.
    - Covington, M. A., & McFall, J. D. (2010). Cutting the Gordian knot: The Moving-Average Type–Token Ratio (MATTR). *Journal of Quantitative Linguistics*, 17(2), 94–100.
    - Daille, B. (1994). *Approche mixte pour l'extraction de terminologie: statistique et linguistique* [Doktora tezi, Université Paris 7].
    - Dugast, D. (1979). *Vocabulaire et stylistique: II. Les indices de richesse lexicale et leurs applications*. Slatkine.
    - Dunning, T. (1993). Accurate methods for the statistics of surprise and coincidence. *Computational Linguistics*, 19(1), 61–74.
    - Even-Zohar, I. (1990). Polysystem studies. *Poetics Today*, 11(1), 1–268.
    - Firth, J. R. (1957). A synopsis of linguistic theory, 1930–1955. *Studies in Linguistic Analysis* (ss. 1–32). Philological Society.
    - Gries, S. T. (2008). Dispersions and adjusted frequencies in corpora. *International Journal of Corpus Linguistics*, 13(4), 403–437.
    - Guiraud, P. (1954). *Les caractères statistiques du vocabulaire*. Presses Universitaires de France.
    - Herdan, G. (1960). *Type-token mathematics: A textbook of mathematical linguistics*. Mouton.
    - Honoré, A. (1979). Some simple measures of richness of vocabulary. *ALLC Bulletin*, 7(2), 172–177.
    - Juilland, A., & Chang-Rodríguez, E. (1964). *Frequency dictionary of Spanish words*. Mouton.
    - Luhn, H. P. (1960). Key word-in-context index for technical literature (KWIC index). *American Documentation*, 11(4), 288–295.
    - Maas, H. D. (1972). Über den Zusammenhang zwischen Wortschatzumfang und Länge eines Textes. *Zeitschrift für Literaturwissenschaft und Linguistik*, 2(8), 73–96.
    - McCarthy, P. M., & Jarvis, S. (2010). MTLD, vocd-D, and HD-D: A validation study of sophisticated approaches to lexical diversity assessment. *Behavior Research Methods*, 42(2), 381–392.
    - Nivre, J., vd. (2016). Universal Dependencies v1: A multilingual treebank collection. *Proceedings of LREC 2016*, 1659–1666.
    - Peng, R. D. (2011). Reproducible research in computational science. *Science*, 334(6060), 1226–1227.
    - Rockwell, G., & Sinclair, S. (2016). *Hermeneutica: Computer-assisted interpretation in the humanities*. MIT Press.
    - Rychlý, P. (2008). A lexicographer-friendly association score. *Proceedings of Recent Advances in Slavonic Natural Language Processing (RASLAN 2008)*, 6–9.
    - Simeoni, D. (1998). The pivotal status of the translator's habitus. *Target: International Journal of Translation Studies*, 10(1), 1–39.
    - Simpson, E. H. (1949). Measurement of diversity. *Nature*, 163, 688.
    - Sinclair, J. (1991). *Corpus, Concordance, Collocation*. Oxford University Press.
    - Spärck Jones, K. (1972). A statistical interpretation of term specificity and its application in retrieval. *Journal of Documentation*, 28(1), 11–21.
    - Suvin, D. (1979). *Metamorphoses of Science Fiction: On the Poetics and History of a Literary Genre*. Yale University Press.
    - Toury, G. (2012). *Descriptive Translation Studies – and beyond* (2. bs.). John Benjamins.
    - Tukey, J. W. (1977). *Exploratory Data Analysis*. Addison-Wesley.
    - Yule, G. U. (1944). *The Statistical Study of Literary Vocabulary*. Cambridge University Press.

    <sub>*Tüm alıntılar doktora tezi araştırma doğruluk tablosunda (`chapter_count_truth_table.tsv`) kayıtlıdır.*</sub>
    """),
          ]
    return c
