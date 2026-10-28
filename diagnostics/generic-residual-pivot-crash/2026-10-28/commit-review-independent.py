from pathlib import Path
import json,hashlib,subprocess,importlib.util,os
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-residual-pivot-crash/2026-10-28');G=D/'GREEN';M=Path('/home/jspitz/JSimplex.jl');os.environ['GIT_OPTIONAL_LOCKS']='0'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(ok,m):
 if not ok:raise RuntimeError(m)
def git(a):return subprocess.check_output(['/usr/bin/git','-C',str(M),*a])
def gt(a):return git(a).decode().strip()
spec=importlib.util.spec_from_file_location('commit_review_common',D/'common_final.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c);c.unchanged()
co=read(D/'production-commit.json');st=read(D/'staged-tree.json');inv=read(D/'source-inverse.json');target=co['commit'];base=c.TARGET
need(target=='85f8275b85183f87fa8f33164cb0fbb5115f17ec','exact requested commit')
need(gt(['rev-list','--parents','-n','1',target]).split()==[target,base],'sole parent')
need(gt(['rev-parse',target+'^{tree}'])==co['tree']==st['tree'],'actual tree')
need(gt(['rev-parse',co['branch']])==target and co['branch']=='refs/heads/codex/generic-residual-pivot-crash','fresh branch target')
need(co['parent']==st['base']==inv['production_baseline']==base,'baseline refs')
names=gt(['diff-tree','--no-commit-id','--name-only','-r',target]).splitlines();need(names==co['names']==st['names']==inv['names'] and len(names)==5,'exact changed five names')
rawbase=git(['ls-tree','-rz','--full-tree',base]);rawnew=git(['ls-tree','-rz','--full-tree',target])
def entries(raw):
 out={}
 for x in raw.split(b'\0'):
  if not x:continue
  meta,path=x.split(b'\t',1);out[path.decode()]=meta.decode().split()
 return out
old=entries(rawbase);new=entries(rawnew)
need(set(new)==set(old)|{'test/generic_residual_pivot_crash_tests.jl'},'full committed tree membership')
need(sorted(k for k in new if old.get(k)!=new[k])==names,'no other committed change')
for n in names:
 need(new[n][0:2]==['100644','blob'],'expected regular mode '+n)
 need(new[n][2]==co['blobs'][n]==st['blobs'][n],'exact object '+n)
 need(git(['show',target+':'+n])==(G/n).read_bytes(),'exact committed bytes '+n)
 need(sha(G/n)==inv['candidate_sha256'][n]==st['sha256'][n],'exact reviewed bytes '+n)
for n,h in inv['whole_stage'].items():
 need(sha(G/n)==h,'whole staged tree '+n)
 if n in new:need(git(['show',target+':'+n])==(G/n).read_bytes(),'whole tracked stage committed '+n)
need({str(p.relative_to(G)) for p in G.rglob('*') if p.is_file()}==set(inv['whole_stage']),'whole stage membership')
for ch in read(D/'changes.json'):
 t=git(['show',target+':'+ch['file']]).decode();need(t.count(ch['new'])==1 and t.replace(ch['new'],ch['old'])==git(['show',base+':'+ch['file']]).decode(),'actual committed inverse '+ch['file'])
for p in [D/'production-review.json',D/'GREEN-run/result-review.json',D/'publication-preparation-reviewed.json']:
 rr=read(p);need(rr['accepted'] is True and rr['findings']==[],'review accepted '+str(p))
 for n,h in rr['bindings'].items():need(sha(n)==h,'review bound '+n)
green=read(D/'GREEN-run/result-review.json');need(green['passed']==green['total']==362111 and green['whole_files']==67 and green['required_MASTER_total']==362111,'accepted GREEN exact')
check=subprocess.run(['/usr/bin/git','-C',str(M),'diff-tree','--check',base,target],capture_output=True,text=True);need(check.returncode==0 and not check.stdout and not check.stderr,'actual committed whitespace')
protected=read(D/'protected-before.json')
for kind in ['files','indexes']:
 for n,h in protected[kind].items():need(sha(n)==h,'protected '+kind+' '+n)
need(co['real_indexes_unchanged'] is True,'author index claim corroborated')
need(not gt(['status','--porcelain=v1','--untracked-files=all','--',*names]),'current target paths clean')
extra=set()
for path in D.rglob('output/process.json'):
 p=read(path);extra.update(p[k][v] for k in ['runner','child'] for v in ['pgid','sid'])
h=c.host(extra);need(len(h['groups'])==665 and len(h['processes'])>10,'fullhost665')
refs={'master_HEAD':c.git(['rev-parse','HEAD']),'master':c.git(['rev-parse','master']),'origin_master':c.git(['rev-parse','origin/master']),'live_master':c.git(['ls-remote','origin','refs/heads/master']).split()[0],'diagnostics_HEAD':c.git(['rev-parse','HEAD'],c.R),'live_diagnostics':c.git(['ls-remote','origin','refs/heads/codex/simplex-core-architecture'],c.R).split()[0]}
need(all(refs[k]==base for k in ['master_HEAD','master','origin_master','live_master']) and refs['diagnostics_HEAD']==refs['live_diagnostics']==read(D/'host-before.json')['diagnostic_head'],'current refs')
e={'accepted':True,'commit':target,'parent':base,'tree':co['tree'],'branch':co['branch'],'changed_paths':names,'changed_tree_entries':{n:new[n] for n in names},'full_tree_entries':len(new),'baseline_tree_entries':len(old),'full_tree_sha256':hashlib.sha256(rawnew).hexdigest(),'baseline_full_tree_sha256':hashlib.sha256(rawbase).hexdigest(),'commit_object':git(['cat-file','-p',target]).decode(),'all_other_tree_entries_identical':True,'all_tracked_stage_files_match_commit':True,'protected_indexes_and_files_unchanged':True,'GREEN_total':362111,'GREEN_files':67,'host':h,'refs':refs}
Path('/tmp/rpc-commit-review-evidence.json').write_text(json.dumps(e,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:v for k,v in e.items() if k not in ['host','commit_object','changed_tree_entries']}));print(json.dumps({'host_time':h['time_utc'],'groups':len(h['groups']),'processes':len(h['processes']),'no_Julia':h['no_Julia'],'available_kib':h['available_kib'],'swap_kib':h['swap_used_kib']}))
