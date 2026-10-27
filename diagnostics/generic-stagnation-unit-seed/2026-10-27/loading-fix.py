from pathlib import Path
import sys,json,shutil,ast
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-stagnation-unit-seed/2026-10-27');sys.path.insert(0,str(D));import common_reviewed as c
p=c.read('GREEN-run/output/process.json');extra=[p[k][v] for k in ['runner','child'] for v in ['pgid','sid']];c.put('GREEN-run/failure-host.json',c.host(set(c.read('GREEN-run/author-host.json')['groups'])|set(extra)));c.unchanged()
log=(D/'GREEN-run/output/run.log').read_text();c.need(p['returncode']==1 and p['pins_unchanged'] and 'UndefVarError: `SimplexWorkspace` not defined' in log and 'INCLUDING ' not in log,'exact pre-test loader failure')
c.put('GREEN-run/failure-checks.json',dict(accepted=False,reason='new concrete method defined before SimplexWorkspace exists',numerical_tests_started=False,Julia_attempt_consumed=True,bindings={str(D/'GREEN-run'/n):c.sha(D/'GREEN-run'/n) for n in ['output/process.json','output/run.log','supervisor.json','failure-host.json']}))
changes=c.read('changes.json');a=changes[0];c.need(a['variant']=='A' and a['new'].startswith(a['old']),'appended A method');method=a['new'][len(a['old']):]
shutil.copytree(D/'GREEN',D/'GREEN-2');(D/'GREEN-2/src/simplex_stalling.jl').write_bytes((D/'baseline/src/simplex_stalling.jl').read_bytes());q=D/'GREEN-2/src/simplex.jl';old=q.read_text();q.write_text(old+method)
corrected=[dict(variant='A',file='src/simplex.jl',old=old,new=old+method),*changes[1:]];c.put('changes-reviewed.json',corrected)
checks={}
for label,source,wanted in [('RED',D/'GREEN',False),('GREEN',D/'GREEN-2',True)]:
 includes=[l.split('"')[1] for l in (source/'src/JSimplex.jl').read_text().splitlines() if l.startswith('include("')]
 typefile=next(n for n in includes if 'mutable struct SimplexWorkspace{' in (source/'src'/n).read_text());methodfile=next(n for n in includes if method.strip() in (source/'src'/n).read_text());okay=includes.index(typefile)<=includes.index(methodfile)
 if typefile==methodfile:okay=(source/'src'/typefile).read_text().index('mutable struct SimplexWorkspace{')<(source/'src'/typefile).read_text().index(method.strip())
 c.need(okay is wanted,'loader order '+label);checks[label]=dict(type_file=typefile,method_file=methodfile,type_available_at_method=okay)
checks['byte_exact_method_move']=True;checks['original_stalling_restored']=(D/'GREEN-2/src/simplex_stalling.jl').read_bytes()==(D/'baseline/src/simplex_stalling.jl').read_bytes();c.need(checks['original_stalling_restored'],'stalling unchanged')
names=sorted(['src/simplex.jl','src/primal_simplex.jl','test/generic_stagnation_unit_seed_tests.jl','test/runtests.jl'])
for n in names:
 if n.startswith('src/'):
  s=(D/'GREEN-2'/n).read_text()
  for ch in reversed(corrected):
   if ch['file']==n:c.need(s.count(ch['new'])==1,'one inverse');s=s.replace(ch['new'],ch['old'])
  c.need(s==(D/'baseline'/n).read_text(),'exact inverse '+n)
c.put('source-inverse-reviewed.json',dict(accepted=True,names=names,candidate_sha256={n:c.sha(D/'GREEN-2'/n) for n in names},whole_stage={str(p.relative_to(D/'GREEN-2')):c.sha(p) for p in (D/'GREEN-2').rglob('*') if p.is_file()},production_baseline=c.TARGET,all_numerical_checks_retained=True,no_added_scans_solves_copies=True))
c.put('loading-fix-checks.json',dict(accepted=True,checks=checks,source_method_sha256=__import__('hashlib').sha256(method.encode()).hexdigest(),original_numerical_tests_unchanged=True))
(D/'LOADING-FIX.md').write_text('''# Concrete-workspace method loading-order correction

Original GREEN child exited1 after3.253s before any tests: simplex_stalling.jl is included before simplex.jl defines SimplexWorkspace. Private measurement namespaces were loaded after real JSimplex, so did not expose this production loading boundary. Preserve original accepted-prelaunch reviews as insufficient for this missed boundary and original run as REJECTED, no audit or numerical rerun on its output.

Move only the added concrete A method, byte-exact, from simplex_stalling.jl to the end of simplex.jl after the concrete type definition. Original stalling file restored byte-exact; B/C and every test/check/threshold/fixture unchanged. Fixed actual changed names remain four: simplex.jl,primal_simplex.jl,new ordinary test,runtests. No arithmetic/dispatch/owner change once loaded; no new scan/solve/copy/conversion/persistent cache. Source-derived loader-order REDfalse/GREENtrue proves the definition boundary; the fresh ordinary full GREEN will verify actual module load. New source-inverse-reviewed and GREEN-2stage preserve old source/stage/pins/reviews.
''')
for oldname,newname in [('commit-integrate-publish.py','commit-integrate-publish-reviewed.py'),('finalize.py','finalize-reviewed.py'),('closure.py','closure-reviewed.py')]:
 s=(D/oldname).read_text().replace("D/'GREEN'","D/'GREEN-2'").replace('GREEN-run','GREEN-2-run').replace('source-inverse.json','source-inverse-reviewed.json').replace('production-review.json','production-review-2.json').replace('publication-preparation-reviewed.json','publication-preparation-reviewed-2.json').replace('preparation-review.json','preparation-review-2.json')
 if oldname=='closure.py':
  s=s.replace("(D/'GREEN-2-run','pins.json')","(D/'GREEN-run','pins.json'),(D/'GREEN-2-run','pins.json')")
  s=s.replace("for phase in [D]:","for phase in [D,D/'GREEN-run']:")
  s=s.replace("private={'baseline','RED','GREEN'","private={'baseline','RED','GREEN','GREEN-2'")
 elif oldname=='finalize.py':
  s=s.replace('/GREEN/\\n','/GREEN/\\n/GREEN-2/\\n')
  s=s.replace('if Path(__file__).resolve()!=(D/\'finalize.py\').resolve():shutil.copyfile(__file__,D/\'finalize.py\')','if Path(__file__).resolve()!=(D/\'finalize-reviewed.py\').resolve():shutil.copyfile(__file__,D/\'finalize-reviewed.py\')')
  s=s.replace('Initial comparison104540PASS/19ERROR', 'Original GREEN rejected before tests: concrete method declared before SimplexWorkspace existed; separately reviewed byte-exact method relocation to simplex.jl after type definition, original stalling file restored, no candidate arithmetic/test changes. Original3.253s run and insufficient prelaunch reviews frozen.\n\nInitial comparison104540PASS/19ERROR')
 ast.parse(s);(D/newname).write_text(s)
s=(D/'diagnostic-publish.py').read_text().replace("private={'baseline','RED','GREEN'","private={'baseline','RED','GREEN','GREEN-2'");ast.parse(s);(D/'diagnostic-publish-reviewed.py').write_text(s)
shutil.copyfile(__file__,D/'loading-fix.py');print('exact method relocation prepared; unchanged numerics and tests; original GREEN frozen')
