# Kontrola kvality Devex vah a obnova rámce — závěrečný výklad

Obnova podle experimentálního poměru >9 na runtime.mps nepřinesla zrychlení. Zvýšila počet iterací a celé řešení zpomalila v obou opakováních: HH +16,30/+16,07 % (poměr průměrů +16,19 %), FT +14,10/+16,65 % (poměr průměrů +15,36 %). Tento kandidát se nedoporučuje k produkční integraci. Výsledek nevyvrací všechny možné strategie Devex obnovy; hodnotí pouze zvolený práh, ukazatel vybraného řádku a provedení resetu.

34 procesů: dvě očekávaná původní RED selhání exit1, dvě GREEN jednotky (114 assertions celkem), 12 celých smoke, 6 runtime auditů a 12 benchmarků. Ostatních 32 procesů exit0. Všech 30 numerických comparison znovu ověřeno, 89 source + 91 reference pinů a 71 produkčních zdrojů beze změny. Obě série byly sekvenční, Devex fronta začala až po ukončení legacy pricing měření. Žádný další solve při finalizaci.

Off/passive mají přesně shodné původní event/guard/sample/end výsledky. Každý pozorovaný již vypočtený referenční součet byl v auditu samostatně přepočten ze skutečného tableau řádku. Active změnil trajektorii úmyslně; bitová shoda s off nebyla vyžadována. Každý OPTIMAL má samostatně true původní primal feasibility a skutečnou původní optimality certificate (last=true, truecalls>0), bez přidaného certifikačního volání. Benchmarky každého ramene odpovídají vlastnímu auditu v koncovém výsledku, počtech obnov, options/input/factory. Benchmarky neobsahují plnou interní stopu.

| Správce / rameno | Ref1 solve s | Kandidát1 s | Δ1 % | Ref2 solve s | Kandidát2 s | Δ2 % | Δ průměr solve % | Δ průměr smyčka % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| huangfu_hall-production / passive | 228.229239 | 228.015546 | -0.094 | 228.237391 | 226.874005 | -0.597 | -0.345 | -0.357 |
| huangfu_hall-production / active | 228.229239 | 265.423319 | +16.297 | 228.237391 | 264.924974 | +16.074 | +16.186 | +16.102 |
| forrest_tomlin-production / passive | 407.804813 | 398.986772 | -2.162 | 398.967385 | 401.078814 | +0.529 | -0.831 | -0.832 |
| forrest_tomlin-production / active | 407.804813 | 465.303512 | +14.100 | 398.967385 | 465.377857 | +16.646 | +15.359 | +15.387 |

Passive ukazuje režii samotného sledování bez změny vah. HH −0,09/−0,60 %, FT −2,16/+0,53 %: dvě opakování nedokazují, že režie je nulová nebo že pozorování samo zrychluje. Active zahrnuje WeakKeyDict, reset O(m+n), plnou kontrolu po resetu a všechnu práci změněné trajektorie; náklady se neodečítaly.

## Trajektorie a pozorovaný ukazatel

| Správce / rameno | Iterace | Refaktorizace | Pozorování | Bad ratio | Proposals | Resety | Staged vynecháno | Δ objective proti off |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| huangfu_hall-production / off | 75776 | 483 | 0 | 0 | 0 | 0 | 0 | +0 |
| huangfu_hall-production / passive | 75776 | 483 | 75760 | 1298 | 1296 | 0 | 12 | +0 |
| huangfu_hall-production / active | 84068 | 543 | 84044 | 1217 | 1217 | 1217 | 20 | -1.2218952179e-06 |
| forrest_tomlin-production / off | 75164 | 479 | 0 | 0 | 0 | 0 | 0 | +0 |
| forrest_tomlin-production / passive | 75164 | 479 | 75140 | 1229 | 1228 | 0 | 15 | +0 |
| forrest_tomlin-production / active | 85205 | 558 | 85174 | 1277 | 1275 | 1275 | 31 | +2.08616256714e-06 |

HH: iterace 75776→84068 (+10,94 %), refaktorizace 483→543. FT: 75164→85205 (+13,36 %), refaktorizace 479→558. Reset neprovádí nový basis solve přímo, ale změna pricingu vedla k více následné práci. Z tohoto experimentu nelze oddělit veškerou přímou cenu resetů od ceny změněné trajektorie.

Všechna bad ratio pozorování nastala ve fázi generation1; ve fázi0 byla pouze good. Neplatných operandů a blokací authority bylo ve všech runtime ramenech0. Fáze generation je identifikátor pozorované fáze, nikoli detail každého interního zápisu. Off ukazatel nesleduje, jeho nulové čítače nejsou důkazem absence špatných odhadů nebo původních resetů. Kompletní phase counts a prvních nejvýše128 bad samples jsou v auditních TOML.

