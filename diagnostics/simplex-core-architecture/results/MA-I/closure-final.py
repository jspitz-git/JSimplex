from pathlib import Path
import hashlib,json,subprocess,time
D=Path(__file__).resolve().parent;R=D.parents[3];H=D.parent/'MA-H';checks={};bindings={}
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(n):return json.loads((D/n).read_text())
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
def validmap(d):return bool(d['sha256']) and all(sha(Path(k) if Path(k).is_absolute() else R/k)==v for k,v in d['sha256'].items())
for n in ['verification.json','context-supplement.json','postprocess.json','continuation.json']:
 d=read(n);checks[n+'_PASS']=d['all_passed'] is True;checks[n+'_bindings']=validmap(d)
for n in ['review-final.json','result-review.json']:
 d=read(n);checks[n+'_accepted']=d.get('accepted') is True and d.get('unresolved_findings')==[];checks[n+'_bindings']=validmap(d)
pins=read('admission-pins-reviewed.json');required=read('required-paths-reviewed.json');checks['all1210pins']=len(pins['inventory'])==1210 and set(pins['files'])==set(pins['inventory']) and set(required)<=set(pins['inventory']) and all(sha(k)==v['sha256'] and str(Path(k).resolve())==v['resolved'] for k,v in pins['inventory'].items()) and all(pins['inventory'][k]['sha256']==v for k,v in required.items())
s=read('summary.json');post=read('postprocess.json');checks['numerical_complete']=post['numerical_all_passed'] is True and post['process_count']==post['accepted_stage_count']==22 and s['qualification_assertions']==[647,0,0,0] and s['red_counts']==[0,2,0,0] and s['qualification_rows']==432
checks['rejection_preserved']=post['benefit_accepted'] is False and s['target_pass']==s['target_cases']==6 and s['control_cases']==32 and len(s['control_fail'])==8
checks['all_samples_retained']=s['steady_windows']==1920 and s['nonzero_steady_compile']==0 and s['nonzero_steady_GC']==3
checks['original_false_preserved']=read('additional-tests.json')['all_passed'] is False and sum(read('additional-tests.json')['checks'].values())==26
status=R/'diagnostics/simplex-core-architecture/STATUS.md';road=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md';mapping={str(status):D/'STATUS.md.before-MA-I',str(road):D/'roadmap.md.before-MA-I'}
for n in ['closure.json','publication.json','review.json']:
 d=json.loads((H/n).read_text());ok=True;used=set()
 for k,v in d['sha256'].items():
  p=Path(k) if Path(k).is_absolute() else R/k
  if str(p) in mapping:used.add(str(p));p=mapping[str(p)]
  ok=ok and sha(p)==v
 checks['H_'+n]=ok and used==set(mapping)
h=read('host.json');groups=set(post['host']['groups']);matches=[]
for p in Path('/proc').glob('[0-9]*'):
 try:
  t=(p/'stat').read_text();v=t[t.rfind(')')+2:].split();comm=(p/'comm').read_text().strip()
  if int(v[2]) in groups or int(v[3]) in groups or comm.lower().startswith('julia'):matches.append(dict(pid=p.name,pgid=int(v[2]),sid=int(v[3]),start_ticks=int(v[19]),command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except FileNotFoundError:pass
checks['fresh134groups_ANDsessions_noJulia']=len(groups)==134 and not matches and Path('/proc/sys/kernel/random/boot_id').read_text().strip()==h['boot_id']
checks['protected']=all(sha(k)==v for k,v in h['protected_sha256'].items())
checks['refs']=git('rev-parse','HEAD')==h['refs']['head'] and git('rev-parse','master')==h['refs']['master'] and git('ls-remote','origin','refs/heads/codex/simplex-core-architecture','refs/heads/master')==h['refs']['remote']
checks['actual_src_test_Project_CI_unchanged']=not git('diff','HEAD','--name-only','--','src','test','Project.toml','.github')
checks['empty_index']=not git('diff','--cached','--name-only')
names=read('publication-names-final.json');expected=set(names)-{str((D/n).relative_to(R)) for n in ['closure.json','publication.json']};actual=set(git('diff','HEAD','--name-only').splitlines())|(set(git('ls-files','--others','--exclude-standard').splitlines())-{'Manifest.toml','LocalPreferences.toml'})
checks['exact_preclosure_names']=actual==expected
w=read('whitespace.json');checks['verbatim_whitespace_only']=w['all_passed'] is True and validmap(w) and all(sha(v['path'])==v['sha256'] for v in w['origins'].values())
for n in sorted(expected):bindings[n]=sha(R/n)
with (D/'closure.json').open('x') as f:json.dump(dict(all_passed=all(checks.values()),checks=checks,sha256=bindings,continuation_map={k:str(v.relative_to(R)) for k,v in mapping.items()},host=dict(time=time.time(),boot_id=h['boot_id'],groups=sorted(groups),matches=matches),scope='Diagnostic closure accepts correctness and explicit failed promotion gates; no production integration. All prior raw/failures preserved.'),f,indent=2);f.write('\n')
print(json.dumps(dict(all_passed=all(checks.values()),checks=checks,bindings=len(bindings)),indent=2))
if not all(checks.values()):raise SystemExit(1)
