# Přebírání kontrol u přímých správců báze na runtime.mps

Každý převzatý výsledek Suhl–Suhl a Bartels–Golub se v samostatném auditu shodoval s výpočtem původní kontroly. Pořadí sledovaných pivotů, výsledky kontrol a vzorky stavu měly v obou ramenech shodný otisk. U přímého FT bylo totéž ověřeno v předchozí sérii. Časový dopad na celý duální průchod závisí na správci, režimu a konkrétní dvojici běhů.

| Správce a režim | 1. pár, reference → převzetí (s) | Δ | 2. pár, reference → převzetí (s) | Δ | Δ poměru průměrných časů |
|---|---:|---:|---:|---:|---:|
| SS přímý | 555,62 → 513,70 | -7,55 % | 479,64 → 527,36 | +9,95 % | +0,56 % |
| SS normalizovaný | 520,83 → 516,63 | -0,81 % | 534,22 → 479,89 | -10,17 % | -5,55 % |
| BG přímý | 505,39 → 471,72 | -6,66 % | 577,90 → 595,12 | +2,98 % | -1,52 % |
| BG normalizovaný | 521,03 → 555,32 | +6,58 % | 563,00 → 562,42 | -0,10 % | +3,11 % |

Ve druhém páru se obrátilo pořadí všech správců, režimů i ramen. U každého řešení se měřil součet celých vnějších volání duální smyčky včetně přestaveb a obnovy. Celý solve, GC, alokované bajty a obě párové změny jsou zvlášť v [tabulce měření](comparison.csv). Dvě opakování na jednom modelu nestačí k odhadu stabilního zrychlení. Rozdíl mezi referencemi dosahoval u přímého BG 14,35 %. Počítač během části měření měnil stav napájení. [Systémové události a rozptyl referencí](run-environment.md).

| Režim | Duální kroky / všechny iterace | Konstrukce + refaktorizace | Převzatá / všechna původní rezidua BTRAN | Skalární kontrola primálu | Převzetí po pivotu / při vstupu | Ušetřené / původní úplné kontroly konečnosti | Zachované kontroly FTRAN |
|---|---:|---:|---:|---:|---:|---:|---:|
| SS přímý | 77025 / 77025 | 1 + 495 | 4781 / 86662 | 76531 | 76531 / 76318 | 229380 / 307403 | 77064 |
| SS normalizovaný | 76922 / 76922 | 1 + 489 | 7546 / 92094 | 76434 | 76434 / 76164 | 229032 / 306941 | 76965 |
| BG přímý | 75995 / 75998 | 1 + 488 | 5244 / 86577 | 75508 | 75508 / 75287 | 226303 / 303288 | 76032 |
| BG normalizovaný | 75290 / 75290 | 1 + 514 | 6762 / 89060 | 74777 | 74777 / 74532 | 224086 / 300412 | 75414 |

Samostatný kandidátní audit přepočítal každé převzaté řádkové reziduum a porovnal je bitově. Každé převzetí konečnosti ověřil původním úplným průchodem. Dříve sdílené kontroly vstupu přes hodinový callback jsou přepočtené v obou auditech a odečtené z počtu původních úplných průchodů. Skutečný backend byl ověřen při konstrukci a po každém zveřejnění refaktorizace. V obou normalizovaných variantách měla diagonála U při každém zveřejnění samé jedničky a škály byly konečné a nenulové. Všechny časované běhy skončily OPTIMAL s původně přípustným primálem a shodnými bity cíle, SHA celého primálu, počty kroků a refaktorizací vůči vlastnímu auditu. Zachycené stavy a události pocházejí z auditů. [Historie režimů](factor-modes.csv) · [Ověření experimentu](final-verification.json).

## Podmínky a přerušení

ARM64, jedno vlákno Julie i BLAS, dual/Devex/legacy, Float64, nativní refaktorizace s intervalem 160, bez presolve, původní tolerance 10⁻⁷. Zahřátí zahrnovalo celé afiro a 100 iterací runtime mimo měření. V každém časovaném procesu byla stejná O(1) kontrola skutečné reprezentace při publikaci. Přepočty kontrol a průchod diagonálou U probíhaly jen v auditech. Srovnání vůči staršímu běhu téhož správce zahrnovalo bity cíle, vstup, přípustnost, počty iterací, refaktorizací a režim. SHA celého primálu a sledované mezistavy porovnáváme s novou vlastní referencí.

