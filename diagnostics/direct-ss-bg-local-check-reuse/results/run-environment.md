# Kolísání doby reference na runtime.mps

Všechny časy událostí níže jsou v UTC. Pražský místní čas byl o hodinu napřed. Oba páry měří stejný vstup a numerická nastavení, s jedním vláknem Julie i BLAS. Všechny výpočty této série běžely za výlučnými zámky. Windows ani ostatní aplikace tyto zámky nepoužívají.

| Reference | Smyčka 1 → 2 (s) | Rozdíl (s) | GC celého solve 1 → 2 (s) | Iterace / refaktorizace v obou |
|---|---:|---:|---:|---:|
| SS přímý | 555,62 → 479,64 | -75,99 (-13,68 %) | 19,24 → 16,02 | 77025 / 495 |
| SS normalizovaný | 520,83 → 534,22 | 13,39 (2,57 %) | 19,52 → 20,30 | 76922 / 489 |
| BG přímý | 505,39 → 577,90 | +72,51 (+14,35 %) | 15,73 → 18,12 | 75 998 / 488 |
| BG normalizovaný | 521,03 → 563,00 | +41,96 (+8,05 %) | 19,86 → 22,53 | 75 290 / 514 |

Kompilace uvnitř všech osmi referenčních solve byla nulová, konečný cíl i celý primál se v rámci režimu přesně shodovaly. U BG připadá na rozdíl GC celého solve 2,39 s v přímém a 2,67 s v normalizovaném režimu. V přímém režimu BG dokonce stejný kandidát trval 471,72 a 595,12 s (+26,16 %). Časový rozptyl mezi dvěma běhy téhož kódu převyšuje v tomto případě naměřené párové změny při zapnutí přebírání.

## Co zaznamenal počítač

| Událost Windows | UTC 6. 11. | Překryv s procesem měření |
|---|---|---|
| Kernel-Power 506 → 507, Modern Standby, Idle Timeout → klávesnice | 22:34:03–22:35:16 | Posledních 11 s procesu první přímé reference BG a začátek procesu prvního přímého kandidáta BG |
| Kernel-Power 506 → 507, Modern Standby, Idle Timeout → myš | 22:40:16–22:48:08 | První přímý kandidát BG a první normalizovaná reference BG |

Časové hranice procesů zahrnují start Julie, warmup i vlastní měření. Vstup do Modern Standby neurčuje dobu, po kterou fyzický CPU přestal vykonávat Julii. Ze záznamu tedy nelze odečíst dobu mezi těmito událostmi. První reference normalizovaného BG byla přes tento překryv rychlejší. V pozorovaném okně nebyly v dotázaných protokolech nalezeny události začátku či konce skenu Defenderu nebo vybraných aktivit Windows Update. WSL zaznamenalo krátké úlohy apt a zálohy dpkg, obě skončily v sekundě spuštění. Dva přechody schématu napájení od ovladače Qualcomm jsou doložené až 7. 11. v 00:01:34 a 00:01:36 UTC, v časovém okně přerušené druhé reference SS. Z událostí nelze určit příčinu ukončení procesu.

Jednorázový dotaz 7. 11. přibližně v 00:03 UTC ukázal na Windows 5 % vytížení 18 logických procesorů. Systémové čítače uváděly mimo jiné SRFeature (41 % jednoho jádra) a dwm (25 % jednoho jádra). Tento pohled byl pořízen několik hodin po prvních referencích a v období, kdy už měřicí proces mohl být ukončen. V původních bězích se průběžně nezaznamenával procesorový čas Julie, čekání na přidělení CPU, frekvence konkrétního jádra, teplota ani zatížení všech procesů Windows. Chybí proto důkaz pro přiřazení konkrétní části rozdílu aplikaci, přechodu napájení, přidělení jádra nebo snížení frekvence.

Po obnovení se u tří zbývajících procesů zvenku každých deset sekund vzorkuje procesorový čas, poslední virtuální jádro, page faults a linuxové plánovací čítače hlavního vlákna. Takové vzorky nemohou zpětně objasnit starší běhy ani určit takt fyzického jádra na hostiteli.

## Dokončená měření po obnovení

Vzorky uvnitř měřené části jsou zvolené konzervativně podle času ukončení procesu a délky solve. Na každém konci přibližného měřeného intervalu se zahazuje nejméně 10 s. Virtuální CPU ve WSL nelze ztotožnit s konkrétním fyzickým jádrem.

| Běh SS, druhý pár | Pozorovaný interval (s) | Procesorový čas procesu / reálný | Evidované čekání hlavního vlákna na CPU (s) | Vzorkovaná vCPU | Velké výpadky stránek |
|---|---:|---:|---:|---|---:|
| direct, candidate.2 | 500.0 | 99.88% | 0.547 | 1, 2, 3, 10, 16 | 0 |
| direct, reference.2 | 450.0 | 99.85% | 0.628 | 1, 2, 4, 10, 16 | 0 |
| normalized, reference.2 | 500.0 | 99.85% | 0.711 | 1, 2, 9, 11, 14, 17 | 0 |

U obnovených běhů proces využíval téměř jedno celé virtuální jádro. Tento záznam omezuje vysvětlení dlouhým čekáním na linuxový plánovač uvnitř těchto konkrétních intervalů. Rozdíl ve skutečném výkonu vCPU, paměťového systému nebo plánování hypervizoru tím oddělit nelze.
