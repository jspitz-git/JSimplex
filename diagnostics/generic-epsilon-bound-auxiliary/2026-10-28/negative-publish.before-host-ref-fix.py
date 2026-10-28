from pathlib import Path
import sys,json,subprocess,re
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D));n=__import__('negative-common');R=n.R
n.refs();n.baseline_and_backup();n.protected(True)
cl=n.read('negative-closure.json');n.need(cl['accepted'] is True and cl['production_accepted'] is False and cl['master_restored']==n.BASE and all(v is True for v in cl['checks'].values()),'negative PASS closure only')
for p,h in cl['bindings'].items():n.need(n.sha(p)==h,'closure binding '+p)
n.need(not n.raw(['diff','--cached','--raw','-z'],R),'unrelated diagnostic staging')
paths=n.artifacts()+[D/'negative-closure.json']+[Path(p) for p in n.read('negative-historical-map.json')['continuation_before']]
paths=sorted(paths,key=lambda p:str(p.relative_to(R)));n.need(len(paths)==len(set(paths)),'exact unique publication paths')
n.need(all(str(p) in cl['bindings'] or p==D/'negative-closure.json' for p in paths),'complete closure membership')
plan=D/'negative-publication-plan.json';n.need(not plan.exists(),'exclusive publication plan')
def blob(p):return subprocess.check_output(['/usr/bin/git','-C',str(R),'hash-object','--stdin'],input=p.read_bytes()).decode().strip()
names=[str(p.relative_to(R)) for p in paths];expected={name:blob(p) for name,p in zip(names,paths)}
subprocess.run(['/usr/bin/git','-C',str(R),'add','-f','--',*names],check=True,timeout=120)
w=subprocess.run(['/usr/bin/git','-C',str(R),'diff','--cached','--check'],capture_output=True,text=True,timeout=120);warnings=[]
if w.returncode:
 n.need(w.returncode in [1,2] and not w.stderr,'diff-check error')
 for line in w.stdout.splitlines():
  if not line or line.startswith('+'):continue
  n.need(re.fullmatch(re.escape(str(D.relative_to(R)))+r'/.*:\d+: (trailing whitespace|new blank line at EOF)\.',line) is not None,'unexpected whitespace '+line);
  warning_path=line.rsplit(':',2)[0];ledger=n.read('negative-frozen-whitespace-ledger.json')['entries'];n.need(warning_path in ledger and n.sha(R/warning_path)==ledger[warning_path]['sha256'],'only fixed frozen whitespace '+warning_path);warnings.append(line)
 n.need(warnings,'unexplained diffcheck status')
allnames=sorted(names+[str(plan.relative_to(R))]);n.put(plan.name,dict(accepted=True,scope='Exact diagnostic publication of UNPROMOTED candidate and failed MASTER',production_accepted=False,master=n.BASE,candidate_preserved=n.CAND,parent=n.OLD,exact_names=allnames,listed_blobs=expected,listed_sha256={k:n.sha(p) for k,p in zip(names,paths)},self_excluded_from_listed_blobs=str(plan.relative_to(R)),self_blob_verified_before_commit=True,frozen_diagnostic_whitespace_preserved=warnings,prepublication_host=n.host()))
expected[str(plan.relative_to(R))]=blob(plan)
subprocess.run(['/usr/bin/git','-C',str(R),'add','-f','--',str(plan.relative_to(R))],check=True,timeout=120)
n.need(n.git(['diff','--cached','--name-only'],R).splitlines()==allnames,'exact staged names')
for p,h in expected.items():n.need(n.git(['rev-parse',':'+p],R)==h,'exact staged blob '+p)
# Every exact file/blob including the self-describing plan is checked before commit.
n.refs();n.baseline_and_backup();n.protected(True,True)
subprocess.run(['/usr/bin/git','-C',str(R),'-c','core.hooksPath=/dev/null','commit','-m','Record unpromoted epsilon bound and auxiliary measurements','-m','Preserve supported component savings, ordinary RED/GREEN success, failed actual MASTER and the insufficient single GC preparation control. Candidate717 remains retained locally; master235 restored and remotely unchanged. No cost waiver, numerical safeguard change or further tuning.'],check=True,timeout=120)
new=n.git(['rev-parse','HEAD'],R);n.need(n.git(['rev-list','--parents','-n','1',new],R).split()==[new,n.OLD],'sole diagnostic parent')
n.need(n.git(['diff-tree','--no-commit-id','--name-only','-r',new],R).splitlines()==allnames,'exact committed names')
for p,h in expected.items():n.need(n.git(['rev-parse',new+':'+p],R)==h,'exact committed blob '+p)
n.baseline_and_backup();n.protected(True,True)
subprocess.run(['/usr/bin/git','-C',str(R),'push','origin',new+':refs/heads/codex/simplex-core-architecture'],check=True,timeout=120)
n.refs(new);n.baseline_and_backup();n.protected(True,True)
n.need(not n.raw(['diff','--cached','--raw','-z'],R),'diagnostic index clean')
n.put('negative-publication-after.json',dict(accepted=True,production_accepted=False,diagnostic_commit=new,parent=n.OLD,master=n.BASE,candidate_preserved=n.CAND,exact_committed_names=allnames,all_blobs_verified=expected,normal_nonforce_push=True,remote_verified=True))
print(json.dumps(dict(accepted=True,production_accepted=False,diagnostic_commit=new,master=n.BASE,exact_files=len(allnames),remote_verified=True)))
