# Přebírání kontrol pro Dantzig a DSE — závěrečný výklad

Celá schválená série je dokončená: 11 jednotkových procesů, 44 plných auditů a 88 časovaných řešení runtime.mps. Všech 143 procesů skončilo exit0; 132 numerických comparison bylo znovu přepočteno původním summarizerem i nezávislou kontrolou. Všechna řešení jsou OPTIMAL s původní primal feasibility. 90 připnutých souborů, 76 původních zdrojových referencí včetně 71 produkčních souborů a vstupní SHA souhlasí. Žádný retry ani vyřazení.

Jednotkové procesy: 1672 úspěšných assertions celkem. Audity přepočítaly každý převzatý výsledek a zachovaly přesné původní event/guard hashe, počty, numerický endpoint, přechody pricingu a skutečný režim faktoru po refaktorizaci. Časované běhy ověřily endpoint, options/input/mode/factory počty proti vlastnímu auditu; nezaznamenávaly všechny mezistavy.

Všech pět produkčních správců zrychlilo pro oba pricingy v obou opakováních. U přímých režimů je výsledek méně stabilní. Normalizovaný FT s Dantzigem měl +4,08 % a −5,34 %, poměr průměrů −0,78 %: stabilní regresi ani malé zrychlení tento výsledek nedokládá. Přímý FT a přímý SS s Dantzigem také změnily znaménko. Normalizovaný SS s DSE měl −15,96 % a +0,77 %; první velký efekt není reprodukován. Windows jako konkrétní příčina kolísání nebyl prokázán; CPU vzorky nejsou měřením frekvence, teplot ani veškeré konkurence hostitele.

Změna se týká celé duální smyčky včetně recovery, nikoli izolovaného kernelu. Nižší počet iterací zde rychlost nevysvětluje: odpovídající reference a kandidát mají shodnou trajektorii. DSE řádky jsou smíšené DSE→Devex běhy, nikoli čistý DSE po celou dobu.

| Správce / pricing | Ref1 s | Cand1 s | Δ1 % | Ref2 s | Cand2 s | Δ2 % | Δ poměr průměrů % |
|---|---:|---:|---:|---:|---:|---:|---:|
| huangfu_hall-production / dantzig | 1119.933681 | 1047.430621 | -6.474 | 1124.372336 | 1052.960554 | -6.351 | -6.412 |
| huangfu_hall-production / steepest_edge | 234.393560 | 218.769122 | -6.666 | 234.030056 | 218.100948 | -6.806 | -6.736 |
| forrest_tomlin-production / dantzig | 1648.347383 | 1569.794784 | -4.766 | 1652.420049 | 1583.401424 | -4.177 | -4.471 |
| forrest_tomlin-production / steepest_edge | 409.025724 | 391.106794 | -4.381 | 408.531345 | 391.717288 | -4.116 | -4.248 |
| suhl_suhl-production / dantzig | 1469.799424 | 1388.487791 | -5.532 | 1445.264009 | 1397.615589 | -3.297 | -4.424 |
| suhl_suhl-production / steepest_edge | 417.412642 | 399.147238 | -4.376 | 419.338741 | 398.151782 | -5.052 | -4.715 |
| bartels_golub-production / dantzig | 1841.469099 | 1761.997088 | -4.316 | 1842.443786 | 1775.698071 | -3.623 | -3.969 |
| bartels_golub-production / steepest_edge | 564.829058 | 546.454670 | -3.253 | 559.602995 | 542.756505 | -3.010 | -3.132 |
| pfi-production / dantzig | 1332.296485 | 1276.165331 | -4.213 | 1341.834605 | 1278.941205 | -4.687 | -4.451 |
| pfi-production / steepest_edge | 307.731691 | 290.722159 | -5.527 | 308.309675 | 297.129390 | -3.626 | -4.576 |
| forrest_tomlin-direct / dantzig | 1816.095854 | 1737.819375 | -4.310 | 1881.876880 | 1918.950790 | +1.970 | -1.114 |
| forrest_tomlin-direct / steepest_edge | 412.557238 | 397.934986 | -3.544 | 443.656176 | 425.978518 | -3.985 | -3.772 |
| forrest_tomlin-normalized / dantzig | 1838.504289 | 1913.515343 | +4.080 | 1958.663081 | 1854.077495 | -5.340 | -0.779 |
| forrest_tomlin-normalized / steepest_edge | 474.968458 | 454.307551 | -4.350 | 414.810962 | 404.731156 | -2.430 | -3.455 |
| suhl_suhl-direct / dantzig | 1952.504004 | 1873.310069 | -4.056 | 1816.186907 | 1870.685047 | +3.001 | -0.655 |
| suhl_suhl-direct / steepest_edge | 496.980886 | 462.800750 | -6.878 | 500.687075 | 459.317004 | -8.263 | -7.573 |
| suhl_suhl-normalized / dantzig | 1965.263753 | 1881.413702 | -4.267 | 1945.974456 | 1822.964650 | -6.321 | -5.289 |
| suhl_suhl-normalized / steepest_edge | 489.189313 | 411.106710 | -15.962 | 469.719931 | 473.351838 | +0.773 | -7.764 |
| bartels_golub-direct / dantzig | 2177.132521 | 2154.497160 | -1.040 | 2082.323490 | 1916.031091 | -7.986 | -4.435 |
| bartels_golub-direct / steepest_edge | 534.697279 | 534.054339 | -0.120 | 466.967919 | 459.103251 | -1.684 | -0.849 |
| bartels_golub-normalized / dantzig | 1943.969302 | 1700.670084 | -12.516 | 1793.447801 | 1705.077459 | -4.927 | -8.874 |
| bartels_golub-normalized / steepest_edge | 491.868714 | 458.160488 | -6.853 | 483.055949 | 468.096836 | -3.097 | -4.992 |

