#!/usr/bin/env python3
"""
Build-Skript für das 20-Minuten-Hitze-Widget.

Erzeugt aus offiziellen Quellen eine einzige, eigenständige HTML-Datei
(hitze-widget.html), die per <iframe> eingebettet werden kann:

  * PLZ -> Koordinaten (LV95) + Ort + Kanton   (swisstopo Ortschaftenverzeichnis)
  * Stations-Metadaten: Kanton + Höhe je Station (MeteoSchweiz OGD-SMN)
  * Matter-Schriften, auf Latin gesubsettet, als WOFF2 inline

Die LIVE-Temperaturwerte werden NICHT hier gezogen, sondern zur Laufzeit
direkt im Browser von data.geo.admin.ch (CORS = *). Dieses Skript muss also
nur selten laufen (z.B. wenn das PLZ-Verzeichnis aktualisiert wird).

Aufruf:  python3 build.py
"""

import base64
import csv
import io
import json
import os
import sys
import urllib.request
import zipfile
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.normpath(os.path.join(HERE, "..", "ASSETS"))
FONT_DIR = os.path.join(ASSETS, "Matter Font")
LOGO = os.path.join(ASSETS, "logo-20min.png")
TEMPLATE = os.path.join(HERE, "template.html")
OUT_HTML = os.path.join(HERE, "hitze-widget.html")
DATA_DIR = os.path.join(HERE, "data")

PLZ_URL = ("https://data.geo.admin.ch/ch.swisstopo-vd.ortschaftenverzeichnis_plz/"
           "ortschaftenverzeichnis_plz/ortschaftenverzeichnis_plz_2056.csv.zip")
STATIONS_URL = ("https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/"
                "ogd-smn_meta_stations.csv")

# Schriftschnitte, die das Widget verwendet (Dateiname -> CSS font-weight)
FONT_WEIGHTS = {
    "Matter-Regular.otf": 400,
    "Matter-Medium.otf": 500,
    "Matter-SemiBold.otf": 600,
    "Matter-Bold.otf": 700,
}

# Zeichen, die wir im Subset behalten (Deutsch/Französisch/Italienisch + Symbole)
SUBSET_UNICODES = "U+0020-00FF,U+0152-0153,U+2013-2014,U+2018-201A,U+201C-201E,U+2022,U+2026,U+202F,U+00B0,U+2212"


def fetch(url):
    print(f"  ↓ {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "20min-hitze-widget/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def build_plz():
    """PLZ4 -> [E, N, Ortsname, Kanton] (eine repräsentative Lage je PLZ)."""
    print("PLZ-Verzeichnis (swisstopo)…")
    raw = fetch(PLZ_URL)
    zf = zipfile.ZipFile(io.BytesIO(raw))
    name = next(n for n in zf.namelist() if n.lower().endswith(".csv"))
    text = zf.read(name).decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text), delimiter=";")

    # je PLZ die Zeile mit dem grössten Adressenanteil als Repräsentant nehmen
    best = {}  # plz -> (anteil, row)
    for row in reader:
        plz = row["PLZ4"].strip()
        if not plz.isdigit():
            continue
        try:
            anteil = float(row["Adressenanteil"].replace("%", "").strip())
        except ValueError:
            anteil = 0.0
        if plz not in best or anteil > best[plz][0]:
            best[plz] = (anteil, row)

    out = {}
    for plz, (_, row) in best.items():
        try:
            e = round(float(row["E"]))
            n = round(float(row["N"]))
        except ValueError:
            continue
        name = row["Ortschaftsname"].strip()
        kt = row["Kantonskürzel"].strip()
        out[plz] = [e, n, name, kt]
    print(f"  → {len(out)} eindeutige PLZ")
    return out


