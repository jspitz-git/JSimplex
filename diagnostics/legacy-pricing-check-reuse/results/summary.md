# Přebírání kontrol při pevném Dantzigu a DSE

Stav plánu: dokončený.

| Správce | Pricing | První pár Δ | Obrácený pár Δ | Poměr průměrů Δ |
|---|---|---:|---:|---:|
| huangfu_hall-production | dantzig | -6.47 % | -6.35 % | -6.41 % |
| huangfu_hall-production | steepest_edge | -6.67 % | -6.81 % | -6.74 % |
| forrest_tomlin-production | dantzig | -4.77 % | -4.18 % | -4.47 % |
| forrest_tomlin-production | steepest_edge | -4.38 % | -4.12 % | -4.25 % |
| suhl_suhl-production | dantzig | -5.53 % | -3.30 % | -4.42 % |
| suhl_suhl-production | steepest_edge | -4.38 % | -5.05 % | -4.71 % |
| bartels_golub-production | dantzig | -4.32 % | -3.62 % | -3.97 % |
| bartels_golub-production | steepest_edge | -3.25 % | -3.01 % | -3.13 % |
| pfi-production | dantzig | -4.21 % | -4.69 % | -4.45 % |
| pfi-production | steepest_edge | -5.53 % | -3.63 % | -4.58 % |
| forrest_tomlin-direct | dantzig | -4.31 % | +1.97 % | -1.11 % |
| forrest_tomlin-direct | steepest_edge | -3.54 % | -3.98 % | -3.77 % |
| forrest_tomlin-normalized | dantzig | +4.08 % | -5.34 % | -0.78 % |
| forrest_tomlin-normalized | steepest_edge | -4.35 % | -2.43 % | -3.45 % |
| suhl_suhl-direct | dantzig | -4.06 % | +3.00 % | -0.66 % |
| suhl_suhl-direct | steepest_edge | -6.88 % | -8.26 % | -7.57 % |
| suhl_suhl-normalized | dantzig | -4.27 % | -6.32 % | -5.29 % |
| suhl_suhl-normalized | steepest_edge | -15.96 % | +0.77 % | -7.76 % |
| bartels_golub-direct | dantzig | -1.04 % | -7.99 % | -4.44 % |
| bartels_golub-direct | steepest_edge | -0.12 % | -1.68 % | -0.85 % |
| bartels_golub-normalized | dantzig | -12.52 % | -4.93 % | -8.87 % |
| bartels_golub-normalized | steepest_edge | -6.85 % | -3.10 % | -4.99 % |

Kladná změna znamená delší duální smyčku. Průměry zahrnují jen úplné čtveřice optimálních, původně přípustných a přesně ověřených reportů. Kompilace se zahrnuje a vykazuje v tabulce. Dvě opakování a změny výkonu hostitele omezují přesnost.

Údaje o skutečném pricingu pocházejí z auditů. Počet completed vychází z post-pivot vstupu na živém workspace. Staged pivot události a cenové přechody se vykazují zvlášť v původních TOML. Absence DSE iterací nebo přechodu omezuje runtime pokrytí dané cesty. Cílené testy vynucují oba důvody DSE→Devex. Převzaté guardy se přepočítávají v auditu, časované běhy ověřují vlastní koncový stav.

[Jednotlivé běhy](summary.csv) · [Párové časy a prostředky](pairs.csv) · [Pokrytí pricingů a převzetí](coverage.csv) · [Vynechané úlohy](skipped.json)
