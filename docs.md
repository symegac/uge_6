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

Til sidst bør hver tabel have form som en *dict* indeholdende to underinddelinger.
Den første af disse er headeren, der er endnu en *dict*, hvori nøglerne består af navnet på de forskellige kolonner, mens værdierne udgøres af datatypen for hver kolonne.
Den anden er en liste af *dict*s, hver tilsvarende en datarække. Nøglerne i denne *dict* er igen navnet på kolonnen, mens værdierne er værdien i samme kolonnes datafelt i den givne række.
Det vil sige, at formatet er
> *dict[dict[str], list[dict[str]]]*

<details>
<summary>På udvidet Backus-Naur-form:</summary>

```bnf
<tabel-dict> ::= '{' <header-dict> ',' <data-list> '}'

<header-dict> ::= '"header": {' <kolonne-kvpair>+ '}'
<kolonne-kvpair> ::= <kolonnenavn-key> ':' <datatype-value> ','

<data-list> ::= '"data": [' <række-dict>+ ']'
<række-dict> ::= '{' <datafelt-kvpair>+ '}'
<datafelt-kvpair> ::= <kolonnenavn-key> ':' <feltværdi-value> ','

<kolonnenavn-key> ::= <str (Python)>
<datatype-value> ::= <type (Python)>
<feltværdi-value> ::= <Any (Python)>
```
</details>
<details>
<summary>Eller illustreret her:</summary>

```py
{
    "header": {
        "kolonne 0-navn": <type K_0_Type>,
        ...,
        "kolonne i-navn": <type K_i_Type>
    },
    "data": [
        {
            "kolonne 0-navn": feltværdi-r_0-k_0,
            ...,
            "kolonne i-navn": feltværdi-r_0-k_i
        },
        ...,
        {
            "kolonne 0-navn": feltværdi-r_i-k_0,
            ...,
            "kolonne i-navn": feltværdi-r_i-k_i
        }
    ]
}
```
</details>

Jeg har valgt at bruge dette format, dels fordi det er utrolig let at gå fra JSON til dette format, dels fordi jeg i *uge_2*-opgaven outputtede rensede data som en *dict* og derfor allerede har noget kode, dels fordi *mysql-connector-python* i forvejen bruger en *dict* til at indsætte værdierne i parameteriserede queries, og jeg derfor også har noget kode fra *uge_4*-opgaven i forvejen.

### Transformation
Her er det vigtigt at kigge på de forskellige datakilders struktur.
Hvilke datafelter har de, og hvilke datatyper?
Hvilke relationer er der i de forskellige datasæt? Primary keys og foreign keys? Har et datasæt alt i én tabel, mens andre har flere tabeller?
Er der overlap mellem datafelterne i datasættene. Hvis ja, er der dubletter blandt de forskellige entries, eller er der måske entries med samme nøgle men forskelligt indhold? Hvis nej, hvilke datafelter skal så tages med fra de forskellige kilder?
Og i den sammenhæng, hvilken struktur skal de endelige data have? Er det i orden, at nogle kolonner ikke har data for nogle rækker?

Herunder følger analyser af strukturen og formatet af de forskellige datasæt og kommentarer til datarensning/-transformation.

#### [Brands](data_db/brands.csv)
Hentet gennem: MySQL-DB
Rådataformat: *list[tuple]*
Eksempel på rådata: `[(1, 'Electra'),` ... `]`
<details>
<summary>Eksempel på slutformat:</summary>

```py
{
    "header": { 
        "brand_id": int,
        "brand_name": str
    },
    "data": [
        { "brand_id": 1, "brand_name": "Electra" },
        ...
    ]
}
```
</details>

##### Struktur
| Kolonne | Type | Format (regex) | SQL |
|:-------:|:----:|:------:|:---:|
| `brand_id` | *int* | `\d{1}` | `int PRIMARY KEY AUTO_INCREMENT` |
| `brand_name` | *str* | `[A-z ]+` | `varchar(40) NOT NULL` |

##### Kommentarer

#### [Categories](data_db/categories.csv)
Hentet gennem: MySQL-DB
Rådataformat: *list[tuple]*
Eksempel på rådata: `[(1, 'Children Bicycles'),` ... `]`
<details>
<summary>Eksempel på slutformat:</summary>

