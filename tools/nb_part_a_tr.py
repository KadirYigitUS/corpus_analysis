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

    from corpus_toolkit import CorpusLoader, TokenView
    from corpus_toolkit import (alignment, analysis, batch_kwic, collocation, depviz, diversity,
                                kwic, nltk_adapter, pos, render, reporter, search, stats, style,
                                tfidf, viz)
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
                         "Temel boyut istatistiklerini (tümce ve sözcük sayıları) inceleme"],
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
          komut_kilavuzu("Kayıt Defteri ve Envanter Komutları", [
              ("loader.registry.inventory()", "13 metnin tüm üstverisini içeren DataFrame döndürür", "display(loader.registry.inventory())"),
              ("loader.registry.verify_files()", "Tüm .pickle.xz dosyalarının diskte var olduğunu doğrular", "loader.registry.verify_files()"),
              ("loader.registry.display(rec)", "Okunabilir tam etiket üretir: 'Yazar — Başlık [KOD]'", "print(loader.registry.display('BR-SM'))"),
              ("loader.registry.resolve_author(query)", "Yazar adı veya kodundan standart yazar koduna çözer", "loader.registry.resolve_author('Selma Mine')"),
              ("loader.registry.resolve_text(query)", "Kitap başlığı veya kodundan TextRecord nesnesine çözer", "loader.registry.resolve_text('Ben, Robot')"),
          ]),
          md("### 1.3 Tüm Derlemin Doğrulanması ve Boyut Dağılımı"),
          code("""
    display(loader.registry.inventory())
    display(loader.registry.verify_files())
    """),
          code("""
    loader.load_all().describe();
    sizes = loader.load_all().summary()          # İlk çalıştırma önbelleği kurar
    display(sizes.sort_values(["author_translator", "type"]))
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
    | `load_translation_pairs()` | list[PairSpec] | 5 hizalanmış çeviri çifti |
    | `load_indigenous()` | CorpusSelection | 3 yerli Türkçe roman |
    | `load_all()` | CorpusSelection | 13 metnin tamamı |
    | `load_author_related(code)` | CorpusSelection | Belirli bir yazarın tüm kaynak, çeviri ve yerli metinleri |
    | `load_author_turkish(code)` | CorpusSelection | Belirli bir yazarın yalnızca Türkçe metinleri |
    | `load_text(code_or_title)` | LazyCorpusText | Belirli bir tekil metin |

    ### 2.2 Adım Adım Bellek Yaşam Döngüsü: Yükle, Ölç ve Tahliye Et
    Tek bir romanı yüklüyoruz, RAM kullanımını gözlemliyoruz ve `.evict()` ile belleği boşaltıyoruz.
    """),
          code("""
    print(f"Başlangıç RAM kullanımı: {loader.rss_mb():.1f} MB")
    text = loader.load_text("BR-SM")             # Selma Mine - Ben, Robot
    print(f"Tablolar yüklenmeden önce: {loader.rss_mb():.1f} MB")
    df_tok = text.tokens                         # Bu satırda Parquet önbellekten RAM'e okunur
    print(f"Tablolar yüklendikten sonra: {loader.rss_mb():.1f} MB (Sözcük tablosu satır sayısı: {len(df_tok)})")
    text.evict()                                 # Bellekten tahliye
    print(f"evict() sonrasında RAM: {loader.rss_mb():.1f} MB")
    """),
          komut_kilavuzu("Yükleme ve Bellek Yönetimi", [
              ("loader.load_all_turkish()", "Tüm Türkçe metinleri içeren CorpusSelection seçkisi", "turkish = loader.load_all_turkish()"),
              ("loader.load_translation_pairs()", "Hizalanmış çeviri çiftleri listesi", "pairs = loader.load_translation_pairs()"),
              ("loader.load_text(code)", "Tekil LazyCorpusText nesnesi yükler", "text = loader.load_text('SU-ZB')"),
              ("text.tokens", "Biçimbilimsel ve sözdizimsel etiketli sözcük DataFrame'i", "tokens = text.tokens"),
              ("text.sentences", "Tümce metinleri ve sözcük sayılarını içeren DataFrame", "sentences = text.sentences"),
              ("text.evict()", "DataFrameleri bellekten atar ve çöp toplayıcıyı tetikler", "text.evict()"),
              ("loader.rss_mb()", "Mevcut Python sürecinin RAM tüketimini MB cinsinden ölçer", "print(loader.rss_mb())"),
          ]),
          md("### 2.3 Sözcük ve Tümce Tablolarının Yapısı"),
          code("""
    text = loader.load_text("SU-ZB")             # Zühtü Bayar - Sahte Uygarlık
    display(text.tokens.head(8))
    display(text.sentences.head(4))
    text.evict()
    """),
          tuzaklar(["`text.tokens` çağrıldığında tablo RAM'e alınır; döngülerde her metin işlendikten sonra `text.evict()` çağırmamak bellek birikimine yol açar.",
                    "Sözcük tablosundaki sütunlar bellek optimizasyonu için `category` tipindedir; metin işlemleri yaparken `astype(str)` kullanın."]),
          alistirmalar([("Özlem Kurdoğlu'nun *Karanlığı Taramak* çevirisindeki tümce sayısını bulunuz.",
                         "```python\nt=loader.load_text('KT-OK'); print(len(t.sentences)); t.evict()\n```")]),
          akademik_not("""
          **Büyük Ölçekli Dijital Beşeri Bilimlerde Veri Verimliliği:**
          Kapsamlı derlem çalışmalarında tüm metinlerin belleğe kontrolsüz biçimde yüklenmesi
          bellek tükenmesine (*Out-Of-Memory*) neden olur. Tembel yükleme ve içerik-adresli Parquet
          önbelleği, yüz binlerce sözcüklük edebi külliyatın taşınabilir dizüstü bilgisayarlarda
          dahi deterministik ve sıfır kayıpla analiz edilmesini mümkün kılar.
          """),
          ]

    # ------------------------------------------------------------------ Bölüm 3
    c += [bolum_basligi(3, "Paralel Derlem ve Tümce Hizalama Analizi", 20,
                        ["İngilizce kaynak ve Türkçe çeviri tümce eşleşmelerini inceleme",
                         "1:1, 1:N, N:1 ve N:M hizalama kalıplarını sayısal olarak sınıflandırma",
                         "Çeviri genişleme ve daralma oranlarını hesaplayabilme"],
                        "Bölüm 1–2", "Çeviride eşdeğerlik ve yeniden yapılandırmanın haritası."),
          md("""
    ### 3.1 Kuramsal Arka Plan: Çeviri Hizalaması
    Paralel derlem çalışmalarında kaynak ve erek metinlerin tümce düzeyinde hizalanması,
    çevirmenin sözdizimsel stratejilerini (bölme, birleştirme, atlama, ekleme) ortaya çıkarır
    (Baker 1993, 1995; Toury 2012).
    - **1:1 Eşleşme**: Kaynak tümce tek bir erek tümceyle karşılanmıştır (doğrudan aktarım).
    - **1:N (Bölme / Parçalama)**: Kaynak tümce erek dilde birden fazla tümceye bölünmüştür (anlatısal sadeleştirme).
    - **N:1 (Birleştirme)**: Birden çok kaynak tümce tek bir tümcede kaynaştırılmıştır (yoğunlaştırma).
    - **1:0 / 0:1 (Atlama ve Ekleme)**: Çeviride tümce düzeyinde eksiltme veya serbest eklemeler.
    """),
          md("""
    ### 3.2 Adım Adım Oyuncak Örnek: Hizalama Oranları
    Kaynakta 100 tümce, erek metinde 115 tümce varsa:
    - Tümce Genişleme Oranı: $R_{\\text{sent}} = 115 / 100 = 1.15$ (tümce sayısı %15 artmıştır, bölme eğilimi).
    - Eğer karakter oranı $R_{\\text{char}} > 1.0$ ise erek metin fiziksel olarak daha uzundur.
    """),
          komut_kilavuzu("Hizalama ve Paralel Derlem Komutları", [
              ("loader.load_translation_pairs()", "Beş çeviri çiftinin PairSpec nesnelerini döndürür", "pairs = loader.load_translation_pairs()"),
              ("pair.alignment_index()", "Hizalama eşleşmelerini sorgulamak için AlignmentIndex üretir", "idx = pair.alignment_index()"),
              ("idx.table()", "Tüm hizalama gruplarını içeren DataFrame (grup no, şekil, tümce ID'leri)", "display(idx.table().head())"),
              ("idx.shape_distribution()", "Hizalama şekillerinin (1:1, 1:2 vb.) frekans ve yüzdeleri", "idx.shape_distribution()"),
              ("idx.expansion_ratios()", "Tümce, sözcük ve karakter genişleme oranlarını hesaplar", "idx.expansion_ratios()"),
          ]),
          code("""
    pairs = [p for p, _, _ in loader.load_translation_pairs()]
    ana = alignment.AlignmentStructureAnalyzer(loader.cache)
    summary = ana.summary(pairs)
    display(summary.round(2))
    """),
          code("""
    fig = viz.alignment_stacked(summary); plt.show()
    tables = {p.tur.title[:28]: ana.cardinality_table(p) for p in pairs}
    fig = viz.alignment_scatter(tables); plt.show()
    """),
          md("### 3.3 Hizalanmış Tümce Kartları Örneği"),
          code("""
    # Selma Mine - Ben, Robot çevirisinden örnek bir 1:1 hizalama kartı
    pair_sm = pairs[0]
    idx_sm = loader.alignment_index(pair_sm)
    sample_ai = idx_sm.table().iloc[5]["ai"]
    eng_str, tur_str = idx_sm.texts(sample_ai)
    print("--- İNGİLİZCE KAYNAK ---")
    print(eng_str)
    print("\\n--- TÜRKÇE ÇEVİRİ ---")
    print(tur_str)
    """),
          tuzaklar(["Hizalama oranları romanların bölümleme farklılıklarından etkilenebilir.",
                    "1:0 veya 0:1 şekilleri her zaman metin atlama anlamına gelmez; bazen OCR veya dipnot farklılıklarını yansıtır."]),
          alistirmalar([("Hangi çevirmen en yüksek 1:1 hizalama oranına sahiptir?",
                         "```python\ndf_align['1:1_pct'].idxmax()\n```")]),
          akademik_not("""
          **Çeviri Normları ve Sentaktik Yeniden Yapılanma (Toury 2012):**
          Türkçe ile İngilizce arasındaki tipolojik sözdizim farkı (SVO'ya karşı SOV, bağıntı tümcelerine
          karşı eylemsi yapıları), İngilizce uzun ve karmaşık periyotların Türkçede bölünmesini (1:N)
          özendirir. Zühtü Bayar'ın 1:N bölme oranlarının yüksekliği, kaynak odaklı yeterlik (*adequacy*)
          yerine erek odaklı benimsenirlik (*acceptability*) normunu benimsediğini somutlaştırır.
          """),
          ]

    # ------------------------------------------------------------------ Bölüm 4
    c += [bolum_basligi(4, "Sözcük Türü (POS) Karşılaştırmalı Analizi", 20,
                        ["Evrensel Sözcük Türü (UPOS) dağılımlarını hesaplama",
                         "Sözcüksel yoğunluk (lexical density) ve ad/eylem oranını ölçme",
                         "Çeviri ile yerli metinler arasındaki sözdizimsel farkları bootstrap güven aralıklarıyla test etme"],
                        "Bölüm 1–3", "Metnin dilbilgisel omurgasını ortaya çıkarma."),
          md("""
    ### 4.1 Kuramsal Temel: Sözcük Türleri ve Biçem
    Sözcük türü dağılımları metnin türsel ve biçemsel kimliğini belirler (Biber 1988, 1993):
    - **Sözcüksel Yoğunluk (Lexical Density)**: İçerik sözcüklerinin (AD, EYLEM, SIFAT, BELİRTEÇ) toplam sözcüklere oranı.
    - **Ad / Eylem Oranı (Noun / Verb Ratio)**: Metnin adlaşmış (kavramsal/statik) mı yoksa eylemsel (anlatısal/dinamik) mi olduğunu gösterir.
    """),
          komut_kilavuzu("Sözcük Türü (POS) Analiz Komutları", [
              ("pos.PosComparativeAnalyzer()", "Karşılaştırmalı POS çözümleyicisini başlatır", "P = pos.PosComparativeAnalyzer()"),
              ("P.distribution(text)", "Tek bir metnin UPOS dağılımını (frekans ve yüzde) döndürür", "P.distribution(text)"),
              ("P.lexical_density(text)", "İçerik sözcükleri / toplam sözcük oranını hesaplar", "P.lexical_density(text)"),
              ("P.noun_verb_ratio(text)", "Ad frekansı / Eylem frekansı oranını döndürür", "P.noun_verb_ratio(text)"),
              ("P.group_comparison(g1, g2, labels)", "İki grup arasında bootstrap güven aralıklı fark testi", "P.group_comparison(trans, indig, ('Çeviri', 'Yerli'))"),
          ]),
          code("""
    P = pos.PosComparativeAnalyzer()
    turkish_texts = list(loader.load_all_turkish())
    pos_rows = []
    for t in turkish_texts:
        dens = P.lexical_density(t)
        nv = P.noun_verb_ratio(t)
        pos_rows.append({
            "code": t.record.code,
            "title": t.record.title,
            "type": t.record.corpus_type,
            "author": t.record.creator,
            "lexical_density": dens,
            "noun_verb_ratio": nv,
        })
        t.evict()
    df_pos = pd.DataFrame(pos_rows)
    display(df_pos.sort_values(["type", "lexical_density"], ascending=[True, False]).round(3))
    """),
          md("### 4.2 Çeviri ve Yerli Metinlerin Grup Karşılaştırması (Bootstrap CIs)"),
          code("""
    trans = [t for t in turkish_texts if t.record.corpus_type == "translation"]
    indig = [t for t in turkish_texts if t.record.corpus_type == "indigenous"]
    grp_res = P.group_comparison(trans, indig, ("translation", "indigenous"), n_bootstrap=1000)
    display(grp_res.round(3))
    """),
          tuzaklar(["İngilizce ve Türkçe için farklı etiketleyiciler (ClearNLP ve VNLP) kullanıldığından ham etiketler yerine Evrensel POS (UPOS) standartlarına odaklanılmalıdır.",
                    "Küçük metin sayılarında (n=3–5) bootstrap aralıkları geniştir; 'kesin kanıtlar' yerine 'uyumludur / işaret eder' dilini tercih edin."]),
          alistirmalar([("Hangi yerli roman en yüksek ad/eylem oranına sahiptir?",
                         "```python\ndf_pos[df_pos['type']=='indigenous'].nlargest(1,'noun_verb_ratio')\n```")]),
          akademik_not("""
          **Çeviri Evrenselleri ve Çevirmen Habitusunun İzleri (Baker 1993; Simeoni 1998):**
          Çeviri kuramında *basitleştirme (simplification)* ve *açıklayıcılık (explicitation)* hipotezleri,
          çeviri dilinin yerli dilden daha düşük sözcüksel yoğunluğa sahip olabileceğini öngörür.
          Öte yandan çevirmenin aynı dönemde kaleme aldığı yerli yapıtlarla çevirileri arasındaki
          sözdizimsel tutarlılık, çeviri sürecinde içselleştirilen eyleyici yatkınlığının (*translating habitus*)
          özgün yazarlığa doğrudan transfer edildiğine ampirik kanıt oluşturur.
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
    """),
          md("""
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
    sid_en = dv.sid_of(en, (1, 4, 4))            # Asimov'un ünlü 'Üç Robot Yasası' tümcesi
    display(dv.table(en, sid_en))
    display(HTML(style.CSS + "<div class='ct'>" + dv.html(en, sid_en) + "</div>"))
    """),
          code("""
    tr = loader.load_text("BR-SM")
    print(loader.registry.display(tr))
    sid_tr = dv.sid_of(tr, (1, 2, 3))            # Selma Mine'nin Türkçe çevirisi
    display(dv.table(tr, sid_tr))
    display(HTML(style.CSS + "<div class='ct'>" + dv.html(tr, sid_tr) + "</div>"))
    """),
          md("### 5.3 İki Dilli Hizalanmış Çift Ağaç Görünümü"),
          code("""
    display(HTML(style.CSS + dv.alignment_html("BR-SM", 4)))
    for t in (en, tr): t.evict()
    """),
          tuzaklar(["İşlev sözcükleri ağaç bütünlüğünü korumak için silinmez, yalnızca rengi soluklaştırılır (*dimmed*).",
                    "Ayrıştırıcı çıktıları istatistiksel modellerce tahmin edilmiştir; uzun ve karmaşık edebi tümcelerde etiket hataları görülebilir."]),
          alistirmalar([("Zühtü Bayar'ın *Sahte Uygarlık* romanının ilk tümcesinin kök (root) sözcüğünü bulunuz.",
                         "```python\nt=loader.load_text('SU-ZB'); s=dv.sid_of(t,(1,1,1)); "
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
