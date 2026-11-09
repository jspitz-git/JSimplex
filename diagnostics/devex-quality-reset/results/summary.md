# Kontrola Devex vah a obnova rámce

Stav: dokončeno.

| Správce | Rameno | Δ solve opakování1 | Δ solve opakování2 | Δ poměr průměrů solve | Δ poměr průměrů smyčky |
|---|---|---:|---:|---:|---:|
| huangfu_hall-production | passive | -0.09% | -0.60% | -0.35% | -0.36% |
| huangfu_hall-production | active | +16.30% | +16.07% | +16.19% | +16.10% |
| forrest_tomlin-production | passive | -2.16% | +0.53% | -0.83% | -0.83% |
| forrest_tomlin-production | active | +14.10% | +16.65% | +15.36% | +15.39% |

Záporná změna znamená kratší čas. Jen úplné optimální čtveřice ověřené proti vlastnímu auditu. Dvě opakování omezují průkaznost malých změn. Kompilace je zahrnutá, neodečítá se.

Passive/off musí mít totožné původní události, guardy, vzorky i endpoint. Active může změnit trajektorii; nižší počet iterací není kernel speedup. Původní feasibility i skutečná původní optimality certificate jsou samostatné podmínky přijetí.

Off nesbírá ukazatel kvality: nuly jeho čítačů neznamenají nulu původních obnov rámce. Ukazatel sleduje pouze vybraný řádek a není certifikátem všech Devex vah. Práh9 je experimentální. Runtime audit přepočítává ukazatel, jeho čas není benchmark. Weak-key metadata neudržují workspace silnou referencí. Velikost stavu nezahrnuje obal slovníku; peak RSS zahrnuje warmup a následné kontroly, není retained memory.

[Všechny časy a prostředky](summary.csv) · [Párové změny](pairs.csv) · [Pokrytí a změna trajektorie](coverage.csv) · [Vynechané](skipped.json)
