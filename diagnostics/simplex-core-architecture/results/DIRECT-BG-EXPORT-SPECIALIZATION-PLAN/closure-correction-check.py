"""Bounded syntax/source review only: never imports or executes closure/helpers."""
from pathlib import Path
import ast,hashlib,json
D=Path(__file__).resolve().parent;R=D.parents[3];P=D.with_name('DIRECT-BG-EXPORT-WORKSPACE-ALLOCATION-PROVENANCE-REVIEWED')
checks={};hashes={}
def data(p):
 p=Path(p);b=p.read_bytes();hashes[str(p)]=hashlib.sha256(b).hexdigest();return b

def tx(p):return data(p).decode()
def rd(p):return json.loads(data(p))
def ck(k,v):checks[k]=bool(v)
a,b=tx(D/'closure.py'),tx(D/'closure-2.py');pa,pb=tx(D/'publication.py'),tx(D/'publication-2.py')
expected=a.replace('import importlib.util,json\n','import importlib.util,json,sys\n').replace("sp=importlib.util.spec_from_file_location('prior_control'","sys.path.insert(0,str(P))\nsp=importlib.util.spec_from_file_location('prior_control'").replace("'publication-names.json'","'publication-names-2.json'").replace("'closure.json'","'closure-2.json'")
ck('closure_exact_import_and_distinct_output_changes',b==expected)
ck('publication_exact_manifest_and_closure_reference_changes',pb==pa.replace("'publication-names.json'","'publication-names-2.json'").replace("'closure.json'","'closure-2.json'"))
for name in ['closure.py','closure-2.py','publication.py','publication-2.py']:
 ast.parse(tx(D/name),filename=name)
ck('four_scripts_parse_without_execution',True)
f=rd(D/'closure-failure.json')
ck('failure_binds_preserved_original',f['exit_code']==1 and f['script_sha256']==hashes[str(D/'closure.py')] and f['error']=="ModuleNotFoundError: No module named 'guard'")
ck('failed_attempt_left_no_outputs',all(not (D/n).exists() for n in ['host-closure.json','closure.json','closure-2.json','publication.json']))
helpers=[P/'control.py',D.with_name('DIRECT-BG-EXPORT-WORKSPACE-COST-PREPARATION')/'control.py',D.with_name('DIRECT-BG-EXPORT-WORKSPACE-GREEN2-PREPARATION')/'control.py',D.with_name('DIRECT-BG-EXPORT-WORKSPACE-DRIVER-PREPARATION')/'control.py',P/'guard.py']
for p in helpers:ast.parse(tx(p),filename=str(p))
ck('correct_guard_directory_precedes_transitive_import',b.index('sys.path.insert(0,str(P))')<b.index('sp.loader.exec_module(c)') and helpers[-1].is_file() and 'import guard\n' in tx(helpers[-2]))
g=ast.parse(tx(P/'guard.py'));last=g.body[-1]
ck('guard_main_is_name_guarded',isinstance(last,ast.If) and ast.unparse(last.test)=="__name__ == '__main__'" and 'sys.exit(main())' in ast.unparse(last))
ck('closure_gate_schema_unchanged',b[b.index('checks={}'):b.index("names=c.rd(D/'publication-names-2.json')")]==a[a.index('checks={}'):a.index("names=c.rd(D/'publication-names.json')")])
ck('publication_gate_and_staging_logic_unchanged',pb.replace("'publication-names-2.json'","'publication-names.json'").replace("'closure-2.json'","'closure.json'")==pa)
r=rd(D/'review.json');spec=R/'docs/superpowers/specs/2026-10-19-direct-bg-export-specialization.md';plan=R/'docs/superpowers/plans/2026-10-19-direct-bg-export-specialization.md'
ck('accepted_plan_sources_unchanged',r['accepted'] and not r['findings'] and all(hashlib.sha256(data(p)).hexdigest()==r['sha256'][str(p)] for p in [spec,plan,D/'SELF-REVIEW.md',D/'review.md']))
data(D/'publication-names.json');data(Path(__file__))
out={'all_passed':all(checks.values()),'checks':checks,'sha256':hashes,'scope':'Narrow offline closure correction source/syntax review; no helpers imported, no closure/publication/old auditor/main execution; final names2 inventory is frozen later'}
with (D/'closure-correction-check.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps({'all_passed':out['all_passed'],'checks':len(checks),'bindings':len(hashes),'failed':[k for k,v in checks.items() if not v]}))
if not out['all_passed']:raise SystemExit(1)
