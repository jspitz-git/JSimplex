"""Exclusive independent offline evidence checker; never imports prepared scripts or Julia."""
from pathlib import Path
import hashlib,json,re,subprocess
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
D=R/'diagnostics/simplex-core-architecture/results/NATIVE-PIVOT-INTEGRATION-PREPARATION'
checks={}
def read(p): return json.loads(Path(p).read_text())
def path(n): return Path(n) if Path(n).is_absolute() else R/n
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def check(n,b): checks[n]=bool(b)
def bindings(n,z):
 for field in ('sha256','evidence_sha256'):
  d=z.get(field,{})
  check(n+' '+field, all(sha(path(p))==h for p,h in d.items()))
def git(*args): return subprocess.check_output(['git',*args],cwd=R,text=True).strip()
pins=read(D/'preparation-pins.json');check('833 fresh readtime pins',len(pins['sha256'])==833);bindings('fresh preparation pins',pins)
s=read(D/'source-check.json');check('source checks 12 true',len(s['checks'])==12 and all(s['checks'].values()) and s['all_passed']);check('source bindings 91',len(s['sha256'])==91);bindings('source',s)
a=read(D/'author-check.json');check('author 12 true',len(a['checks'])==12 and all(a['checks'].values()) and a['all_passed'])
b=read(D/'actual-baseline.json');check('actual baseline 520',len(b['sha256'])==520);bindings('actual baseline',b)
# Independent HEAD read through git plumbing; no index mutation or old code execution.
for n,h in b['sha256'].items():
 data=subprocess.check_output(['git','show','HEAD:'+n],cwd=R)
 if hashlib.sha256(data).hexdigest()!=h: raise RuntimeError('HEAD baseline mismatch '+n)
check('all 520 baseline files equal HEAD',True)
check('HEAD unchanged',git('rev-parse','HEAD')=='fac3ffc1065f9c34852ce82a6d33b496aa641936')
check('master unchanged',git('rev-parse','master')=='6f68e24e8ddac42b948da8fcc2d636c010751194')
check('branch unchanged',git('branch','--show-current')=='codex/simplex-core-architecture')
check('no tracked unstaged or staged changes',not git('diff','--name-only') and not git('diff','--cached','--name-only'))
old=read(D.parent/'NATIVE-PIVOT-PREPARATION/overlay-manifest.json')['candidate'];new=read(D/'overlay-manifest.json')['candidate']
check('old75 new76',len(old)==75 and len(new)==76)
check('all old overlay entries identical',all(e in new for e in old))
check('unique new destinations',len({e['destination'] for e in new})==76)
check('overlay hashes independently read',all(sha(e['source'])==e['sha256'] for e in new))
extra=[e for e in new if e not in old]
check('only new focused test',len(extra)==1 and extra[0]['destination']=='test/native_pivot_integration_tests.jl' and Path(extra[0]['source'])==D/'native_pivot_integration_tests.jl')
prod=[e for e in old if '/candidate/src/' in e['source']]
check('seven existing production replacements',len(prod)==7)
i=read(D/'runtests-inverse.json');c=(D/'candidate/test/runtests.jl').read_text();o=(R/'test/runtests.jl').read_text()
check('runtests one exact two-include inverse',c.count(i['after'])==1 and c.replace(i['after'],i['before'])==o and sha(D/'candidate/test/runtests.jl')==i['candidate_sha256'] and sha(R/'test/runtests.jl')==i['original_sha256'])
seams=read(D/'observer-seams.json');f=Path(next(e['source'] for e in new if e['destination']=='src/factorization.jl')).read_text();g=f
check('six future seams',len(seams['edits'])==6 and sorted(seams['application_order'])==list(range(6)))
for j in seams['application_order']:
 e=seams['edits'][j];check('seam forward '+str(j),g.count(e['before'])==e['count']);g=g.replace(e['before'],e['after'])
check('two refactor completion return sites',g.count('return Main.NativePivotIntegrationProbe.completed(:refactor, backend)')==2)
for j in reversed(seams['application_order']):
 e=seams['edits'][j];check('seam inverse '+str(j),g.count(e['after'])==e['count']);g=g.replace(e['after'],e['before'])
check('whole observer inverse identity',g==f)
check('observer data only',not (D/'runs').exists() and not (R/'.superpowers/native-pivot-integration').exists())
mp=read(D/'continuation-mappings.json')['mappings'];check('four continuation mappings',len(mp)==4)
for j,m in enumerate(mp):
 v=read(R/m['record'])
 for k in m['pointer']:v=v[k]
 check('continuation mapping '+str(j),v==m['sha256']==sha(R/m['preserved_path']))
for label in ('NATIVE-PIVOT-COST/closure.json','NATIVE-PIVOT-COST/publication.json'):
 z=read(D.parent/label);check(label+' passed',z['all_passed'])
 for n,h in z['sha256'].items():
  mapped=[m for m in mp if m['record']==str((D.parent/label).relative_to(R)) and m['key']==n]
  check(label+' binding '+n,sha(R/mapped[0]['preserved_path'] if mapped else path(n))==h)