Po třinácti hotových časovaných bězích skončil proces druhé normalizované reference SS bez výsledného času a bez numerického hlášení. Bylo ověřeno uvolnění všech 30 zámků a zachováno 25 hotových úloh včetně auditů a jednotkových testů. Se souhlasem uživatele byl jednou zopakován jediný přerušený pokus. Druhý normalizovaný pár SS má kandidáta před přerušením a referenci po něm. Oba běhy druhého přímého páru SS proběhly po obnovení. Srovnatelnost těchto časů je dále omezená. [Doklady přerušení](environment-interruption.json) · [Schválená obnova](authorized-resume-20261107/authorization.json).

## Práce a paměť

Integrované rozhodnutí na místě původního typového testu nahlédne do právě zveřejněného backendu. Čte pouze příznak požadavku, přítomnost škálovací diagonály a fallbacku. Nepotřebuje přidat průchod vektorem, další řešení s bází, kopii ani pole držené mezi iteracemi. Ochrany aliasingu, politiky, callbacků, diagnostiky a přestaveb dál rozhodují ve společné smyčce. Původní rezidua FTRAN se vyhodnotila ve všech režimech. Měřený počet bajtů je kumulativní za celý solve. Počet alokací ani špičkovou či trvale drženou paměť tato série neměřila.

Kompilace během šestnácti časovaných solve byla v intervalu 0 až 0 s. Nenulových hodnot bylo 0. Diagnostická kompilace v auditech je vykázána samostatně v JSON.

## Integrované chování

Sdílená duální smyčka používá stejnou podmínku pro pět dříve ověřených produkčních správců. Při explicitním nahrání přímých správců dostanou oprávnění jen konkrétní přímé faktory FT, SS a BG, jejichž aktuální reprezentace odpovídá požadovanému režimu. Při přechodu na obyčejné LU nebo při neuskutečněné normalizaci se použijí plné původní kontroly. Výchozí volba správce v balíčku se nemění. Uživatel výslovně zvolil zapnutí i tam, kde se numerika potvrdila a časy byly smíšené.

[Integrační test publikace, ztráty a obnovení režimu](../../basis-direct-lu/reproduce/check-reuse.jl) · [Dřívější měření FT](../../direct-ft-local-check-reuse/results/interpretation.md).

Po integraci proběhlo šest dalších úplných auditů runtime.mps, tentokrát s metodou způsobilosti přímo z integrovaného kódu. Všech šest dosáhlo OPTIMAL a původní primální přípustnosti. Pro každý režim přesně souhlasil konečný primál a cíl, hash událostí a kontrol, počty všech převzetí a úplný seznam zveřejněných faktorů s příslušným dříve změřeným kandidátem. Samostatné regresní testy přímých správců prošly 45/45 v obou režimech, dalších 82/82 kontrol prošlo u pěti produkčních správců. [Ověření integrovaných běhů](integration/verification.json).

Nezávislá revize nenašla zbytečné průchody, řešení s bází, alokované buffery ani růst držené paměti. Opravila se testovací konfigurace, která při testu mutujícího callbacku nastavila přestavbu po každém kroku a přepočítala tím váhy ještě před kontrolou. Upravená regrese proti původní verzi selhala pouze na devíti očekávaných kontrolách způsobilosti. Jeden start integračního testu se zablokoval na zámku předkompilace před spuštěním testů. Všechny dokončené testy použily existující kompilované moduly, stejně jako benchmarky. Celá testovací sada projektu nebyla spuštěna.

Párový experiment předcházel integraci a používal společnou smyčku z revize `00068f59` a připnutý historický zdroj přímých faktorů. Pro opakování původních měření je třeba vycházet z uvedené revize. Integrační audity načítají aktuální udržovanou implementaci přímých faktorů. Výstupní složky a značky zahájených úloh chrání před automatickým opakováním.