| Správce / rameno | Row residual volání | Direction guard | Full finite | Události | Původní certificate true/calls |
|---|---:|---:|---:|---:|---:|
| huangfu_hall-production / off | 87092 | 76061 | 76754 | 250947 | 1/1 |
| huangfu_hall-production / passive | 87092 | 76061 | 76754 | 250947 | 1/1 |
| huangfu_hall-production / active | 100126 | 84624 | 86385 | 285680 | 2/2 |
| forrest_tomlin-production / off | 84652 | 75279 | 76136 | 245135 | 1/1 |
| forrest_tomlin-production / passive | 84652 | 75279 | 76136 | 245135 | 1/1 |
| forrest_tomlin-production / active | 99195 | 85324 | 87605 | 284205 | 1/1 |

Původní safeguards, tolerance, precision, refaktorizace160 a vstup zůstaly. Uložená Devex váha se porovnává s max(1, stávající reference-frame sum), nikoli s plnou DSE normou. Plošná kvalita všech vah není měřena. Reset až po dokončeném běžném pivotu; staged/retry/refactor/phase invalidace a plný finite guard zůstaly.

## Práce, alokace a paměť

Žádný dodatečný dimension-dependent sken, převod, kopie velkých polí nebo basis solve pro obyčejné pozorování. Hodnota weak-key stavu obsahuje jen skaláry (sizeof56B); ve full výsledcích passive/active jedna metadata položka, off žádná. To není celá velikost slovníku ani měření retained memory. Auditní kopie, streamy a vzorky nejsou v benchmarku. Statická kontrola nenašla nepotřebnou další práci nebo retenční numerická pole; nezbytná práce resetu je však drahá v součtu se změněnou trajektorií.

HH active přibližně 110,61 milionu alokací proti 62,87 milionu off; FT 218,54 milionu proti 191,01 milionu. Tento růst nelze připsat samotnému scalar state ani z něj izolovat cenu obnov. Passive má téměř stejné allocation counts jako off. Bytes jsou kumulované alokované bajty, nikoli živá paměť. Peak RSS zahrnuje warmup i následné kontroly. Kompilace je zahrnuta v celém solve a neodečtena; audity nejsou benchmark.

| Správce / pricing / rameno / repeat | Solve s | Smyčka s | GC s | Compile ms | Alokace | Bytes | Peak RSS MiB |
|---|---:|---:|---:|---:|---:|---:|---:|
| huangfu_hall-production / runtime / off.1 | 228.229239 | 228.107343 | 4.719148 | 0.000000 | 62866992 | 24029171592 | 2439.625 |
| huangfu_hall-production / runtime / passive.1 | 228.015546 | 227.893364 | 4.538279 | 0.000000 | 62867000 | 24029140088 | 2337.656 |
| huangfu_hall-production / runtime / active.1 | 265.423319 | 265.172623 | 5.495352 | 25.464300 | 110613392 | 29350722672 | 2397.254 |
| forrest_tomlin-production / runtime / off.1 | 407.804813 | 407.606367 | 7.964299 | 19.308700 | 191007984 | 34809702256 | 2608.887 |
| forrest_tomlin-production / runtime / passive.1 | 398.986772 | 398.780277 | 7.874578 | 18.518500 | 191007998 | 34809753760 | 2492.309 |
| forrest_tomlin-production / runtime / active.1 | 465.303512 | 465.183505 | 8.750312 | 21.464500 | 218537412 | 39677335648 | 2441.781 |
| forrest_tomlin-production / runtime / active.2 | 465.377857 | 465.264585 | 8.717055 | 19.096200 | 218537410 | 39677361568 | 2494.148 |
| forrest_tomlin-production / runtime / passive.2 | 401.078814 | 400.880032 | 8.371269 | 21.134500 | 191007994 | 34809552864 | 2394.023 |
| forrest_tomlin-production / runtime / off.2 | 398.967385 | 398.762866 | 8.050355 | 20.465500 | 191007982 | 34809737232 | 2507.594 |
| huangfu_hall-production / runtime / active.2 | 264.924974 | 264.519510 | 5.591509 | 26.057002 | 110613398 | 29350642848 | 2394.332 |
| huangfu_hall-production / runtime / passive.2 | 226.874005 | 226.710519 | 4.387001 | 0.000000 | 62867000 | 24029100536 | 2396.902 |
| huangfu_hall-production / runtime / off.2 | 228.237391 | 228.123176 | 4.519657 | 0.000000 | 62866992 | 24029156360 | 2340.621 |

Omezení: jeden model, dvě opakování, pouze produkční HH/FT a fixed Devex/legacy/Float64. Bez garance pro ostatní správce nebo vstupy. Přínos obnovy se nepotvrdil a do produkce nic integrováno nebylo. Další automatické prohledávání prahů ani nové solve nejsou součástí tohoto závěru.

[Strojové ověření](final-verification.json) · [Páry CSV](pairs.csv) · [Pokrytí CSV](coverage.csv)
