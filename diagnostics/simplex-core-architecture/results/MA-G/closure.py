"""One-shot MA-G diagnostic closure, never a numerical runner."""
from pathlib import Path
import hashlib,json,subprocess,time
G=Path(__file__).resolve().parent;R=G.parents[3];F=G.parent/'MA-F-repair'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=R,text=True).strip()
checks={};bindings={}
def bind(p):bindings[str(p.relative_to(R))]=digest(p)
a=json.loads((G/'analysis.json').read_text());s=json.loads((G/'source-supplement.json').read_text());review=json.loads((G/'review.json').read_text())
checks['original_false_and_separate_supplement']=a['all_passed'] is False and sum(a['checks'].values())==58 and len(a['checks'])==61 and s['all_passed'] and len(s['checks'])==8 and all(s['checks'].values())
checks['review_accepted']=review.get('accepted') is True and not review.get('unresolved_findings')
for label,doc in [('analysis',a),('supplement',s),('review',review)]:
 checks[label+'_bindings']=bool(doc['sha256']) and all(digest(Path(k) if Path(k).is_absolute() else R/k)==v for k,v in doc['sha256'].items())
status=R/'diagnostics/simplex-core-architecture/STATUS.md';road=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
mapping={str(status):G/'STATUS.md.before-MA-G',str(road):G/'roadmap.md.before-MA-G'}
for name in ['closure.json','closure-final.json','publication.json','result-review.json']:
 p=F/name;d=json.loads(p.read_text());ok=True;used=set()
 for k,v in d['sha256'].items():
  q=Path(k) if Path(k).is_absolute() else R/k
  if str(q) in mapping:used.add(str(q));q=mapping[str(q)]
  ok=ok and digest(q)==v
 checks['previous_'+name]=ok and used==(set() if name=='result-review.json' else set(mapping))
 bind(p)
h=json.loads((G/'host.json').read_text());groups=set(h['groups']);matches=[]
for p in Path('/proc').iterdir():
 if not p.name.isdecimal():continue
 try:
  stat=(p/'stat').read_text();tail=stat[stat.rfind(')')+2:].split();cmd=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace');comm=(p/'comm').read_text().strip()
 except (FileNotFoundError,PermissionError,ProcessLookupError):continue
 if int(tail[2]) in groups or int(tail[3]) in groups or comm.lower().startswith('julia'):
  matches.append({'pid':int(p.name),'pgid':int(tail[2]),'sid':int(tail[3]),'start_ticks':int(tail[19]),'command':cmd})
checks['fresh90groups_ANDsessions_noJulia']=len(groups)==90 and not matches
checks['boot_unchanged']=Path('/proc/sys/kernel/random/boot_id').read_text().strip()==h['boot_id']
checks['protected_files']=all(digest(Path(k))==v for k,v in h['protected_sha256'].items())
checks['refs']=git('rev-parse','HEAD')==h['refs']['head'] and git('rev-parse','master')==h['refs']['master'] and git('branch','--show-current')==h['refs']['branch'] and git('ls-remote','origin','refs/heads/codex/simplex-core-architecture','refs/heads/master')==h['refs']['remote']
checks['no_actual_source_changes']=not git('diff','HEAD','--name-only','--','src','test','Project.toml','.github')
checks['empty_index']=not git('diff','--cached','--name-only')
names=json.loads((G/'publication-names.json').read_text())
tracked=set(git('diff','HEAD','--name-only').splitlines());unknown=set(git('ls-files','--others','--exclude-standard').splitlines())-{'Manifest.toml','LocalPreferences.toml'}
expected=set(names)-{str((G/'closure.json').relative_to(R)),str((G/'publication.json').relative_to(R))}
checks['exact_preclosure_names']=tracked|unknown==expected
check=subprocess.run(['git','diff','--check'],cwd=R,text=True,capture_output=True)
checks['authored_diff_clean']=check.returncode==0 and not check.stdout and not check.stderr
for n in sorted(expected):bind(R/n)
o={'all_passed':all(checks.values()),'checks':checks,'sha256':bindings,'host':{'time':time.time(),'boot_id':h['boot_id'],'groups':sorted(groups),'matches':matches},'continuation_map':{k:str(v.relative_to(R)) for k,v in mapping.items()},'scope':'MA-G diagnostic only; old evidence never rerun. Original false analysis preserved, supplement required. No Julia or production edit.'}
with (G/'closure.json').open('x') as f:json.dump(o,f,indent=2);f.write('\n')
print(json.dumps({'all_passed':o['all_passed'],'checks':checks,'bindings':len(bindings)},indent=2))
if not o['all_passed']:raise SystemExit(1)
