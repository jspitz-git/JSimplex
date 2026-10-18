# Prospective assertion inventory — no Julia execution

RED: six individual missing-symbol assertions in the original 75-file stage.
No factorization, basis construction, solve or candidate loading occurs in RED.
This demonstrates missing contracts, not numerical failure or performance.

GREEN calls the three frozen entry functions once, after all module includes at
file top level. Eleven exact leaf groups are bound in JSON and TOML. Expected
passing leaves: 42,6,35,56,108,53,303,6236,378,108,610 = **7935**.
These are prospective counts, not observed passes. Error/broken/unexpected nesting
or any group mismatch is rejected even when the total matches.

Independent source derivation:
- workspace: 5*5+(3*3+2)+6=42; reuse6; (3*3+2)+4*3+12=35.
- importer helper7; fused4*2*7=56; rejection6*(7+3)+4*(7+1)+2*8=108;
  validation17*3+2=53; fixtures14*18+6*6+6*2+3=303.
- paired_solutions15; aliases17; preserve_failure3.
- repeated:28*34+24*(8*23+2*18)+4=6236.
- failure:194+4*(M_native+M_markowitz)=378 with M_native25, M_markowitz21.
  n8 normalized importer20 requests, seen1; native orientation4, Markowitz0.
- copy:2*(8+2*15+1+15)=108.
- dimension:4*(6*17+49)+P+2=610 with P4 dense64 retained branches.

General count is7747+4*(M_native+M_markowitz)+P. Actual native orientation acceptance,
request reachability and dense64 retention are runtime premises. They MUST NOT be
retuned after output. Exact per-group counts reject differing reachability; actual
GREEN failure remains failure even if arithmetic outputs otherwise match. Warm
native64 and Markowitz witnesses additionally assert real owner reuse directly.
The recorder counts Test result leaves (including evaluated macro branches), not
lexical @test sites. All accepted candidate/test bytes remain unchanged.
