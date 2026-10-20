"""Bölüm 6–9 (Türkçe): Arama motoru, KWIC dizinleyici, toplu KWIC istatistikleri ve sözcüksel çeşitlilik."""

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

    # ------------------------------------------------------------------ Bölüm 6
    c += [bolum_basligi(6, "Derlem Arama Motoru ve Düğüm Sözcük Sorgulama", 25,
                         ["Sözcükbirim (token), sözlükbirim (lemma), joker karakter (glob), düzenli ifade (regex) ve UPOS etiketine göre arama yapabilme",
                          "Bağlam sözcüğü kısıtı ekleyebilme (eşdizimli sözcük filtreleme)",
                          "İçerik sözcüğü görünümünde arama yapabilme (işlevsel sözcükler gizlenmiş) ve `drop` ile `mask` farkını kavrama",
                          "Noktalama işaretlerini koruma/çıkarma/ayırma (`keep`, `drop`, `strip`, `split`) ve Türkçe kesme işareti düzeltmesini anlama"],
                         "Bölüm 0–2", "Merak ettiğiniz her sözcüksel örüntüyü derlemde bulup ortaya çıkarma."),
          md("""
    ### 6.1 Kuramsal Çerçeve: Düğüm Sözcük ve Arama Parametreleri
    Derlembilimde aradığınız temel hedef sözcüğe **düğüm sözcük (node word)** adı verilir (Sinclair 1991).
    Türkçe sondan eklemeli bir dil olduğundan, doğrudan yüzey biçimi olan *token* `robot` arandığında
    `robotlar`, `robotun`, `robotuyla` gibi biçimbilimsel çekimler kaçırılır. Oysa **sözlükbirim (lemma)**
    olan `robot` arandığında tüm bu çekimli biçimler tek bir çatı altında toplanır. Arama motorumuz
    araştırma sorunuza göre şu parametrelerle inceltilebilir:

    | `SearchQuery` Seçeneği | İşlevi | Örnek |
    |---|---|---|
    | `terms` | Aranacak bir veya birden fazla sözcük (liste birleştirilerek taranır) | `["robot", "makine"]` |
    | `field` | `'lem'` (sözlük tabanı) veya `'tok'` (yüzey sözcükbirim) | `field='tok'` |
    | `match` | `'exact'` (tam eşleşme), `'glob'` (`*`, `?`), `'regex'` (düzenli ifade) | `match='glob'`, `gel*` |
    | `case_sensitive` | Büyük/küçük harf duyarlılığı (Türkçe İ/I dönüşümüne duyarlıdır) | Varsayılan: `False` |
    | `pos` | Düğüm sözcük üzerinde UPOS sözcük türü kısıtı | `{"NOUN"}` (yalnızca adlar) |
    | `collocate`, `collocate_span` | Belirlenen sol/sağ pencerede eşdizimli bağlam sözcüğü zorunluluğu | `collocate=["insan"], collocate_span=(5,5)` |
    | `filter_function_words`, `mode` | İçerik sözcüğü görünümü; `drop` (çıkar) veya `mask` (maskele) | Ayrıntılar aşağıda |
    | `punct` | Noktalama kipi: `'drop'`, `'keep'`, `'strip'`, `'split'` | Passim ve VNLP yöntemi |

    **İşlevsel Sözcüklerden Arındırılmış Arama (`scripts/passim_analysis` Yöntemi).**
    `filter_function_words=True` seçildiğinde belirteçler, adıllar, ilgeçler, yardımcı eylemler, bağlaçlar
    ve ünlemler gizlenir (Türkçe metinlerde ayrıca biçimbilimsel baş koruması
    `Postp, Conj, Det, Pron, Ques, Interj, Punc` uygulanır). **`drop`** bu sözcükleri diziden bütünüyle
    atar, bu nedenle $\pm 5$ penceresi tam olarak 5 *içerik sözcüğü* anlamına gelir; **`mask`** ise
    bu sözcükleri dizideki yerlerinde tutar (böylece aralık 5 *akan sözcük* olarak kalır) ancak bunların
    eşleşmesini ya da eşdizim üretmesini engeller.

    ### 6.2 Elle Doğrulanabilir Oyuncak Örnek
    Metin: *“the cat saw the dog | the dog saw the cat”*. `saw` eylemi arandığında $\Rightarrow$ 2 bulgu.
    `collocate=['dog'], span=(1,1)` kısıtı eklendiğinde yalnızca ikinci tümce (*“dog saw”*) eşleşir;
    çünkü birinci tümcede `the` araya girdiği için `dog` 2 sözcük uzaklıktadır. (Bu durum `test_search_options`
    birim testimizin temel mantığıdır.)
    """),
          komut_kilavuzu("Arama Motoru Komutları", [
              ("SearchQuery(['terim'], field='lem')", "Sözlükbirim araması (tüm çekimler toplanır)", "SearchQuery(['robot'], field='lem')"),
              ("SearchQuery(['gel*'], match='glob')", "Joker karakter araması (* 0+, ? 1 karakter)", "SearchQuery(['gel*'], match='glob')"),
              ("SearchQuery(['^rob'], match='regex')", "Düzenli ifade (regex) araması", "SearchQuery([r'^[a-z]+ing$'], match='regex')"),
              ("SearchQuery(['...'], pos={'NOUN'})", "Belirli bir UPOS sözcük türü ile kısıtlama", "SearchQuery(['robot'], pos={'NOUN'})"),
              ("SearchQuery(['...'], collocate=['...'], collocate_span=(5, 5))", "Belirtilen pencerede bağlam sözcüğü zorunluluğu", "SearchQuery(['robot'], collocate=['insan'])"),
              ("CorpusSearchEngine().search(q, texts)", "Aramayı metin listesi üzerinde yürütme", "engine.search(q, texts)"),
          ]),
          code("""
    engine = search.CorpusSearchEngine()
    all_texts = list(loader.load_all())
    q = search.SearchQuery(["robot"], field="lem")
    res = engine.search(q, all_texts)
    print(q.describe())
    display(res.summary())             # hits (bulgular) ve per10k (10 000 akan sözcük başına sıklık)
    display(res.hits.head(6))
    """),
          md("**Sözlükbirim (Lemma) ve Yüzey Sözcük (Token) Karşılaştırması** — Çekimli ve çekimsiz Türkçe sözcük:"),
          code("""
    turkish = list(loader.load_all_turkish())
    for field in ("tok", "lem"):
        r = engine.search(search.SearchQuery(["robot"], field=field), turkish)
        print(f"field={field}: {len(r)} bulgu")
    r = engine.search(search.SearchQuery(["robot*"], field="tok", match="glob"), turkish)
    print("glob robot*:", len(r), "bulgu;", r.hits["token"].str.lower().value_counts().head(6).to_dict())
    """),
          md("**Sözcük Türü (POS) ve Bağlam Kısıtları** — Yalnızca adlar, *insan* sözcüğünün yakınında:"),
          code("""
    r1 = engine.search(search.SearchQuery(["robot"], "lem", pos={"NOUN"}), turkish)
    r2 = engine.search(search.SearchQuery(["robot"], "lem", pos={"NOUN"}, collocate=["insan"],
                                          collocate_span=(10, 10)), turkish)
    print(f"robot (NOUN): {len(r1)} bulgu;  … 'insan' sözcüğüne ±10 mesafede: {len(r2)} bulgu")
    display(r2.summary())
    """),
          md("**Düzenli İfadeler (Regex)** — Türkçe iyelik/çoğul ekleri, İngilizce `-ing` eylemleri:"),
          code("""
    r = engine.search(search.SearchQuery([r"^robot(lar)?(ın|un|ı)?$"], "tok", match="regex"), turkish)
    print(len(r), r.hits["token"].str.lower().value_counts().head(8).to_dict())
    en_texts = list(loader.load_all_english())
    r = engine.search(search.SearchQuery([r"^[a-z]+ing$"], "tok", match="regex", pos={"VERB"}), en_texts)
    print(len(r), r.hits["token"].str.lower().value_counts().head(8).to_dict())
    """),
          md("**İşlevsel Sözcüklerden Arındırılmış Arama** — Ham vs içerik, drop vs mask (`robot` için bulgu sayıları):"),
          code("""
    rows = []
    for fw, mode in [(False, "drop"), (True, "drop"), (True, "mask")]:
        r = engine.search(search.SearchQuery(["robot"], "lem", filter_function_words=fw, mode=mode),
                          turkish)
        s = r.summary()
        rows.append({"filter_function_words": fw, "mode": mode, "hits": s["hits"].sum(),
                     "running_words": s["running_words"].sum(),
                     "per10k": 1e4 * s["hits"].sum() / s["running_words"].sum()})
    display(pd.DataFrame(rows))
    """),
          md("""
    **Noktalama İşaretleri ile / İşaretsiz Arama ve Sözcük İçi Noktalama (Passim Yöntembilimi):**
    VNLP ile ayrıştırılan Türkçe metinler, sözcük içi noktalama işaretlerini korur (örn. `Türkiye'nin`,
    `Fred'`, `robot-bilim`, `1882'de`) ve bu özellik sözlükbirim (lemma) alanında da yer alır
    (`fred'`, `ay'da`, `1882'`). Dört farklı noktalama kipi desteklenmektedir:
    - `punct='drop'` (varsayılan): Bağımsız noktalama işaretlerini kaldırır; sözcük içi noktalamayı korur.
    - `punct='keep'`: Bağımsız noktalamayı saklar; böylece `?`, `!`, `,` gibi işaretler doğrudan aranabilir.
    - `punct='strip'`: Sözcüğü bölmeden sözcük içi noktalamayı temizler (`Türkiye'nin` → `Türkiyenin`, `Fred'` → `Fred`).
    - `punct='split'`: Bileşik yapıları alt birimlere ayırır (`Türkiye'nin` → `['türkiye', 'nin']`, `robot-bilim` → `['robot', 'bilim']`).
    Hem `strip` hem de `split` kipleri yüzey sözcüklerde (`tok`) ve sözlükbirimlerde (`lem`) eksiksiz çalışır.

    **Türkçe Sözlükbirim Kesme İşareti Düzeltmesi (Lemma Apostrophe Remediation):**
    Ham VNLP çıktılarında, özel adlar ve tireli bileşikler sözlükbirim alanında kesme işaretinden sonraki
    çekim eklerini korumaktaydı (`Türkiye'nin` → `türkiye'nin`, `bilim-kurgu'nun` → `bilim-kurgu'nun`).
    Araç setimiz bu durumu otomatik olarak düzeltmektedir: tüm Türkçe sözlükbirimlerde kesme işaretinden
    sonraki ekler temizlenir (`türkiye'nin` → `türkiye`, `bilim-kurgu'nun` → `bilim-kurgu`, tireli bileşik yapı
    korunurken `'nun` durum eki silinir). Böylece `field="lem"` üzerinden yapılan `türkiye` araması,
    tüm çekimli biçimlerle doğrudan eşleşir.
    """),
          code("""
    # 1. Noktalamalı arama ('keep'): Soru işaretlerini bulma
    r_punct = engine.search(search.SearchQuery(["?"], field="tok", punct="keep"), turkish)
    print("Türkçe derlemde bulunan soru işareti sayısı:", len(r_punct), "bulgu")

    # 2. Sözcük içi noktalama: 'strip' (birleştir/temizle) vs 'split' (ayır)
    r_strip = engine.search(search.SearchQuery(["Türkiyenin"], field="tok", punct="strip"), turkish)
    r_split = engine.search(search.SearchQuery(["Türkiye"], field="tok", punct="split"), turkish)
    print(f"Türkiyenin (strip): {len(r_strip)} bulgu;  Türkiye (split): {len(r_split)} bulgu")

    # 3. İyileştirilmiş Türkçe sözlükbirim (kesme işareti sonrası silinmiş, bileşik tire korunmuş):
    r_lem = engine.search(search.SearchQuery(["türkiye"], field="lem"), turkish)
    print(f"Düzeltilmiş Türkçe sözlükbirim 'türkiye': {len(r_lem)} bulgu (tüm çekimli biçimlerle eşleşir)")

    # 4. Sözcük içi noktalama ayrıştırması ile sözlükbirim araması:
    r_lem_sp = engine.search(search.SearchQuery(["bilim"], field="lem", punct="split"), turkish)
    print(f"Sözlükbirim 'bilim' (split kipi, robot-bilim içinde bulur): {len(r_lem_sp)} bulgu")
    """),
          tuzaklar(["Bulgu sayıları `drop` ve `mask` arasında değişmez; değişen şey **aralıkların (span) kapsamıdır** (Bölüm 7 ve 10).",
                    "`per10k` değeri, **seçilen görünümün** toplam akan sözcük sayısına bölünür — içerik görünümünde payda daha küçük olduğu için, bulgu sayısı aynı kalsa bile per10k oranı *yükselir*.",
                    "Türkçe VNLP çıktısında, varsayılan `punct='drop'` kipinde `Fred` araması `Fred'` sözcüğünü kaçırır; bunu yakalamak için `punct='strip'` veya `punct='split'` kullanılmalıdır.",
                    "Düzenli ifade (regex) aramaları, `case_sensitive=True` belirtilmedikçe *küçük harfe dönüştürülmüş (folded)* metin üzerinde çalışır."]),
          alistirmalar([("Selma Mine'nin telif bilimkurgu romanında (*OBİ,J.S.927*) `makine` sözlükbirimi `robot` sözcüğünün yakınında (±5) kaç kez geçmektedir?",
                         "```python\nr = engine.search(search.SearchQuery(['makine'], 'lem', collocate=['robot'], "
                         "collocate_span=(5, 5)), list(loader.load_indigenous('SM')))\ndisplay(r.summary())\n```")]),
          akademik_not("""
          **Düğüm Seçimi ve Repertuar Haritalama (Sinclair 1991; Stubbs 2001):**
          Çeviribilimsel derlem analizlerinde sorgu tasarımı, sözcüksel repertuarın hangi boyutunun
          aydınlatılacağını belirler. Sözlükbirim odaklı sorgular anlamsal alan genişlemesini ortaya
          koyarken, biçimsözdizimsel kısıtlar erek dildeki çeviri rutinlerini ve erek dil normlarını sergiler.
          """),
          ]

    # ------------------------------------------------------------------ Bölüm 7
    c += [bolum_basligi(7, "Bağlam İçinde Anahtar Sözcük (KWIC) Dizinleyici", 30,
                         ["KWIC mantığını açıklayabilme ve amaca uygun pencere aralığı seçebilme",
                          "Hizalı, koordinat rozeti (chip) ve tümce kartı görünümlerini okuyabilme",
                          "Dizin satırlarını düğümün sağındaki (`R1`) veya solundaki (`L1`) sözcüğe göre sıralayabilme",
                          "NLTK kütüphanesinin aracıyla çapraz doğrulama yapabilme"],
                         "Bölüm 6", "Yalnızca sıklık sayılarını değil, metinsel kanıtın kendisini okuma."),
          md("""
    ### 7.1 KWIC Nedir?
    **KWIC = Key Word In Context (Bağlam İçinde Anahtar Sözcük).** Bir dizinleme yöntemi olarak KWIC,
    aranan bir **düğüm sözcüğün (node)** geçtiği her konumu, solundaki ve sağındaki sözcüklerle birlikte
    **düğüm sözcük merkezde hizalanacak biçimde** listeler (Luhn 1960; Sinclair 1991, *Corpus, Concordance, Collocation*).
    Böylece tekrarlanan dilsel kalıplar ve kalıplaşmış yapılar görsel olarak belirginleşir. Sıklık sayımı
    bir sözcüğün *ne sıklıkla* geçtiğini söyler; KWIC dizini ise o sözcüğün *nasıl kullanıldığını* gösterir.

    ### 7.2 Pencere Aralığı (Span) Seçimi
    | Belirteç | (Sol, Sağ) | Kullanım Alanı |
    |---|---|---|
    | `'phrase'` | (3, 3) | Deyimler, sabit söz öbekleri, belirteç kalıpları |
    | `'collocation'` | (5, 5) | Klasik eşdizim penceresi (Sinclair 1991) |
    | `'extended'` | (10, 10) | Anlamsal bürün (semantic prosody), izleksel bağlam |
    | `'discourse'` | (20, 20) | Söylem düzeyinde çerçeveleme |
    | `'sentence'` | Tüm tümce | Eksiksiz bağlamsal çevre |
    | `7`, `(5, 2)`, `'L5R2'` | Özel | Asimetrik: *ardından ne geliyor?* $\\rightarrow$ `(0, 4)`; *öncesinde ne var?* $\\rightarrow$ `(4, 0)` |

    `sentence_clamped=True` (varsayılan) seçeneği, pencere aralığının tümce sınırını aşmasına asla izin vermez.

    ### 7.3 Elle Doğrulanabilir Oyuncak Örnek: Dizin Satırları ve Sıralama
    Verilen tümceler:
    1. *“The smart **robot** moved quickly .”* $\\rightarrow$ L1=`smart`, düğüm=`robot`, R1=`moved`
    2. *“A tiny **robot** spoke quietly .”* $\\rightarrow$ L1=`tiny`, düğüm=`robot`, R1=`spoke`
    - **R1** sözcüğüne göre sıralandığında: Önce 1. satır (`moved`), sonra 2. satır (`spoke`).
    - **L1** sözcüğüne göre sıralandığında: Önce 1. satır (`smart`), sonra 2. satır (`tiny`).
    """),
          komut_kilavuzu("Dizinleyici Komutları ve Görünümleri", [
              ("Concordancer().run(search_res, texts, span='collocation')", "Seçilen pencereyle tüm bulgular için KwicLine nesneleri çıkarma", "conc = kwic.Concordancer().run(res, texts, span='L5R2')"),
              ("conc.sorted('R1')", "Dizin satırlarını sağdaki ilk sözcüğe göre sıralama (R1...R5, L1...L5)", "conc_sorted = conc.sorted('R1')"),
              ("render.show(conc, view='kwic')", "Düğüm sözcüğü vurgulanmış HTML merkezli hizalama görünümü", "render.show(conc, 'kwic')"),
              ("render.show(conc, view='chips')", "Akademik alıntılar için tam koordinat rozetleri (bölüm·paragraf·tümce·sözcük)", "render.show(conc, 'chips')"),
              ("render.show(conc, view='cards', loader=loader)", "İki dilli hizalanmış karşılıkları içeren tümce kartları", "render.show(conc, 'cards', loader=loader)"),
              ("render.show(conc, view='parallel', loader=loader)", "NDA yan yana EN ⇄ TR tümce tablosu (SVG bağlantıları ve sözlükbirimler)", "render.show(conc, 'parallel', loader=loader, max_lines=4)"),
              ("render.show(conc, view='table')", "Etkileşimli sayfalı (20 satır/sayfa), sıralanabilir ve boyutlandırılabilir tablo", "render.show(conc, 'table', max_lines=20)"),
              ("render.show(conc, view='console')", "Uçbirim ve günlük incelemelerine uygun düz metin görünümü", "render.show(conc, 'console')"),
          ]),
          code("""
    pair_texts = [loader.load_text("IR-IA"), loader.load_text("BR-SM")]
    print(loader.registry.display(pair_texts[0]))
    print(loader.registry.display(pair_texts[1]))
    res = engine.search(search.SearchQuery(["robot"], "lem", pos={"NOUN"}), pair_texts)
    conc = kwic.Concordancer().run(res, pair_texts, span="collocation", max_lines_per_text=12)
    print(f"Toplam {conc.total_hits} bulgudan {len(conc)} satır gösteriliyor")
    """),
          md("#### Görünüm 1 — Merkezde Hizalanmış KWIC (Düğüm merkezde; rozet = metin türü; yazar için üzerine gelin)"),
          code("render.show(conc, 'kwic', max_lines=14)"),
          md("#### Görünüm 2 — Koordinat Rozetleri (Her bulgu alıntılanabilir: bölüm · paragraf · tümce · sözcük)"),
          code("render.show(conc, 'chips', max_lines=8)"),
          md("#### Görünüm 3 — İki Dilli Tümce Kartları (Hizalanmış çeviri karşılığı altta görüntülenir)"),
          code("render.show(conc, 'cards', loader=loader, max_lines=4)"),
          md("#### Görünüm 4 — NDA Yan Yana Paralel Görünüm (`view='parallel'`) ve Görünüm 5 — Etkileşimli Sayfalı Tablo (`view='table'`)"),
          code("""
    render.show(conc, "parallel", loader=loader, max_lines=3)
    render.show(conc, "table", max_lines=20)
    """),
          md("#### Uçbirim Görünümü (Konsol / Günlük çıktıları için)"),
          code("render.show(conc, 'console', max_lines=8)"),
          md("#### Sıralama Örüntüleri Ortaya Çıkarır — Düğümün *sağındaki* (`R1`), ardından *solundaki* (`L1`) sözcüğe göre"),
          code("""
    render.show(conc.sorted("R1"), "kwic", max_lines=10)
    render.show(conc.sorted("L1"), "kwic", max_lines=10)
    """),
          md("""
    #### Asimetrik ve Tümce Sınırına Duyarlı Pencereler
    Yalnızca düğümden *sonra* gelenler (`'L0R4'`), ardından tüm tümce:
    """),
          code("""
    render.show(kwic.Concordancer().run(res, pair_texts, span="L0R4", max_lines_per_text=5), "kwic", max_lines=8)
    render.show(kwic.Concordancer().run(res, pair_texts, span="sentence", max_lines_per_text=3), "cards", loader=loader, max_lines=3)
    """),
          md("""
    #### İçerik Sözcüğü Dizini (İşlevsel sözcükler soluklaştırılmış)
    `filter_function_words=True` seçildiğinde pencere yalnızca *içerik sözcüklerini* sayar (`drop`);
    soluklaştırılan işlevsel sözcükler satırın okunabilir kalması için gösterilir.
    """),
          code("""
    res_c = engine.search(search.SearchQuery(["robot"], "lem", pos={"NOUN"}, filter_function_words=True, mode="drop"), pair_texts)
    conc_c = kwic.Concordancer().run(res_c, pair_texts, span=(4, 4), max_lines_per_text=8)
    render.show(conc_c, "kwic", max_lines=10)
    """),
          md("#### NLTK ile Çapraz Kontrol (Farklı ve yalın bir algoritma)"),
          code("""
    v = TokenView(loader.load_text("IR-IA"), "tok", False)
    for line in nltk_adapter.nltk_concordance(v, "robot", width=70, lines=5):
        print(line)
    print("NLTK dağılımsal benzer sözcükler:", nltk_adapter.nltk_similar(v, "robot", 6))
    """),
          tuzaklar(["NLTK'nin dizinleyicisi noktalama işaretleri dahil *tüm* belirteçleri sayar ve tümce sınırlarını dikkate almaz — satırları tasarım gereği bizim çıktımızdan biraz farklı olacaktır.",
                    "Tümce sınırına ulaşan bir pencere aralığı, sınır noktalama işaretini de doğal olarak görüntüler."]),
          alistirmalar([("Isaac Asimov'un *I, Robot* romanında `human` (insan) İngilizce sözlükbiriminden *hemen sonra* gelen 4 sözcüğü listeleyin ve bir sonraki söze göre sıralayın.",
                         "```python\nt = [loader.load_text('IR-IA')]\nr = engine.search(search.SearchQuery(['human'], 'lem'), t)\n"
                         "render.show(kwic.Concordancer().run(r, t, 'L0R4').sorted('R1'), 'kwic')\n```")]),
          akademik_not("""
          **Niteliksel Dizin İncelemesi ve Anlam Birimleri (Sinclair 1991; Luhn 1960):**
          KWIC dizini okumak, niceliksel kalıpların **niteliksel kanıtıdır**: bir çevirmenin bir terimi
          yerlileştirdiğini veya yabancılaştırdığını iddia etmeden önce, her iki dilde 20–30 dizin satırı
          okunmalı ve *sözdizimsel çerçeveler* (Sinclair'in *anlam birimi* kavramı) incelenmelidir.
          Alıntıladığınız her örneğin tez metninde denetlenebilir olması için koordinatları (`bölüm·paragraf·tümce·sözcük`)
          kaydedilmelidir.
          """),
          ]

    # ------------------------------------------------------------------ Bölüm 8
    c += [bolum_basligi(8, "Toplu KWIC: Sözcük Listeleri, Kümeler ve Dağılım Bağıntıları", 30,
                         ["Aynı anda bir sözcük listesini veya anlamsal alanı çözümleyebilme",
                          "10 bin sözcük başına sıklık (per10k), Juilland D yayılım katsayısı ve metin içi dilim profillerini hesaplayabilme",
                          "Pearson r, Spearman ρ, kosinüs benzerliği ve Benjamini-Hochberg FDR düzeltmeli q değerlerini yorumlayabilme"],
                         "Bölüm 6–7", "Tekil sözcüklerden anlamsal alanlara ve sözvarlığı dağılımına geçiş."),
          md("""
    ### 8.1 Kuramsal Çerçeve
    Belirli bir *anlamsal alanı* (örneğin robot / insan / makine) araştırırken, farklı uzunluktaki
    metinler arasında karşılaştırılabilir olan ve bir sözcüğün metin geneline **ne kadar dengeli yayıldığını**
    gösteren ölçütlere gereksinim duyulur:

    1. **Sıklık Standartlaştırma**: `per10k = 10 000 · bulgular / toplam akan sözcük`.
    2. **Sözcüksel Yayılım — Juilland's D** (Juilland & Chang-Rodríguez 1964; Gries 2008):
       Her metin *n = 10* eşit dilime (chunk) bölünür. Dilim sıklıklarının değişim katsayısı
       `V = σ / μ` hesaplanır (yığın standart sapması $\sigma$):
       $D = 1 - \\frac{V}{\sqrt{n - 1}}$ $\Rightarrow$ 1 = kusursuz dengeli dağılım, 0 = tek bir dilime yığılmış dağılım.
    3. **Profil Karşılaştırma**: Her sözcük metin dilimlerindeki oranlardan oluşan bir vektör alır (metin başına 10 dilim).
       **Pearson r** (doğrusal bağıntı), **Spearman ρ** (sıra bağıntısı) ve **kosinüs** (vektör açısı)
       sözcüklerin metin boyunca birlikte hareket edip etmediğini gösterir.
    4. **Çoklu Hipotez Testi**: Çok sayıda sözcük çifti çok sayıda p değeri üretir; **Benjamini–Hochberg FDR** (1995)
       yöntemiyle bu değerler güvenilir q değerlerine dönüştürülür.

    ### 8.2 Elle Doğrulanabilir Oyuncak Örnek
    *a* sözcüğünün dilim sıklıkları: [1, 2, 3, 4]; *b* sözcüğü: [2, 4, 6, 8] $\Rightarrow$ Birebir aynı *eğri*
    olduğundan Pearson r = 1, Spearman ρ = 1, kosinüs = 1.
    *c* sözcüğü: [4, 3, 2, 1] $\Rightarrow$ r = −1, kosinüs = 0.84.
    [4, 0, 0, 0] dağılımı için: $\mu = 1, \sigma = \sqrt{3} \Rightarrow V = \sqrt{3} \Rightarrow D = 1 - \sqrt{3}/\sqrt{3} = \mathbf{0}$ (bütünüyle tek bir bölüme yığılmış).
    """),
          komut_kilavuzu("Toplu KWIC Komutları", [
              ("BatchKwicAnalyzer().analyze(words, texts, field='lem')", "Birden çok terimi veya anlamsal alan sözlüğünü metinler boyunca çözümleme", "bk.analyze(['robot', 'insan'], texts)"),
              ("result.summary()", "Terim başına toplam bulgu, per10k sıklık ve Juilland D yayılım tablosu", "display(out.summary())"),
              ("result.pairwise()", "İkili Pearson r, Spearman rho, kosinüs benzerliği ve FDR q değerleri", "display(out.pairwise())"),
              ("result.matrix('pearson_r')", "Terim dilim profilleri arasındaki kare korelasyon matrisi", "out.matrix('pearson_r')"),
          ]),
          code("""
    a, b, cvec = [1, 2, 3, 4], [2, 4, 6, 8], [4, 3, 2, 1]
    print("pearson a,b:", stats.pearson(a, b)[0], "| a,c:", stats.pearson(a, cvec)[0])
    print("kosinus a,c:", round(stats.cosine(a, cvec), 3))
    print("Juilland D [4,0,0,0] =", round(stats.juilland_d([4, 0, 0, 0]), 6),
          "| [1,1,1,1] =", stats.juilland_d([1, 1, 1, 1]))
    """),
          md("""
    ### 8.3 Türkçe Metinler Üzerinde Yürütme (Sözlükbirimler, Ham Görünüm)
    Bir **liste** (her sözcük bağımsız) ya da bir **sözlük** (birleştirilecek adlandırılmış gruplar) verilebilir:
    `{"makine terimleri": ["robot", "makine"], "insan terimleri": ["insan", "kişi"]}`.
    """),
          code("""
    bk = batch_kwic.BatchKwicAnalyzer()
    turkish = list(loader.load_all_turkish())
    words = ["robot", "insan", "makine", "bilgisayar", "uzay", "dünya"]
    out = bk.analyze(words, turkish, field="lem")
    display(out.counts); display(out.rates.round(1)); display(out.summary().round(3))
    """),
          code("""
    display(out.pairwise().round(3))
    fig = viz.heatmap(out.rates, "10 000 Akan Sözcük Başına Sıklık (Per10k)", fmt=".0f"); plt.show()
    fig = viz.heatmap(out.matrix("pearson_r"), "Sözcük Profilleri Arasında Pearson r Bağıntısı", cmap="vlag",
                      center=0, fmt=".2f"); plt.show()
    fig = viz.chunk_dispersion({k: out.chunks[k] for k in ["robot", "insan"]}, out.codes); plt.show()
    """),
          md("**Adlandırılmış Gruplar** (Birleştirilmiş Anlamsal Alanlar) ve İçerik Sözcüğü Görünümü:"),
          code("""
    groups = {"makine alanı": ["robot", "makine", "bilgisayar"], "insan alanı": ["insan", "kişi", "adam"]}
    g_raw = bk.analyze(groups, turkish, "lem")
    g_con = bk.analyze(groups, turkish, "lem", filter_function_words=True, mode="drop")
    display(g_raw.summary().round(3)); display(g_con.summary().round(3))
    display(g_raw.pairwise().round(3))
    """),
          tuzaklar(["Tek bir metnin dilimleri **içsel bağıntılıdır (otokorelasyon)**: buradaki p değerleri bir tarama aracıdır — bilimsel raporda öncelikle r / ρ / kosinüs ve D değerleri aktarılmalıdır.",
                    "Bir metinde hiç geçmeyen bir sözcük tümüyle sıfırdan oluşan bir profil verir: Pearson/Spearman NaN, kosinüs ise 0 döndürür — bu beklenen matematiksel davranıştır, hata değildir.",
                    "Çok kısa metinlerde (*The Light* gibi) 10 dilim her biri ~400 sözcüğe karşılık gelir; bu durumda D metriğinde gürültü artabilir."]),
          alistirmalar([("İngilizce kaynak metinlerde `robot`, `human`, `machine` sözcüklerinin yayılımını karşılaştırın.",
                         "```python\nbk.analyze(['robot', 'human', 'machine'], list(loader.load_all_english()), 'lem').summary()\n```")]),
          akademik_not("""
          **Çevresel Türlerde Anlamsal Alanlar ve Sözcüksel Yayılım (Gries 2008; Juilland 1964):**
          Yalnızca ham terim sıklığı, bir sözcüğün genel tür repertuarına mal olup olmadığını ya da
          belirli bir sahneye sıkışıp kalmış bir anlık buluş mu olduğunu açıklayamaz. Juilland'ın $D$
          katsayısı dağılımın türdeşliğini ölçerek, araştırmacının kanonlaşmış bilimkurgu terimlerini
          (yüksek $D$) geçici veya yerel kullanımlardan ayırt etmesini sağlar.
          """),
          ]

    # ------------------------------------------------------------------ Bölüm 9
    c += [bolum_basligi(9, "Sözcüksel Zenginlik ve Çeşitlilik (LancsBox-X Ailesi)", 35,
                         ["Ham TTR oranının neden farklı uzunluktaki metinleri karşılaştıramayacağını açıklayabilme",
                          "14'ten fazla sözcüksel çeşitlilik metriğini hesaplayabilme ve yorumlayabilme",
                          "Radar grafiği, MATTR hareketli ortalama yörüngesi ve Zipf eğrilerini okuyabilme"],
                         "Bölüm 0–2", "Her yazarın sözvarlığı ne kadar zengin — metin boyundan bağımsız adil ölçüm."),
          md("""
    ### 9.1 Kuramsal Çerçeve: Metin Uzunluğu Sorunu
    **TTR (Type-Token Ratio = Sözcük Türü / Sözcükbirim Oranı)**, bir metin uzadıkça kaçınılmaz olarak
    *düşer*; çünkü eklenen her yeni sözcükbirimin daha önce geçmiş bir sözcüğün tekrarı olma olasılığı
    artar (Heaps Yasası). Bu nedenle bir öykü ile kalın bir romanın ham TTR değerleri asla doğrudan
    karşılaştırılamaz. Modern derlembilim, metin uzunluğundan (yaklaşık olarak) bağımsız metrikler
    geliştirmiştir: **STTR** (1000 sözcüklük standart blokların ortalama TTR'si), **MATTR** (kayan pencere
    üzerinde hareketli ortalama TTR; Covington & McFall 2010), **MTLD** (McCarthy & Jarvis 2010) ve
    **HD-D** (McCarthy & Jarvis 2007, 2010; hipergeometrik modelleme).
    *LancsBox X* (Brezina, Weill-Tessier & McEnery 2021) yazılımının sunduğu bu zengin aileyi burada
    sıfırdan uyguluyoruz:

    | Metrik | Formül | Yüksek Değer Anlamı | Uzunluktan Bağımsız mı? |
    |---|---|---|---|
    | TTR | $V / N$ | Daha çeşitli | ❌ $N$ arttıkça çöker |
    | Guiraud R | $V / \sqrt{N}$ | Daha çeşitli | ❌ Kısmen düzeltir |
    | CTTR (Carroll) | $V / \sqrt{2N}$ | Daha çeşitli | ❌ Kısmen düzeltir |
    | Herdan C | $\ln V / \ln N$ | Daha çeşitli | ❌ |
    | Dugast U | $\ln^2 N / (\ln N - \ln V)$ | Daha çeşitli | ❌ |
    | Maas a² | $(\ln N - \ln V) / \ln^2 N$ | **Daha az** çeşitli | ❌ |
    | Yule K | $10^4 (\sum m^2 V_m - N) / N^2$ | **Daha az** çeşitli (tekrarlayıcı) | ✅ Evet |
    | Simpson D | $\sum n(n-1) / (N(N-1))$ | **Daha az** çeşitli | ✅ Evet |
    | Honoré R | $100 \ln N / (1 - V_1/V)$ | Daha zengin sözvarlığı | ❌ |
    | Hapax % | $V_1 / V$, $V_1 / N$ | Tek seferlik sözcük çokluğu | ❌ |
    | STTR (L=1000) | 1000 sözcüklük blokların ortalama TTR'si | Daha çeşitli | ✅ Evet |
    | MATTR (w=100) | Kayan pencere ortalama TTR'si | Daha çeşitli | ✅ Evet |
    | MTLD | Ortalama faktör uzunluğu (TTR $\le 0.72$), ileri/geri ortalaması | Daha çeşitli | ✅ Evet |
    | HD-D | $\sum (1 - C(N-f, 42)/C(N, 42)) / 42$ (hipergeometrik çekim) | Daha çeşitli | ✅ Evet |

    ### 9.2 Elle Doğrulanabilir Oyuncak Örnek
    Sözcükler: `the cat saw the dog the dog saw the cat` ($N = 10$): sözcük türleri {the: 4, cat: 2, dog: 2, saw: 2}
    $\Rightarrow V = 4$, $\\text{TTR} = 0.4$, $\\text{Guiraud} = 4 / \sqrt{10} = 1.26$,
    $\\text{Yule K} = 10^4(16 + 3 \cdot 4 - 10) / 100 = \mathbf{1800}$,
    $\\text{Simpson D} = (12 + 2 + 2 + 2) / 90 = \mathbf{0.2}$ — tümü `tests/test_corpus_toolkit.py` içinde doğrulanmıştır.
    """),
          komut_kilavuzu("Çeşitlilik Yöntemleri ve Komutları", [
              ("diversity.diversity_metrics(forms)", "14+ LancsBox-X metriğinin tümünü sözlük olarak döndürür", "diversity.diversity_metrics(forms)"),
              ("diversity.mattr(forms, window=100)", "Kayan pencere boyunca hareketli ortalama TTR", "diversity.mattr(forms, 100)"),
              ("diversity.mtld(forms, threshold=0.72)", "İleri ve geri MTLD geçişlerinin ortalaması", "diversity.mtld(forms)"),
              ("diversity.hdd(forms, sample_size=42)", "Hipergeometrik HD-D örnekleme beklentisi", "diversity.hdd(forms)"),
              ("analysis.diversity_for(loader, texts, field='lem')", "Birden fazla metin için önbellekli özet tablosu", "analysis.diversity_for(loader, texts)"),
          ]),
          md("#### 9.3 Metin Uzunluğu Sorununu Kendi Gözlerinizle Görün"),
          code("""
    text = loader.load_text("IR-IA")
    print(loader.registry.display(text))
    forms = TokenView(text, "lem", False).analysed()
    sizes = np.unique(np.linspace(500, len(forms), 14).astype(int))
    rows = [{"N": n, "TTR": diversity.ttr(forms[:n]),
             "MATTR_100": diversity.mattr(forms[:n], 100), "MTLD": diversity.mtld(forms[:n])}
            for n in sizes]
    df = pd.DataFrame(rows).set_index("N")
    ax = df[["TTR", "MATTR_100"]].plot(marker="o", figsize=(7, 4), title="TTR metin boyuyla çöker; MATTR ise dirençlidir")
    plt.show(); display(df.round(3).T)
    text.evict()
    """),
          md("#### 9.4 13 Metnin Çeşitlilik Profili (Sözlükbirimler, Ham Görünüm) — İlk çalıştırmadan sonra önbelleklenir"),
          code("""
    div_raw = analysis.diversity_for(loader, loader.load_all(), field="lem", filter_function_words=False)
    show_table(div_raw.round(3), page_size=20, title="Sözcüksel Çeşitlilik (13 Metin — Ham Sözlükbirimler)")
    """),
          code("""
    div_con = analysis.diversity_for(loader, loader.load_all(), field="lem", filter_function_words=True)
    show_table(div_con[["N", "V", "TTR", "STTR", "MATTR_100", "MTLD", "HD_D", "Yule_K", "Hapax_types_pct"]].round(3),
               page_size=20, title="Sözcüksel Çeşitlilik (İçerik Sözlükbirimleri)")
    """),
          code("""
    # Yüzey sözcük (token) ve sözlükbirim (lemma) çeşitliliği: Sondan eklemelilik Türkçede token türlerini şişirir
    div_tok = analysis.diversity_for(loader, loader.load_all_turkish(), field="tok")
    cmp = pd.DataFrame({"MATTR_100 (tokens)": div_tok["MATTR_100"],
                        "MATTR_100 (lemmas)": div_raw.loc[div_tok.index, "MATTR_100"]})
    display(cmp.round(3))
    """),
          code("""
    # Noktalama kiplerinin çeşitliliğe etkisi: drop (standart) vs strip (birleştir) vs split (ayrıştır)
    t_samples = [loader.load_text("BR-SM"), loader.load_text("KT-OK")]
    div_p_drop = analysis.diversity_for(loader, t_samples, field="tok", punct="drop")
    div_p_strip = analysis.diversity_for(loader, t_samples, field="tok", punct="strip")
    div_p_split = analysis.diversity_for(loader, t_samples, field="tok", punct="split")
    p_comp = pd.DataFrame({
        "N (drop)": div_p_drop["N"], "V (drop)": div_p_drop["V"],
        "N (strip)": div_p_strip["N"], "V (strip)": div_p_strip["V"],
        "N (split)": div_p_split["N"], "V (split)": div_p_split["V"],
    })
    display(p_comp)
    for s in t_samples: s.evict()
    """),
          md("#### 9.5 Çeşitlilik Şekilleri: Radar Grafiği, MATTR Yörüngesi ve Zipf Eğrisi"),
          code("""
    fig = viz.diversity_radar(div_raw.loc[[i for i in div_raw.index if i.split(' · ')[0] in
                                           ('IR-IA','BR-SM','O-SM','ASD-PKD','KT-OK','SCS-OK')]]); plt.show()
    sel = [loader.load_text(c) for c in ("IR-IA", "BR-SM", "O-SM")]
    for s in sel: print(loader.registry.display(s))
    traj = analysis.mattr_trajectories_for(sel, window=500)
    fig = viz.mattr_trajectories(traj, 500); plt.show()
    fig = viz.zipf_plot(analysis.zipf_for(sel)); plt.show()
    for s in sel: s.evict()
    """),
          tuzaklar(["`STTR` metriği $N < 1000$ olduğunda bir uyarı vererek TTR değerine geri döner; benzer şekilde `MATTR` $N < w$ durumunda TTR'ye döner. *The Light* metni (~4 000 sözcük) sınırdadır; dikkatle değerlendirilmelidir.",
                    "Dugast ve Honoré metrikleri, $V = N$ veya $V_1 = V$ olduğunda tanımsız (NaN) kalır.",
                    "Karşılaştırma yaparken her zaman **sözlükbirim ile sözlükbirimi**, **ham görünüm ile ham görünümü** eşleştirin."]),
          alistirmalar([("Hangi yerli bilimkurgu romanı en yüksek MTLD değerine sahiptir (sözlükbirimler, içerik görünümü)?",
                         "```python\nd = div_con.reset_index()\nd[d['index'].str.startswith(('SCS-OK', 'O-SM', 'SU-ZB'))].nlargest(1, 'MTLD')\n```")]),
          akademik_not("""
          **Çeviri Dili Sadeleşmesi ve Sözcüksel Repertuar (Baker 1993; Toury 2012):**
          Aynı yazar-çevirmenin *yerli telif* yapıtlarında, *çeviri* yapıtlarına kıyasla daha yüksek
          çeşitlilik gözlenmesi, çeviribilim literatüründeki **normalleşme / standartlaşma** evrenseliyle
          (Baker 1993) uyumludur. Bununla birlikte çevirideki düşük çeşitlilik, kaynak metnin üslubundan da
          (Asimov'un yalın ve denetimli sözvarlığı) kaynaklanabilir. Metrikler her zaman dizin satırlarıyla
          birlikte okunmalıdır.
          """),
          ]
    return c
