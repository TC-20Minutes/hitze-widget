# Hitze-Widget „So heiss ist es bei Ihnen" — v2 (Design-System)

> **v2:** visuell auf das offizielle **20-Minuten-Design-System** ausgerichtet
> (Graustufen-Grundgerüst + Electricity-Blau/Azure sparsam als Akzent, Eyebrow in
> Versalien, max. SemiBold, 8px-Radien, Hairlines, schwarze Schatten). Struktur,
> Funktion, i18n und Tracking sind identisch zur ursprünglichen Version; nur die
> Design-Tokens (`:root` hell/dunkel) und die Typo wurden angepasst. Light- und
> Dark-Mode bleiben erhalten.


Eingebettetes Widget: Leser:in gibt eine PLZ ein und sieht die **Höchsttemperatur
(24 h)** der nächstgelegenen MeteoSchweiz-Messstation, plus eine Rangliste und
eine Übersichts-Statistik. Im 20-Minuten-Design (Matter-Schrift, Markenfarben).

## Das Wichtigste: kein Backend nötig

`hitze-widget.html` (~266 KB) hat **PLZ-Tabelle, Stations-Metadaten und die
Matter-Schriften fest eingebettet**:

- die **PLZ→Koordinaten**-Tabelle (3190 PLZ, swisstopo)
- die **Stations-Metadaten** (Kanton + Höhe, MeteoSchweiz)
- die **Matter-Schriften** (auf Latin gesubsettet, als WOFF2)

Daneben liegen zwei kleine Dateien, die **zusammen mit der HTML** deployt werden
müssen (relative Pfade):

- `translations/de.json` + `translations/fr.json` – UI-Texte je Sprache
- `tracking.js` – Analytics-Anbindung (GTM)

Die **Live-Temperaturen** holt das Widget zur Laufzeit direkt im Browser von
`data.geo.admin.ch` (MeteoSchweiz Open Data, CORS = `*`), alle 10 Minuten neu.
Es gibt also **nichts zu betreiben** – kein Cron-Job, kein Server, keine
Datenbank. Einfach die Dateien hosten und per iframe einbinden.

## Sprachen & Mandanten

Das Widget ist mehrsprachig (Deutsch/Französisch). Die Sprache wird über den
Query-Parameter `?tenant=` gewählt:

- `20min-de` (Standard) → Deutsch
- `20min-fr` → Französisch
- `lematin` → Französisch

Ohne oder mit unbekanntem `tenant` fällt das Widget auf `20min-de` (Deutsch)
zurück. Die Texte kommen aus `translations/<lang>.json`.

## Tracking

`tracking.js` stellt `window.TrackHitze` bereit und schreibt Events in den GTM
`dataLayer` (Container `GTM-PKTSKJX` via `sst.20min.ch`): `page_view` beim Laden,
`search_plz` / `search_plz_invalid` bei PLZ-Eingabe, `mode_now` / `mode_max`
beim Umschalten. `platform_name` richtet sich nach dem `tenant`.

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

> **Achtung 20-Minuten-CMS:** Das Embed-`<script>` oben wird vom CMS **gestrippt**,
> das Auto-Resize läuft dort also nicht. Praktisch: feste Höhe `1340px` setzen
> (deckt den höchsten Zustand ab, kein Scroll/Abschneiden). Details, gemessene
> Höhen und der saubere Weg (Haus-Resizer) stehen in
> [`../IFRAME-EINBETTUNG.md`](../IFRAME-EINBETTUNG.md).

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
