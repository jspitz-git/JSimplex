from pathlib import Path
import json,hashlib,importlib.util,sys,math
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;W=D.parents[2];checks=[];cache={}
def read(p):return json.loads(p.read_text())
def sha(p):
 p=str(p)
 if p not in cache:
  with open(p,'rb') as f:cache[p]=hashlib.file_digest(f,'sha256').hexdigest()
 return cache[p]
def require(v,m):
 checks.append(dict(check=m,passed=bool(v)))
 if not v:raise ValueError(m)
s=importlib.util.spec_from_file_location('task6postdefs',D/'run.py');L=importlib.util.module_from_spec(s);s.loader.exec_module(L)
require(L.G.pins_match(read(D/'qualify-pins.json')),'622 qualification pins unchanged')
require(L.G.pins_match(read(D/'compare-pins.json')),'642 comparison pins unchanged')
qualification=read(D/'qualify-run/audit.json');comparison=read(D/'compare-run/audit.json')
require(qualification['accepted'] is True and qualification['assertions']==236,'observed ordinary qualification236')
require(comparison['accepted'] is True and comparison['assertions']==749,'observed ordinary comparison749')
require(len(qualification['summary'])==len(comparison['summary'])==16,'all16 fixed cases qualified and measured')
runs={}
for mode in ('qualify','compare'):
 out=D/(mode+'-run');r=read(out/'result.json');p=read(out/'guard/process.json');cfg=read(D/(mode+'-contract.json'));a=read(D/(mode+'-admission.json'))
 require(r['accepted'] is True and r['exit']==p['returncode']==0 and p['reason']=='exit0' and r['audit_exit']==0,mode+' actual guarded and audit exit0')
 require(r['pins_unchanged'] and p['pins_unchanged'] and r['elapsed_seconds']<=r['limit_seconds']==1800,mode+' actual common1800 allowance and source pins')
 require(cfg['command']==p['command'],mode+' exact actual command')
 require(a['accepted'] is True and a['pins_sha256']==sha(D/(mode+'-pins.json')),mode+' exact independent numerical admission')
 resources=[json.loads(x) for x in (out/'guard/resources.jsonl').read_text().splitlines()]
 require(resources and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in resources),mode+' all resource samples within memory limits')
 terminal=read(out/'terminal-host.json');require(terminal['no_julia'] and not terminal['conflicts'],mode+' full historicalgroupsANDsessions closed')
 runs[mode]=dict(elapsed_seconds=r['elapsed_seconds'],samples=len(resources),min_available_kib=min(x['available_kib'] for x in resources),max_swap_kib=max(x['swap_used_kib'] for x in resources),child_maxrss_kib=p['child_maxrss_kib'])
for c,entry in comparison['summary'].items():
 q=qualification['summary'][c];samples=[x for x in comparison['records']['SAMPLE'] if x['case']==c and x['phase']=='measure']
 for x in samples:
  require(float(x['compile'])==float(x['recompile'])==0,c+' actual compile-zero measured '+x['arm']+x['pair'])
  require(math.isclose(float(x['objective']),float(q['objective']),rel_tol=1e-6,abs_tol=1e-6),c+' objective matches separately qualified reference')
  if x['arm']=='candidate':
   for k,v in q.items():
    if k.startswith(('EC_','KC_','RC_','LD_')) or k in ('entries','imports','exports','legacy_fallbacks','original_retries','original_cleanups','original_recoveries'):
     require(x[k]==v,c+' same observed candidate work '+x['pair']+k)
 for k in ('paired_seconds','paired_bytes','paired_allocs'):
  require(all(math.isfinite(x) and x>=0 for x in entry[k].values()),c+' finite statistics '+k)
 require(entry['activated']==(int(q['EC_accepted_pivots'])>0 and int(q['legacy_fallbacks'])==0),c+' truthful performance admission')
require(read(D/'parser-red-result.json')['expected_failure_observed'] is True,'initial parser RED preserved')
require(read(D/'parser-tests.json')['accepted'] is True and len(read(D/'parser-tests.json')['checks'])==27,'27 separate offline parser tests PASS')
require(read(D/'before-admission-review/admission.json')['accepted'] is False,'original exact numerical admission rejection preserved')
for n,v in read(D/'admission-before-map.json').items():require(sha(v['preserved'])==v['sha256'],'initial source/pin bytes preserved '+n)
for n,v in read(D.parent/'task5/qualified-sources.json').items():require(sha(n)==v['sha256']==sha(v['preserved']),'Task5 qualified source unchanged '+n)
require(not L.H.H.git(W,'diff','--name-only','--','src','test','experimental','Project.toml','Manifest.toml','.github','diagnostics/dual-step-experiment/task1','diagnostics/dual-step-experiment/task2','diagnostics/dual-step-experiment/task3','diagnostics/dual-step-experiment/task4','diagnostics/dual-step-experiment/task5','docs/superpowers/plans/2026-10-31-experimental-dual-engine.md','docs/superpowers/specs/2026-10-31-experimental-dual-engine-design.md'),'no source/tests/env/CI/old evidence/plan changes in Task6')
h=L.host();require(h['no_julia'] and not h['conflicts'] and len(h['checked_groups'])==820,'fresh820 historical groups ANDsessions/noJulia/current refs')
with (D/'postcheck-host.json').open('x') as f:json.dump(h,f,indent=2)
with (D/'postcheck.json').open('x') as f:json.dump(dict(accepted=True,checks=checks,runs=runs,pins_sha256=sha(D/'compare-pins.json'),ordinary_assertions=985,scope='new offline actual observed Task6 records only; no oldauditor/Julia rerun, no large-model/nativefree/performance-generalization proof'),f,indent=2)
print(json.dumps(dict(accepted=True,checks=len(checks),ordinary_assertions=985,cases=16)))
