# Invarianty pricingů a náklady izolovaného kandidáta

Základ ca265583. Kandidát mění pouze dvě podmínky v `_can_reuse_dual_checks`, společné numerické výrazy zůstávají přesně původní. Nejde o produkční integraci.

- Pevný Dantzig: původní `_finite_workspace` kontroluje primal, reduced_costs a costs, ale podle skutečného pricingu nevyžaduje pozitivní pricing_weights. Kandidát zachovává tento původní predikát a opakovaný výsledek přebírá jen v existujících nemutujících úsecích.
- Pevné DSE: po `update_dse!` zůstává plná kontrola. Její původní úspěšná větev již sdílí výsledek s koncem `update_dual_pricing_weights!`; audit znovu ověřuje i toto starší sdílení v obou ramenech.
- Neplatné DSE váhy: přechod na Devex nejprve přestaví váhy, následuje plná kontrola, potom Devex aktualizace pro dosud nenahrazený pivot a opět plná kontrola. Žádná z těchto kontrol se neodstraňuje.
- Přechod při nespolehlivé DSE váze: autorita je odvozena od skutečného aktuálního pricingu, nikoli jen od původní volby. DSE→Devex je způsobilý, DSE→Dantzig nikoli. Auto a nepodporované režimy zůstávají mimo rozšíření.
- Publikace faktoru nemění sledovaná numerická pole v podporovaných správcích; jediný následně změněný primal je kontrolován skalárně. Po refaktorizaci se použije původní plná kontrola. BTRAN korekce může převzít již přijaté reziduum jen při původních podmínkách nealiasování.

Frekvence: podmínka způsobilosti se vyhodnocuje na existujících místech v iteraci a při přijaté BTRAN korekci. Přidaná práce je konstantní: ověření pevně zvoleného pricingu, původní dotaz na skutečný pricing a porovnání symbolů. Nejsou přidány nové skeny vektorů/matic, basis solves, konverze, kopie nebo trvalé buffery. Kandidát může vynechat opakované O(m+n) kontroly a opakovaný reziduální výpočet; kolik takových případů skutečně nastalo, ukáží teprve runtime audity. Z menšího počtu kontrol samotného nelze vyvodit rychlost.

Audity přidávají plné přepočty, záznamy a vzorky stavu; jejich čas není výkonový benchmark. Plain měření mají symetrické čítače publikace faktoru a časovač celé duální smyčky. Původní aritmetika DSE, včetně dodatečného váhového FTRAN, zůstává v obou ramenech. DSE a Dantzig mohou mít odlišné trajektorie; jejich přímé vzájemné časy nejsou izolovaným měřením této optimalizace.
