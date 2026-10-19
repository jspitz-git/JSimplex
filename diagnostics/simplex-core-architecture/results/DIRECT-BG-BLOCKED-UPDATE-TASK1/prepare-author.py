from pathlib import Path
import json,hashlib
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');C=R/'diagnostics/direct-bg-blocked-update/reproduce';Q=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-TASK1'
for name in ['panel.jl','panel-tests.jl']:
 with (Q/(name+'.before-author-fix')).open('xb') as f:f.write((C/name).read_bytes())
p=C/'panel.jl';t=p.read_text();t=t.replace('    J._invalidate_sparse_upper!(inner,r)\n    inner.row_columns_ready = false\n    for i in 1:h','    J._invalidate_sparse_upper!(inner,r)\n    inner.row_columns_ready = false\n    try\n      for i in 1:h').replace('    end\n    try\n        for j in 1:w\n            pos=', '      end\n        for j in 1:w\n            pos=')
t=t.replace('        inner.row_columns_ready=true\n    finally','        inner.row_columns_ready=true\n    catch\n        inner.row_cache.upper_prefix_candidate=false\n        inner.row_cache.upper_prefix_safe=false\n        rethrow()\n    finally')
p.write_text(t)
p=C/'panel-tests.jl';t=p.read_text();t=t.replace('A=denseband(96);r=3;b=8;f=carrier(A;', 'A=denseband(96);r=3;b=8;A[r,r-1]=0.0;f=carrier(A;')
t=t.replace('f=carrier(denseband(96));ws=prepared(f,33,8);saved=snapshot(f)', 'A=denseband(96);A[33,32]=0.0;f=carrier(A);ws=prepared(f,33,8);saved=snapshot(f)')
t=t.replace('f=carrier(denseband(96);reverse_rows=true);ws=prepared(f,3,8);before=unpack(f)', 'A=denseband(96);A[3,2]=0.0;f=carrier(A;reverse_rows=true);ws=prepared(f,3,8);before=unpack(f)')
t=t.replace('        @test ws.counts.values[20]==9*94 # row-capacity prepass', '''        @test ws.counts.values[20]==9*94 # row-capacity prepass
        @test ws.owner===nothing && ws.phase==0x00
        @test all(iszero(before[i,j]) for i in 3:11 for j in 1:2)
        # Repeated adversarial support proposals always refuse before allocating.
        for r in (17,25,33)
            A=denseband(96);A[r,r-1]=0.0;f=carrier(A);saved=snapshot(f)
            ws=prepared(f,r,8)
            for j in 1:ws.width
                ws.present[j,1]=false;ws.values[j,1]=0.0
            end
            ws.phase=0x02
            d=K._bgb_commit!(f,ws,K._bgb_decision(ws,true,:ok,true))
            @test d.reason==:store_budget
            @test ws.counts.values[12]==0 && ws.counts.values[13]==0
            @test snapshot(f)==saved && ws.owner===nothing
        end
        # Four-step internal panel boundary; width admission remains independent.
        ws=prepared(carrier(denseband(64)),1,4)
        @test K._bgb_apply!(ws,1,4,64).accepted''')
p.write_text(t)
(Q/'AUTHOR-NOTES.md').write_text('''# Task1 author rulings and preparation record

User authorizes offline Task1 implementation/test text, not Julia. Tests were written before panel.jl; original tests-first bytes and initial author versions are preserved. No RED/GREEN execution or runtime pass is claimed. New Python text/hash checks are not a Julia parser or a mathematical simulation.

Task1 exports standalone helpers. Task2 must retain original prepare/begin/incidence/spike/column rotation and scalar suffix, latch first rejection for rest of update, preserve the two prepared RHS owners and append chronological active steps once. Task1 never starts a solver/factorization or appends history. Zero-operation step slots must be skipped on final history append; b scratch slots are bounded rather than a growing ledger. Whole-update busy/rollback/copy/refactor tests belong to Task2.

The workspace temporarily binds the upper-vector owner to prevent committing into a different factor. It releases that reference on commit/rejection. On a gather/exception failure Task2 must discard the workspace; no independent copy of source arrays is retained. A scalar source mutation between gather/commit is forbidden by the Task2 exclusive-update contract, not detected by an O(nnz) rehash.

A source review caught fixture-only mistakes before any Julia execution: missing LinearAlgebra.I import, immutable structural carrier, and an uneliminated subdiagonal in earlier columns when preparing r>1. These have separate preserved originals. Reservation/writeback exceptions now clear eligibility and release the workspace through the same try/finally. No plan/gate relaxation.

No baseline Julia setup/test is run because the explicit no-Julia request supersedes generic skill setup/TDD execution. Future admission must execute these tests before runtime acceptance. Existing linked diagnostic worktree reused, master/source/test/env/CI/global continuation untouched. No production-cost finding is inferred from source counts alone.
''')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=['src/triangular_factorization.jl','src/triangular_indices.jl','src/bartels_golub_rows.jl','src/triangular_rows.jl','src/hypersparse_updates.jl']
j={'scope':'Intentional new isolated algorithm; NOT a whole-source inverse','dependencies':{x:sha(R/x) for x in source},'mapping':{
'PackedUpperColumn/UpperRowIndices/UpperRowOrder':'Imported actual types; fresh indices map logical row via existing order.order; no global permutation mutation.',
'_pivot_magnitude and original BG loop':'Strict comparison/division/zero guard retained; new FMA and private sequential panel; zero diagonal rejected before original unrestricted pure-lookahead.',
'_set_upper_value_at!':'Replaced by bounded final support commit. Exact zero canonicalizes absent +0. Whole-column replacement uses two exact-length arrays.',
'_ensure_bartels_golub_incidence!':'Only h rows cleared/rebuilt, one ascending stable-ID pass; row capacity prepass counts separately.',
'_begin_upper_update!/_finish_upper_update!':'Task2 boundary responsibility; kernel commit calls original invalidation before mutation and never finish.',
'BartelsGolubStep':'Eight original-type scratch slots; Task2 appends only nonidentity steps after successful writeback.',
'copy/refactor/prepared/scalar suffix':'Not implemented Task1; explicit Task2 consumer contract, no qualification claim.'}}
(C/'source-map.json').write_text(json.dumps(j,indent=2)+'\n')
print('Task1 author corrections and source map saved; no Julia')
