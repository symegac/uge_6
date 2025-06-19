# Uge 6 — ETL-opgave
## Introduktion til opgaven
### Formål
Den fiktive virksomhed *BikeCorp Inc.* skal have konsolideret data fra tre forskellige kilder til en enkelt database, hvorudfra virksomheden får et solidt datagrundlag som pejlemærke for forretningens fremtidige drift.
I opgaven er der fokus på design og implementering af ETL-processer i kode, dokumentation af trufne beslutninger og intentionen bag ETL-processer, samt kommunikation af relevante dele af ETL-processen til kolleger, ledere eller andre i virksomheden.

### Produktets indhold
En præsentation, der skal indeholde følgende:
1. Et overblik over den endelige datastruktur, dvs. database-schemaet, samt evt. andre relevante ting.
2. Introduktion til dokumentationen, så brugere af databasen kan tjekke forskellige ting relevante for deres arbejde.
3. Evt. implementeringen af processen i kode.
4. Evt. om interface til databasen lavet i Python eller PowerBI.

### Data
Dataen til opgaven forefindes tre forskellige steder:
1. Lokalt på arbejdscomputeren i form af CSV-filer ([Data CSV](data_csv/)).
2. Hos en central butik, som kan tilgås via en API ([Data API](data_api/)).
3. I en eksisterende database ([Data DB](data_db/)).

## Setup
1. Hent repositoriet ned lokalt.
    `git clone https://github.com/symegac/uge_6.git`

2. Naviger til mappen.
    `cd uge_6`

3. Opret et virtuelt miljø.
    `python -m venv .venv`

4. Aktivér det virutelle miljø.
    `. .venv/Scripts/activate`

5. Installér de påkrævede moduler.
    `pip install -r requirements.txt`

### Test dit setup
6. Opsæt (lokal) API-forbindelse. Forbindelsen burde gerne have 127.0.0.1 som host og 8000 som port.
    `fastapi dev data_api/main.py`

7. Opsæt eksempeldatabasen ved at loade filen [*productdb.sql*](/data_db/productdb.sql) ind i din lokale MySQL-instans. (Filen [*etl_db_setup.py*](/data_db/create_db/etl_db_setup.py) virker ikke nødvendigvis på alle opsætninger, så jeg måtte gøre det manuelt). Forbindelsen burde gerne have 127.0.0.1 som host og 3306 som port.

8. Opret en fil i grundmappen [*uge_6*](./) ved navn *config\.py* med koden fra [*config.txt*](/config.txt) (som selfølgelig skal tilrettes med de korrekte info for din opsætning).

9. Prøvekør [*main.py*](/main.py).
    `python main.py`

## Struktur
Koden ligger ved en fejl ikke i *src/* og *tests/*-mapper. Dette rettes snarest.

### Datakilder
De forskellige datakilder (API, CSV-fil og SQL-database) findes i hver deres mappe med *data_* som præfiks: [*data_api*](/data_api/), [*data_csv*](/data_csv/) og [*data_db*](/data_db/).

### Kode
Til at hente data fra API'en bruges [*api.py*](/api.py). Til CSV-filen bruges [*csvr.py*](/csvr.py). En videreudviklet udgave af projektet fra [Uge 4](https://github.com/symegac/uge_4) findes i mappen [*db*](/db/). Denne bruges både til at udtrække data fra SQL-datakilden og til at lave den endelige konsoliderede database.

I [*intertable.py*](/intertable.py) har jeg udviklet et custom-format, som de forskellige datakilder kan omdannes til for at sikre, at dataene korrekt kan indsættes i den endelige database. Her bliver datatyper og -værdier automatisk tjekket, så fejl bliver opfanget. Funktioner til at omdanne en kildes data til intertable-formatet findes i samme fil som bruges til at hente dataen.

I [*main.py*](/main.py) findes et script, der laver en prøvekørsel af hele ETL-processen og samler de tre datakilder i en ny database.

### Dokumentation
Ræsonnementet bag fremgangsmåden og databehandlingen, samt forklaring af intertable-formatet findes [her](/docs.md):
**NB!** *Dokumentationen er ufuldstændig, da den ikke er opdateret til at tilsvare nyeste udgave af intertable-formatet.*
