# Manifest: OMR for NB Notemateriale

## Formaal

Dette prosjektet etablerer en praktisk og repeterbar demonstrasjon av OMR (Optical Music Recognition) pa notemateriale fra Nasjonalbiblioteket (NB).

Maalet er a ga fra skannede sider og bildefiler til maskinlesbare notefiler i `MusicXML`/`MXL`, slik at materialet kan analyseres, valideres og viderebehandles i standard noteverktoy.

## Retning

Vi prioriterer en enkel produksjonslinje med tydelige grensesnitt mellom steg:

1. Innhenting av kildefiler (forst `png`, deretter flere formater)
2. Klargjoring og eventuell filtrering av sider med notasjon
3. OMR-konvertering til `MusicXML`/`MXL`
4. Manuell og/eller semiautomatisk inspeksjon av resultat

## Na-status

Forste ende-til-ende gjennomkjoring er vellykket:

- Input i `pages/` (`*.png`)
- Konvertering via Audiveris
- Output i `scores/`
- Genererte `mxl`-filer tilgjengelige for inspeksjon

## Prinsipper

- **Reproduserbarhet:** Samme input skal gi samme output med dokumentert kommandokjede.
- **Sporbarhet:** Input, parametervalg og output skal kunne knyttes sammen.
- **Kvalitet foran volum:** Vi validerer kvalitet i liten skala for vi skalerer opp.
- **Apenhet:** Vi bruker aapne formater (`MusicXML`/`MXL`) og dokumenterer metodevalg.

## Verktoy

- **Audiveris** brukes som hovedmotor for OMR-konvertering.
- **Eksterne inspeksjonsverktoy** brukes for kvalitetskontroll av notefiler.
- Egne skript brukes for datatilpasning, filtrering og kjorelogikk.

## Neste milepaeler

- Utvide inputstotte utover `png` (for eksempel PDF-til-bilde-flyt)
- Definere enkel kvalitetsscore for OMR-resultat per side
- Lage standard demooppsett som kan kjares pa nytt materiale med minimal manuell innsats
- Dokumentere kjente feiltyper i NB-materialet og foresla handtering
