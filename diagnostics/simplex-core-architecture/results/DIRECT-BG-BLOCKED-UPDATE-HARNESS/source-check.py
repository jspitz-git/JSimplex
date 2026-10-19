"""New offline literal/AST/hash checks. No Julia parsing or execution."""
from pathlib import Path
import ast,json,hashlib,re,sys
D=Path(__file__).resolve().parent;R=D.parents[3];C=R/'diagnostics/direct-bg-blocked-update/reproduce'
checks={}
def ck(n,v):
 checks[n]=bool(v)
 if not v:raise RuntimeError(n)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
sites=json.loads((D/'assertion-sites.json').read_text());m=json.loads((D/'test-transform.json').read_text())
for name,item in m.items():
 s=(D/name).read_text();ck('clone_hash_'+name,sha(D/name)==item['clone_sha256']);ck('frozen_hash_'+name,sha(item['original'])==item['sha256'])
 for change in reversed(item['changes'][1:]):
  ck('inverse_count_'+name+'_'+str(len(checks)),s.count(change['new'])==change['count']);s=s.replace(change['new'],change['old'])
 s=s.replace('using ..HarnessRecords: @check, @checkthrows\nimport ..HarnessRecords\nusing Test','using Test')
 for sid in item['changes'][0]['sites']:
  macro='@checkthrows' if sites[sid]['kind']=='@test_throws' else '@check';ck('site_once_'+sid,s.count(macro+' "'+sid+'"')==1);s=s.replace(macro+' "'+sid+'"',sites[sid]['kind'])
 ck('exact_original_inverse_'+name,s==(C/name).read_text())
for p in D.glob('*.py'):
 tree=ast.parse(p.read_text());ck('python_syntax_'+p.name,True)
 if p.name in ['control.py','seal.py','launch.py','outer.py','audit.py','oracle.py','post-return.py']:
  ck('failclosed_no_assert_'+p.name,not any(isinstance(n,ast.Assert) for n in ast.walk(tree)))
d=(D/'driver.jl').read_text();ck('all_includes_before_main',d.rfind('include(')<d.index('function main()'))
ck('top_level_loader', 'using JSimplex' in d and 'realpath(pathof(JSimplex))' in d)
ck('no_world_age_workaround',not any(t in d for t in ['invokelatest','eval(','include_string','@fastmath']))
ck('raw_before_exit',d.index('save("raw.toml"')<d.index('exit(valid'))
ck('same_structural_lifecycle_both_modes',d.count('run_task1_tests')==d.count('run_lifecycle')==1 and 'reference_route=RED' in d)
ck('no_actual_launch',not (D/'runs').exists() and not (D/'outers').exists())
ck('candidate_review_accepted',json.loads((D.with_name('DIRECT-BG-BLOCKED-UPDATE-TASK2')/'review.json').read_text())['accepted'] is True)
ck('160_sites',len(sites)==160)
ck('ordinary_stage',json.loads((D/'stages.json').read_text())['red']==json.loads((D/'stages.json').read_text())['green'])
files=[p for p in D.iterdir() if p.is_file()]+list(C.iterdir())
with (D/'source-check.json').open('x') as f:json.dump(dict(all_passed=True,checks=checks,sha256={str(p):sha(p) for p in files},scope=__doc__),f,indent=2)
print('Offline source/inverse PASS',len(checks))
