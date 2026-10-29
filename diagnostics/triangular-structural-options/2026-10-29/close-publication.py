from pathlib import Path
import json,hashlib,subprocess
W=Path('/home/jspitz/.codex/worktrees/native-quality-scans/JSimplex.jl');D=W/'diagnostics/triangular-structural-options/2026-10-29';B=W/'diagnostics/bg-local-rotation/2026-10-29'
p=D/'REPORT.md';(D/'REPORT.before-norm-clarification.md').write_bytes(p.read_bytes());p.write_text(p.read_text().replace('norm(B)*norm(x),norm(rhs)','norm_inf(B)*norm_inf(x),norm_inf(rhs)'))
(D/'REVIEW-FINAL.md').write_text('''# Final report review

Reviewer /root/long_chain_review accepted both reports, matching raw/source, allocationevents vsbytes distinction, existingcontroller/default20, allGCsamples and limits. Confirmed SS pre-rowunion32vs40; localBG endpointbelow64 exactly128/256blockupdates; identicalnonblockfinaldigests. Optional residualformula wording clarified to explicit infinitynorm, retaining norm1(B) fortranspose. No code/test/measurement change.

Original structural result-bindings.json REPORT.md SHA24f8fad6041da652fdfca7dc8787ba57b122d2cc9409cc8a907b498385d3dbb6 maps ONLY to REPORT.before-norm-clarification.md. Otherbindingsunchanged. BG report reviewedSHA8d468e1e71c3b7d579c5625b81a72bc46a1f7f3f22d6a2bfd8a77e0bed810c55 remains unchanged. Final report separately bound by closure/publication.\n''')
checks={}
for P,pinsname,expected in [(D,'pins.json',235),(B,'pins-2.json',113)]:
 a=json.loads((P/'analysis-1.json').read_text());pins=json.loads((P/pinsname).read_text());binding=json.loads((P/'result-bindings.json').read_text())
 checks[P.parent.name+'_audit']=a['accepted'] and len(a['checks'])==expected and all(a['checks'].values())
 checks[P.parent.name+'_pins']=all(hashlib.sha256(Path(k).read_bytes()).hexdigest()==v['sha256']for k,v in pins['inventory'].items())
 checks[P.parent.name+'_result_bindings']=all(hashlib.sha256((P/('REPORT.before-norm-clarification.md'if P==D and k=='REPORT.md'else k)).read_bytes()).hexdigest()==v for k,v in binding.items())
checks['production_worktree_diff_absent']=not subprocess.check_output(['git','diff','HEAD','--name-only','--','src','test','Project.toml','.github'],cwd=W)
checks['master_unchanged']=subprocess.check_output(['git','-C','/home/jspitz/JSimplex.jl','rev-parse','master'],text=True).strip()=='c0fa748ffa61ccb7c1caaf248c40324f60bc737b'
if not all(checks.values()):raise RuntimeError(checks)
with(D/'closure.json').open('x')as f:json.dump({'accepted':True,'checks':checks,'report_hashes':{str(p.relative_to(W)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [D/'REPORT.md',B/'REPORT.md']}},f,indent=2);f.write('\n')
subprocess.run(['git','add','--',str(D.relative_to(W)),str(B.relative_to(W))],cwd=W,check=True)
r=subprocess.run(['git','diff','--cached','--check'],cwd=W,capture_output=True,text=True)
with(D/'whitespace-initial.json').open('x')as f:json.dump({'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr},f,indent=2);f.write('\n')
print('CLOSURE',checks,'WHITESPACE',r.returncode,r.stdout[:4000],r.stderr)
