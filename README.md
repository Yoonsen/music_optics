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
- Konvertering med Audiveris
- Last ned generert `mxl`

Kjor lokalt:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install streamlit pymupdf
.venv/bin/python -m streamlit run app.py
```

Hvis Audiveris ligger et annet sted enn standardsti pa macOS:

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

Appen blir tilgjengelig pa:

- `http://localhost:8501` (lokalt)
- `http://<LAN-IP>:8501` (fra andre maskiner i nettverket)

Merk:

- Docker-oppsettet bruker Audiveris Linux `.deb` for Ubuntu 24.04 x86_64.
- Hvis LAN-maskinen er ARM, ma vi lage en egen ARM-strategi.
