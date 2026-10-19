"""Fresh independent cost1-300 admission: definitions-only, no launch or old checker."""
from pathlib import Path
import sys,json,hashlib,subprocess,time,os
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
P=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-EXPORT-SPECIALIZATION-COST'
Q=P.with_name(P.name+'-FIRST'); RUN=P/'runs/cost1-300'; O=P/'outers/cost1-300'
sys.path.insert(0,str(P));import control as c
checks=[]
def check(v,label):
 checks.append({'check':label,'passed':bool(v)})
 if not v:raise AssertionError(label)
def read(p):return json.loads(Path(p).read_text())
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bindings(j,label):
 for p,h in j.items():check(digest(c.path(p))==h,label+': '+p)
def fresh():
 h=c.full_host(s['groups']);m=c.guard.memory();i=c.verify_outer('cost1-300',s,live=True)
 check(c.host_safe(h),'full prior groups AND sessions absent/no Julia/readable identities')
 check(len(h['groups'])==265,'265 prior groups/sessions')
 check(all(h[k]==s[k] for k in ('head','master','boot_id')),'current refs boot match seal')
 check(h['head']=='e149671cd2c9560ae2a91b80614d36799b845240','exact diagnostic HEAD')
 check(h['master']=='26e2291745999f485a74f643298ca997d65c7205','exact master')
 check(h['boot_id']=='1ecae454-f1f5-4e2e-a95c-7b5474243126','boot identity')
 check(i['pid']==i['pgid']==i['sid']==140961 and i['start_ticks']==11823805,'live outer identity')
 env=dict(x.split('=',1) for x in Path('/proc/140961/environ').read_bytes().decode().split('\0') if '=' in x)
 expected=read(P/'environment.json');check({k:env.get(k) for k in expected}==expected,'actual outer /proc environment matches pinned env')
 check(Path('/proc/140961/cwd').resolve()==R,'outer cwd')
 check(not c.guard.pressure(m),'RAM>=6GiB and swap<=1GiB')
 check(not any((O/n).exists() for n in ('release.json','outer-invocation.json','outer-outcome.json')),'outer still waiting; no release/invocation/outcome')
 check(not any((RUN/n).exists() for n in ('reservation.json','output','launch-pins.json','invocation.json','audit.json')),'no numerical reservation/output/launch')
 h['memory']=m;h['outer_identity']=i;h['outer_environment']= {k:env.get(k) for k in expected};return h
s=read(RUN/'sealed.json');cfg=c.config('cost1-300')
try:
 check(s['config']==cfg==read(RUN/'config.json'),'actual exact config')
 check(cfg['process']==1 and cfg['seconds']==300,'first ONLY 300')
 prepared=c.preparation();pred,groups=c.predecessor('cost1-300');c.verify_seal(cfg,s);check(True,'definitions-only preparation/predecessor/exact seal membership')
 check(s['files']==c.seal_files(cfg,prepared,pred),'independent exact seal file list equality')
 check(c.guard.pins_match(s),'full seal current inventory')
 check(set(s['groups'])==set(groups)|set(read(P/'host-entry.json')['groups']),'complete prior groups set')
 bindings({n:digest(n) for n in s['files']},'readable sealed file')
 canonical=read(P/'preparation-pins-final.json');check(len(canonical['sha256'])==2609,'2609 canonical paths')
 check(set(canonical['sha256'])==set(read(P/'required-paths-final.json')['paths']),'exact canonical required paths')
 bindings(canonical['sha256'],'canonical current hash')
 review=read(P/'review-final.json');check(review['accepted'] is True and review['findings']==[] and review['launch_admitted'] is False,'accepted preparation is not admission')
 bindings(review['sha256'],'final reviewer binding');bindings(review['evidence_sha256'],'final reviewer evidence')
 prior=read(c.G/'runs/greengc300/result-review.json');closure=read(c.G/'runs/greengc300/outer-closure.json')
 check(len(prior['sha256'])==81 and len(prior['evidence_sha256'])==24 and len(closure['sha256'])==8,'GREEN 81+24+8 exact bindings')
 bindings(prior['sha256'],'GREEN RUN');bindings(prior['evidence_sha256'],'GREEN evidence');bindings(closure['sha256'],'GREEN external closure')
 stage=read(P/'stages.json')['cost'];check(len(stage['sha256'])==87,'87 staged files')
 bindings({str(Path(stage['path'])/n):h for n,h in stage['sha256'].items()},'stage')
 c.validate_sources();check(True,'diagnostic/production source membership runtime and stage')
 remote=c.git('ls-remote','origin','refs/heads/codex/simplex-core-architecture','refs/heads/master')
 check(s['head']+'\trefs/heads/codex/simplex-core-architecture' in remote and s['master']+'\trefs/heads/master' in remote,'remote refs exact')
 check(not c.git('diff','--name-only') and not c.git('diff','--cached','--name-only'),'clean tracked worktree/index')
 driver=(P/'cost.jl').read_text();check('GC.gc' not in driver,'original Task3 no explicit GC')
 guard=(P/'guard.py').read_text();check('resource.RLIMIT_AS, (8 * 1024**3, 8 * 1024**3)' in guard,'VM8GiB')
 check('--threads=1' in cfg['command'] and '--gcthreads=1,0' in cfg['command'] and '--heap-size-hint=2G' in cfg['command'] and '--compiled-modules=existing' in cfg['command'],'exact Julia flags')
 check(c.guard_command(cfg,RUN/'launch-pins.json',0)[6]=='292.0' if False else '--seconds' in c.guard_command(cfg,RUN/'launch-pins.json',0) and str(cfg['seconds']-8) in c.guard_command(cfg,RUN/'launch-pins.json',0),'inner292')
 host=fresh();host['remote']=remote
 summaries={}
 for n in ['reviewer-final-check.json','probe-inverse.json','source-check.json','publication.json']:
  j=read(P/n);summaries[n]={k:v for k,v in j.items() if isinstance(v,(str,int,bool)) or (isinstance(v,list) and len(v)<10)}
 result=dict(accepted=True,findings=[],scope='Fresh independent exact cost1-300 admission checks',checks=checks,count=len(checks),sealed_sha256=digest(RUN/'sealed.json'),sealed_files=len(s['files']),inventory_entries=len(s['inventory']),prepared_files=len(prepared),predecessor_files=len(pred),host=host,summaries=summaries)
except BaseException as e:
 result=dict(accepted=False,findings=[repr(e)],checks=checks,count=len(checks))
with (Q/'admission-check.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('checks','host')},indent=2))
if not result['accepted']:sys.exit(1)
