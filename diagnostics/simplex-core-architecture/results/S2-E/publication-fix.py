from pathlib import Path
import json,hashlib,subprocess,tempfile
R=Path.cwd();E=R/'diagnostics/simplex-core-architecture/results/S2-E'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
old=(E/'publication-reviewed.py').read_text();before='if run.returncode or run.stdout or run.stderr:';after='if run.returncode not in (0,1) or run.stdout or run.stderr:'
if old.count(before)!=1 or old.count("E/'publication.json'")!=1:raise SystemExit('selector mismatch')
new=old.replace(before,after).replace("E/'publication.json'","E/'publication-final.json'")
with (E/'publication-final.py').open('x') as f:f.write(new)
results={}
with tempfile.TemporaryDirectory(prefix='s2e-whitespace-') as td:
 for n,s in [('clean.txt','clean\n'),('bad.txt','bad \n')]:
  p=Path(td)/n;p.write_text(s);r=subprocess.run(['git','diff','--no-index','--check','/dev/null',str(p)],capture_output=True,text=True);results[n]={'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'old_reject':bool(r.returncode or r.stdout or r.stderr),'new_reject':bool(r.returncode not in (0,1) or r.stdout or r.stderr)}
a=json.loads((E/'publication.json').read_text());c=results['clean.txt'];b=results['bad.txt']
checks={'original5of6_false_preserved':a['all_passed'] is False and sum(a['checks'].values())==5 and a['checks']['authored_whitespace_clean'] is False,'original_all_rows_status1_empty_diagnostics':bool(a['authored_whitespace']) and all(v['returncode']==1 and not v['stdout'] and not v['stderr'] for v in a['authored_whitespace']),'RED_clean_file_rejected_by_old_status_rule':c['returncode']==1 and not c['stdout'] and not c['stderr'] and c['old_reject'],'GREEN_clean_file_accepted':not c['new_reject'],'actual_trailing_whitespace_still_rejected':b['new_reject'] and 'trailing whitespace' in b['stdout'],'change_only_status_interpretation_and_new_output':new.replace(after,before).replace("E/'publication-final.json'","E/'publication.json'")==old,'no_staging_occurred':not subprocess.check_output(['git','diff','--cached','--name-only'],text=True).strip()}
paths=[E/n for n in ['publication.json','publication-reviewed.py','publication-final.py','publication-fix.py','closure-final.json']]
o={'checks':checks,'all_passed':all(checks.values()),'synthetic':results,'sha256':{str(p):sha(p) for p in paths},'explanation':'git diff --no-index returns1 for a clean nonempty file differing from /dev/null. No whitespace diagnostics were emitted. Accept0/1 only when stdout/stderr empty; actual whitespace still rejects. Original false publication preserved before staging/commit/push. No old script or numerical rerun.'}
with (E/'publication-fix.json').open('x') as f:json.dump(o,f,indent=2);f.write('\n')
print(json.dumps({'checks':checks,'synthetic':results}))
if not o['all_passed']:raise SystemExit(1)
