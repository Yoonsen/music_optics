# Bidrag og arbeidsflyt

Takk for at du bidrar til `music_optics`!

Målet med denne filen er å gjøre samarbeid enkelt, forutsigbart og trygt når flere jobber samtidig.

## Kortversjon

- Jobb aldri direkte på `main`.
- Opprett én branch per oppgave.
- Åpne Pull Request (PR) for alle endringer.
- Få minst én godkjenning før merge.
- Bruk squash merge for ryddig historikk.

## Branch-navn

Bruk tydelige branch-navn:

- `feat/<kort-beskrivelse>`
- `fix/<kort-beskrivelse>`
- `docs/<kort-beskrivelse>`
- `chore/<kort-beskrivelse>`

Eksempler:

- `feat/pdf-sidevalg`
- `fix/audiveris-timeout`
- `docs/lan-oppsett`

## Anbefalt flyt

1. Oppdater lokal `main`
2. Opprett ny branch
3. Gjør endringer lokalt
4. Kjør enkel lokal test
5. Push branch
6. Opprett PR
7. Få review og merge

Eksempel:

```bash
git checkout main
git pull
git checkout -b feat/pdf-sideintervall
# ... gjør endringer ...
git add .
git commit -m "feat: legg til sideintervall for PDF"
git push -u origin feat/pdf-sideintervall
```

## Commit-meldinger

Bruk korte meldinger med tydelig type:

- `feat:`
- `fix:`
- `docs:`
- `chore:`

Eksempler:

- `feat: legg til XML-visning i appen`
- `fix: håndter lav oppløsning med retry`
- `docs: oppdater docker-instruksjoner`

## Hva skal med i PR?

- Hva er endret?
- Hvorfor er det endret?
- Hvordan er det testet?
- Eventuelle kjente begrensninger/risiko

## Før du oppretter PR

- Kjør appen lokalt og verifiser hovedflyten.
- Sjekk at nye avhengigheter er nødvendige.
- Unngå store binære filer med mindre de er bevisst del av demoen.

## Beskyttelse av `main` (anbefalt i GitHub)

- Krev PR før merge
- Krev minst 1 approval
- Krev grønn CI
- Blokker direkte push til `main`