```py
{
    "header": { 
        "category_id": int,
        "category_name": str
    },
    "data": [
        { "category_id": 1, "category_name": "Children Bicycles" },
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
|||||

##### Kommentarer

#### [Customers](data_api/data/customers.csv)
Hentet gennem: API
Rådataformat: JSON
Eksempel på rådata: `'[{"customer_id":1,"first_name":"Debra","last_name":"Burks","phone":"NULL","email":"debra.burks@yahoo.com","street":"9273 Thorne Ave. ","city":"Orchard Park","state":"NY","zip_code":14127},` ... `]'`
<details>
<summary>Eksempel på slutformat:</summary>

```py
{
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
| `customer_id` | *int* | `\d{1,4}` | `int PRIMARY KEY AUTO_INCREMENT` |
| `first_name` | *str* | `[A-z]+` | `varchar(40) NOT NULL` |
| `last_name` | *str* | `[A-z]+` | `varchar(40) NOT NULL` |
| `phone` | *str* | `\(\d{3}\) \d{3}-\d{4}` eller `NULL` | `char(14)` |
| `email` | *str* | `[a-z]+\.[a-z]+@[a-z]+\.com` | `varchar(80) NOT NULL` |
| `street` | *str* | `\d+[A-Z]* [A-z \.\d]+ ` | `varchar(80) NOT NULL` |
| `city` | *str* | `[A-z ]+` | `varchar(80) NOT NULL` |
| `state` | *str* | `[A-Z]{2}` | `char(2) NOT NULL` |
| `zip_code` | *int* | `\d{5}` | `mediumint NOT NULL` |

##### Kommentarer
Virksomheden sælger ikke internationalt, og derfor er `phone`, `state` og `zip_code` fast defineret med `char` (sparer lidt tid og plads) og `mediumint` (sparer 1 byte pr. entry...) efter det amerikanske format. Men hvis virksomheden en dag ville udvide til internationalt salg, ville det være en god ide at bruge mere variable datatyper. I det tilfælde skulle man også tilføje en `country`-kolonne og udfylde den med *USA* før tilføjelse af ny data.
Formatet for `phone` kunne man godt ændre fra *(###) ###-####* til f.eks. *###-###-####*, som er lidt lettere at splitte, hvis man skal bruge det programmatisk. Men enhver autodialler brugt i USA godtager vel standardformatet som input, og så kan man lige så godt bevare formatet, der på f.eks. udskrevne kundelister også er mere læsbart for virksomhedens ansatte.

I kolonnen `last_name` er der efternavne af gælisk afstamning, f.eks. O'Neill og McMahon, der gengives med ukorrekt brug af store bogstaver som *O'neill* og *Mcmahon*. Ligeledes kan dette findes i `city` for byen McAllen i Texas, der gengives som *Mcallen*.
I kolonnen `email` er der 10 emailadresser, der indeholder en apostrof i lokaladressen, f.eks. *harold.o'connor@...*. Mens dette er et ASCII-tegn og teknisk set kan være en gyldig adresse ifølge [RFC 3696](https://datatracker.ietf.org/doc/html/rfc3696#section-3), så er det en ugyldig adresse hos Gmail og sandsynligvis også hos langt de fleste andre store email-hosts.

I kolonnen `street` ender alle entries på et mellemrum. Dette lader ikke til at have en særlig betydning og strippes derfor væk.

#### [Order Items](data_api/data/order_items.csv)
Hentet gennem: API
Rådataformat: JSON
Eksempel på rådata: `'[{"order_id":1,"item_id":1,"product_id":20,"quantity":1,"list_price":599.99,"discount":0.2},` ... `]`
<details>
<summary>Eksempel på slutformat:</summary>

```py
{
    "header": { 
        "order_id": int,
        "item_id": int,
        "product_id": int,
        "quantity": int,
        "list_price": decimal.Decimal,
        "discount": float
    },
    "data": [
        {
            "order_id": 1,
            "item_id": 1,
            "product_id": 20,
            "quantity": 1,
            "list_price": decimal.Decimal('599.99'),
            "discount": 0.2
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
|||||

##### Kommentarer

#### [Orders](data_api/data/orders.csv)
Hentet gennem: API
Rådataformat: JSON
Eksempel på rådata: `'[{"order_id":1,"customer_id":259,"order_status":4,"order_date":"01/01/2016","required_date":"03/01/2016","shipped_date":"03/01/2016","store":"Santa Cruz Bikes","staff_name":"Mireya"},` ... `]`
<details>
<summary>Eksempel på slutformat:</summary>

```py
{
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
|||||

##### Kommentarer

#### [Products](data_db/products.csv)
Hentet gennem: MySQL-DB
Rådataformat: *list[tuple]*
Eksempel på rådata: `[(1, 'Trek 820 - 2016', 9, 6, 2016, 379.99),` ... `]`
<details>
<summary>Eksempel på slutformat:</summary>

```py
{
    "header": { 
        "product_id": int,
        "product_name": str,
        "brand_id": int,
        "category_id": int,
        "model_year": int,
        "list_price": decimal.Decimal
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
|||||

##### Kommentarer

#### [Staff](data_csv/staffs.csv)
Hentet gennem: MySQL-DB
Rådataformat: *list[tuple]*
Eksempel på rådata: `[(1, 'Electra'),` ... `]`
<details>
<summary>Eksempel på slutformat:</summary>

```py
{
    "header": {},
    "data": [{}]
}
```
</details>

##### Struktur
| Kolonne | Type | Format (regex) | SQL |
|:-------:|:----:|:------:|:---:|
|||||

##### Kommentarer
Hvorfor har man her addressen på butikken, når den allerede findes i Stores?

#### [Stock](data_db/stocks.csv)
Hentet gennem: MySQL-DB
Rådataformat: *list[tuple]*
Eksempel på rådata: `[('Santa Cruz Bikes', 1, 27), ` ... `]`
<details>
<summary>Eksempel på slutformat:</summary>

```py
{
    "header": { 
        "store_name": str,
        "product_id": int,
        "quantity": int
    },
    "data": [
        {
            "store_name": "Santa Cruz Bikes",
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
|||||

##### Kommentarer

#### [Stores](data_csv/stores.csv)
Hentet gennem: MySQL-DB
Rådataformat: *list[tuple]*
Eksempel på rådata: `[(),` ... `]`
<details>
<summary>Eksempel på slutformat:</summary>

```py
{
    "header": {},
    "data": [{}]
}
```
</details>

##### Struktur
| Kolonne | Type | Format (regex) | SQL |
|:-------:|:----:|:------:|:---:|
|||||

##### Kommentarer

### Loading
Da vi på kurset har arbejdet med MySQL, er det kun naturligt, at den samlede data lagres i sådan en databse.
