# Pevný Dantzig a DSE v legacy duální smyčce

Izolované rozšíření způsobilosti již integrovaného přebírání kontrol. Rozsah schválený uživatelem 7. 11. 2026 zahrnuje všech pět produkčních správců a šest přímých variant. Podrobný protokol je v PLAN.md.

Kandidát rozšiřuje dvě pricingové podmínky. Pevný DSE smí přebírat kontrolu také po skutečném přechodu na Devex. Původní kontrola po změně vah, po opravě vah a po následné Devex aktualizaci se zachovává. Pevný Dantzig zachovává svůj původní predikát konečnosti bez požadavku na kladné váhy. Auto pricing, DSE s Dantzig fallbackem a nepovolené callbacky/aliasing používají plné původní kontroly. Produkční kód v src se v tomto pokusu neupravuje.

Kopii balíčku obsahuje snapshot, původ je doložen results/source-provenance.json. reproduce/common.jl instaluje symetrické časovače a kontrolu typu/reprezentace faktoru při všech třech publikacích refaktorizace včetně rollbacku a postsolve. Zbylé numerické výrazy přebírá z vlastního snapshotu. Očekávané dvě chyby unit-red.log dokazují, že základní verze nové pricingy nepovoluje. Rozšířené cílené testy ověřují skutečně použitou BTRAN korekci, všechny chráněné aliasy, mutující callback i oba důvody přechodu DSE→Devex v každém správci. Malé reference/kandidát solves afiro/sc50a porovnávají přesný primál, cíl, přípustnost a počty.

Audity přepočítávají každý převzatý guard včetně dříve společně přebírané kontroly DSE vah a vstupu přes hodinový callback. Počty etapovaných událostí jsou oddělené. Počet dokončených duálních pivotů pochází z následné kontroly živého stavu. Přechody během etapovaných pokusů mohou být zahozené a jsou ve výkladu oddělené od přechodů živého workspace. Audit ukládá pole pricing_counts a switches, včetně důvodu, fáze a příznaku etapovaného pokusu. Výsledky auditu se porovnávají s vlastním referenčním auditem, jednotlivé pricingy mohou zvolit odlišné trajektorie.

Runner drží celou řadu existujících suite locks a předává je potomkům. Každý job má samostatný proces, trvalou značku zahájení a report návratového kódu. Heartbeat a vzorky využití CPU vznikají každých deset sekund, bez časového omezení řešení. Výsledný stav po neoptimálním solve se uloží a zbytek kombinace se vynechá bez opakování. Výjimka či numerický drift zastaví frontu. Běh nelze znovu spustit do stejného adresáře automaticky.

Spuštění nové, prázdné série:
```sh
PYTHONDONTWRITEBYTECODE=1 python3 diagnostics/legacy-pricing-check-reuse/reproduce/run.py
```
Ověření dosud uložených výsledků nebo dokončené série:
```sh
PYTHONDONTWRITEBYTECODE=1 python3 diagnostics/legacy-pricing-check-reuse/reproduce/summarize.py
```
Shrnutí zahrne pouze kompletní čtveřice reportů s procesním reportem a ověřeným comparison. Chybějící nebo neoptimální běh zůstane ve výkazu bez průměrného zrychlení.
