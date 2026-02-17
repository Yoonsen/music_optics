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
