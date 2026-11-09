# Kontrola kvality Devex vah mezi refaktorizacemi

Uživatelem požadovaný izolovaný experiment na runtime.mps, první rozsah produkční Huangfu–Hall a Forrest–Tomlin. Produkční kód se nemění. Nové numerické procesy smějí začít teprve po dokončení legacy-pricing-check-reuse, se společnými zámky. Pravidla a přijetí výsledků obsahuje PLAN.md.

Ukazatel porovnává uloženou Devex váhu vybraného řádku s max(1, součtem čtverců prvků aktuálního tableau řádku omezeným na devex_reference). Tento součet už počítá původní update_devex!, kandidát ho získá bez nového průchodu nebo basis solve. Nejde o normu DSE ani certifikát přesnosti váhy. Sledujeme jen vybraný řádek.

Tři ramena: off (původní), passive (ukazatel bez změny vah), active (obnova rámce po dokončeném běžném pivotu při poměru >9). Práh je experimentální, inspirovaný poměrem čtvercových vah v HiGHS newDevexFramework, nikoli nové numerické kritérium přijatelnosti pivotu. Původní safeguards, tolerance, arithmetic a interval refaktorizace160 zůstávají. Referenční rámec se neobnovuje na spekulativním/staged pivotu, při neplatných hodnotách, přes refaktorizaci nebo při nepodporovaném stop callbacku.

Sledování používá WeakKeyDict se skalárními metadaty; hodnoty nedrží workspace ani velká pole. Jeho režie je v passive/active časovaných bězích. Reset zapisuje existující O(m+n) reference/weights a provede plnou původní kontrolu; není zdarma. V auditu se ukazatel přepočítává samostatným průchodem. Čas auditu není benchmark.

Žádný automatic retry zahájeného procesu. Numerický neúspěch zachovat a vynechat další běhy stejné kombinace správce/rameno; off neúspěch vyřadí správce. Výjimka, drift passive/off nebo OPTIMAL bez původní feasibility/certifikace zastaví. Benchmarky se porovnávají proti vlastnímu auditu stejného ramene. Active smí změnit trajektorii, objektivní rozdíl se vykáže bez nové akceptační tolerance. Dvě opakování s obráceným pořadím; kompilaci vykázat a neodečítat. Peak RSS zahrnuje warmup a následné kontroly.

Inspirace pro práh: [HiGHS HEkkDual::newDevexFramework](https://github.com/ERGO-Code/HiGHS/blob/master/highs/simplex/HEkkDual.cpp), poměr čtvercových vah >3². Z tohoto postupu nepřebíráme věkový limit rámce; původní interval refaktorizace zůstává160.

Spuštění: `python3 diagnostics/devex-quality-reset/reproduce/run.py`. Původní launcher je jednorázový: existující piny a started markers zakazují tiché opakování. Po dokončení `python3 diagnostics/devex-quality-reset/reproduce/summarize.py`, nezávislé ověření a český výklad výsledků. Příprava zatím není výsledkem numerické validace.
