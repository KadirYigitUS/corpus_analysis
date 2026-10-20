"""Bölüm 0–5 (Türkçe): Yönelim, derlem mimarisi, bellek yönetimi, hizalama, sözcük türü (POS) ve bağımlılık ağaçları."""

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

    # ------------------------------------------------------------------ Bölüm 0
    c += [md("""
    # 📖 Türk Bilimkurgu Yazar-Çevirmenleri Derlem Analizi
    ### Temelden İleriye, Akademik ve Bellek Korumalı Derlembilim Not Defteri

    **Kapsam ve Bağlam.** Bu not defteri, modern Türk bilimkurgu edebiyatının öncü kuşağını
    temsil eden **üç öncü yazar-çevirmenin** yapıtlarını incelemektedir:
    **Selma Mine**, **Zühtü Bayar** ve **Özlem Kurdoğlu** — toplamda **13 metin**:
    - **5 İngilizce Kaynak Metin**: Asimov (*I, Robot*), Anderson (*The Light*), Leinster (*The Lonely Planet*), London (*The Scarlet Plague*), Dick (*A Scanner Darkly*);
    - **5 Türkçe Çeviri**: *Ben, Robot* (Mine 1983), *Aydınlık* (Bayar 1998), *Yalnız Gezegen* (Bayar 1998), *Kıyametten Sonra* (Bayar 1998), *Karanlığı Taramak* (Kurdoğlu 1998);
    - **3 Özgün Yerli Türkçe Bilimkurgu Romanı**: *OBİ,J.S.927* (Mine 1980), *Sahte Uygarlık* (Bayar 1999), *Son Cephede Şafak* (Kurdoğlu 2000).

    Bu 13 metin, doktora tezinin 18 kitaplık geniş analitik derleminin (8 yazar-çevirmen, 10 çeviri metin, 8 yerli roman)
    kurucu çekirdeğini oluşturmaktadır. Arayüzdeki her menü, tablo ve ileti **yazarın tam adını ve kitabın tam başlığını**
    gösterir (`BR-SM` gibi kısa kodlar yalnızca iç anahtar olarak kullanılır).

    **Öğretim Yöntemi.** Her bölüm tutarlı bir pedagojik şablonu izler:
    🎯 Öğrenme hedefleri → 🧪 Elle doğrulanabilir küçük oyuncak örnekler →
    🧰 Parametre ve komut kılavuzu → ▶️ Gerçek derlem üzerinde çalışan Python kodu → ⚠️ Sık yapılan hatalar →
    ✏️ Çözümlü alıştırmalar → 🎓 Kuramsal çerçeve ve akademik literatür bağlantıları (Even-Zohar, Toury, Simeoni, Biber).
    Hiçbir işlem bir kara kutu değildir: her istatistiksel formül `corpus_toolkit/` içinde sıfırdan,
    okunabilir Python ile yazılmış ve birim testlerle doğrulanmıştır.

    | Renk | Anlamı |
    |---|---|
    | 🟦 Camgöbeği rozet | İngilizce Kaynak Metin (Source) |
    | 🟧 Kehribar rozet | Türkçe Çeviri Metin (Translation) |
    | 🟩 Zümrüt rozet | Yerli Özgün Türkçe Bilimkurgu Romanı (Indigenous) |
    | 🌹 Gül kurusu vurgu | Arama düğüm sözcüğü (*node word*) |
    | Şekiller: Mor / Yeşil / Mavi | Selma Mine / Zühtü Bayar / Özlem Kurdoğlu |
    """),
          bolum_basligi(0, "Yönelim, Terimler ve Önbellek Politikası", 10,
                        ["**Sözcükbirim (token)**, **sözcük türü (type)**, **sözlükbirim (lemma)** kavramlarını ayırt edebilme",
                         "**Ham (raw)** ve **içerik (content)** görünümleri ile **drop / mask** aralık farklarını kavrama",
                         "Bu çalışmanın neden *tembel yükleme (lazy)* ve *önbellek (cache)* kullandığını açıklayabilme",
                         "Önbellek politikasını (sakla / temizle) bilinçli olarak seçebilme"],
                        "Yok", "Hesaplayacağınız her istatistiği belirleyen üç temel anahtar."),
          md("""
    ### 0.1 Temel Dilbilim ve Derlembilim Terimleri

    | Terim | Tanım | Örnek (Türkçe) |
    |---|---|---|
    | **Sözcükbirim (Token)** | Metinde geçen her bir bağımsız sözcük veya noktalama birimi | `robotların` |
    | **Sözcük Türü (Type)** | Tekrarlardan arındırılmış *özgün* sözcük biçimi | Metinde kaç kez geçerse geçsin `robotların` bir kez sayılır |
    | **Sözlükbirim (Lemma / Taban)** | Biçimbilimsel çözümleme sonrası elde edilen sözlük tabanı | `robot` |
    | **İçerik Sözcüğü (Content word)** | Açık sözcük sınıfları: AD, EYLEM, SIFAT, BELİRTEÇ, ÖZEL AD, SAYI | `robot`, `yap-`, `hızlı` |
    | **İşlevsel Sözcük (Function word)** | Kapalı dilbilgisel sınıflar: BELİRTEÇ, ADIL, İLGEÇ, BAĞLAÇ, ÜNLEM | `bir`, `ve`, `bu`, `ile` |

    Türkçe **sondan eklemeli (agglutinative)** bir dildir: tek bir sözlük tabanı çok sayıda yüzey biçimi üretir
    (`robot, robotlar, robotların, robotlara, robotlaşmak …`). Dolayısıyla *lemma* analizi, yüzey sözcük analizinin
    dağıttığı anlamsal birimleri bir araya getirir. Bu nedenle buradaki her araç `field='lem'` **ve** `field='tok'`
    seçeneklerine sahiptir.

    ### 0.2 Üç Temel Analiz Anahtarı
    | Anahtar | Değerler | İşlevi |
    |---|---|---|
    | `field` | `'tok'` / `'lem'` | Yüzey sözcüklerini (`tok`) veya sözlük tabanlarını (`lem`) analiz eder |
    | `filter_function_words` | `False` (**ham**) / `True` (**içerik**) | `scripts/passim_analysis` kurallarını uygular; işlevsel sözcükleri süzerek yalnızca anlamsal içeriğe odaklanır |
    | `mode` | `'drop'` / `'mask'` | İşlev sözcükleri gizlendiğinde: *drop* onları diziden tamamen çıkarır (±5 pencere = 5 içerik sözcüğü); *mask* konumları korur fakat işlev sözcüklerini eşleşmeye kapatır |

    ### 0.3 Neden Tembel Yükleme (Lazy) ve Önbellek?
    Disk üzerindeki pickle dosyaları liste sütunlarını metin olarak saklar; bunları her seferinde ayrıştırmak
    roman başına ≈ 2 saniye sürer. Geliştirdiğimiz mimari: (1) metni **yalnızca ihtiyaç duyulduğunda** yükler,
    (2) bellek dostu kategorik tablolara dönüştürür (70.000 sözcük için ≈ 7 MB), (3) bu tabloları `data/corpus_analysis/.cache/`
    altında **Parquet formatında önbelleğe alır**, ve (4) işi bittiğinde RAM'den temizler (`text.evict()`).
    """),
          md("""
    ### 0.4 Adım Adım Oyuncak Örnek: Üç Anahtarın Çalışması
    Örnek Cümle: *“Robotlar insanları gördü ve hızla kaçtı .”*
    - **Sözcükbirimler (Token, N=7)**: `['Robotlar', 'insanları', 'gördü', 've', 'hızla', 'kaçtı', '.']` (V=7 tip)
    - **Sözlükbirimler (Lemma, N=7)**: `['robot', 'insan', 'gör', 've', 'hız', 'kaç', '.']`
    - **İçerik Sözcükleri (`filter_function_words=True`, noktalama hariç)**: `['robot', 'insan', 'gör', 'hız', 'kaç']` (5 sözcük; `ve` bağlaçtır süzülür, `.` noktalamadır hariç tutulur).
    - **`drop` modu penceresi (`gör` çevresinde ±1)**: `[insan, hız]` (ardışık içerik sözcükleri)
    - **`mask` modu penceresi (`gör` çevresinde ±1)**: `[insan, ve]` (orijinal metin akışı korunur, `ve` düğüm/eşdizimli olamaz)
    """),
          komut_kilavuzu("Analiz Seçenekleri ve Anahtarlar", [
              ("field='lem'", "Sözlük tabanlı (lemmatize) temsil (Türkçe için önerilir)", "TokenView(text, field='lem')"),
              ("field='tok'", "Yüzey biçimli sözcükbirim temsili", "TokenView(text, field='tok')"),
              ("filter_function_words=True", "Yalnızca içerik sözcükleri (kapalı sınıflar elenir)", "TokenView(text, filter_function_words=True)"),
              ("mode='drop'", "İşlev sözcüklerini diziden çıkararak ardışık içerik zinciri kurar", "TokenView(text, filter_function_words=True, mode='drop')"),
              ("mode='mask'", "Metin akış konumlarını korur, işlev sözcüklerini maskeler", "TokenView(text, filter_function_words=True, mode='mask')"),
          ]),
          code("""
    import os, sys, warnings
    from pathlib import Path

    # Not defteri çalışma dizinindedir; corpus_toolkit paketini yüklenebilir yapıyoruz
    sys.path.insert(0, str(Path.cwd()))
    warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")

    import numpy as np
    import pandas as pd
    import nltk
    import matplotlib.pyplot as plt
    from IPython.display import HTML, display

    from corpus_toolkit import (CorpusLoader, TokenView, enable_interactive_tables,
                                show_parallel, show_table)
    from corpus_toolkit import (alignment, analysis, batch_kwic, collocation, depviz, diversity,
                                kwic, nltk_adapter, parallel_view, pos, render, reporter, search,
                                stats, style, table_view, tfidf, viz)
    display(HTML(style.CSS))                      # HTML görünümleri için merkezi CSS
    pd.set_option("display.max_columns", 40); pd.set_option("display.width", 160)
    """),
          md("""
    ### 0.5 Önbellek Politikasını Belirleme
    Sonraki hücreyi çalıştırdığınızda `data/corpus_analysis/.cache/` önbelleğinin temizlenip temizlenmeyeceği
    sorulur (`y` temiz bir başlangıç yapar; boş geçilirse önbellek korunur).
    """),
          code("""
    loader = CorpusLoader()               # kayıt defterini kurar ve önbellek durumunu denetler
    print(loader.cache.info())
    """),
          tuzaklar(["5.000 sözcüklük kısa bir öykünün ham TTR değerini 70.000 sözcüklük bir romanla doğrudan karşılaştırmayın (Bölüm 9 bunun nedenini açıklamaktadır).",
                    "`mask` ve `drop` modları farklı pencere genişlikleri üretir — raporlarınızda hangi modu kullandığınızı mutlaka belirtin."]),
          akademik_not("""
          **Çoğuldizim Konumlanışı ve Biçemsel Değişkenler (Even-Zohar 1990; Toury 2012):**
          20. yüzyıl Türk bilimkurgusu gibi çevresel bir edebi çoğuldizimde çeviri metinler,
          özgün yazına yeni sözcüksel modeller, yapılar ve terimler (*neologism*) taşır.
          Yüzey sözcükleri (`tok`) ile sözlükbirimler (`lem`) arasında geçiş yapabilmek,
          Türkçenin zengin çekim varyasyonunu altta yatan sözvarlığı repertuarından ayrıştırmayı sağlar.
          """),
          ]

    # ------------------------------------------------------------------ Bölüm 1
    c += [bolum_basligi(1, "Derlem Envanteri ve Boyut Dağılımı", 10,
                        ["Tüm yazar-çevirmenleri, yapıtları ve çeviri çiftlerini tam adlarıyla listeleme",
                         "13 ayrıştırılmış pickle dosyasının disk üzerindeki varlığını doğrulama",
                         "Temel boyut istatistiklerini (tümce ve sözcük sayıları) etkileşimli sayfalı tablolarda inceleme"],
                        "Bölüm 0", "Verinizi ölçmeden önce onu envanteriyle tanıyın."),
          md("""
    ### 1.1 Neden Önce Envanter?
    Derlem dilbilim öncelikle *derlem tasarımı* ile başlar (Baker 1993; Biber 1988): derlemde ne var,
    büyüklüğü nedir ve ne derece dengelidir? İncelediğimiz alt derlem asimetriktir — *The Light* ≈ 4.000
    sözcük iken *A Scanner Darkly* ≈ 88.000 sözcüktür. Bu nedenle sonraki bölümlerde uzunluktan bağımsız
    (standartlaştırılmış) metrikler kullanılacaktır.
    """),
          md("""
    ### 1.2 Adım Adım Oyuncak Örnek: Envanter Sorgulama
    Yazar-çevirmen Selma Mine (`SM`) için envanter tablosunu filtreliyoruz:
    - Beklenen kayıt: Tam 3 kitap (1 İngilizce kaynak *I, Robot*, 1 Türkçe çeviri *Ben, Robot*, 1 yerli roman *OBİ,J.S.927*).
    - Her kayıt kod, yazar/çevirmen, başlık, tür ve yıl bilgilerini içerir.
    """),
          code("""
    inv = loader.registry.inventory()
    display(inv[inv["focal_code"] == "SM"][["code", "creator", "title", "type", "year"]])
    """),
          komut_kilavuzu("Kayıt Defteri ve Etkileşimli Tablo Komutları", [
              ("loader.registry.inventory()", "13 metnin tüm üstverisini içeren DataFrame döndürür", "show_table(loader.registry.inventory())"),
              ("loader.registry.verify_files()", "Tüm .pickle.xz dosyalarının diskte var olduğunu doğrular", "loader.registry.verify_files()"),
              ("show_table(df, page_size=20)", "Sayfalı (20 satır/sayfa), sıralanabilir ve sütun genişliği ayarlanabilir tablo", "show_table(inv, page_size=20, title='Envanter')"),
              ("enable_interactive_tables()", "Tüm DataFrame çıktılarını etkileşimli tabloya dönüştürür", "enable_interactive_tables(page_size=20)"),
              ("loader.registry.display(rec)", "Okunabilir tam etiket üretir: 'Yazar — Başlık [KOD]'", "print(loader.registry.display('BR-SM'))"),
          ]),
          md("### 1.3 Tüm Derlemin Doğrulanması ve Boyut Dağılımı (Etkileşimli Sütunlu Tablo Görünümü)"),
          code("""
    show_table(loader.registry.inventory(), page_size=20, title="Derlem Envanteri (13 Metin)")
    show_table(loader.registry.verify_files(), page_size=20, title="Disk Pickle Doğrulama Tablosu")
    """),
          code("""
    loader.load_all().describe();
    sizes = loader.load_all().summary()          # İlk çalıştırma önbelleği kurar
    show_table(sizes.sort_values(["author_translator", "type"]), page_size=20, title="Derlem Boyut Özeti")
    """),
          code("""
    fig, ax = plt.subplots(figsize=(9, 4))
    d = sizes.merge(loader.registry.inventory()[["code", "focal_code", "year"]], on="code")
    ax.bar(d["code"], d["tokens"], color=[viz.color_for(c) for c in d["focal_code"]],
           alpha=0.85)
    ax.set_ylabel("Sözcük sayısı (noktalama dahil)"); ax.set_title("Metin Boyutları Dağılımı")
    plt.xticks(rotation=45, ha="right"); plt.show()
    """),
          tuzaklar(["Buradaki `tokens` sütunu noktalama işaretlerini de içerir; sonraki analizlerde noktalama elenerek *akan sözcükler (running words)* kullanılır.",
                    "Metin uzunluklarını kontrol etmeden yazarlar arası istatistiksel genellemeler yapmayın."]),
          alistirmalar([("Hangi yazar-çevirmen en büyük *yerli* metne sahiptir ve kaç sözcükten oluşur?",
                         "```python\nsizes[sizes['type']=='indigenous'].nlargest(1,'tokens')"
                         "[['author_translator','title','tokens']]\n```")]),
          akademik_not("""
          **Derlem Temsiliyeti ve Yazar-Çevirmen Örneklemesi (Toury 2012; Biber 1988):**
          Selma Mine, Zühtü Bayar ve Özlem Kurdoğlu üçlüsü, modern Türk bilimkurgu yazınının kurucu
          kuşağını teşkil eder. Hem çeviri yapıtlarının hem de özgün romanlarının derleme dahil edilmesi,
          çeviri normlarının yerli yazar habitusuna aktarımını incelemek için doğal bir yarı-deneysel
          karşılaştırma olanağı sunar.
          """),
          ]

    # ------------------------------------------------------------------ Bölüm 2
    c += [bolum_basligi(2, "Tembel Yükleme ve Bellek Yönetimi (RAM)", 15,
                        ["8 farklı derlem yükleyici yöntemini kullanabilme",
                         "Sözcük ve tümce tablolarının bellek dostu mimarisini inceleme",
                         "Süreç belleğini ölçme ve `evict()` ile RAM'i serbest bırakma"],
                        "Bölüm 0–1", "İhtiyacın olanı yükle, işin bittiğinde belleği geri ver."),
          md("""
    ### 2.1 Sekiz Temel Derlem Yükleyici
    | Yöntem | Döndürdüğü Nesne | Kapsam |
    |---|---|---|
    | `load_all_english()` | CorpusSelection | 5 İngilizce kaynak roman |
    | `load_all_turkish()` | CorpusSelection | 5 çeviri + 3 yerli roman |
    | `load_translation_pairs([author])` | ParallelCorpus | 5 hizalanmış çeviri çifti |
    | `load_indigenous([author])` | CorpusSelection | 3 yerli Türkçe roman |
    | `load_all()` | CorpusSelection | 13 metnin tamamı |
    | `load_author_related([author])` | CorpusSelection | Belirli bir yazarın tüm kaynak, çeviri ve yerli metinleri |
    | `load_author_turkish([author])` | CorpusSelection | Belirli bir yazarın yalnızca Türkçe metinleri |
    | `load_text(code_or_title)` | LazyCorpusText | Belirli bir tekil metin (`'BR-SM'` veya `'Karanlığı Taramak'`) |

    `author` parametresi kısa kod (`'SM'`) **veya** tam yazar adı (`'Selma Mine'`, `'ozlem kurdoglu'`) kabul eder.
    """),
          md("""
    ### 2.2 Adım Adım Bellek Yaşam Döngüsü: Yükle, Ölç ve Tahliye Et
    1. Yükleyici çağrıldığında veri tablosu henüz belleğe açılmaz (`text.is_loaded() == False`).
    2. `text.tokens` erişildiğinde Parquet/pickle tablosu RAM'e alınır (`text.is_loaded() == True`).
    3. `text.evict()` çağrıldığında tablo bellekten silinir ve çöp toplayıcı (`gc.collect()`) çalıştırılır.
    """),
          code("""
    toy_t = loader.load_text("BR-SM")
    print("tokens erişiminden önce:", toy_t.is_loaded())
    _ = toy_t.tokens
    print("tokens erişiminden sonra:", toy_t.is_loaded(), f"({toy_t.memory_mb():.1f} MB)")
    toy_t.evict()
    print("evict() sonrasında:", toy_t.is_loaded())
    """),
          komut_kilavuzu("Yükleme ve Bellek Yönetimi", [
              ("loader.load_all_english()", "5 İngilizce kaynak bilimkurgu metni", "loader.load_all_english()"),
              ("loader.load_all_turkish()", "5 çeviri + 3 yerli Türkçe bilimkurgu romanı", "loader.load_all_turkish()"),
              ("loader.load_translation_pairs(author=None)", "5 paralel hizalanmış çeviri çifti", "loader.load_translation_pairs('SM')"),
              ("loader.load_indigenous(author=None)", "3 yerli Türkçe bilimkurgu romanı", "loader.load_indigenous('ZB')"),
              ("loader.load_all()", "Odak derlemdeki 13 metnin tamamı", "loader.load_all()"),
              ("loader.load_text(identifier)", "Kod veya başlık alt-dizesiyle tekil metin yükleme", "loader.load_text('BR-SM')"),
              ("text.evict()", "DataFrame belleğini serbest bırakır ve gc.collect() tetikler", "text.evict()"),
          ]),
          code("""
    loader.load_all_english().describe()
    loader.load_all_turkish().describe()
    loader.load_translation_pairs().describe()
    loader.load_indigenous().describe()
    loader.load_author_related("Özlem Kurdoğlu").describe()
    loader.load_author_turkish("zuhtu bayar").describe();
    """),
          md("""
    ### 2.3 Sözcük ve Tümce Tablolarının Yapısı
    Her sözcükbirim bir satırdır; sütunlar: `sid` (tümce), `ti` (konum), `tok`, `lem`, `pos` (UPOS),
    `morph`, `head`, `rel` (bağımlılık), `fcl` (0 içerik / 1 işlevsel / 2 noktalama).
    """),
          code("""
    import time
    text = loader.load_text("Ben, Robot: Mekanik Adam Devri")     # henüz tembel (lazy) …
    print(loader.registry.display(text))
    t0 = time.perf_counter(); tab = text.tokens                    # … şimdi belleğe alındı
    print(f"{len(tab):,} sözcük {time.perf_counter()-t0:.2f} sn içinde · tablo ≈ {text.memory_mb():.1f} MB")
    display(tab.head(8))
    """),
          code("""
    # Soğuk vs sıcak yükleme: tahliye et, ardından Parquet önbellekten yeniden yükle
    text.evict(verbose=True)
    t0 = time.perf_counter(); _ = text.tokens
    print(f"önbellekten yeniden yükleme: {time.perf_counter()-t0:.3f} sn")
    display(loader.memory_report())
    """),
          code("""
    # Çok sayıda metin üzerinde bellek korumalı döngü: her metin kullanımdan hemen sonra tahliye edilir
    rows = []
    for t in loader.load_all().iter_evicting():
        n = len(TokenView(t, "lem", filter_function_words=True))
        rows.append((t.record.focal_name, t.record.title, n))
    pd.DataFrame(rows, columns=["author_translator", "title", "content_lemmas"])
    """),
          tuzaklar(["Bir değişkende tutulan `LazyCorpusText`, `.evict()` çağrılana (veya `iter_evicting()` kullanılana) dek tablolarını RAM'de tutar.",
                    "Bir `.pickle.xz` dosyasının güncellenmesi önbellek kaydını otomatik olarak geçersiz kılar; `.cache/` dizinini silmek her zaman güvenlidir."]),
          alistirmalar([("Zühtü Bayar'ın çeviri çiftlerini yükleyiniz ve her İngilizce/Türkçe metnin tümce sayısını yazdırınız.",
                         "```python\nfor pair, en, tr in loader.load_translation_pairs('ZB'):\n"
                         "    print(en.summary()['title'], en.summary()['n_sentences'], '→', "
                         "tr.summary()['title'], tr.summary()['n_sentences'])\n```")]),
          akademik_not("""
          **Dijital Çeviribilimde Hesaplamalı Bellek Korunumu (Sinclair 1991):**
          Kitap uzunluğundaki paralel ve karşılaştırılabilir derlemlerin analizi disiplinli bir bellek
          yönetimi gerektirir. DataFrame yapılarını yalnızca talep anında belleğe açarak, optimize edilmiş
          sütun tiplerini Parquet olarak önbellekleyerek ve işi biten yapıları tahliye ederek yüz binlerce
          etiketli sözcüğü 1.5 GB RAM sınırının altında analiz edebiliyoruz.
          """),
          ]

    # ------------------------------------------------------------------ Bölüm 3
    c += [bolum_basligi(3, "Paralel Derlem Hizalama Yapısı ve NDA Yan Yana Görünüm", 20,
                        ["Tümce hizalamalarını 1:1, 1:N, N:1, N:M, atlama (omission) ve ekleme (addition) olarak sınıflandırma",
                         "`R_sent`, sözcük ve karakter genişleme oranlarını hesaplayıp yorumlama",
                         "Neologism Dictionary Annotation (NDA) yan yana paralel görünümüyle İngilizce ⇄ Türkçe hizalı öğeleri inceleme"],
                        "Bölüm 0–2", "Çevirmenler tümceleri nasıl böler, birleştirir ve yeni sözcükleri nasıl aktarır?"),
          md("""
    ### 3.1 Kuramsal Arka Plan: Çeviri Hizalaması
    Tümce hizalayıcı, İngilizce ve Türkçe tümce *gruplarını* eşleştirir. Grubun **kardinalite şekli**
    çevirmen kararlarının somut izidir (Toury 2012: *yeterlik* vs *benimsenirlik*; Baker 1993:
    *açıklayıcılık, sadeleştirme*):

    | Tür | (İngilizce, Türkçe) | Okuma |
    |---|---|---|
    | 1:1 | (1, 1) | Tümce sınırı korunmuş |
    | 1:N | (1, n≥2) | İngilizce tümce **bölünmüş** |
    | N:1 | (n≥2, 1) | Tümceler **birleştirilmiş** |
    | N:M | (n≥2, m≥2) | Yeniden yapılandırılmış |
    | omission | (n, 0) | Türkçe karşılığı olmayan İngilizce tümce |
    | addition | (0, m) | İngilizce karşılığı olmayan Türkçe tümce |

    `R_sent = Türkçe tümce sayısı ÷ İngilizce tümce sayısı` (>1: Türkçe çeviri daha fazla tümce kullanır).

    ### 3.2 Adım Adım Oyuncak Örnek
    Altı hizalama grubu: şekiller (1,1), (1,1), (1,2), (2,1), (1,0), (0,1).
    İngilizce tümceler = 1+1+1+2+1+0 = 6; Türkçe = 1+1+2+1+0+1 = 6 → `R_sent = 1.0`.
    İki grupta yeniden yapılandırma olmasına rağmen genel oran 1.0 çıkabilir — *1'e yakın bir oran zıt yönlü hareketleri gizleyebilir*.
    """),
          code("""
    toy = [(1,1),(1,1),(1,2),(2,1),(1,0),(0,1)]
    print([alignment.alignment_type(a, b) for a, b in toy])
    print("R_sent =", sum(b for _, b in toy) / sum(a for a, _ in toy))
    """),
          komut_kilavuzu("Hizalama ve NDA Yan Yana Paralel Görünüm Komutları", [
              ("alignment.alignment_type(n_en, n_tr)", "Kardinaliteyi '1:1', '1:N', 'N:1', 'N:M', 'omission', 'addition' olarak sınıflandırır", "alignment.alignment_type(1, 2)"),
              ("AlignmentStructureAnalyzer(cache).summary(pairs)", "Tüm çeviri çiftleri için yüzde dağılımı ve R_sent özet tablosu", "ana.summary(pairs)"),
              ("AlignmentStructureAnalyzer.cardinality_table(pair)", "Hizalama grubu başına sözcük sayısı ve tür tablosu", "ana.cardinality_table(pair)"),
              ("show_parallel(loader, pair_or_code, ais, overlay=True)", "NDA sözlük bağlantıları, SVG çizgileri ve sözlükbirimlerle EN ⇄ TR yan yana görünüm", "show_parallel(loader, 'I_Robot', [3350, 4288, 4313])"),
              ("AlignmentIndex.texts(ai)", "ai numaralı hizalama grubu için (eng_text, tur_text) döndürür", "idx.texts(14)"),
          ]),
          code("""
    pairs = [p for p, _, _ in loader.load_translation_pairs()]
    ana = alignment.AlignmentStructureAnalyzer(loader.cache)
    summary = ana.summary(pairs)
    show_table(summary.round(2), page_size=20, title="Paralel Hizalama Yapısı Özeti")
    """),
          code("""
    fig = viz.alignment_stacked(summary); plt.show()                       # Şekil 1A
    tables = {p.tur.title[:28]: ana.cardinality_table(p) for p in pairs}
    fig = viz.alignment_scatter(tables); plt.show()                        # Şekil 1B
    """),
          md("""
    ### 3.3 Yorumlama Kılavuzu ve NDA Yan Yana Paralel Derlem Görünümü
    - **Yüksek 1:1** → Çeviri tümce sınırlarını korur; yüksek **1:N** → İngilizce uzun tümceler Türkçede bölünmüştür.
    - **omission / addition** çevirmen kararı olabileceği gibi **hizalayıcı/baskı farkı** da olabilir; yorumlamadan önce örnekleri inceleyin.
    - **`show_parallel(loader, pair, ais)`** işlevi, `scripts/Neologism_Dictionary_Annotation` (NDA) aracının
      yöntembilimini ve veri akışını içe aktarır: her sözcük iki katmanlı bir kapsül (`yüzey biçim` + `lemma·UPOS`)
      olarak çizilir; eşlenmiş iki dilli yeni sözcükler (`initial_dictionary.pickle`) **SVG bağlantı çizgileriyle (`L#`)**
      birleştirilir; tek dilli *Gerçekdışı Özolgular* (`single_eng` camgöbeği / `single_tur` gül kurusu) ve yüksek
      adaylık puanlı sözcükler (`scored_alignment_rows.pickle`) renklendirilir; her `ai` grubunun altında
      **Etiket Atamaları Özeti (Current Label Attributions)** yer alır.
    """),
          code("""
    # NDA yan yana paralel görünüm: eşlenmiş iki dilli çiftler (L#), tek dilli özolgular ve SVG bağlantı çizgileri
    show_parallel(loader, "I_Robot", [3350, 4288, 4313], overlay=True, hits={"brain"})
    """),
          code("""
    # Bir çeviri çiftindeki ilk atlamaları (omission) doğrudan metin üzerinde inceleyelim
    pair = pairs[1]
    idx = loader.alignment_index(pair)
    tab = ana.cardinality_table(pair)
    for ai in tab[tab["type"] == "omission"]["ai"].head(3):
        print(ai, "| EN:", idx.texts(ai)[0][:120])
    """),
          tuzaklar(["Yüzdeler *hizalama grupları* üzerinden, `R_sent` ise *tümceler* üzerinden hesaplanır — ikisi farklı sorulara yanıt verir.",
                    "Çok kısa metinler (*The Light*) yüzdelerde dalgalanmaya yol açabilir."]),
          alistirmalar([("Hangi çeviri çifti en yüksek N:M yeniden yapılandırma oranına sahiptir?",
                         "```python\nsummary.loc[summary['N:M_pct'].idxmax(), ['pair','N:M_pct']]\n```")]),
          akademik_not("""
          **Çeviri Normları ve Sentaktik Yeniden Yapılanma (Toury 2012; Baker 1993):**
          Toury, kaynak odaklı *yeterlik (adequacy)* ile erek odaklı *benimsenirlik (acceptability)*
          arasındaki gerilimi tanımlar. $R_{\\text{sent}}$ oranı ve 1:N bölme yüzdeleri, çevirmenin
          İngilizce karmaşık tümceleri Türkçe tümce normlarına nasıl uyarladığını somutlaştırır.
          """),
          ]

    # ------------------------------------------------------------------ Bölüm 4
    c += [bolum_basligi(4, "Sözcük Türü (POS) Karşılaştırmalı Analizi", 25,
                        ["Evrensel Sözcük Türü (UPOS) profillerini, sözcüksel yoğunluğu ve ad/eylem oranlarını hesaplama",
                         "Bir çeviri çifti içinde İngilizce kaynak ile Türkçe çeviriyi karşılaştırma",
                         "Çeviri ve yerli Türkçe metinler arasındaki farkları bootstrap güven aralıklarıyla test etme"],
                        "Bölüm 0–2", "Çevirmenler kendi telif romanlarını çevirdikleri kitaplardan farklı mı yazarlar?"),
          md("""
    ### 4.1 Kuramsal Temel: Sözcük Türleri ve Biçem
    UPOS (Evrensel Sözcük Türleri, Nivre vd. 2016) diller arası karşılaştırılabilir bir etiket kümesi sunar.
    İki klasik gösterge: **sözcüksel yoğunluk (lexical density)** = içerik sözcükleri ÷ akan sözcükler
    (Ure 1971; Halliday 1985) ve **ad/eylem oranı (noun/verb ratio)** (Biber 1988).
    Tablolarımızda sözcüksel yoğunluk = (NOUN+VERB+ADJ+ADV) ÷ noktalama dışı sözcükler × 100 olarak hesaplanır.
    İngilizce ve Türkçe *tipolojik* olarak farklılaştığından İngilizce↔Türkçe farkları kalite değil **yapısal profil**
    farkıdır. Tez için asıl anlamlı karşılaştırma Türkçe içindeki **çeviri ↔ yerli** karşılaştırmasıdır (Simeoni 1998).

    ### 4.2 Adım Adım Oyuncak Örnek
    Cümle: “The cat saw the dog .” → etiketler DET NOUN VERB DET NOUN PUNCT. Noktalama dışı sözcük = 5;
    içerik sözcükleri = NOUN, VERB, NOUN = 3 → sözcüksel yoğunluk %60; ad/eylem oranı = 2.
    """),
          komut_kilavuzu("Sözcük Türü (POS) Analiz Komutları", [
              ("PosComparativeAnalyzer().profile_table(texts)", "Her metin için UPOS % sütunları ve yoğunluk metrikleri", "P.profile_table(loader.load_all())"),
              ("PosComparativeAnalyzer().pair_comparison(en, tr)", "Paralel çeviri çifti için doğrudan UPOS karşılaştırması", "P.pair_comparison(en, tr)"),
              ("PosComparativeAnalyzer().group_comparison(g1, g2, labels)", "Alt derlemler arası ortalama farkların bootstrap güven aralıkları", "P.group_comparison(trans, indig, ('translation', 'indigenous'))"),
          ]),
          code("""
    P = pos.PosComparativeAnalyzer()
    profile = P.profile_table(loader.load_all())
    show_table(profile.round(1), page_size=50, title="13 Metnin UPOS Profil Tablosu")
    fig = viz.pos_heatmap(profile, pos.UPOS_ORDER); plt.show()             # Şekil 2A
    """),
          md("""
    ### 4.3 Tek Bir Çeviri Çifti Karşılaştırması (Şekil 2B)
    Kodları Bölüm 2'de listelenen herhangi bir çeviri çiftiyle değiştirebilirsiniz (`IR-IA ⇄ BR-SM`, `ASD-PKD ⇄ KT-OK`, …).
    """),
          code("""
    en, tr = loader.load_text("IR-IA"), loader.load_text("BR-SM")
    print(loader.registry.display(en)); print(loader.registry.display(tr))
    cmp_df = P.pair_comparison(en, tr)
    show_table(cmp_df.round(1), page_size=20, title="Çift UPOS Karşılaştırması: I, Robot ⇄ Ben, Robot")
    fig = viz.pos_pair(cmp_df, f"{en.record.title} → {tr.record.title}"); plt.show()
    en.evict(); tr.evict()
    """),
          md("""
    ### 4.4 Çeviri ve Yerli Türkçe Metinlerin Grup Karşılaştırması (Şekil 2C)
    **Metinler** üzerinden %95 bootstrap güven aralıklı UPOS ortalama farkları, ayrıca birleştirilmiş
    sayımlar üzerinden $\\chi^2$ ve Cramér V (etki büyüklüğü).
    """),
          code("""
    trans = [loader.load_text(c) for c in ["BR-SM", "A-ZB", "YG-ZB", "KS-ZB", "KT-OK"]]
    indig = list(loader.load_indigenous())
    print("Çeviriler:\\n", "\\n".join(loader.registry.display(t) for t in trans))
    print("Yerli Romanlar:\\n", "\\n".join(loader.registry.display(t) for t in indig))
    grp = P.group_comparison(trans, indig, ("translation", "indigenous"))
    show_table(grp.round(2), page_size=20, title="Çeviri vs Yerli Türkçe UPOS (Bootstrap %95 GA)")
    print(grp.attrs)
    fig = viz.pos_group(grp, ("translation", "indigenous")); plt.show()
    """),
          code("""
    # Aynı soruyu yalnızca içerik sözcükleriyle (işlevsel sözcükler gizlenmiş) inceleyelim
    grp_c = P.group_comparison(trans, indig, ("translation", "indigenous"), content_only=True)
    show_table(grp_c.round(2), page_size=20, title="Yalnızca İçerik Sözcükleri UPOS Karşılaştırması")
    """),
          tuzaklar(["İngilizce ve Türkçe için farklı etiketleyiciler kullanıldığından etiket *envanterleri* karşılaştırılabilir olsa da etiketleme *doğruluğu* birebir aynı değildir.",
                    "n=3–5 metinle hesaplanan bootstrap güven aralıkları geniştir — 'kesin kanıtlar' yerine 'uyumludur / işaret eder' dilini kullanın.",
                    "Bir kitap içindeki sözcükler bağımsız değildir: p-değerleri yerine Cramér V etki büyüklüğünü raporlayın."]),
          alistirmalar([("Yalnızca *yerli* metinler için sözcüksel yoğunluk ortalamasını hesaplayınız.",
                         "```python\nprofile[profile['type']=='indigenous']['lexical_density'].mean()\n```")]),
          akademik_not("""
          **Çevirmen Habitusu ve Çeviri Evrenselleri (Simeoni 1998; Toury 2012):**
          Çeviri Türkçenin aynı yazarın telif romanlarına kıyasla daha adcil (nominal) veya farklı yoğunlukta
          olması kaynak metin baskısıyla (*aktarım / interference*, Toury 2012) uyumludur; ancak aynı
          yazar-çevirmenin hem çeviri hem telif yapıtlarını birlikte incelemek, tür farkı ile **habitus**
          etkisini ayrıştırmamıza olanak tanır.
          """),
          ]

    # ------------------------------------------------------------------ Bölüm 5
    c += [bolum_basligi(5, "Sözdizimsel Bağımlılık Ağaçları (İngilizce ve Türkçe)", 20,
                        ["Bağımlılık ağacı gösterimini okuma ve yorumlama",
                         "spaCy displaCy tarzında iki dil için de bağımlılık yayları çizdirme",
                         "İşlev sözcüklerini karartarak (dim) ağaç bütünlüğünü bozmadan içeriği vurgulama",
                         "Hizalanmış iki dilli tümce çiftlerinin ağaçlarını alt alta görselleştirme"],
                        "Bölüm 0–2", "Sözdizimini görsel ve somut kılma."),
          md("""
    ### 5.1 Kuramsal Çerçeve: Bağımlılık Dilbilgisi
    **Bağımlılık Ağacı (Dependency Tree)**, cümledeki her bir sözcüğü (*dependent / bağımlı*)
    etiketli bir bağıntıyla bir üst ögeye (*head / baş*) bağlar; cümlenin ana yüklemi ise köktür (baş indeksi 0;
    Tesnière 1959; Nivre vd. 2016). Yaylar cümlenin üzerinde gösterilir.

    **Görselleştirme Yaklaşımı.** VNLP kütüphanesi doğrudan bir ağaç çizici sunmaz; geliştirdiğimiz
    `DependencyVisualizer`, spaCy'nin **displaCy** çizim motorunu harici model gerektirmeksizin (`manual=True`)
    çalıştırır. İngilizce etiketler ClearNLP tarzındadır (`dobj, prep, pobj`), Türkçe etiketler ise
    Evrensel Bağımlılıklar (UD) biçimindedir (`obj, case, nmod:poss`).

    ### 5.2 Adım Adım Oyuncak Örnek: 4 Sözcüklü Bir Bağımlılık Ağacı
    Cümle: *“Selma robotu gördü .”*
    - Sözcükler: `[1: Selma, 2: robotu, 3: gördü, 4: .]`
    - Baş İndeksleri: `[3, 3, 0, 3]` (0 = kök / root)
    - İlişki Etiketleri: `[nsubj, obj, root, punct]`
    - Yaylar: `Selma` (1) $\\xrightarrow{\\text{nsubj}}$ `gördü` (3); `robotu` (2) $\\xrightarrow{\\text{obj}}$ `gördü` (3).
    """),
          komut_kilavuzu("Bağımlılık Ağacı Görselleştirme Komutları", [
              ("dv.sid_of(text, (ch, p, s))", "Bölüm, paragraf ve tümce koordinatını sıralı tümce ID'sine çevirir", "sid = dv.sid_of(text, (1, 4, 4))"),
              ("dv.table(text, sid)", "Tümcenin (id, token, lemma, pos, head, deprel) tablosunu döndürür", "display(dv.table(text, sid))"),
              ("dv.html(text, sid)", "displaCy bağımlılık yaylarını içeren HTML dizesi üretir", "display(HTML(dv.html(text, sid)))"),
              ("dv.svg(text, sid)", "Ağacın vektörel SVG çıktısını üretir (makale ve tez için)", "svg_str = dv.svg(text, sid)"),
              ("dv.alignment_html(code, ai)", "Hizalama grubundaki İngilizce ve Türkçe tümceleri alt alta dizer", "dv.alignment_html('BR-SM', 4)"),
          ]),
          code("""
    dv = depviz.DependencyVisualizer(loader)
    en = loader.load_text("IR-IA")
    print(loader.registry.display(en))
    sid = dv.sid_of(en, (1, 4, 4))            # Asimov'un ünlü 'Üç Robot Yasası' tümcesi
    display(dv.table(en, sid))
    """),
          code("""
    display(HTML(style.CSS + "<div class='ct'>" + dv.html(en, sid) + "</div>"))
    """),
          code("""
    tr = loader.load_text("BR-SM")
    print(loader.registry.display(tr))
    sid_tr = dv.sid_of(tr, (1, 2, 3))         # Selma Mine'nin Türkçe çevirisi
    display(dv.table(tr, sid_tr))
    display(HTML(style.CSS + "<div class='ct'>" + dv.html(tr, sid_tr) + "</div>"))
    """),
          md("""
    ### 5.3 İki Dilli Hizalanmış Çift Ağaç Görünümü
    `alignment_html(code, ai)` işlevi, `ai` hizalama grubundaki tüm İngilizce tümcelerin ağaçlarını,
    ardından Türkçe karşılıklarının ağaçlarını alt alta çizer.
    """),
          code("""
    display(HTML(style.CSS + dv.alignment_html("BR-SM", 4)))
    """),
          code("""
    # UD-normalize etiketler yerine ham etiketler ve yalnızca içerik sözcükleri vurgulanmış görünüm
    display(HTML(style.CSS + "<div class='ct'>" + dv.html(en, sid, normalize_labels=False,
                                                       dim_function_words=True) + "</div>"))
    for t in (en, tr): t.evict()
    """),
          tuzaklar(["İşlev sözcükleri ağaç bütünlüğünü korumak için silinmez, yalnızca rengi soluklaştırılır (*dimmed*).",
                    "Ayrıştırıcı çıktıları istatistiksel modellerce tahmin edilmiştir; uzun ve karmaşık edebi tümcelerde etiket hataları görülebilir.",
                    "Çok uzun tümceler yatay kaydırma gerektirir; sıkıştırmak için `compact=True` kullanabilirsiniz."]),
          alistirmalar([("*Karanlığı Taramak* çevirisinin ilk tümcesinin bağımlılık ağacını çizdiriniz ve kök (root) sözcüğünü bulunuz.",
                         "```python\nt=loader.load_text('KT-OK'); s=dv.sid_of(t,(1,1,1)); "
                         "tab=dv.table(t,s); tab[tab['deprel']=='root']\n```")]),
          akademik_not("""
          **Çeviride Yapısal Kaymalar ve Bağımlılık Sözdizimi (Catford 1965; Tesnière 1959):**
          İngilizce tümce düzeyinde başı-önde (*head-initial, SVO*), Türkçe ise başı-sonda (*head-final, SOV*)
          bir dil tipolojisine sahiptir. İki dilli bağımlılık ağaçlarının karşılaştırılması, Catford'un
          *birim kayması (unit shift)* ve *yapı kayması (structure shift)* kavramlarını somut biçimde
          resmeder: İngilizce ilgeç öbekleri (`prep + pobj`) Türkçede ad durum eklerine dönüşür;
          bağıntı tümceleri ise eylemsi öbeklerine sıkıştırılır.
          """),
          ]
    return c
