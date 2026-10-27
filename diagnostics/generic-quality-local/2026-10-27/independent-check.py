from pathlib import Path
import hashlib,json,subprocess,os,datetime,ast
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-quality-local/2026-10-27');M=Path('/home/jspitz/JSimplex.jl');R=D.parents[2]
BASE='ca64312f7f74b1d7bec047718399f229674b3e1d'
def need(x,s):
 if not x:raise RuntimeError(s)
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(n):return json.loads((D/n).read_text())
def git(*a,root=M):return subprocess.check_output(['/usr/bin/git','-C',str(root),*a],env=dict(os.environ,GIT_OPTIONAL_LOCKS='0')).decode().strip()
P=read('pins.json')
for n,v in P['inventory'].items():need(str(Path(n).resolve(strict=True))==v['resolved'] and sha(n)==v['sha256'],'inventory '+n)
for tree in P['trees']:need({str(p) for p in Path(tree).rglob('*') if p.is_file()}=={n for n in P['inventory'] if Path(n).is_relative_to(tree)},'membership '+tree)
need(git('rev-parse','HEAD')==git('rev-parse','master')==git('rev-parse','origin/master')==BASE,'M refs')
need(git('rev-parse','HEAD',root=R)==read('host-before.json')['diagnostic_head'],'R head')
for n,v in {**read('protected-before.json')['files'],**read('protected-before.json')['indexes']}.items():need(sha(n)==v,'protected '+n)
for n,v in read('baseline-tree.json').items():
 need(sha(D/'baseline'/n)==sha(M/n)==v,'baseline '+n)
 if n.startswith(('src/','test/')) or n=='Project.toml':
  need(hashlib.sha256(subprocess.check_output(['/usr/bin/git','-C',str(M),'show',BASE+':'+n])).hexdigest()==v,'base commit '+n)
s=(M/'src/simplex_numerics.jl').read_text();p=(M/'src/primal_updates.jl').read_text();changes=read('changes.json')
quality=s[s.index('function _componentwise_backward_error('):s.index('\nend',s.index('function solve_quality!'))+5]+'\n\n'
audit=p[p.index('function _audit_primal_values!'):p.index('\nend',p.index('function _audit_primal_values!'))+5]+'\n\n'
i=p.index('function _quality_components!(r::AbstractVector{W},scale,terms,B::_PriceAuditMatrix');virtual='_quality_values(B::_PriceAuditMatrix) = nonzeros(B.matrix)\n'+p[i:p.index('\nend',i)+5]+'\n\n'
header='using JSimplex,SparseArrays\nusing JSimplex: SimplexWorkspace,SolveQualityScratch,NumericalPolicy,SolveQuality,\n    _is_exact,_compensated_solve_quality!,_primal_direction_magnitude,\n    _with_recovery_precision,_finite_workspace,_recomputed_basis_reliable,\n    _primal_price_prediction_reliable,recompute!,_PriceAuditMatrix\n'
for arm in ['Reference','CandidateA','CandidateB','CandidateAB','CandidateC']:
 q=quality;a=audit;extra=""
 if arm in ('CandidateA','CandidateAB'):q=q.replace(changes['A']['old'],changes['A']['new'])
 if arm in ('CandidateB','CandidateAB'):extra=changes['B']['new'].removesuffix(changes['B']['old'])
 if arm=='CandidateC':a+=changes['C']['new'].removesuffix(changes['C']['old'])
 expected='module Local'+arm+'\n'+header+q+extra+virtual+a+'end\n'
 need(expected==(D/(arm+'.jl')).read_text(),'clone exact '+arm)
for arm in ['A','B','C']:
 c=changes[arm];source=(M/'src'/c['file']).read_text();need(source.count(c['old'])==1,'unique old '+arm);out=source.replace(c['old'],c['new']);need(out.count(c['new'])==1 and out.replace(c['new'],c['old'])==source,'inverse '+arm)
for f in D.glob('*.py'):ast.parse(f.read_text())
for f in (D/'guard').glob('*.py'):ast.parse(f.read_text())
contract=read('contract.json');need(contract['cases']==15*136+2*34+2*32==2172,'cells');need(contract['measured_windows']==2172*18==39096,'windows')
need(not (D/'output').exists() and not (D/'reservation.json').exists(),'prior attempt')
H=read('author-host.json');need(len(H['groups'])==585,'585 groups');need(Path('/proc/sys/kernel/random/boot_id').read_text().strip()==H['boot_id'],'boot');processes=[]
for proc in Path('/proc').glob('[0-9]*'):
 try:
  st=(proc/'stat').read_text().rsplit(')',1)[1].split();cmd=(proc/'cmdline').read_bytes().split(b'\0');names=[(proc/'comm').read_text().strip()]+[v.decode(errors='replace') for v in cmd[:1]];need(int(st[2]) not in H['groups'] and int(st[3]) not in H['groups'],'historical group/session');need(not any(Path(n).name.lower().startswith('julia') for n in names),'Julia live');processes.append(dict(pid=int(proc.name),pgid=int(st[2]),sid=int(st[3]),start_ticks=int(st[19]),command=[v.decode(errors='replace') for v in cmd if v]))
 except (FileNotFoundError,ProcessLookupError):pass
mem={l.split(':')[0]:int(l.split()[1]) for l in Path('/proc/meminfo').read_text().splitlines()};need(mem['MemAvailable']>=6*1024**2 and mem['SwapTotal']-mem['SwapFree']<=1024**2,'RAM/swap')
result=dict(accepted=True,findings=[],checked_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),inventory_files=len(P['inventory']),baseline_files=len(read('baseline-tree.json')),exact_clones=5,source_inverse_variants=3,cells=2172,measured_windows=39096,historical_groups=585,boot_id=H['boot_id'],no_Julia=True,processes=processes,available_kib=mem['MemAvailable'],swap_used_kib=mem['SwapTotal']-mem['SwapFree'],checker_sha256=sha(__file__))
with Path('/tmp/local-quality-independent-evidence.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps({k:v for k,v in result.items() if k!='processes'}))
