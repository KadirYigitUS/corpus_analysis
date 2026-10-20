"""Türkçe ders not defteri hücre yardımcıları (Bölüm modülleri tarafından kullanılır)."""

from textwrap import dedent

Cell = tuple[str, str]


def md(text: str) -> Cell:
    return ("md", dedent(text).strip("\n"))


def code(text: str) -> Cell:
    return ("code", dedent(text).strip("\n"))


def bolum_basligi(numara: int, baslik: str, dakika: int, hedefler: list[str],
                  onkosullar: str, ozet: str) -> Cell:
    obj = "\n".join(f"- {o}" for o in hedefler)
    return md(f"""
    ---
    # Bölüm {numara} · {baslik}
    ⏱ ~{dakika} dk · 📚 Önkoşullar: {onkosullar}

    > {ozet}

    **Kazanımlar ve Öğrenme Hedefleri** — Bu bölümün sonunda şunları yapabileceksiniz:
    {obj}
    """)


def tuzaklar(maddeler: list[str]) -> Cell:
    body = "\n".join(f"- {i}" for i in maddeler)
    return md(f"""
    <div class="learn" style="border-left:4px solid #f59e0b;background:#fffbeb;padding:8px 12px;border-radius:0 8px 8px 0">

    **⚠️ Sık Yapılan Hatalar ve Dikkat Edilmesi Gerekenler**
    {body}

    </div>
    """)


def alistirmalar(maddeler: list[tuple[str, str]]) -> Cell:
    """maddeler = [(soru, cozum_markdown_veya_kod)] → açılır kapanır çözümler."""
    parts = ["### ✏️ Kendini Sınama Alıştırmaları (Önce kendiniz deneyin, sonra çözümü açın)"]
    for i, (q, sol) in enumerate(maddeler, 1):
        parts.append(f"**{i}.** {q}\n\n<details><summary>Çözümü Göster</summary>\n\n{sol}\n\n"
                     "</details>\n")
    return md("\n".join(parts))


def akademik_not(metin: str) -> Cell:
    """Sonuçları tez metodolojisi, Çeviribilim ve Derlem Dilbilim literatürüne bağlayan kuramsal not."""
    return md(f"""
    <div class="scholarly" style="border-left:4px solid #3b82f6;background:#eff6ff;padding:8px 12px;border-radius:0 8px 8px 0;margin:12px 0;">

    **🎓 Kuramsal Çerçeve ve Akademik Not (Çeviribilim & Derlem Dilbilim)**

    {metin.strip()}

    </div>
    """)


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
    return md("\n".join(lines))
