# Questions asked of the map data
Database: `01-use-cases/maps/04-from-map-data/operations/work/research.duckdb` (DuckDB with the spatial extension). Each row is one *name* of one place; `source_page_id` is the GOV id.

## What kinds of object are in the rectangle?

```sql
SELECT split_part(notes, '; ', 2) AS kind, count(DISTINCT source_page_id) AS places FROM records GROUP BY 1 ORDER BY 2 DESC LIMIT 12
```

| kind | places |
|---|---|
| Stadtteil/Ortsteil | 1054 |
| Pfarrei (ev.) | 253 |
| Pfarrei (kath.) | 98 |
| Kirche | 82 |
| Amtsbezirk | 38 |
| Gutsbezirk | 35 |
| Kirche (kath.) | 32 |
| Kreis | 31 |
| Stadt | 23 |
| Standesamt | 21 |
| Gemeinde | 21 |
| type 121 | 6 |

## How many places carry a German name that ended in 1945, and a Polish name that began then?

```sql
SELECT sum(CASE WHEN notes LIKE 'deu;%' AND year_end = 1945 THEN 1 ELSE 0 END) AS german_names_ended_1945, sum(CASE WHEN notes LIKE 'pol;%' AND year_start = 1945 THEN 1 ELSE 0 END) AS polish_names_from_1945, count(DISTINCT source_page_id) AS places FROM records
```

| german_names_ended_1945 | polish_names_from_1945 | places |
|---|---|---|
| 497 | 955 | 1715 |

## Which places had more than two names over time?

```sql
SELECT source_page_id AS gov_id, normalized AS today, count(*) AS names, string_agg(surface_form || CASE WHEN year_start IS NULL AND year_end IS NULL THEN '' ELSE ' (' || coalesce(year_start::VARCHAR, '?') || '–' || coalesce(year_end::VARCHAR, '') || ')' END, ' · ' ORDER BY year_start NULLS FIRST) AS history FROM records GROUP BY 1, 2 HAVING count(*) > 2 ORDER BY names DESC, gov_id LIMIT 12
```

| gov_id | today | names | history |
|---|---|---|---|
| object_186094 | Szczytniki | 13 | Schzitthnik, Schzithnik · Schytnik, Shtenik · Szytnik · Altscheidnig (?–1868) · Tscheitnigk · Schitnik · Scithniki · Alt-Scheitnig · Scheidnigk · Schitenig · Sczytnik · Sczytnik · Szczytniki (1945–) |
| STHGISJO81IG | Brzeg Dolny (św. Jadwigi) | 6 | St. Hedwigsstift Dyhernfurth (S. Hedwigis) · St. Hedwigsstift Dyhernfurth (Hl. Hedwig) · Brzeg Dolny (św. Jadwigi) · Kloster Hedwigsruh (S. Familiae) · Kloster Hedwigsruh (Hl. Hedwig) · Kloster Hedwigsruh (Kirche der Boromäerinnen) |
| BECAUFJO81FA | Piekary (św. Jana Chrzciciela) | 5 | Beckern (Hl. Johannes Täuf.) · Beckern (Hl. Johannes Täuf.) · Piekary (św. Jana Chrzciciela) · Beckern (S. Joannes Bapt.) · Beckern (S. Joannes Bapt.) |
| BREADTJO81MC | Wrocław | 5 | Breslau · Wrezlaue · Wreczelaw · Wratislavia (1295–1305) · Wrocław (1946–) |
| HALNAEJO80OT | Półwiosek, Wiązów (św. Marii Magdaleny) | 5 | Półwiosek, Wiązów (św. Marii Magdaleny) · Halbendorf (Hl. Magdalena) · Halbendorf (Begräbniskirche) · Halbendorf (S. Magdalenae) · Halbendorf (S. Mariae Magdalenae) |
| JARAUFJO80FX | Jaroszów (św. Jana Chrzciciela) | 5 | Järischau (Hl. Johannes Täuf.) · Järischau (S. Joannes Bapt.) · Jarischau (Hl. Johannes Täuf.) · Jarischau (S. Joannes Bapt.) · Jaroszów (św. Jana Chrzciciela) |
| NIEWIGJO80EU | Mokrzeszów (św. Jadwigi) | 5 | Nieder Kunzendorf (Hl. Hedwig) · Mokrzeszów (św. Jadwigi) · Ober- und Nieder Kunzendorf (S. Hedwigis) · Nieder Kunzendorf (S. Hedwigis) · Ober- und Nieder Kunzendorf (Hl. Hedwig) |
| PROBMVJO81GD | Środa Śląska (Narodzenia Najświętszej Maryi Panny) | 5 | Środa Śląska (Narodzenia Najświętszej Maryi Panny) · Propstei (B. M. V.) · Propstei (Propsteikirche) · Propstei (St. Maria) · Probostwo (Narodzenia Najświętszej Maryi Panny) |
| ALTHKEJO81LH | Kuraszków | 4 | Alt Karoschke (?–1936) · Karoschke (1936–1937) · Lindenwaldau (1937–1945) · Kuraszków (1945–) |
| ALTTTEJO81RM | Czeszyce | 4 | Alt Glashütte · Glashütte Tscheschen · Tschechen-Glashütte (1937–) · Czeszyce (1945–) |
| ARNANGJO80EU | Milikowice (św. Michała Archanioła) | 4 | Nieder Arnsdorf · Arnsdorf (S. Michael Archang.) · Arnsdorf (Hl. Michael Erzeng.) · Milikowice (św. Michała Archanioła) |
| BENGISJO81MH | Będkowo (św. Jadwigi) | 4 | Bentkau (S. Hedwigis) · Będkowo (św. Jadwigi) · Bentkau (Hl. Hedwig) · Bentkau (Feldkapelle) |

