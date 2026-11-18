#!/usr/bin/env python3
"""Colezium genel XML'inden sadece fantezi / iç giyim kategorilerini süzer.

Kullanım:  python3 filter.py [kaynak_url_veya_dosya] [çıktı_dosyası]
"""
import html
import re
import sys
import urllib.request

SOURCE = "https://colezium.com/disariexport/xml/1-stok1.xml"
OUTPUT = "public/fantezi.xml"

# Kadın Giyim > Fantazi Giyim alt kategorileri
FANTAZI = [
    "Fantazi Gecelik", "Fantazi Babydoll", "Fantazi Külot", "Fantazi Sütyen",
    "Fantazi Kostüm", "Fantazi Elbise", "Fantezi Etek", "Fantezi Tayt",
    "Jartiyer Takımı", "Jartiyer Çorabı", "Vucut Çorabı", "Vücut Çorabı",
    "Deri gecelik", "Çeyizlik Setler", "Çeyizlik Pijama", "İkili Takımlar",
]
# Ek iç giyim kategorileri
EKSTRA = [
    "Korse", "Korse Standart", "Sütyen Takımları", "Toparlayıcı Sütyen", "Sütyen",
]

def norm(s: str) -> str:
    s = html.unescape(html.unescape(s))
    s = s.replace("<![CDATA[", "").replace("]]>", "")
    s = s.replace("İ", "i").replace("I", "ı")
    return " ".join(s.lower().split())

WANTED = {norm(c) for c in FANTAZI + EKSTRA}
CAT_RE = re.compile(r"<Category>(.*?)</Category>", re.S)


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
    import codecs
    dec = codecs.getincrementaldecoder("utf-8")(errors="replace")

    with open_source(src) as f, open(out, "w", encoding="utf-8") as w:
        w.write('<?xml version="1.0" encoding="UTF-8"?>\n<products>\n')
        while True:
            chunk = f.read(1 << 20)
            if not chunk:
                break
            buf += dec.decode(chunk)
            pos = 0
            while True:
                end = buf.find("</product>", pos)
                if end < 0:
                    break
                block = buf[pos: end + len("</product>")]
                pos = end + len("</product>")
                start = block.find("<product>")
                if start < 0:
                    continue
                block = block[start:]
                total += 1
                m = CAT_RE.search(block)
                cat = norm(m.group(1)) if m else ""
                if cat in WANTED:
                    kept += 1
                    counts[cat] = counts.get(cat, 0) + 1
                    w.write("  " + block + "\n")
            buf = buf[pos:]
        w.write("</products>\n")

    print(f"Toplam ürün: {total}  |  Süzülen: {kept}")
    for c, n in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {n:4d}  {c}")
    if total == 0:
        sys.exit("Kaynak XML boş ya da okunamadı")
    if kept == 0:
        sys.exit("Hiç ürün süzülemedi, kategori adları değişmiş olabilir")


if __name__ == "__main__":
    main()
