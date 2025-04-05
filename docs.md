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

#### Besluttet proces
* **API**: Til at hente data fra API'en bruger jeg modulerne *requests* og *json*. Førstnævnte bruges til at sende selve requesten til API'en, og sidstnævnte bruges derefter til at afkode JSON-formatet til en Python-*dict*.
* **CSV**: Til at hente data fra CSV-filerne tager jeg inspiration fra noget af koden, som jeg skrev til [*uge_2*](https://github.com/symegac/uge_2/blob/main/opgave_3/src/fejlhåndtering.py) og [*uge_4*](https://github.com/symegac/uge_4/blob/main/src/database.py), dog i revideret form. Jeg læser dataene og omdanner dem til en Python-*dict*.
* **DB**: Til at hente data fra MySQL-databasen, bruger jeg igen min kode fra [*uge_4*](https://github.com/symegac/uge_4/blob/main/src/database.py) i revideret udgave til at forbinde til databasen og læse dataene og omdanne dem til en Python-*dict*.

Til sidst bør hver tabel have form som en *dict* indeholdende tre underinddelinger.
Den første af disse er headeren, der er endnu en *dict*, hvori nøglerne består af navnet på de forskellige kolonner, mens værdierne udgøres af datatypen for hver kolonne.
Den anden er en *dict* med tabellens relationelle keys. Primary key er enten et kolonnenavn eller en liste af kolonnenavne, hvis flere kolonner udgør primary key. Foreign keys er en *dict*, der kan være tom, hvis der ikke findes nogen foreign keys, eller være en række nøgle-værdi-par, hvor nøglen er kolonnenavnet i nuværende tabel, og værdien indeholder tabel- og kolonnenavn for den anden tabel.
Den tredje er en liste af *dict*s, hver tilsvarende en datarække. Nøglerne i denne *dict* er igen navnet på kolonnen, mens værdierne er værdien i samme kolonnes datafelt i den givne række.
Det vil sige, at formatet er *dict[str, dict[str, type] | dict[str, str | list[str] | dict[str, str]] | list[dict[str, Any]]]*.

<details>
<summary>Eller på udvidet Backus-Naur-form:</summary>

```bnf
<tabel-dict> ::= <tabelnavn> '=' '{' <header-dict> ',' <keys-dict> ',' <data-list> '}'

<header-dict> ::= '"header"' ':' '{' <kolonne-kvpair>+ '}'
<kolonne-kvpair> ::= <kolonnenavn> ':' <datatype> ','

<keys-dict> ::= '"keys"' ':' '{' <primary_key-kvpair> ',' <foreign_key-dict> '}'
<primary_key-kvpair> ::= '"primary"' ':' <primary_key-value>
<primary_key-value> ::= <kolonnenavn> | '[' <kolonnenavn-list>+ ']'
<kolonnenavn-list> ::= <kolonnenavn> ','
<foreign_key-dict> ::== '"foreign"' ':' '{' <foreign_key-kvpair>* '}'
<foreign_key-kvpair> ::== <kolonnenavn> ':' <tabelnavn_kolonnenavn-value> ','
<tabelnavn_kolonnenavn-value> ::== <tabelnavn> '(' <kolonnenavn> ')'

<data-list> ::= '"data"' ':' '[' <række-dict>+ ']'
<række-dict> ::= '{' <datafelt-kvpair>+ '}'
<datafelt-kvpair> ::= <kolonnenavn> ':' <feltværdi> ','

<tabelnavn> ::= <navn>
<kolonnenavn> ::= <navn>

; Nedenstående værdier er alle Python-typer (<Any> specificeres dog yderligere til de Python-typer, der optræder i dette datasæt, selvom Any i teorien kunne være hvilken som helst Python-type)
<navn> ::= <str>
<datatype> ::= <type>
<feltværdi> ::= <Any>
<Any> ::= <str> | <int> | <decimal.Decimal> | <datetime.date>
```
</details>
<details>
<summary>Eller demonstreret her:</summary>

```py
{
    "header": {
        "kolonne 0-navn": <class K_0_Type>,
        ...,
        "kolonne i-navn": <class K_i_Type>
    },
    "keys": {
        "primary": [    # eller "pk kolonne-navn"
            "pk kolonne 1/i-navn",
            ...,
            "pk kolonne i/i-navn"
        ],
        "foreign": {    # eller {}
            "fk kolonne 1-navn": "tabel x-navn(kolonne y-navn)",
            ...,
            "fk kolonne i-navn": "tabel m-navn(kolonne n-navn)"
        }
    }
    "data": [
        {
            "kolonne 0-navn": r_0-k_0-værdi,
            ...,
            "kolonne i-navn": r_0-k_i-værdi
        },
        ...,
        {
            "kolonne 0-navn": r_i-k_0-værdi,
            ...,
            "kolonne i-navn": r_i-k_i-værdi
        }
    ]
}
```
</details>

Jeg har valgt at bruge dette format, dels fordi det er utrolig let at gå fra JSON til dette format, dels fordi jeg i *uge_2*-opgaven outputtede rensede data som en *dict* og derfor allerede har noget kode, dels fordi *mysql-connector-python* i forvejen bruger en *dict* til at indsætte værdierne i parameteriserede queries, og jeg derfor også har noget kode fra *uge_4*-opgaven i forvejen.

### Transformation
Der er mange vigtige ting at kigge på, når det angår transformation af den udtrukne data.
Først er der de forskellige datakilders struktur. Hvilke datafelter har de, og hvilke datatyper?
Hvilke relationer er der i de forskellige datasæt? Primary keys og foreign keys?
Er der overlap mellem datafelterne i datasættene? Hvis ja, er der dubletter blandt de forskellige entries, eller er der måske entries med samme nøgle men forskelligt indhold? Hvis nej, hvilke datafelter skal så tages med fra de forskellige kilder?
Og i den sammenhæng, hvilken struktur skal de endelige data have? Er det i orden, at nogle kolonner ikke har data for nogle rækker?

Herunder følger analyser af kommentarer til de forskellige datasæt.
Først vises rådataformatet, samt eksempler på rådata og slutformatet.
Herefter beskrives datasættets struktur i en tabel, der indeholder følgende kolonner:

* *Kolonne*: Navnet på kolonnen. Hvis navnet ændres, vises det gamle navn overstreget ~~således~~.
* *Type*: Den Python-type, som data fra kolonnen skal behandles som i koden.
* *Format (regex)*: Det format rådata fra kolonnen har (i regex). Hvis dette felt er tomt, er kolonnen en, som jeg selv opretter, og som ikke findes i det oprindelige datasæt.
* *SQL*: Den datatype, som jeg definerer kolonnen som i SQL-queriet til den konsoliderede, endelige database.

Til sidst kommenterer jeg på relevante overvejelser vedr. datarensning og -transformation af de forskellige tabeller i datasættene og forklarer, hvorfor jeg evt. udelader kolonner eller opretter nye, når jeg samler alle dataene til sidst.

#### [Brands](data_db/brands.csv)
Hentet gennem: MySQL-DB
Rådataformat: *list[tuple]*
Eksempel på rådata: `[(1, 'Electra'),` ... `]`
<details>
<summary>Eksempel på slutformat:</summary>

```py
brands = {
    "header": { 
        "brand_id": int,
        "brand_name": str
    },
    "keys": {
        "primary": "brand_id",
        "foreign": {}
    },
    "data": [
        {
            "brand_id": 1,
            "brand_name": "Electra"
        },
```
...
```py
    ]
}
```
</details>

##### Struktur
| Kolonne | Type | Format (regex) | SQL |
|:-------:|:----:|:------:|:---:|
| `brand_id` | *int* | `\d` | `SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT UNIQUE` |
| `brand_name` | *str* | `[A-z ]+` | `VARCHAR(40) NOT NULL` |

##### Keys
`PRIMARY KEY (brand_id)`

##### Kommentarer
Til `brand_id` bruger jeg `SMALLINT`, da det er usandsynligt, at virksomheden nogensinde kommer til at forhandle mere end 65535 ($2^{16}$) forskellige brands.

Det længste navn i tabellen over brands er på 12 bogstaver, så man kunne gøre `VARCHAR` endnu kortere end 40 tegn og spare lidt, men der skal på den anden side også være noget plads til et potentielt langt brandnavn.

#### [Categories](data_db/categories.csv)
Hentet gennem: MySQL-DB
Rådataformat: *list[tuple]*
Eksempel på rådata: `[(1, 'Children Bicycles'),` ... `]`
<details>
<summary>Eksempel på slutformat:</summary>

```py
categories = {
    "header": { 
        "category_id": int,
        "category_name": str
    },
    "keys": {
        "primary": "category_id",
        "foreign": {}
    },
    "data": [
        {
            "category_id": 1,
            "category_name": "Children Bicycles"
        },
```
...
```py
    ]
}
```
</details>

##### Struktur
| Kolonne | Type | Format (regex) | SQL |
|:-------:|:----:|:------:|:---:|
| `category_id` | *int* | `\d` | `SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT UNIQUE` |
| `category_name` | *str* | `[A-z ]+` | `VARCHAR(40) NOT NULL` |

##### Keys
`PRIMARY KEY (category_id)`

##### Kommentarer
Se [ovenfor](#kommentarer) for længden af `category_id` og `category_name`. Her er det længste navn i `category_name` på 19 bogstaver, altså stadig under halvdelen af den samlede allokerede længde i `VARCHAR`.

#### [Customers](data_api/data/customers.csv)
Hentet gennem: API
Rådataformat: *str* (JSON)
Eksempel på rådata: `'[{"customer_id":1,"first_name":"Debra","last_name":"Burks","phone":"NULL","email":"debra.burks@yahoo.com","street":"9273 Thorne Ave. ","city":"Orchard Park","state":"NY","zip_code":14127},` ... `]'`
<details>
<summary>Eksempel på slutformat:</summary>

```py
customers = {
    "header": {
        "customer_id": int,
        "first_name": str,
        "last_name": str,
        "phone": str,
        "email": str,
        "street": str,
        "city": str,
        "state": str,
        "zip_code": int
    },
    "keys": {
        "primary": "customer_id",
        "foreign": {}
    },
    "data": [
        {
            "customer_id": 1,
            "first_name": "Debra",
            "last_name": "Burks",
            "phone": "NULL",
            "email": "debra.burks@yahoo.com",
            "street": "9273 Thorne Ave.",
            "city": "Orchard Park",
            "state": "NY",
            "zip_code": 14127
        },
```
...
```py
    ]
}
```
</details>

##### Struktur
| Kolonne | Type | Format (regex) | SQL |
|:-------:|:----:|:------:|:---:|
| `customer_id` | *int* | `\d{1,4}` | `MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT UNIQUE` |
| `first_name` | *str* | `[A-z]+` | `VARCHAR(40) NOT NULL` |
| `last_name` | *str* | `[A-z]+` | `VARCHAR(40) NOT NULL` |
| `phone` | *str* | `\(\d{3}\) \d{3}-\d{4}` eller `NULL` | `CHAR(14)` |
| `email` | *str* | `[a-z]+\.[a-z]+@[a-z]+\.com` | `VARCHAR(80) NOT NULL UNIQUE` |
| `street` | *str* | `\d+[A-Z]* [A-z \.\d]+` | `VARCHAR(63) NOT NULL` |
| `city` | *str* | `[A-z ]+` | `VARCHAR(40) NOT NULL` |
| `state` | *str* | `[A-Z]{2}` | `CHAR(2) NOT NULL` |
| `zip_code` | *int* | `\d{5}` | `MEDIUMINT UNSIGNED NOT NULL` |

##### Keys
`PRIMARY KEY (customer_id)`

##### Kommentarer
Virksomheden sælger ikke internationalt, og derfor er `phone`, `state` og `zip_code` fast defineret med `CHAR` (sparer lidt tid og plads ved de to første) og `MEDIUMINT` (sparer 1 byte pr. entry...) efter det amerikanske format. Men hvis virksomheden en dag ville udvide til internationalt salg, ville det være en god ide at bruge mere variable datatyper. I det tilfælde skulle man også tilføje en `country`-kolonne og udfylde den med *USA* før tilføjelse af ny data.
Formatet for `phone` kunne man godt ændre fra *(###) ###-####* til f.eks. *###-###-####*, som er lidt lettere at splitte, hvis man skal bruge det programmatisk. Men enhver autodialler brugt i USA godtager vel standardformatet som input, og så kan man lige så godt bevare formatet, der på f.eks. udskrevne kundelister også er mere læsbart for virksomhedens ansatte.

En email kan egentlig være meget længere end de 80 tegn, der allokeres her, men [langt størstedelen](https://atdata.com/blog/long-email-addresses/) er under 40 tegn. Men fordi telefonnummeret tilsyneladende ikke er en påkrævet værdi for kunden at udfylde (kun 177 ud af 1445 kunder har oplyst telefonnummer), er det vigtigt at kunne få kontakt gennem email, så derfor giver jeg en ekstra god længde.
Bl.a derfor er `email` også unik, mens `phone` ikke er. Af andre årsager kan nævnes, at det er normalt for telefonnumre at blive overtaget af ikke-relaterede folk i fremtiden, da nummeret ofte varetages af et bestemt teleselskab og kan mistes ved skift til et andet selskab, mens det ikke er normalt, at emailadresser overtages. Og også at flere personer i en husstand kan dele samme telefonnummer, hvis det er fastnet. Man kan dog også dele emailadresse i en husholdning, men så ville man nok også dele bruger hos virksomheden.

Et af de længste vejnavne i USA er 'Jean Baptiste Pointe du Sable Lake Shore Drive' i Chicago, Illinois på 46 tegn inkl. mellemrum. Derfor er `VARCHAR(40)` ikke nok, og en længde på 63 ($2^6-1$) bruges til `street`.

Et af de længste bynavne i USA er '[Bonadelle Ranchos-Madera Ranchos](https://www.businessinsider.com/longest-town-names-us-list-2019-7?op=1#30-letters-fetters-hot-springs-agua-caliente-california-2)' i Californien på 33 tegn inkl. mellemrum. Derfor burde `VARCHAR(40)` være nok til `city`.

I kolonnen `last_name` er der efternavne af gælisk afstamning, f.eks. O'Neill og McMahon, der gengives med ukorrekt brug af store bogstaver som *O'neill* og *Mcmahon*. Ligeledes kan dette findes i `city` for byen McAllen i Texas, der gengives som *Mcallen*.
I kolonnen `email` er der 10 emailadresser, der indeholder en apostrof i lokaladressen, f.eks. *harold.o'connor@...*. Mens dette er et ASCII-tegn og teknisk set kan være en gyldig adresse ifølge [RFC 3696](https://datatracker.ietf.org/doc/html/rfc3696#section-3), så er det en ugyldig adresse hos Gmail og sandsynligvis også hos langt de fleste andre store email-hosts.

I kolonnen `street` ender alle entries på et mellemrum. Dette lader ikke til at have en særlig betydning og strippes derfor væk.

#### [Order Items](data_api/data/order_items.csv)
Hentet gennem: API
Rådataformat: *str* (JSON)
Eksempel på rådata: `'[{"order_id":1,"item_id":1,"product_id":20,"quantity":1,"list_price":599.99,"discount":0.2},` ... `]`
<details>
<summary>Eksempel på slutformat:</summary>

```py
order_items = {
    "header": { 
        "order_id": int,
        "item_id": int,
        "product_id": int,
        "quantity": int,
        "list_price": decimal.Decimal,
        "discount": decimal.Decimal
    },
    "keys": {
        "primary": [
            "order_id",
            "item_id"
        ],
        "foreign": {
            "order_id": "orders(order_id)",
            "product_id": "products(product_id)"
        }
    },
    "data": [
        {
            "order_id": 1,
            "item_id": 1,
            "product_id": 20,
            "quantity": 1,
            "list_price": decimal.Decimal('599.99'),
            "discount": decimal.Decimal('0.20')
        },
```
...
```py
    ]
}
```
</details>

##### Struktur
| Kolonne | Type | Format (regex) | SQL |
|:-------:|:----:|:------:|:---:|
| `order_id` | *int* | `\d{1,4}` | `MEDIUMINT UNSIGNED NOT NULL` |
| `item_id` | *int* | `\d` | `TINYINT UNSIGNED NOT NULL` |
| `product_id` | *int* | `\d{1,3}` | `MEDIUMINT UNSIGNED NOT NULL` |
| `quantity` | *int* | `\d` | `SMALLINT UNSIGNED NOT NULL` |
| `list_price` | *decimal.Decimal* | `\d{2,5}\.*\d*` | `decimal(8,2) NOT NULL` |
| `discount` | *decimal.Decimal* | `0\.\d{1,2}` | `decimal(3,2)` |

##### Keys
`CONSTRAINT PK_order_item PRIMARY KEY (order_id,item_id)`

`FOREIGN KEY (order_id) REFERENCES orders(order_id)`

`FOREIGN KEY (product_id) REFERENCES products(product_id)`

##### Kommentarer
Kolonnen `item_id` opdeler hver ordre i de forskellige produkter, der købtes. Selvom værdien for alle ordrer i datasætten kun er etcifret, kunne man i teorien godt få en ordre med 10+ forskellige produkter, og derfor kan man ikke sætte en bestemt grænse på denne. Jeg bruger derfor `INT`.
Man kunne også overveje, om der overhovedet er nogen grund til at bevare `item_id`. Det eneste, jeg lige kan komme på, er, at man måske kunne bruge det til at analysere noget med vareprioritering, da tallet afspejler rækkefølgen, hvori de forskellige produkter i en given ordre blev lagt i varekurven. Ellers ved

I kolonnen `quantity` findes ligeledes kun etcifrede tal, og man kunne igen forestille sig, at man kunne sælge f.eks. 10+ reflekser el.lign., hvis virksomheden nu også begynder at bruge databasen til ekstraudstyr, og ikke kun cykler. Men kommer de mon til at sælge over 255 af samme vare? Måske, så for at være på den sikre side, kunne man bruge `SMALLINT` istf. `TINYINT`.

Man kunne måske tro, at `list_price` var overflødig, fordi man altid kan hente den gennem `product_id`, men man må ikke glemme, at prisen her i ordrelisten er den specifikke pris på ordretidspunktet, og at prisen i produktlisten er dynamisk og kan ændres pga. prisjusteringer, inflation mm. Hvis man henter prisen gennem `product_id` kan det hurtigt gå galt med regnskabet. Derfor sletter jeg ikke kolonnen `list_price`, selvom prisen for hvert produkt i denne ordreliste er identisk med prisen i prislisten.

Den højeste pris i dataene er 11999.99, der indeholder 7 cifre. Det er usandsynligt, at forretningen får en cykel med en pris på over 99999.99 dollars, så derfor er `M = 7` i `decimal(M,D)`. For alligevel at være på den sikre side, sætter jeg dog `M = 8`. Da dollaren deles i 100 underenheder (cent), har alle priserne kun 2 decimaler (.00 til .99), og derfor ender vi på `decimal(7,2)`. Når priserne i tabellen er heltal, angives ingen decimaltal. Ved konvertering til `decimal.Decimal` kan man bruge `.quantize(decimal.Decimal("1.00"))` til at sørge for, at heltallene også har præcis to decimaler.

Rabatten i tabellen er altid en procent i decimalform, og der er aldrig mere end to decimaler, f.eks. 0.75, så denne sættes til `decimal(3,2)`.
**NB!** Man skal passe ved udregning af den endelige pris efter rabat pga. *round-to-even*-konceptet:
```py
>>> import decimal
>>> price = decimal.Decimal("12.25") * decimal.Decimal("0.5")
>>> round(price, 2)
decimal.Decimal('6.12')
>>> price = decimal.Decimal("12.75") * decimal.Decimal("0.5")
>>> round(price, 2)
decimal.Decimal('6.38')
```
Man ville ellers forvente, at 6.125 blev rundet op til 6.13, ligesom 6.375 bliver rundet til 6.38.

#### [Orders](data_api/data/orders.csv)
Hentet gennem: API
Rådataformat: *str* (JSON)
Eksempel på rådata: `'[{"order_id":1,"customer_id":259,"order_status":4,"order_date":"01/01/2016","required_date":"03/01/2016","shipped_date":"03/01/2016","store":"Santa Cruz Bikes","staff_name":"Mireya"},` ... `]`
<details>
<summary>Eksempel på slutformat:</summary>

```py
orders = {
    "header": { 
        "order_id": int,
        "customer_id": int,
        "order_status": int,
        "order_date": datetime.date,
        "required_date": datetime.date,
        "shipped_date": datetime.date,
        "store": str
        "staff_name": str
    },
    "keys": {
        "primary": "order_id",
        "foreign": {
            "customer_id": "customers(customer_id)",
            "store_id": "stores(store_id)",
            "staff_id": "staff(staff_id)"
        }
    },
    "data": [
        {
            "order_id": 1,
            "customer_id": 259,
            "order_status": 4,
            "order_date": datetime.date(2016, 1, 1),
            "required_date": datetime.date(2016, 1, 3),
            "shipped_date": datetime.date(2016, 1, 3),
            "store": "Santa Cruz Bikes",
            "staff_name": "Mireya"
        },
```
...
```py
    ]
}
```
</details>

##### Struktur
| Kolonne | Type | Format (regex) | SQL |
|:-------:|:----:|:------:|:---:|
| `order_id` | *int* | `\d{1,4}` | `MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT UNIQUE` |
| `customer_id` | *int* | `\d{1,4}` | `MEDIUMINT UNSIGNED NOT NULL` |
| `order_status` | *int* | `[1-4]` | `TINYINT UNSIGNED NOT NULL` |
| `order_date` | *datetime.date* | `\d{2}/\d{2}/\d{4}` | `DATE NOT NULL` |
| `required_date` | *datetime.date* | `\d{2}/\d{2}/\d{4}` | `DATE NOT NULL` |
| `shipped_date` | *datetime.date* | `\d{2}/\d{2}/\d{4}` eller `NULL` | `DATE` |
| `store_id` | *int* | — | `SMALLINT UNSIGNED NOT NULL` |
| `store` | *str* | `[A-z ]+` | — |
| `staff_id` | *int* | — | `SMALLINT UNSIGNED NOT NULL` |
| `staff_name` | *str* | `[A-z]+` | — |

##### Keys
`PRIMARY KEY (order_id)`

`FOREIGN KEY (customer_id) REFERENCES customers(customer_id)`

`FOREIGN KEY (store_id) REFERENCES stores(store_id)`

`FOREIGN KEY (staff_id) REFERENCES staff(staff_id)`

##### Kommentarer
Jeg erstatter `store` og `staff_name` med hhv. `store_id` og `staff_id`, se hvorfor [her](#kommentarer-8) og [her](#kommentarer-6).
Man kunne overveje helt at fjerne `store`/`store_id`, fordi denne værdi kan findes gennem `staff_id`. Men en ansat kan jo også skifte arbejdsplads internt i virksomheden, og hvis man skal lave statistik over salg fra bestemte branches, duer det ikke, at et salg pludselig tæller for en anden branch, bare fordi medarbejderen er flyttet derover. Hvis en succesfuld sælger f.eks. bliver forfremmet til manager af en ny branch, skal vedkommendes salgsstatistik jo ikke tælle med for en nyåbnet butik, der ikke har solgt noget endnu. Så kommer ordredatoerne også til at ligge før denne branchs åbningsdato.

`order_status` kan have en af fire værdier: 1, 2, 3 eller 4. Denne kunne altså laves som en `ENUM`, da hver værdi har en bestemt betydning. Jeg gætter på, at det er noget i stil med

1. Ordre modtaget
2. Ordre under behandling
3. Ordre klargjort
4. Ordre afsendt

I så fald ville man skrive `ENUM('received', 'processing', 'ready', 'shipped')`. Det smarte ved en `ENUM` er, at de forskellige værdier både kan refereres til via navn eller indeks. F.eks. svarer `'received'` til værdien 1, `'processing'` til 2, osv.

Men det er lidt svært at tyde ud fra dataene, udover nr. 4, da det er den eneste status, hvor `shipped_date` er udfyldt.
De andre statusser er der ikke så meget unikt ved. `shipped_date` er den eneste af datoerne, der kan være `NULL` og differentiere.
`order_date` altid vil blive oprettet sammen med selve ordren og blive udfyldt, og `required_date` er også altid udfylt, uanset om `order_status` er 1, 2, 3 eller 4.
Statussen 3 kunne f.eks. også være en afbestilt ordre, da den findes rundt omkring i tabellen genne flere år blandt afsendte ordrer med status 4.
Status 1 og 2 findes kun i bunden af datasættet i måneden april 2018, der ud fra de senest afsendte ordrer med status 4 i starten af april ser ud til at passe med ikke-afsendte order, der er modtaget eller under forberedelse i "nutiden". 
Men der er også status 3 i bunden, der ser ud til at være "fremtidige" ordrer, og altså ikke afbestillinger. Måske er det rettere inaktive ordrer.

#### [Products](data_db/products.csv)
Hentet gennem: MySQL-DB
Rådataformat: *list[tuple]*
Eksempel på rådata: `[(1, 'Trek 820 - 2016', 9, 6, 2016, 379.99),` ... `]`
<details>
<summary>Eksempel på slutformat:</summary>

```py
products = {
    "header": { 
        "product_id": int,
        "product_name": str,
        "brand_id": int,
        "category_id": int,
        "model_year": int,
        "list_price": decimal.Decimal
    },
    "keys": {
        "primary": "product_id",
        "foreign": {
            "brand_id": "brands(brand_id)",
            "category_id": "categories(category_id)"
        }
    },
    "data": [
        {
            "product_id": 1,
            "product_name": "Trek 820 - 2016",
            "brand_id": 9,
            "category_id": 6,
            "model_year": 2016,
            "list_price": decimal.Decimal('379.99')
        },
        ...
    ]
}
```
</details>

##### Struktur
| Kolonne | Type | Format (regex) | SQL |
|:-------:|:----:|:------:|:---:|
| `product_id` | *int* | `\d{1,3}` | `MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT UNIQUE` |
| `product_name` | *str* | `[A-z ]+` | `VARCHAR(40) NOT NULL UNIQUE` |
| `brand_id` | *int* | `\d` | `SMALLINT UNSIGNED NOT NULL` |
| `category_id` | *int* | `\d` | `SMALLINT UNSIGNED NOT NULL` |
| `model_year` | *int* | `\d{4}` | `SMALLINT UNSIGNED NOT NULL` |
| `list_price` | *decimal.Decimal* | `\d{2,5}\.*\d*` | `DECIMAL(8,2) NOT NULL` |

##### Keys
`PRIMARY KEY (product_id)`

`FOREIGN KEY (brand_id) REFERENCES brands(brand_id)`

`FOREIGN KEY (category_id) REFERENCES categories(category_id)`

##### Kommentarer
Se [her](#kommentarer-3) for længden af `list_price`.

#### [Staff](data_csv/staffs.csv)
Hentet gennem: CSV
Rådataformat: *list[str]* (CSV)
Eksempel på rådata: `['Fabiola,Jackson,fabiola.jackson@bikes.shop,(831) 555-5554,1,Santa Cruz Bikes,3700 Portola Drive,NULL',` ... `]`
<details>
<summary>Eksempel på slutformat:</summary>

```py
staff = {
    "header": {
        "staff_id": int,
        "first_name": str,
        "last_name": str,
        "email": str,
        "phone": str,
        "active": int,
        "store_id": int,
        "manager_id": int
    },
    "keys": {
        "primary": "staff_id",
        "foreign": {
            "store_id": "stores(store_id)",
            "manager_id": "staff(staff_id)"
        }
    },
    "data": [
        {
            "staff_id": 1,
            "first_name": "Fabiola",
            "last_name": "Jackson",
            "email": "fabiola.jackson@bikes.shop",
            "phone": "(831) 555-5554,
            "active": 1,
            "store_id": 1,
            "manager_id": None
        },
```
```py
    ]
}
```
</details>

##### Struktur
| Kolonne | Type | Format (regex) | SQL |
|:-------:|:----:|:------:|:---:|
| `staff_id` | *int* | — | `SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT UNIQUE` |
| ~~`name`~~ `first_name` | *str* | `[A-z]+` | `VARCHAR(40) NOT NULL` |
| `last_name` | *str* | `[A-z]+` | `VARCHAR(40) NOT NULL` |
| `email` | *str* | `[a-z]+\.[a-z]+@bikes\.shop` | `VARCHAR(80) NOT NULL UNIQUE` |
| `phone` | *str* | `\(\d{3}\) \d{3}-\d{4}` | `CHAR(14) NOT NULL UNIQUE` |
| `active` | *int* | `\d` | `BOOLEAN NOT NULL` |
| `store_id` | *int* | — | `SMALLINT UNSIGNED NOT NULL` |
| `store_name` | *str* | `[A-z ]+ Bikes` | — |
| `street` | *str* | `\d+[A-Z]* [A-z \.\d]+` | — |
| `manager_id` | *int* | `\d+` eller `NULL` | `SMALLINT UNSIGNED` |

##### Keys
`PRIMARY KEY (staff_id)`

`FOREIGN KEY (store_id) REFERENCES stores(store_id)`

`FOREIGN KEY (manager_id) REFERENCES staff(staff_id)`


##### Kommentarer
Jeg refererer til butikkens id istf. navn, se [hvorfor](#kommentarer-8). Navnet på kolonnen `name` ændrer jeg samtidig til `first_name`.

Jeg laver en kolonne `staff_id` som primary key. `manager_id` bruger allerede et nummer for at referere til en ansat. Chefen Fabiola Jackson har ingen leder, så værdien her er `NULL` (hvilket bliver til `None` i *dict*-strukturen?), mens Mireya, Jannette og Kali leder hver deres afdeling, og alle har Fabiola (1) som chef. Genna og Virgie i Santa Cruz har Mireya (2) som chef, Marceline og Venita i Baldwin har Jannette (5) som chef. Layla og Bernardine i Rowlett burde stå med Kali (8) som chef, men de står med Venita (7) som chef. Det giver ikke mening, at ansatte i Rowlett har en ansat i Baldwin som chef, mens lederen i Rowlett ikke har nogle ansatte under sig. Det er et eksempel på, hvorfor det er en god ide at få et id som primary key, så man ikke laver fejl som denne ved at tælle manuelt.

Jeg gør `email` og `phone` til kolonner, der skal indeholde unikke værdier, da hver emailadresse er på virksomhedens domæne og tildeles til hver medarbejder, og da telefonnumrene er konsekutive og derfor også ser ud til at være blevet tildelt af virksomheden.

`active` kan være en `BIT(1)` eller `BOOLEAN` (som er alias for `TINYINT(1)`). Jeg har valgt at bruge boolean, da det er en sand/falsk værdi, og da heltalsværdierne 0 og 1 så bevares, uden at man skal til at bøvle med `b'0'`, `b'1'`, `0b0`, `0b1` eller lignende.

`street` er ikke medarbejderens adresse, men butikkens, så denne kolonne fjernes sammen med `store_name`, da de begge kan udledes af `store_id`.

#### [Stock](data_db/stocks.csv)
Hentet gennem: MySQL-DB
Rådataformat: *list[tuple]*
Eksempel på rådata: `[('Santa Cruz Bikes', 1, 27), ` ... `]`
<details>
<summary>Eksempel på slutformat:</summary>

```py
stock = {
    "header": { 
        "store_id": int,
        "product_id": int,
        "quantity": int
    },
    "keys": {
        "primary": [
            "store_id",
            "product_id"
        ]
        "foreign": {
            "product_id": "products(product_id)"
        }
    },
    "data": [
        {
            "store_id": 1,
            "product_id": 1,
            "quantity": 27
        },
        ...
    ]
}
```
</details>

##### Struktur
| Kolonne | Type | Format (regex) | SQL |
|:-------:|:----:|:------:|:---:|
| `store_id` | *int* | — | `SMALLINT UNSIGNED NOT NULL` |
| `store_name` | *str* | `[A-z ]+` | — |
| `product_id` | *int* | `\d{1,3}` | `MEDIUMINT UNSIGNED NOT NULL` |
| `quantity` | *int* | `\d{1,2}` | `MEDIUMINT UNSIGNED NOT NULL` |

##### Keys
`CONSTRAINT PK_store_id_product_id PRIMARY KEY (store_id,product_id)`

`FOREIGN KEY (product_id) REFERENCES products(product_id)`

##### Kommentarer
Jeg refererer til butikkens id istf. navn, se [hvorfor](#kommentarer-8). Selvom virksomheden har meget lang udsigt til at åbne mere end 255 butikker, så bruger jeg `SMALLINT` hertil for en sikkerheds skyld.

#### [Stores](data_csv/stores.csv)
Hentet gennem: CSV
Rådataformat: *list[str]* (CSV)
Eksempel på rådata: `['Santa Cruz Bikes,(831) 476-4321,santacruz@bikes.shop,3700 Portola Drive,Santa Cruz,CA,95060',` ... `]`
<details>
<summary>Eksempel på slutformat:</summary>

```py
stores = {
    "header": {
        "store_id": int,
        "name": str,
        "phone": str,
        "email": str,
        "street": str,
        "city": str,
        "state": str,
        "zip_code": int,
    },
    "keys": {
        "primary": "store_id"
        "foreign": {}
    }
    "data": [
        {
            "store_id": 1,
            "name": "Santa Cruz Bikes",
            "phone": "(831) 476-4321",
            "email": "santacruz@bikes.shop",
            "street": "3700 Portola Drive",
            "city": "Santa Cruz",
            "state": "CA",
            "zip_code": 95060,
        },
```
...
```py
    ]
}
```
</details>

##### Struktur
| Kolonne | Type | Format (regex) | SQL |
|:-------:|:----:|:------:|:---:|
| `store_id` | *int* | — | `SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT UNIQUE` |
| `name` | *str* | `[A-z ]+ Bikes` | `VARCHAR(80) NOT NULL` |
| `phone` | *str* | `\(\d{3}\) \d{3}-\d{4}` | `CHAR(14) NOT NULL` |
| `email` | *str* | `[a-z]+@bikes\.shop` | `VARCHAR(80) NOT NULL` |
| `street` | *str* | `\d+[A-Z]* [A-z \.\d]+` | `VARCHAR(63) NOT NULL` |
| `city` | *str* | `[A-z ]+` | `VARCHAR(40) NOT NULL` |
| `state` | *str* | `[A-Z]{2}` | `CHAR(2) NOT NULL` |
| `zip_code` | *int* | `\d{5}` | `MEDIUMINT UNSIGNED NOT NULL` |

##### Keys
`PRIMARY KEY (store_id)`

##### Kommentarer
Jeg har valgt at introducere et heltal `store_id` som primary key, da det er besværligt at skulle skrive hele butiksnavnet, hver gang data fra tabellen skal bruges. Der er også risiko for at komme til at lave stavefejl, hvorimod et heltal på et enkelt ciffer er meget hurtigere at bruge og sværere at skrive forkert.
Derudover har butiksnavnet formatet [bynavn] + 'Bikes'. I USA er der alt efter kilden mellem 34 og 67 forskellige befolkede steder med toponymet Springfield. Hvis virksomheden en dag havde en afdeling i flere forskellige byer ved navn Springfield, ville `name` ikke kunne bruges som primary key, da de alle ville hedde 'Springfield Bikes', eller måske 'Springfield Bikes Oregon'. Det er sikrere at bruge `store_id`.

Mange af `VARCHAR`-længderne forklares [her](#kommentarer-2).

### Loading
Da vi på kurset har arbejdet med MySQL, er det kun naturligt, at den samlede data lagres i sådan en databse.
