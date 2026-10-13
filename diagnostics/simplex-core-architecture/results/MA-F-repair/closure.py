"""One-shot closure: qualified correctness, failed overall benefit, no promotion."""
from pathlib import Path
import hashlib,json,subprocess,time
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-F-repair';F=D.parent/'MA-F';E=D.parent/'MA-E';prefix=str(D.relative_to(R))+'/'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
def save(n,v):
 with (D/n).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
review=read(D/'result-review.json');post=read(D/'postprocess.json');summary=read(D/'summary.json');host=read(D/'host.json');names=read(D/'publication-names.json');checks={}
checks['result_review_accepted']=review['accepted'] is True and review['unresolved_findings']==[]
checks['all_review_bindings']=all(sha(p)==v for p,v in review['sha256'].items())
checks['all_admission_bindings']=all(sha(p)==v for p,v in read(D/'review-final.json')['sha256'].items())
checks['postcheck_PASS_and_raw_bound']=post['all_passed'] is True and all(post['checks'].values()) and all(sha(p)==v for p,v in post['sha256'].items())
checks['numerical_correctness_not_promotion']=post['numerical_all_passed'] is True and post['benefit_accepted'] is False and post['process_count']==post['accepted_stage_count']==22 and summary['target_pass']==summary['target_cases']==6 and len(summary['control_fail'])==6 and summary['control_cases']==32 and summary['nonzero_steady_compile']==0 and summary['nonzero_steady_GC']==5
checks['summary_raw_bindings']=all(sha(p)==v for p,v in summary['raw_sha256'].items())
mapping={str(R/'diagnostics/simplex-core-architecture/STATUS.md'):D/'STATUS.md.before-MA-F-repair',str(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'):D/'roadmap.md.before-MA-F-repair'}
for n in ('closure.json','publication.json','review.json'):
 checks['MA_F_'+n+'_mapped_unchanged']=all(sha(mapping.get(str(R/p),R/p))==v for p,v in read(F/n)['sha256'].items())
checks['protected_files_unchanged']=all(sha(p)==v for p,v in host['protected_sha256'].items())
checks['refs_unchanged']=git('rev-parse','HEAD')==host['refs']['head'] and git('rev-parse','master')==host['refs']['master'] and subprocess.check_output(['git','-C','/home/jspitz/JSimplex.jl','rev-parse','HEAD'],text=True).strip()==host['refs']['master']
checks['actual_src_test_Project_CI_unchanged']=not git('diff','HEAD','--','src','test','Project.toml','.github')
checks['initial_index_empty']=not git('diff','--cached','--name-only')
groups=post['host']['groups'];matches=[];boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
for p in Path('/proc').glob('[0-9]*'):
 try:
  s=(p/'stat').read_text();f=s[s.rfind(')')+2:].split()
  if int(f[2]) in groups or int(f[3]) in groups or (p/'comm').read_text().strip().lower().startswith('julia'):matches.append(dict(pid=p.name,pgid=int(f[2]),sid=int(f[3]),start_ticks=int(f[19]),boot_id=boot,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except FileNotFoundError:pass
checks['fresh90groups_ANDsessions_noJulia']=len(groups)==90 and boot==post['host']['boot_id'] and not matches
# Preserve exact copied historical source whitespace; never rewrite pinned content.
warnings=[];bad=[]
for n in names:
 if n in [prefix+x for x in ('closure.json','publication.json','whitespace.json')]:continue
 p=R/n;r=subprocess.run(['git','diff','--no-index','--check','--','/dev/null',str(p)],capture_output=True,text=True)
 if r.stderr or r.returncode not in (0,1):bad.append(n)
 if r.stdout:
  source=E/p.name
  exact=p.parent==D and source.exists() and sha(p)==sha(source)
  warnings.append(dict(path=n,source=str(source) if exact else None,sha256=sha(p),diagnostics=r.stdout.replace(str(R)+'/', '')))
  if not exact:bad.append(n)
save('whitespace.json',dict(all_passed=not bad,warnings=warnings,invalid=bad))
checks['authored_whitespace_clean_verbatim_copies_preserved']=not bad
checks['exact_names_complete_before_outputs']=set(str(p.relative_to(R)) for p in D.rglob('*') if p.is_file())=={n for n in names if n.startswith(prefix)}-{prefix+'closure.json',prefix+'publication.json'}
inputs=[n for n in names if n not in (prefix+'closure.json',prefix+'publication.json')]
save('closure.json',dict(all_passed=all(checks.values()),checks=checks,sha256={n:sha(R/n) for n in inputs},host=dict(time=time.time(),boot_id=boot,groups=groups,matches=matches),continuation_map={p:str(v) for p,v in mapping.items()},scope='Correctness qualified; overall performance admission NOT ACCEPTED. No production integration.'))
print(json.dumps(checks,indent=2));print('preserved whitespace',len(warnings))
if not all(checks.values()):raise SystemExit('closure failed before staging')
