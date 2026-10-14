from pathlib import Path
import hashlib,json,subprocess,time
R=Path.cwd(); E=R/'diagnostics/simplex-core-architecture/results/MA-R'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],text=True).strip()
def require(ok,msg):
 if not ok:raise SystemExit(msg)
def save(p,obj):
 with p.open('x') as f:json.dump(obj,f,indent=2);f.write('\n')
h=json.loads((E/'host.json').read_text()); groups=set(h['groups']); matches=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:
  fields=(p/'stat').read_text().rsplit(')',1)[1].split(); pgid,sid=int(fields[2]),int(fields[3]); exe=(p/'exe').resolve().name
  if pgid in groups or sid in groups or exe.startswith('julia'):matches.append(dict(pid=int(p.name),pgid=pgid,sid=sid,start_ticks=int(fields[19]),exe=exe,command=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')))
 except (OSError,ValueError,IndexError):pass
require(not matches and len(groups)==158,'Process gate')
require(git('rev-parse','HEAD')==h['refs']['head'] and git('rev-parse','master')==h['refs']['master'] and git('branch','--show-current')==h['refs']['branch'],'Refs drift')
require(git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture')==h['refs']['remote'],'Remote drift')
save(E/'completion-host.json',dict(time=time.time(),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),groups=sorted(groups),matches=matches,refs=h['refs']))
review=json.loads((E/'review-final.json').read_text())
require(review['accepted'] is True and review['findings']==[],'Review not accepted')
require(len(review['sha256'])==58 and all(sha(p)==s for p,s in review['sha256'].items()),'Final review58 drift')
report=R/'diagnostics/simplex-core-architecture/MA-DENSELU-BIGFLOAT-PREPARATION.md'
status=R/'diagnostics/simplex-core-architecture/STATUS.md'
road=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
paths={report:'report.before-completion',status:'STATUS.md.before-completion',road:'roadmap.md.before-completion',E/'plan.md':'plan.md.before-completion',E/'ledger.md':'ledger.md.before-completion'}
mapping={}
for p,n in paths.items():
 q=E/n
 with q.open('xb') as f:f.write(p.read_bytes())
 mapping[str(p)]={'preserved':str(q),'sha256':sha(q)}
save(E/'completion-map.json',{'mapping':mapping,'scope':'Exact expected hashes select preserved review/fix versions; older review-fix and MA-Q continuation maps remain intact.'})
def replace(p,old,new):
 t=p.read_text();require(t.count(old)==1,'Replacement not unique: '+str(p)+' '+old);p.write_text(t.replace(old,new))
replace(report,'Status: offline preparation complete; independent review pending.','Status: offline preparation complete and independently accepted for MA-S admission preparation.')
replace(report,'review and input bytes are preserved. Final amendment review is pending.','review and input bytes are preserved. The final independent gpt-6-astra review\naccepted the amendment with no unresolved findings and no unnecessary candidate\nwork or retained memory. See [final review](results/MA-R/review-final.md).\nThe six offline amendment checks passed; the final review binds58artifacts.\nCompletion wording preserves all prior bound bytes in completion-map.json.')
replace(status,'MA-R isolated DenseLU BigFloat candidate/reference/tests are prepared offline;\nindependent review is pending.','MA-R isolated DenseLU BigFloat candidate/reference/tests are independently accepted\nfor MA-S admission preparation. One cancellation-fixture coverage finding was fixed\noffline; final gpt-6-astra review has no unresolved findings.')
replace(status,'After accepted independent review, next MA-S prepares its own concrete short-run','Next MA-S prepares its own concrete short-run')
replace(road,'MA environment prepared; independent review pending. Seven exact source inverses,','MA environment prepared and independently accepted. One cancellation-fixture P2\nwas resolved by a single offline amendment; final gpt-6-astra review has no\nunresolved findings or unnecessary candidate work/memory. Seven exact source inverses,')
replace(E/'plan.md','Status: prepared, independent review pending. All Julia files UNEXECUTED.','Status: independently accepted for MA-S admission preparation. All Julia files UNEXECUTED.')
replace(E/'plan.md','Julia runtime result; final review of the amendment is pending.','Julia runtime result. Final independent review accepted this amendment without\nunresolved findings; see review-final.md/json. All prior bindings are preserved\nthrough review-fix-map.json and completion-map.json.')
replace(E/'ledger.md','Task1 MA-R in progress.','Task1 MA-R complete and independently accepted.')
replace(E/'ledger.md','Original review is superseded for admission pending separate final amendment review.','Original review is superseded by the accepted final amendment review (58 bindings,\nno unresolved findings, no unnecessary candidate work or retained memory).\nSource15/38 and amendment6checks remain source-only; no Julia executed.\nTask2 MA-S remains pending: its own guarded admission preparation is required.\nCompletion text preserves exact prior bytes through completion-map.json.')
maps=[json.loads((E/'review-fix-map.json').read_text())['mapping'],mapping]
def resolves(p,s):
 return sha(p)==s or any(p in m and m[p]['sha256']==s and sha(m[p]['preserved'])==s for m in maps)
checks={n:all(resolves(p,s) for p,s in json.loads((E/n).read_text())['sha256'].items()) for n in ['source-check.json','review.json','review-amendment.json','review-fix.json','review-final.json']}
checks['five_completion_copies']=all(sha(v['preserved'])==v['sha256'] for v in mapping.values())
checks['review_accepted']=review['accepted'] is True and review['findings']==[]
checks['old_six_continuation_bindings']=all(sha(x['preserved'])==x['sha256'] for x in json.loads((E/'continuation-map.json').read_text())['old_bindings'])
obj={'checks':checks,'all_passed':all(checks.values()),'sha256':{str(p):sha(p) for p in [*paths,E/'completion-map.json',E/'completion-host.json',E/'complete-step.py']}}
save(E/'completion-check.json',obj)
print(json.dumps({'checks':checks,'bindings':len(obj['sha256'])}))
require(obj['all_passed'],'Completion failed')
