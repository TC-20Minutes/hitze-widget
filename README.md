# Hitze-Widget „So heiss ist es bei Ihnen"

Eingebettetes Widget: Leser:in gibt eine PLZ ein und sieht die **Höchsttemperatur
(24 h)** der nächstgelegenen MeteoSchweiz-Messstation, plus eine Rangliste und
eine Übersichts-Statistik. Im 20-Minuten-Design (Matter-Schrift, Markenfarben).

## Das Wichtigste: kein Backend nötig

`hitze-widget.html` ist **eine einzige, eigenständige Datei** (~250 KB). Darin
fest eingebettet:

- die **PLZ→Koordinaten**-Tabelle (3190 PLZ, swisstopo)
- die **Stations-Metadaten** (Kanton + Höhe, MeteoSchweiz)
- die **Matter-Schriften** (auf Latin gesubsettet, als WOFF2)

Die **Live-Temperaturen** holt das Widget zur Laufzeit direkt im Browser von
`data.geo.admin.ch` (MeteoSchweiz Open Data, CORS = `*`), alle 10 Minuten neu.
Es gibt also **nichts zu betreiben** – kein Cron-Job, kein Server, keine
Datenbank. Einfach die HTML-Datei hosten und per iframe einbinden.

Quelle der Live-Daten:
- Höchstwert 24 h: `ch.meteoschweiz.messwerte-lufttemperatur-24h-max-1h`
- Aktuell (10 min): `ch.meteoschweiz.messwerte-lufttemperatur-10min`

## Einbetten

`hitze-widget.html` auf euer CDN / euren Webspace legen und einbinden:

```html
<iframe id="hitze" src="https://cdn.20min.ch/.../hitze-widget.html"
        style="width:100%;border:0;height:1100px" loading="lazy"
        title="So heiss ist es bei Ihnen"></iframe>

<!-- optional: iframe automatisch an Inhaltshöhe anpassen -->
<script>
addEventListener("message", e => {
  if (e.data && e.data.type === "hitze-widget-height")
    document.getElementById("hitze").style.height = e.data.height + "px";
});
</script>
```

Das Widget meldet seine Höhe per `postMessage` – mit dem Snippet oben wächst das
iframe automatisch mit (sonst eine feste `height` setzen).

## Neu bauen (selten nötig)

Nur nötig, wenn das PLZ-Verzeichnis oder die Stationsliste aktualisiert werden
soll – die Temperaturen sind ja immer live.

```bash
cd hitze-widget
python3 build.py        # lädt PLZ + Stations-Meta, subsettet Fonts, baut HTML
```

Voraussetzungen: `python3` mit `fonttools` und `brotli`
(`pip install fonttools brotli`). Fehlen sie, wird ohne eingebettete Schrift
gebaut (System-Fallback).

Das Skript erzeugt zusätzlich `data/plz.json` und `data/stations_meta.json`,
falls ihr die Daten anderweitig (eigene Pipeline) verwenden wollt.

## Dark Mode & Barrierefreiheit

Das Widget folgt automatisch der **Browser-/System-Einstellung**
(`prefers-color-scheme`) – heller oder dunkler Modus, kein Schalter nötig. Die
Hitze-Farben passen ihre Textkontraste je Theme an (WCAG ≥ 4.5:1). Ergänzt:
`aria-live` für Vorlese-Software, sichtbare Fokusringe, `tabular-nums`,
sowie `prefers-reduced-motion`-Fallback für alle Animationen.

## Konfiguration

In `template.html` (dann neu bauen):

- `HEAT_THRESHOLD` – Schwelle für die Aggregat-Statistik (Standard 30 °C)
- `REFRESH_MS` – Aktualisierungsintervall (Standard 10 min)
- `heatColor()` – Stützpunkte der Hitze-Farbskala
- Top-N der Rangliste: `sorted.slice(0,5)` in `render()`

## Methodik (für Transparenz im Artikel)

Das Widget **interpoliert nicht** und mittelt keine Gebiete. Es zeigt den real
gemessenen Wert der **nächstgelegenen Station** (Luftlinie, in LV95). Bei grosser
Distanz (> 15 km) erscheint ein Hinweis. Höhenangabe der Station wird genannt,
weil sie die Temperatur stark beeinflusst (~0,65 °C / 100 m). Das ist die
ehrlichste Darstellung von Punktmessdaten – ohne Scheingenauigkeit.

Fehlwerte (Platzhalter wie 99999) und Stationen ohne Messwert werden gefiltert.

Quelle: MeteoSchweiz / swisstopo (Open Government Data, BGDI).
