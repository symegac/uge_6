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

## Data
Dataen til opgaven forefindes tre forskellige steder:
1. Lokalt på arbejdscomputeren i form af CSV-filer ([Data CSV](data_csv/)).
2. Hos en central butik, som kan tilgås via en API ([Data API](data_api/)).
3. I en eksisterende database ([Data DB](data_db/)).

### Extraction
Her er det vigtigt at kigge på, hvordan man forbinder til de forskellige datakilder, og hvordan man læser dataene. Hertil er det også vigtigt at finde ud af, hvilket format den læste forekommer i.
* **API**: Data hentet gennem en REST API vil typisk være i JSON- eller XML-format. I denne opgave er det JSON. Det kan man indlæse i Python til forskellige datastrukturer, alt efter hvilken metode man bruger. Det enkleste er at omdanne JSON til en *dict*.
* **CSV**: Data indlæst fra en CSV-fil vil som udgangspunkt være en kommasepareret tekststreng, men hvis man bruger et specifikt modul til at indlæse dataen, kan den være i et andet format, f.eks. en *DataFrame* eller *dict*.
* **DB**: Data indlæst fra en MySQL-database vil med modulet *mysql-connector-python* blive hentet fra en cursor som en liste af tuples, der hver svarer til en række i tabellen.

Det er en fordel, hvis man allerede her i extraction-fasen kan få læst dataene fra de forskellige kilder ind til samme type i Python, så det er nemt at skrive kode, der fungerer på data fra alle kilderne. Det kunne f.eks. være en *polars*- eller *pandas*-*DataFrame*, eller en *dict*, så der er et eksplicit forhold mellem kolonne/felt og tilhørende værdi, og at det for `null`-værdier tydeligt markeres, hvilket datafelt de hører til.

### Transformation
Her er det vigtigt at kigge på de forskellige datakilders struktur.
Hvilke datafelter har de, og hvilke datatyper?
Hvilke relationer er der i de forskellige datasæt? Primary keys og foreign keys? Har et datasæt alt i én tabel, mens andre har flere tabeller?
Er der overlap mellem datafelterne i datasættene. Hvis ja, er der dubletter blandt de forskellige entries, eller er der måske entries med samme nøgle men forskelligt indhold? Hvis nej, hvilke datafelter skal så tages med fra de forskellige kilder?
Og i den sammenhæng, hvilken struktur skal de endelige data have? Er det i orden, at nogle kolonner ikke har data for nogle rækker?

### Loading
Da vi på kurset har arbejdet med MySQL, er det kun naturligt, at den samlede data lagres i sådan en databse.