## Skutečné pokrytí a práce

Ve všech 11 DSE konfiguracích nastal živý přechod na Devex; přímý FT měl dva. Důvody a fáze jsou v původních auditních TOML. Cílené testy navíc vynucují oba důvody přechodu. Počty completed níže jsou dokončené duální pivoty na živém workspace; nemusí se rovnat všem solver iterations včetně dalších fází.

| Správce / pricing | Dantzig pivoty | DSE pivoty | Devex pivoty | Živé DSE→Devex | Převzatý row residual | Převzatá konečnost* | DSE weight reuse |
|---|---:|---:|---:|---:|---:|---:|---:|
| huangfu_hall-production / dantzig | 276498 | 0 | 0 | 0 | 126295 | 824871 | 0 |
| huangfu_hall-production / steepest_edge | 0 | 16978 | 54506 | 1 | 11007 | 212458 | 16978 |
| forrest_tomlin-production / dantzig | 303034 | 0 | 0 | 0 | 111419 | 904115 | 0 |
| forrest_tomlin-production / steepest_edge | 0 | 12394 | 59695 | 1 | 11575 | 214239 | 12394 |
| suhl_suhl-production / dantzig | 270144 | 0 | 0 | 0 | 90282 | 805948 | 0 |
| suhl_suhl-production / steepest_edge | 0 | 21949 | 46935 | 1 | 12587 | 204673 | 21949 |
| bartels_golub-production / dantzig | 285751 | 0 | 0 | 0 | 91926 | 852568 | 0 |
| bartels_golub-production / steepest_edge | 0 | 13081 | 60886 | 1 | 10808 | 219847 | 13081 |
| pfi-production / dantzig | 272818 | 0 | 0 | 0 | 88449 | 813917 | 0 |
| pfi-production / steepest_edge | 0 | 26976 | 42195 | 1 | 12247 | 205543 | 26976 |
| forrest_tomlin-direct / dantzig | 293939 | 0 | 0 | 0 | 102062 | 876963 | 0 |
| forrest_tomlin-direct / steepest_edge | 0 | 11547 | 59326 | 2 | 4275 | 210629 | 11547 |
| forrest_tomlin-normalized / dantzig | 312659 | 0 | 0 | 0 | 120461 | 932818 | 0 |
| forrest_tomlin-normalized / steepest_edge | 0 | 12196 | 58786 | 1 | 6207 | 141046 | 12196 |
| suhl_suhl-direct / dantzig | 261452 | 0 | 0 | 0 | 81816 | 779882 | 0 |
| suhl_suhl-direct / steepest_edge | 0 | 10312 | 60987 | 1 | 4498 | 211874 | 10312 |
| suhl_suhl-normalized / dantzig | 277999 | 0 | 0 | 0 | 105772 | 829302 | 0 |
| suhl_suhl-normalized / steepest_edge | 0 | 20972 | 50202 | 1 | 7503 | 141443 | 20972 |
| bartels_golub-direct / dantzig | 281773 | 0 | 0 | 0 | 93963 | 840541 | 0 |
| bartels_golub-direct / steepest_edge | 0 | 21525 | 44267 | 1 | 4509 | 195472 | 21525 |
| bartels_golub-normalized / dantzig | 277918 | 0 | 0 | 0 | 98536 | 829104 | 0 |
| bartels_golub-normalized / steepest_edge | 0 | 15514 | 55315 | 1 | 7034 | 140701 | 15514 |