for label in ('NATIVE-PIVOT-GREEN2-PREPARATION/runs/green2/audit.json','NATIVE-PIVOT-GREEN2-PREPARATION/runs/green2/result-review.json','NATIVE-PIVOT-COST-PREPARATION/runs/cost/audit.json','NATIVE-PIVOT-COST-PREPARATION/runs/cost/result-review.json','NATIVE-PIVOT-COST/postcheck.json'):
 z=read(D.parent/label);check(label+' accepted',z.get('accepted',z.get('all_passed')) is True);bindings(label,z)
z=read(D.parent/'NATIVE-PIVOT-COST-PREPARATION/runs/cost/result-review.json')['summary']
check('preserved 176 DSE FTRAN failures and 2112 policy passes',z['default_failures']==176 and z['default_failure_rhs']=='dse' and z['default_failure_operation']=='forward' and z['threshold_passed']==z['threshold_total']==2112 and z['gc_windows']==2)
z=read(D.parent/'NATIVE-PIVOT-GREEN2-PREPARATION/runs/green2/result-review.json')['summary'];check('GREEN2 6977 includes119 regression',z['original_assertions']+z['regression_assertions']==6977 and z['regression_assertions']==119)
check('original failed GREEN preserved',read(D.parent/'NATIVE-PIVOT-QUALIFICATION/runs/green/audit.json')['all_passed'] is False)
t=(D/'native_pivot_integration_tests.jl').read_text();public=t.split('function public_case(mode, symbol)',1)[1].split('function copied_options',1)[0];rec=t.split('function recovery_case()',1)[1].split('@testset "Native pivot policy public integration"',1)[0]
check('six public assertions',len(re.findall(r'(?m)^\s*@test ',public))==6)
check('29 recovery assertions',len(re.findall(r'(?m)^\s*@test ',rec))==29)
opt=next(Path(e['source']).read_text() for e in new if e['destination']=='src/options.jl');fields=opt.split('struct SolverOptions{T<:Real,M,R}',1)[1].split('\nend',1)[0]
check('17 option fields',len(re.findall(r'(?m)^    \w+::',fields))==17)
check('five full-field comparisons',rec.count('copied_options(options,')==5 and 'for name in fieldnames(typeof(a))' in t)
check('162 prospective assertions',8*6+29+5*17==162)
check('one public call per eight literal cases','for mode in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub), symbol in (:default,:threshold_one)' in t and public.count('solve(problem; options)')==1)
check('original LP and exact oracles',all(x in public for x in ['sparse([1.0 1.0; 1.0 0.0; 0.0 1.0])','[-3.0, -2.0]','row_upper=[4.0, 2.0, 3.0]','result.status == OPTIMAL','result.primal == [2.0, 2.0]','result.objective_value == -10.0']))
check('original public settings',all(x in public for x in ['algorithm=:dual','simplex_strategy=:legacy','pricing=:steepest_edge','basis_refactorization=:native','presolve=false','scaling=:off','partial_pricing=false','refactorization_interval=2','time_limit=5.0','iteration_limit=100']))
check('one private recovery entry',rec.count('J.initialize_workspace(')==1 and rec.count('J.checkpoint_basis(')==1 and rec.count('J._recovery_trial(')==1 and 'restore_checkpoint!' not in rec)
check('BigFloat option roundtrip only','setprecision(BigFloat,256)' in rec and rec.count('J._copy_precision_options(BigFloat,options)')==2 and 'J._copy_precision_options(Float64,J._copy_precision_options(BigFloat,options))' in rec)
check('guard ceiling arithmetic',(8*64+2,8*64,8*4096+2,8*4096+6)==(514,512,32770,32774))
check('public23 entries recovery44 checkpoint9',(3+4+4+2+3+3+2+2,15+9+20,2+2+2+1+2)==(23,44,9))
# Code has six objects; CSC owns three buffers, the other five are vectors.
ledger=(D/'WORK-AND-ADMISSION.md').read_text()
check('public snapshot object/buffer ledger accurate','seven input snapshots' not in ledger and 'nine buffers; seven copied objects' not in ledger)
out={'all_passed':all(checks.values()),'checks':checks,'check_count':len(checks),'failures':[n for n,v in checks.items() if not v],'scope':'Independent read-only Python evidence and literal source checks; no prepared code execution or Julia parser/import/run.','pins_sha256':sha(D/'preparation-pins.json'),'counts':{'pins':833,'source_bindings':91,'baseline':520,'overlay':76,'predecessor_overlay':75,'assertions_prospective':162,'public_snapshot_entries':23,'public_snapshot_objects':6,'public_snapshot_buffers':8,'recovery_snapshot_entries':44,'checkpoint_entries':9},'reviewer_script_sha256':sha(Path(__file__))}
with (D/'reviewer-checks.json').open('x') as w:json.dump(out,w,indent=2);w.write('\n')
print(json.dumps({k:out[k] for k in ('all_passed','check_count','failures','counts')}))
