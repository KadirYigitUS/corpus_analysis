"""Türkçe ders not defteri hücre yardımcıları (Bölüm modülleri tarafından kullanılır).

Önemli: Markdown'da 4+ boşlukla başlayan satırlar *kod bloğu* sayılır. Bu yüzden çok satırlı
değerler (``{body}``, ``{metin}``) bir üç tırnaklı f-string'e gömülmez; satırlar baştan sola
dayalı kurulur ve ``flush`` ile ortak girinti ayrıca temizlenir.
"""

from textwrap import dedent

Cell = tuple[str, str]

LEARN_STYLE = ("border-left:4px solid #f59e0b;background:#fffbeb;padding:8px 12px;"
               "border-radius:0 8px 8px 0;margin:12px 0;")
SCHOLARLY_STYLE = ("border-left:4px solid #3b82f6;background:#eff6ff;padding:8px 12px;"
                   "border-radius:0 8px 8px 0;margin:12px 0;")


def flush(text: str) -> str:
    """Ortak girintiyi kaldır ve baştaki/sondaki boş satırları at."""
    return dedent(text).strip("\n")


def md(text: str) -> Cell:
    return ("md", flush(text))


def code(text: str) -> Cell:
    return ("code", flush(text))


def bolum_basligi(numara: int, baslik: str, dakika: int, hedefler: list[str],
                  onkosullar: str, ozet: str) -> Cell:
    lines = [
        "---",
        f"# Bölüm {numara} · {baslik}",
        f"⏱ ~{dakika} dk · 📚 Önkoşullar: {onkosullar}",
        "",
        f"> {ozet}",
        "",
        "**Kazanımlar ve Öğrenme Hedefleri** — Bu bölümün sonunda şunları yapabileceksiniz:",
        "",  # liste öncesi boş satır: aksi halde madde imleri paragrafın parçası olur
        *[f"- {o}" for o in hedefler],
    ]
    return ("md", "\n".join(lines))


def tuzaklar(maddeler: list[str]) -> Cell:
    lines = [
        f'<div class="learn" style="{LEARN_STYLE}">',
        "",
        "**⚠️ Sık Yapılan Hatalar ve Dikkat Edilmesi Gerekenler**",
        "",
        *[f"- {i}" for i in maddeler],
        "",
        "</div>",
    ]
    return ("md", "\n".join(lines))


def alistirmalar(maddeler: list[tuple[str, str]]) -> Cell:
    """maddeler = [(soru, cozum_markdown_veya_kod)] → açılır kapanır çözümler."""
    parts = ["### ✏️ Kendini Sınama Alıştırmaları (Önce kendiniz deneyin, sonra çözümü açın)"]
    for i, (q, sol) in enumerate(maddeler, 1):
        parts.append(f"**{i}.** {q}\n\n<details><summary>Çözümü Göster</summary>\n\n{flush(sol)}\n\n"
                     "</details>\n")
    return ("md", "\n".join(parts))


def akademik_not(metin: str) -> Cell:
    """Sonuçları tez metodolojisi, Çeviribilim ve Derlem Dilbilim literatürüne bağlayan kuramsal not."""
    lines = [
        f'<div class="scholarly" style="{SCHOLARLY_STYLE}">',
        "",
        "**🎓 Kuramsal Çerçeve ve Akademik Not (Çeviribilim & Derlem Dilbilim)**",
        "",
        flush(metin),
        "",
        "</div>",
    ]
    return ("md", "\n".join(lines))


def komut_kilavuzu(baslik: str, satirlar: list[tuple[str, str, str]]) -> Cell:
    """Yöntemler, parametreler ve örnek çağrıların yer aldığı temiz Markdown tablosu."""
    lines = [
        f"### 📋 Komut ve İşlev Kılavuzu · {baslik}",
        "",
        "| Yöntem / İşlev | Parametreler ve Seçenekler | Örnek Kullanım |",
        "| :--- | :--- | :--- |",
    ]
    for fn, params, eg in satirlar:
        lines.append(f"| `{fn}` | {params} | `{eg}` |")
    return ("md", "\n".join(lines))
