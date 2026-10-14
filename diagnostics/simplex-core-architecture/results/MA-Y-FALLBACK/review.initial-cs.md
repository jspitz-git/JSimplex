# Nezávislé review MA-Y-FALLBACK

Analýza je přijata jako rozbor uložených dat a zdrojových textů. MA-Y zůstává
NOT ACCEPTED. Nebyl nalezen kritický, významný ani drobný věcný nález vyžadující
opravu. Toto review neschvaluje kandidáta ani nové měření.

Nový review-check.py byl uložen před jediným spuštěním. Jeho 29 kontrol prošlo;
review-check.json zachycuje 622 SHA-256 vazeb. Nebyl spuštěn či importován žádný
původní skript, autorův analyze.py nebyl opakován a nebyla použita Julia, nový
profiler, disassembler ani numerický experiment. Zdrojové a nativní soubory byly
pouze čteny, nativní knihovna pouze hashována.

- Nezávislá aritmetika ověřila všech 480 kontrolních párů, z nich 336 měřených,
  48 souhrnů proces/případ a přesné pořadí i obsah všech 2 080 uložených journal
  záznamů v každém ze tří procesů. Žádný vzorek ani GC nebyl vyřazen. Výstupy,
  zachování vstupů/vlastníků, pořadí ramen, čtyři volání na okno a nulová měřená
  kompilace souhlasí. Mediány obou ramen, párové statistiky, pořadí hodnot a
  původní auditor mají stejné výsledky pro všech 16 kontrol v každém procesu.
- Bylo znovu ověřeno všech 36 readtime hashů, včetně 13 původních launch pinů,
  514 zdrojových identit, šest chráněných souborů, 74 starých publikačních hashů
  a šest vazeb na zachované beforecopies. Přesná nativní knihovna i všechny tři
  staré S4-O assembly texty souhlasí s uloženou identitou. Readtime hash není
  vydáván za historický launch pin.
- Obě kompletní tabulky sedmi neúspěšných párů souhlasí s raw daty. BigFloat
  BTRAN proces3 má časové mediány 299,575 a 351,150 us/volání: rozdíl 51,575 us
  překračuje původní mez 29,9575 us. Mediány pocházejí z různých párů; medián
  párových poměrů 1,007321966 nenahrazuje předepsaný predikát. Všech 42 scoped
  BigFloat párů má nulový rozdíl bajtů i událostí.
- Rational FTRAN proces3 má mediány 3 247 376 a 3 247 408 bajtů/okno, tedy +32;
  medián párových rozdílů je +48. Všech sedm párů má 74 525 událostí na obou
  stranách. Ze všech 42 Rational párů má 20 kladný, 18 záporný a čtyři nulový
  rozdíl bajtů; rozdíly událostí jsou vždy nulové. Všech 21 FTRAN párů má nulový
  zaznamenaný GC. Všech 41 Rational párů bez zaznamenaného GC pokrývá -560 až
  +416 bajtů; tato popisná kontrola není filtrované rozhodnutí o přijetí.

Textová kontrola MA-U candidate.jl potvrzuje, že Rational skončí na prvním
BigFloat typovém testu. Scoped BigFloat projde typovými a rozměrovými testy,
provede lookup aktuálního scope a kvůli nesouladu zaokrouhlování přejde do
reference. Obě větve se vracejí před BigFloat pracovním objektem a MA smyčkami.
MA-R reference.jl volá původní ldiv!. Driver vytváří dvě samostatné deepcopy
kopie a resetuje destination mimo časované okno; serializace, kontroly vlastníků
a flush journalu probíhají rovněž mimo okno a mohou ovlivnit pozdější stav.

Zdroj timing.jl rozlišuje agregované bajty a události. gmp.jl vytváří čerstvé
BigInt vlastníky a pokouší se instalovat counted callbacky v try/catch. Uložené
nativní instrukce potvrzují použití malloc_usable_size a oddělené účtování
realloc události od nezáporného rozdílu nové usable size a předané old size.
Tento mechanismus umožňuje stejné počty událostí při různých bajtech; neprokazuje
historický stav callbacků, konkrétní požadavek, size class ani příčinu +32 bajtů.

Aktuální zpráva výslovně připouští, že proměnlivé celkové časy neizolují případnou
pevnou složku režie guardu. Nepřisuzuje změny scheduleru, frekvenci CPU, cache,
GC nebo alokátoru bez důkazu. Nebyl nalezen zbývající kauzální nadvýklad. Fyzická
příčina jednotlivých časů a native alokací zůstává nevyřešená a jako taková je
správně označena. Původní nulová bajtová tolerance, časové meze i zamítnutí
zůstávají zachovány; pooled acceptance nebyla počítána a aggregate.json neexistuje.

Review výpočetní práce a paměti podle AGENTS.md: nebyla nalezena nová zbytečná
produkční práce ani paměťová režie. git diff HEAD byl prázdný a zdrojové hashové
identity souhlasily. Jde výhradně o nový offline rozbor a dokumentaci. Stávající
fallback guard běží při každém volání; přidává typové/rozměrové podmínky a u
scoped BigFloat jeden lookup závislý na scope mapě, nikoli nový průchod faktorem,
basis solve, kopii či konverzi. Nezavádí solver cache ani zadržené native objekty.
U Rational nedochází ani k rozměrovým testům či lookupu. Není doložen materiální
časový náklad guardu. Offline skripty drží konečné množství raw/journal dat a
skalárních souhrnů; nejde o změnu solver hot path. Nový benchmark není pro tento
rozbor nutný a byl výslovně zakázán. Beze změn zůstávají numerické safeguards,
přesnosti a vlastnické předpoklady.

Odložené posouzení: následná změna živého STATUS/roadmap a finální publikace
nejsou součástí tohoto review; původní obsah je ověřen přes beforecopies/map.
Kauzální experimenty nebyly provedeny, protože tento úkol je výslovně omezen na
uložené důkazy. Žádná další zvažovaná vlastnost nebyla tiše vyřazena z posouzení.