def build_stations():
    """station_abbr -> [Kanton, Höhe_m]."""
    print("Stations-Metadaten (MeteoSchweiz)…")
    raw = fetch(STATIONS_URL)
    text = raw.decode("cp1252")  # Datei ist Latin-1/CP1252 kodiert
    reader = csv.DictReader(io.StringIO(text), delimiter=";")
    out = {}
    for row in reader:
        abbr = row["station_abbr"].strip()
        kt = row["station_canton"].strip()
        try:
            alt = round(float(row["station_height_masl"]))
        except (ValueError, KeyError):
            alt = None
        out[abbr] = [kt, alt]
    print(f"  → {len(out)} Stationen")
    return out


def build_fonts():
    """Matter-OTFs subsetten -> WOFF2 -> base64 -> @font-face CSS."""
    print("Schriften subsetten (Matter → WOFF2)…")
    try:
        from fontTools import subset
    except ImportError:
        print("  ! fonttools fehlt – baue OHNE eingebettete Schrift (System-Fallback).")
        return ""

    css_parts = []
    for fname, weight in FONT_WEIGHTS.items():
        src = os.path.join(FONT_DIR, fname)
        if not os.path.exists(src):
            print(f"  ! {fname} nicht gefunden – übersprungen")
            continue
        opts = subset.Options()
        opts.flavor = "woff2"
        opts.desubroutinize = True
        opts.layout_features = ["kern", "liga", "calt", "ccmp", "locl"]
        opts.name_IDs = []
        opts.notdef_outline = True
        opts.recalc_bounds = True
        font = subset.load_font(src, opts)
        subsetter = subset.Subsetter(options=opts)
        subsetter.populate(unicodes=subset.parse_unicodes(SUBSET_UNICODES))
        subsetter.subset(font)
        buf = io.BytesIO()
        subset.save_font(font, buf, opts)
        font.close()
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        kb = len(buf.getvalue()) / 1024
        print(f"  → {fname}: {kb:.1f} KB (woff2)")
        css_parts.append(
            "@font-face{font-family:'Matter';font-style:normal;font-weight:%d;"
            "font-display:swap;src:url(data:font/woff2;base64,%s) format('woff2');}"
            % (weight, b64)
        )
    return "\n".join(css_parts)


def build_logo():
    """20-Minuten-Logo als data:-URI (base64) für eigenständige HTML."""
    if not os.path.exists(LOGO):
        print(f"  ! Logo nicht gefunden: {LOGO}")
        return ""
    with open(LOGO, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    print(f"Logo eingebettet ({os.path.getsize(LOGO)/1024:.1f} KB)")
    return "data:image/png;base64," + b64


def main():
    plz = build_plz()
    stations = build_stations()
    font_css = build_fonts()
    logo = build_logo()

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(os.path.join(DATA_DIR, "plz.json"), "w", encoding="utf-8") as f:
        json.dump(plz, f, ensure_ascii=False, separators=(",", ":"))
    with open(os.path.join(DATA_DIR, "stations_meta.json"), "w", encoding="utf-8") as f:
        json.dump(stations, f, ensure_ascii=False, separators=(",", ":"))
    print(f"  → data/plz.json, data/stations_meta.json geschrieben")

    if not os.path.exists(TEMPLATE):
        print(f"! Template fehlt: {TEMPLATE}", file=sys.stderr)
        sys.exit(1)
    with open(TEMPLATE, encoding="utf-8") as f:
        html = f.read()

    html = html.replace("/*__FONT_CSS__*/", font_css)
    html = html.replace("__LOGO__", logo)
    html = html.replace("/*__PLZ_DATA__*/", json.dumps(plz, ensure_ascii=False, separators=(",", ":")))
    html = html.replace("/*__STATION_DATA__*/", json.dumps(stations, ensure_ascii=False, separators=(",", ":")))

    for out in (OUT_HTML, os.path.join(HERE, "index.html")):
        with open(out, "w", encoding="utf-8") as f:
            f.write(html)
    size_kb = os.path.getsize(OUT_HTML) / 1024
    print(f"\n✓ {OUT_HTML} + index.html erzeugt ({size_kb:.0f} KB) – fertig zum Einbetten.")


if __name__ == "__main__":
    main()