## The ten places nearest Breslau's centre (17.0325, 51.11), by great-circle distance

```sql
SELECT DISTINCT source_page_id AS gov_id, normalized AS today, round(ST_Distance_Sphere(ST_Point(lon, lat), ST_Point(17.0325, 51.11)) / 1000, 1) AS km FROM records WHERE source_page_id NOT LIKE 'BREADT%' ORDER BY km LIMIT 10
```

| gov_id | today | km |
|---|---|---|
| object_172537 | Breslau/St.Elisabeth | 0.2 |
| BREIAEJO81MC | Wrocław (św. Macieja) | 0.4 |
| BREHEAJO81MC | Wrocław (św. Stanisława, św. Doroty i św. Wacława) | 0.4 |
| BRERAEJO81MC | Wrocław (św. Klary i św. Jadwigi) | 0.5 |
| object_1187180 | Wrocław (Katedra greckokatolicka pw. św. Wincentego i św. Jakuba) | 0.5 |
| BREERTJO81MC | Wrocław (św. Wojciecha) | 0.5 |
| BREGISJO81MC | Wrocław (św. Klary i św. Jadwigi) | 0.5 |
| BREESUJO81MC | Wrocław (Imienia Jezus) | 0.5 |
| object_172549 | Breslau/St.Barbara | 0.6 |
| BRENIIJO81MC | Wrocław (św. Antoniego z Padwy) | 0.6 |

## Towns (Stadt) in the rectangle, with the name a 1786 traveller would have used

```sql
SELECT source_page_id AS gov_id, string_agg(DISTINCT surface_form, ' / ') AS names, any_value(normalized) AS today FROM records WHERE notes LIKE '%Stadt%' AND notes NOT LIKE '%Stadtteil%' GROUP BY 1 ORDER BY 1 LIMIT 20
```

| gov_id | names | today |
|---|---|---|
| BERADTJO81SC | Bierutów / Bernstadt | Bierutów |
| BREADTJO81MC | Wrezlaue / Wrocław / Wreczelaw / Breslau / Wratislavia | Wrocław |
| DYHADTJO81IG | Brzeg Dolny / Dyhernfurth | Brzeg Dolny |
| FESADTJO81RI | Twardagóra / Festenberg | Twardagóra |
| FRELESJO80DU | Świebodzice / Freiburg in Schlesien | Świebodzice |
| KANADTJO81JA | Kanth / Canth / Kąty Wrocławskie | Kąty Wrocławskie |
| LASITZJO81QA | Markstädt / Laskowitz / Jelcz-Laskowice | Jelcz-Laskowice |
| NEUADTJO81HE | Środa Śląska / Neumarkt in Schlesien | Środa Śląska |
| OELADTJO81QF | Oleśnica / Oels / Öls | Oleśnica |
| OHLADTJO80PW | Oława / Ohlau | Oława |
| PARADTJO81EG | Prochowice / Parchwitz | Prochowice |
| SCHITZJO80FT | Świdnica / Schweidnitz | Świdnica |
| STEADTJO81FK | Steinau an der Oder / Ścinawa | Ścinawa |
| STRADTJO80EX | Striegau / Strzegom | Strzegom |
| TRAER1JO81KL | Trachenberg / Żmigród | Żmigród |
| TREADTJO81MH | Trzebnica / Trebnitz | Trzebnica |
| WANSENJO80OT | Wansen / Wiązów | Wiązów |
| WOHADTJO81HH | Wołów / Wohlau | Wołów |
| object_186081 | Sobótka / Zobten am Berge | Sobótka |
| object_186125 | Brieg / Brzeg | Brzeg |

## Which stops of the 1786 route (maps/01) fall inside the rectangle, and what GOV has at that point

| stop | nearest GOV object | km |
|---|---|---|
| Breslau | BREADTJO81MC (Wrocław) | 0.0 |
