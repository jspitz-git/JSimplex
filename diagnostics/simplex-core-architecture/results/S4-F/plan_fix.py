from pathlib import Path
import json,hashlib
p=Path('docs/superpowers/plans/2026-10-12-hh-symbolic-publication.md');o=Path('diagnostics/simplex-core-architecture/results/S4-F');s=p.read_text()
def check(t):
 return {'prepare_before_success':'MOVED planned live forward solve: FTRAN rhs[1,2] on B2' in t,'true_to_false_oracle':'assert prepared_valid==true before successful refactor' in t,'five_matrix_oracles':'five2x2matrices' in t,'forward_B3_reused_check':'verify forward correctness on owned B3 using this already-planned RHS' in t}
red=check(s);assert not any(red.values())
with (o/'publication-plan-before-review.md').open('x') as f:f.write(s)
s=s.replace('   ownership and expected B1 outside all measured calls.','   ownership and expected B1 outside all measured calls.\n   MOVED planned live forward solve: FTRAN rhs[1,2] on B2; check its fixed\n   residual against B2, assert prepared_valid==true before successful refactor\n   and own its prepared values. This consumes the former step3live forward call,\n   not an extra call. Immediately after successful refactor require false.')
s=s.replace('   One forward and one transpose solve on liveB3 and savedB1 (4calls).','   One transpose solve on liveB3 and forward+transpose on savedB1 (3calls).\n   The fourth call moved before refactor to B2 in step2; no B3forward here.')
s=s.replace('4. FTRAN for[8,1], replace_column! at1: B4=[8 1;1 3]. FTRAN for current column2','4. FTRAN for[8,1]; verify forward correctness on owned B3 using this already-planned RHS\n   and fixed residual bound before replace_column! at1: B4=[8 1;1 3]. FTRAN for current column2')
s=s.replace('oracles for the four2x2matrices','oracles for the five2x2matrices B0/B1/B2/B3/B4')
green=check(s);assert all(green.values());p.write_text(s)
with (o/'plan-fix.json').open('x') as f:json.dump({'red_missing':4,'green':green,'all_passed':True,'unchanged_total_HH_solves':24,'before_sha256':hashlib.sha256((o/'publication-plan-before-review.md').read_bytes()).hexdigest(),'after_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'scope':'offline plan correction only; no numerical rerun'},f,indent=2)
print(green)
