#!/usr/bin/env python3
"""Tegan XML'ini SecretJoy için hazırlar.

Tegan'ın "Özel XML-Marka Oluşturma" rehberine göre:
  - TG ile başlayan ürün kodu, barkod ve varyant kodlarını kendi ön ekimizle değiştirir
  - Marka ve ürün adındaki "Tegan" yerine kendi markamızı yazar
Ayrıca erkek kategorilerini çıkarır.

Kullanım:  python3 tegan.py [kaynak_url_veya_dosya] [çıktı_dosyası]
"""
import codecs
import re
import sys
import urllib.request

SOURCE = "https://teganicgiyim.com.tr/xml/tegan_ic_giyim.xml"
OUTPUT = "public/tegan.xml"

MARKA = "SecretJoy"      # <Marka> ve ürün adındaki "Tegan" yerine
ON_EK = "SJ"             # TG272364 -> SJ272364

# Kategori kodu (ör. "13T") ile çıkarılacaklar
CIKAR = {"11T", "12T", "13T"}   # Erkek İç Giyim, Erkek Fantezi Kostüm, Erkek Slip-Jockstrap

KAT_RE = re.compile(r"<Kategori>\s*(?:<!\[CDATA\[)?\s*(\d+T)\b", re.S)
KOD_RE = re.compile(r"<(UrunKodu|Barkod|VaryantKodu)>(\s*(?:<!\[CDATA\[)?\s*)TG", re.I)
AD_RE = re.compile(r"(<UrunAdi>.*?</UrunAdi>)", re.S)
ACIK_RE = re.compile(r"(<Aciklama>.*?</Aciklama>)", re.S)
MARKA_RE = re.compile(r"<Marka>.*?</Marka>", re.S)


def degistir(blok: str) -> str:
    blok = KOD_RE.sub(lambda m: f"<{m.group(1)}>{m.group(2)}{ON_EK}", blok)
    blok = MARKA_RE.sub(f"<Marka>{MARKA}</Marka>", blok)

    def ad(m):
        s = m.group(1)
        s = re.sub(r"\bTG(\d)", ON_EK + r"\1", s)
        s = re.sub(r"\bTegan\b", MARKA, s)
        return s

    blok = AD_RE.sub(ad, blok)
    blok = ACIK_RE.sub(lambda m: re.sub(r"\bTegan\b", MARKA, m.group(1)), blok)
    return blok


def open_source(src):
    if src.startswith("http"):
        req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0 secretjoy-xml"})
        return urllib.request.urlopen(req, timeout=600)
    return open(src, "rb")


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else SOURCE
    out = sys.argv[2] if len(sys.argv) > 2 else OUTPUT

    total = kept = 0
    counts = {}
    buf = ""
    dec = codecs.getincrementaldecoder("utf-8")(errors="replace")

    with open_source(src) as f, open(out, "w", encoding="utf-8") as w:
        w.write('<?xml version="1.0" encoding="UTF-8"?>\n<Urunler>\n')
        while True:
            chunk = f.read(1 << 20)
            if not chunk:
                break
            buf += dec.decode(chunk)
            pos = 0
            while True:
                end = buf.find("</Urun>", pos)
                if end < 0:
                    break
                block = buf[pos: end + len("</Urun>")]
                pos = end + len("</Urun>")
                start = block.find("<Urun>")
                if start < 0:
                    continue
                block = block[start:]
                total += 1
                m = KAT_RE.search(block)
                kod = m.group(1) if m else "?"
                if kod in CIKAR:
                    continue
                kept += 1
                counts[kod] = counts.get(kod, 0) + 1
                w.write("  " + degistir(block) + "\n")
            buf = buf[pos:]
        w.write("</Urunler>\n")

    print(f"Toplam ürün: {total}  |  Kalan: {kept}")
    for c, n in sorted(counts.items(), key=lambda x: int(x[0][:-1]) if x[0][:-1].isdigit() else 99):
        print(f"  {n:4d}  {c}")
    if total == 0:
        sys.exit("Kaynak XML boş ya da okunamadı")
    if kept == 0:
        sys.exit("Hiç ürün kalmadı, kategori kodları değişmiş olabilir")


if __name__ == "__main__":
    main()