*Převzatá konečnost je součet finite_reused/from_last_pivot/driver_entry; audity ji pro ověření přepočítávají. Tyto počty nejsou procenta zrychlení celého solveru.

Kontrola práce a paměti: experiment rozšiřuje pouze způsobilost původního přebírání, nepřidává skeny, basis solves ani velké cache v běžném kroku. Mimo ověřenou způsobilost zůstávají původní kontroly, včetně konečnosti po změnách vah a původních podmínek Dantzigu. Nebyla nalezena nepotřebná dodatečná práce ani retenční paměť kandidátní změny. Měřicí factory kontroly/časovače jsou symetrické; instrumentované auditní kopie a hashování nejsou v benchmarku. Produkční integrace Dantzig/DSE touto sérií nebyla provedena.

## Časy a prostředky všech benchmarků

Warmup celé afiro a 100 iterací runtime je mimo měření. Solve zahrnuje setup, iterace, recovery i cleanup; smyčka zahrnuje vstupy do duální optimalizace. GC a kompilace jsou zahrnuté a neodečtené. Peak RSS zahrnuje warmup a následné kontroly, není retained memory samotné smyčky. Dvě opakování na jediném modelu omezují zobecnění.

| Správce / pricing / rameno / repeat | Solve s | Smyčka s | GC s | Compile ms | Alokace | Bytes | Peak RSS MiB |
|---|---:|---:|---:|---:|---:|---:|---:|
| huangfu_hall-production / dantzig / reference.1 | 1120.040797 | 1119.933681 | 28.339699 | 19.514403 | 1080338610 | 139378489232 | 2577.449 |
| huangfu_hall-production / dantzig / candidate.1 | 1047.531546 | 1047.430621 | 27.950291 | 19.393500 | 1080338610 | 139378960304 | 2576.043 |
| huangfu_hall-production / steepest_edge / reference.1 | 234.518676 | 234.393560 | 5.242770 | 19.049300 | 118046018 | 26139902848 | 2464.578 |
| huangfu_hall-production / steepest_edge / candidate.1 | 218.888722 | 218.769122 | 5.202037 | 19.367500 | 118046016 | 26139774464 | 2329.324 |
| forrest_tomlin-production / dantzig / reference.1 | 1648.453833 | 1648.347383 | 38.420320 | 20.038003 | 1527167947 | 183030279064 | 2776.125 |
| forrest_tomlin-production / dantzig / candidate.1 | 1569.911618 | 1569.794784 | 38.325494 | 20.391702 | 1527167967 | 183031002104 | 2725.762 |
| forrest_tomlin-production / steepest_edge / reference.1 | 409.131002 | 409.025724 | 7.085007 | 18.674200 | 127532717 | 31006981800 | 2412.223 |
| forrest_tomlin-production / steepest_edge / candidate.1 | 391.225648 | 391.106794 | 7.063783 | 19.526500 | 127532719 | 31006900952 | 2399.684 |
| suhl_suhl-production / dantzig / reference.1 | 1469.908238 | 1469.799424 | 31.545681 | 20.278000 | 1075804896 | 146977989136 | 2727.438 |
| suhl_suhl-production / dantzig / candidate.1 | 1388.592320 | 1388.487791 | 31.322670 | 22.604600 | 1075804891 | 146978566704 | 2607.809 |
| suhl_suhl-production / steepest_edge / reference.1 | 417.552675 | 417.412642 | 8.335448 | 23.383500 | 150803572 | 35990296536 | 2426.922 |
| suhl_suhl-production / steepest_edge / candidate.1 | 399.289093 | 399.147238 | 8.685647 | 27.130500 | 150803574 | 35990335016 | 2468.648 |
| bartels_golub-production / dantzig / reference.1 | 1841.590111 | 1841.469099 | 29.155959 | 21.501699 | 810703186 | 140160130896 | 2639.992 |
| bartels_golub-production / dantzig / candidate.1 | 1762.112230 | 1761.997088 | 29.585009 | 21.694100 | 810703183 | 140159576544 | 2583.152 |
| bartels_golub-production / steepest_edge / reference.1 | 565.080976 | 564.829058 | 6.153865 | 18.773001 | 98162752 | 30225765304 | 2394.254 |
| bartels_golub-production / steepest_edge / candidate.1 | 546.720904 | 546.454670 | 6.142973 | 19.625700 | 98162744 | 30225752472 | 2391.859 |
| pfi-production / dantzig / reference.1 | 1332.469260 | 1332.296485 | 15.770209 | 0.000000 | 949192777 | 106880653472 | 2585.703 |
| pfi-production / dantzig / candidate.1 | 1276.336795 | 1276.165331 | 15.694706 | 0.000000 | 949192771 | 106880776768 | 2647.367 |
| pfi-production / steepest_edge / reference.1 | 308.013678 | 307.731691 | 0.980215 | 21.292600 | 22033957 | 15276097120 | 2364.316 |
| pfi-production / steepest_edge / candidate.1 | 290.999428 | 290.722159 | 0.936246 | 22.256597 | 22033956 | 15276075056 | 2334.762 |
| forrest_tomlin-direct / dantzig / reference.1 | 1816.531926 | 1816.095854 | 69.423993 | 0.000000 | 1989831576 | 247988777400 | 2587.859 |
| forrest_tomlin-direct / dantzig / candidate.1 | 1738.249872 | 1737.819375 | 68.165450 | 0.000000 | 1989831578 | 247988779576 | 2539.191 |
| forrest_tomlin-direct / steepest_edge / reference.1 | 413.001760 | 412.557238 | 14.735224 | 26.061698 | 367018871 | 52457710984 | 2449.766 |
| forrest_tomlin-direct / steepest_edge / candidate.1 | 398.368771 | 397.934986 | 14.873994 | 25.222500 | 367018875 | 52457811768 | 2451.781 |
| forrest_tomlin-normalized / dantzig / reference.1 | 1838.649783 | 1838.504289 | 72.367068 | 0.000000 | 1825917997 | 258539818816 | 2593.379 |
| forrest_tomlin-normalized / dantzig / candidate.1 | 1913.694394 | 1913.515343 | 80.022162 | 0.000000 | 1825917993 | 258541270880 | 2598.875 |
| forrest_tomlin-normalized / steepest_edge / reference.1 | 476.291951 | 474.968458 | 19.723229 | 0.000000 | 333137954 | 53287908192 | 2540.246 |
| forrest_tomlin-normalized / steepest_edge / candidate.1 | 455.977868 | 454.307551 | 19.192990 | 0.000000 | 333137954 | 53287853920 | 2356.195 |
| suhl_suhl-direct / dantzig / reference.1 | 1952.831389 | 1952.504004 | 78.117948 | 0.000000 | 1632495192 | 212063056800 | 2729.168 |
| suhl_suhl-direct / dantzig / candidate.1 | 1873.689528 | 1873.310069 | 76.815788 | 0.000000 | 1632495195 | 212063273136 | 2647.301 |
| suhl_suhl-direct / steepest_edge / reference.1 | 497.164401 | 496.980886 | 18.647923 | 0.000000 | 365543250 | 52938537896 | 2522.625 |
| suhl_suhl-direct / steepest_edge / candidate.1 | 462.988803 | 462.800750 | 17.683146 | 0.000000 | 365543244 | 52938591224 | 2543.609 |
| suhl_suhl-normalized / dantzig / reference.1 | 1965.430529 | 1965.263753 | 87.038734 | 0.000000 | 2068130212 | 252328975408 | 2696.078 |
| suhl_suhl-normalized / dantzig / candidate.1 | 1881.592232 | 1881.413702 | 89.611313 | 0.000000 | 2068130215 | 252329152416 | 2623.629 |
| suhl_suhl-normalized / steepest_edge / reference.1 | 490.903758 | 489.189313 | 19.098265 | 0.000000 | 264297778 | 50153734864 | 2470.855 |
| suhl_suhl-normalized / steepest_edge / candidate.1 | 412.517401 | 411.106710 | 17.081826 | 0.000000 | 264297778 | 50153782416 | 2612.375 |
| bartels_golub-direct / dantzig / reference.1 | 2177.365586 | 2177.132521 | 98.810566 | 0.000000 | 2420705400 | 270643778328 | 2740.973 |
| bartels_golub-direct / dantzig / candidate.1 | 2154.928757 | 2154.497160 | 98.193401 | 0.000000 | 2420705402 | 270643381848 | 2704.059 |
| bartels_golub-direct / steepest_edge / reference.1 | 534.969515 | 534.697279 | 17.000845 | 0.000000 | 195113936 | 40869921384 | 2507.094 |
| bartels_golub-direct / steepest_edge / candidate.1 | 534.342760 | 534.054339 | 18.110926 | 0.000000 | 195113938 | 40869913864 | 2496.965 |
| bartels_golub-normalized / dantzig / reference.1 | 1944.386804 | 1943.969302 | 83.704098 | 0.000000 | 1692083955 | 229818248440 | 2734.812 |
| bartels_golub-normalized / dantzig / candidate.1 | 1701.073442 | 1700.670084 | 78.727273 | 0.000000 | 1692083955 | 229818870504 | 2693.164 |
| bartels_golub-normalized / steepest_edge / reference.1 | 491.935897 | 491.868714 | 21.100010 | 0.000000 | 309874572 | 54111802888 | 2639.293 |
| bartels_golub-normalized / steepest_edge / candidate.1 | 458.241877 | 458.160488 | 18.721448 | 0.000000 | 309874572 | 54112073112 | 2595.246 |
| bartels_golub-normalized / steepest_edge / candidate.2 | 468.172112 | 468.096836 | 19.656098 | 0.000000 | 309874573 | 54112089464 | 2515.746 |
| bartels_golub-normalized / steepest_edge / reference.2 | 483.114292 | 483.055949 | 19.678382 | 0.000000 | 309874572 | 54112048136 | 2447.023 |
| bartels_golub-normalized / dantzig / candidate.2 | 1705.474534 | 1705.077459 | 80.677289 | 0.000000 | 1692083955 | 229819404792 | 2719.289 |
| bartels_golub-normalized / dantzig / reference.2 | 1793.841109 | 1793.447801 | 80.968088 | 0.000000 | 1692083955 | 229818243912 | 2745.688 |
| bartels_golub-direct / steepest_edge / candidate.2 | 459.364416 | 459.103251 | 16.455287 | 0.000000 | 195113932 | 40869904184 | 2483.914 |
| bartels_golub-direct / steepest_edge / reference.2 | 467.251278 | 466.967919 | 15.655298 | 0.000000 | 195113938 | 40869793496 | 2485.242 |
| bartels_golub-direct / dantzig / candidate.2 | 1916.255428 | 1916.031091 | 94.033119 | 0.000000 | 2420705400 | 270642783688 | 2739.660 |
| bartels_golub-direct / dantzig / reference.2 | 2082.553949 | 2082.323490 | 94.208586 | 0.000000 | 2420705400 | 270643758360 | 2724.891 |
| suhl_suhl-normalized / steepest_edge / candidate.2 | 474.982686 | 473.351838 | 18.742780 | 0.000000 | 264297778 | 50153751808 | 2339.473 |
| suhl_suhl-normalized / steepest_edge / reference.2 | 471.321842 | 469.719931 | 17.787601 | 0.000000 | 264297778 | 50153766960 | 2570.691 |
| suhl_suhl-normalized / dantzig / candidate.2 | 1823.120334 | 1822.964650 | 82.342528 | 0.000000 | 2068130211 | 252329108288 | 2700.059 |
| suhl_suhl-normalized / dantzig / reference.2 | 1946.121866 | 1945.974456 | 87.126699 | 0.000000 | 2068130209 | 252328916160 | 2581.531 |
| suhl_suhl-direct / steepest_edge / candidate.2 | 459.513237 | 459.317004 | 17.476867 | 0.000000 | 365543250 | 52938616344 | 2456.180 |
| suhl_suhl-direct / steepest_edge / reference.2 | 500.927923 | 500.687075 | 19.271039 | 0.000000 | 365543250 | 52938621064 | 2515.723 |
| suhl_suhl-direct / dantzig / candidate.2 | 1870.994148 | 1870.685047 | 78.177560 | 0.000000 | 1632495193 | 212062591872 | 2485.430 |
| suhl_suhl-direct / dantzig / reference.2 | 1816.490682 | 1816.186907 | 74.466896 | 0.000000 | 1632495195 | 212062837408 | 2545.898 |
| forrest_tomlin-normalized / steepest_edge / candidate.2 | 406.302055 | 404.731156 | 18.868044 | 0.000000 | 333137954 | 53287890016 | 2433.117 |
| forrest_tomlin-normalized / steepest_edge / reference.2 | 416.081299 | 414.810962 | 18.202521 | 0.000000 | 333137954 | 53287889744 | 2541.348 |
| forrest_tomlin-normalized / dantzig / candidate.2 | 1854.242399 | 1854.077495 | 86.536490 | 0.000000 | 1825917999 | 258541033264 | 2704.762 |
| forrest_tomlin-normalized / dantzig / reference.2 | 1958.824362 | 1958.663081 | 86.634445 | 0.000000 | 1825917997 | 258539820960 | 2618.504 |
| forrest_tomlin-direct / steepest_edge / candidate.2 | 426.307458 | 425.978518 | 17.512971 | 28.483899 | 367018873 | 52457899336 | 2526.664 |
| forrest_tomlin-direct / steepest_edge / reference.2 | 443.957517 | 443.656176 | 17.986704 | 27.091596 | 367018877 | 52457815256 | 2396.531 |
| forrest_tomlin-direct / dantzig / candidate.2 | 1919.450602 | 1918.950790 | 85.314507 | 0.000000 | 1989831578 | 247990006024 | 2674.332 |
| forrest_tomlin-direct / dantzig / reference.2 | 1882.393838 | 1881.876880 | 75.456690 | 0.000000 | 1989831578 | 247989500632 | 2544.051 |
| pfi-production / steepest_edge / candidate.2 | 297.417381 | 297.129390 | 1.473537 | 21.229700 | 22033957 | 15276055808 | 2358.262 |
| pfi-production / steepest_edge / reference.2 | 308.596571 | 308.309675 | 1.000814 | 19.459000 | 22033956 | 15276095664 | 2343.059 |
| pfi-production / dantzig / candidate.2 | 1279.107395 | 1278.941205 | 15.676072 | 0.000000 | 949192774 | 106880593632 | 2670.328 |
| pfi-production / dantzig / reference.2 | 1342.010019 | 1341.834605 | 16.091230 | 0.000000 | 949192783 | 106880721280 | 2596.734 |
| bartels_golub-production / steepest_edge / candidate.2 | 543.022369 | 542.756505 | 6.263084 | 20.152001 | 98162740 | 30225750792 | 2427.953 |
| bartels_golub-production / steepest_edge / reference.2 | 559.876281 | 559.602995 | 6.164929 | 19.029800 | 98162740 | 30225746952 | 2356.969 |
| bartels_golub-production / dantzig / candidate.2 | 1775.811431 | 1775.698071 | 29.374531 | 22.617700 | 810703186 | 140160222640 | 2595.461 |
| bartels_golub-production / dantzig / reference.2 | 1842.566809 | 1842.443786 | 28.996245 | 19.833500 | 810703198 | 140159064240 | 2664.797 |
| suhl_suhl-production / steepest_edge / candidate.2 | 398.278762 | 398.151782 | 8.236521 | 19.455200 | 150803559 | 35990261704 | 2476.984 |
| suhl_suhl-production / steepest_edge / reference.2 | 419.485714 | 419.338741 | 8.517084 | 26.131500 | 150803577 | 35990282920 | 2493.375 |
| suhl_suhl-production / dantzig / candidate.2 | 1397.732163 | 1397.615589 | 31.250219 | 20.442700 | 1075804892 | 146978947792 | 2688.719 |
| suhl_suhl-production / dantzig / reference.2 | 1445.378752 | 1445.264009 | 31.339943 | 21.512401 | 1075804892 | 146978552048 | 2631.855 |
| forrest_tomlin-production / steepest_edge / candidate.2 | 391.822399 | 391.717288 | 7.277908 | 19.085500 | 127532710 | 31006979624 | 2392.285 |
| forrest_tomlin-production / steepest_edge / reference.2 | 408.640696 | 408.531345 | 7.027027 | 19.366701 | 127532718 | 31007008024 | 2409.039 |
| forrest_tomlin-production / dantzig / candidate.2 | 1583.511336 | 1583.401424 | 38.998910 | 21.337700 | 1527167966 | 183030142328 | 2604.957 |
| forrest_tomlin-production / dantzig / reference.2 | 1652.530489 | 1652.420049 | 39.304891 | 18.768797 | 1527167958 | 183030305880 | 2555.711 |
| huangfu_hall-production / steepest_edge / candidate.2 | 218.221440 | 218.100948 | 5.131973 | 19.827898 | 118046018 | 26139530384 | 2328.258 |
| huangfu_hall-production / steepest_edge / reference.2 | 234.150911 | 234.030056 | 5.145135 | 20.717700 | 118046016 | 26139880848 | 2386.629 |
| huangfu_hall-production / dantzig / candidate.2 | 1053.062645 | 1052.960554 | 28.534248 | 19.231800 | 1080338610 | 139378669872 | 2519.168 |
| huangfu_hall-production / dantzig / reference.2 | 1124.481076 | 1124.372336 | 28.138874 | 20.064100 | 1080338610 | 139378711808 | 2752.762 |

[Strojové ověření](final-verification.json) · [Páry a prostředky CSV](pairs.csv) · [Pokrytí CSV](coverage.csv)
