# Music Optics - Manifest

Dette prosjektet er de forste stegene i en demo av OMR (Optical Music Recognition) pa NB sitt notemateriale.

## Mal

Vi bygger en enkel og robust kjede for a ga fra bilder av noter til maskinlesbar notasjon:

- Input: note-sider i bildeformat (`.png` og etter hvert andre formater)
- OMR-prosessering: deteksjon og tolkning av notasjons-symboler
- Output: `MusicXML`/`MXL` for videre bruk, analyse og redigering

## Hva som fungerer na

En forste ende-til-ende test er gjennomfort:

- `*.png` i `pages/`
- konvertert via Audiveris
- resultater skrevet til `scores/`
- `mxl`-filer generert

## Verktoy brukt sa langt

- **Audiveris** for hovedkonvertering fra bilde til notefil
- **annen programvare for inspeksjon** av resultatfiler (`mxl`/MusicXML)

## Neste steg

- Stotte flere inputformater enn `png`
- Forbedre kvalitetssjekk av OMR-resultater
- Dokumentere evalueringskriterier for NB-materiale
- Lage en repeterbar demo-flyt for nye datasett

## Lokal Streamlit-app (MVP)

Appen i `app.py` gir en enkel flyt:

- Last opp `png/jpg/jpeg/pdf`
- Eller bruk NB IIIF-kilde (URN/sesamid/manifest-URL)
- Konvertering med Audiveris
- Last ned generert `mxl`

Kjor lokalt:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install streamlit pymupdf
.venv/bin/python -m streamlit run app.py
```

Appen prover automatisk vanlige Audiveris-stier pa macOS og Linux. Hvis binaren ligger et annet sted, kan du overstyre manuelt:

```bash
AUDIVERIS_BIN="/path/til/Audiveris" .venv/bin/python -m streamlit run app.py
```

Valgfritt for MID-eksport (avspilling i eksternt program):

```bash
.venv/bin/python -m pip install music21
```

## Docker (LAN-maskin)

Denne varianten bygger appen med Audiveris inne i containeren (Ubuntu x86_64).

Kjor:

```bash
docker compose up --build
```

Hvis build stopper i Audiveris-steget, prover:

```bash
docker compose build --no-cache
docker compose up -d
```

Appen blir tilgjengelig pa:

- `http://localhost:8501` (lokalt)
- `http://<LAN-IP>:8501` (fra andre maskiner i nettverket)

Merk:

- Docker-oppsettet bruker Audiveris Linux `.deb` for Ubuntu 24.04 x86_64.
- Hvis LAN-maskinen er ARM, ma vi lage en egen ARM-strategi.

## Tidligere deploy (rekonstruert)

Basert pa lokal historikk og tidligere oppsett ser det ut til at appen ble brukt pa to mater:

- Lokalt med `uv run streamlit run app.py`
- Som pakket Docker-app eksponert fra `sprakbank4`

Det mest sannsynlige tidligere oppsettet var:

1. Appen ble bygget lokalt til et Docker-image som inneholdt Streamlit, Audiveris, Tesseract og Python-avhengigheter.
2. Imaget ble eksportert til en `.tar`-fil (`music-optics_latest.tar`).
3. Filen ble kopiert til `sprakbank4.lx.nb.no`.
4. Appen ble kjort derfra fordi den maskinen hadde bedre tilgang til NB sine bildedata / resolver-endepunkter.
5. Tjenesten ble deretter eksponert pa en URL via port `8501`.

Dette stemmer ogsa med at appen lokalt kan laste manifest og metadata, mens selve bildeuthentingen i noen miljoer kan gi `403` fra NB-resolveren. Appen har derfor fallback til PDF fra manifestet ved konvertering.

## Samarbeid

Se `CONTRIBUTING.md` for branch-strategi, commit-konvensjon og PR-flyt.
