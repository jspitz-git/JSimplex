"""Offline context repair and disjoint attempt paths; original artifacts immutable."""
from pathlib import Path
import json,hashlib,re
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-F-repair';E=D.parent/'MA-E'
def write(p,s):
 with p.open('x') as f:f.write(s)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
old=(E/'driver.jl').read_text()
def context_checks(s):return dict(no_removed_API='Test.push_testset' not in s and 'Test.pop_testset' not in s,scoped_entry='Test.@with_testset ts begin' in s,parent_and_depth='parent_testset=Test.get_testset()' in s and 'parent_depth=Test.get_testset_depth()' in s,restore='Test.get_testset()===parent_testset && Test.get_testset_depth()==parent_depth' in s)
red=context_checks(old)
write(D/'context-red.json',json.dumps(dict(checks=red,expected_failures=4,original_raw=str(D.parent/'MA-F/attempt-1/red/raw.toml'),scope='Static repair predicates fail on original driver; original runtime UndefVarError is preserved.'),indent=2)+'\n')
if any(red.values()):raise SystemExit('unexpected original context')
a='''        Test.push_testset(ts)
        try
            Base.include(Main,joinpath(@__DIR__,"tests-instrumented.jl"))
        finally
            Test.pop_testset()===ts||error("test stack")'''
b='''        parent_testset=Test.get_testset()
        parent_depth=Test.get_testset_depth()
        try
            Test.@with_testset ts begin
                Base.include(Main,joinpath(@__DIR__,"tests-instrumented.jl"))
            end
        finally
            Test.get_testset()===parent_testset && Test.get_testset_depth()==parent_depth || error("test scope restoration")'''
if old.count(a)!=1:raise SystemExit('driver anchor')
new=old.replace(a,b);write(D/'driver.jl',new)
for n in ['kernels.jl','reference-upper.jl','test-collector.jl','tests-instrumented.jl','fixtures.toml','test-counts.json','finite_oracle.py','guard-reviewed.py']:
 with (D/n).open('xb') as f:f.write((E/n).read_bytes())
# Same fail-closed oracle, only reference/candidate source-root anchor is relocated.
s=(E/'auditor.py').read_text();s=s.replace("(D/'overlays'/side/'src/JSimplex.jl')","(D.parent/'MA-E/overlays'/side/'src/JSimplex.jl')");write(D/'auditor.py',s)
s=(E/'control_reviewed.py').read_text().replace("MA-F/attempt-1","MA-F/attempt-2").replace("str(D/'overlays'/s['side'])","str(D.parent/'MA-E/overlays'/s['side'])").replace("'MA-F-attempt-1'","'MA-F-attempt-2'");write(D/'control_reviewed.py',s)
s=(E/'seal-reviewed.py').read_text().replace("'MA-F-attempt-1'","'MA-F-attempt-2'");write(D/'seal-reviewed.py',s)
write(D/'launcher-reviewed.py',(E/'launcher-reviewed.py').read_text())
(D/'configs').mkdir()
for p in sorted((E/'configs').glob('*.toml')):write(D/'configs'/p.name,p.read_text().replace('MA-F/attempt-1/','MA-F/attempt-2/'))
checks=context_checks(new);checks['exact_driver_inverse']=new.replace(b,a)==old;checks['original_test_and_kernels_unchanged']=all(sha(D/n)==sha(E/n) for n in ['kernels.jl','reference-upper.jl','test-collector.jl','tests-instrumented.jl','fixtures.toml','test-counts.json','finite_oracle.py','guard-reviewed.py','launcher-reviewed.py']);checks['22_configs_only_output_change']=len(list((D/'configs').glob('*.toml')))==22 and all(p.read_text().replace('MA-F/attempt-2/','MA-F/attempt-1/')==(E/'configs'/p.name).read_text() for p in (D/'configs').glob('*.toml'))
T=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/stdlib/v1.13/Test/src/Test.jl');ts=T.read_text();symbols=sorted(set(re.findall(r'Test\.(@?\w+)',new+(D/'test-collector.jl').read_text())))
checks['all_Test_symbols_in_installed_source']=all(re.search(r'\b'+re.escape(s.lstrip('@'))+r'\b',ts) for s in symbols);checks['scoped_macro_has_finally']='macro with_testset(ts, expr)' in ts and '@with(CURRENT_TESTSET => $(esc(ts)), TESTSET_DEPTH => get_testset_depth() + 1' in ts
write(D/'context-green.json',json.dumps(dict(all_passed=all(checks.values()),checks=checks,Test_symbols=symbols,sha256={str(p):sha(p) for p in [D/'prepare.py',D/'driver.jl',E/'driver.jl',T,D.parent/'S4-AD-green-bounded/driver.jl']},scope='Source checks only; exception restoration and custom recording require review of installed macro and collector. No Julia execution.'),indent=2)+'\n')
print(checks)
if not all(checks.values()):raise SystemExit('repair source check failure')
