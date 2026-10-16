"""Exclusive added test coverage, preserving initial test text and bindings."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[4];E=Path(__file__).resolve().parent;C=R/'diagnostics/direct-bg-block-upper/reproduce';p=C/'block-bg-tests.jl';before=p.read_bytes();s=before.decode()
old='''        @test calls[]==0
        # Force a storage failure after mutation began.'''
new='''        @test calls[]==0
        narrow=SparseMatrixCSC{Float64,Int32}(3,3,Int32[1,2,3,4],Int32[1,2,3],[1.,1.,1.])
        @test_throws ArgumentError J._block_bg_with_exporter(narrow,Val(:native),J._NATIVE_PIVOT_ONE,J._export_basis_lu;factorize)
        @test calls[]==0
        for (A,q) in ((spdiagm(0=>ones(3)),[1,1,3]),
                      (SparseMatrixCSC(3,3,[1,3,3,3],[2,1],[1.,1.]),[1,2,3]))
            exporter=x->J.BasisLUExport(spdiagm(0=>ones(3)),copy(A),[1,2,3],copy(q),ones(3),false)
            @test_throws ArgumentError J._block_bg_with_exporter(B,Val(:native),J._NATIVE_PIVOT_ONE,exporter;normalize=false)
        end
        # The synthetic handle limit fails at the first need for a new block;
        # column removal has happened, so only structure/cache/history persist.
        r,d=controlled_pair(spdiagm(0=>ones(33)),collect(1:33))
        @test_throws OverflowError J._block_bg_replace!(d,ones(33),1,0.0;limit=31)
        @test _check_block_upper(d.upper) && isempty(d.updates) && !d.row_cache.upper_prefix_safe
        J.refactorize!(d,spdiagm(0=>ones(33)))
        # Force a storage failure after mutation began.'''
if s.count(old)!=1:raise RuntimeError('Failure test marker')
s=s.replace(old,new)
old2='''            @test_throws ArgumentError op(f.work,f,ones(3))
        end
    end
end

function run_block_bg_tests()'''
new2='''            @test_throws ArgumentError op(f.work,f,ones(3))
            scratch=f.upper.scratch_value
            GC.@preserve scratch begin
                overlap=unsafe_wrap(Vector{Float64},pointer(scratch,2),3;own=false)
                @test_throws ArgumentError op(overlap,f,ones(3))
            end
        end
    end
end

function run_block_bg_tests()'''
if s.count(old2)!=1:raise RuntimeError('Scratch test marker')
s=s.replace(old2,new2)
with (E/'block-bg-tests.jl.before-coverage-amendment').open('xb') as f:f.write(before)
p.write_text(s)
record=dict(scope='Source-only test strengthening, no Julia; old tests-first/reviewer-v1 hashes map to before-coverage-amendment',before_sha256=hashlib.sha256(before).hexdigest(),after_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),checks=dict(unsupported_CSC_index_sentinel=True,malformed_export_q_and_rows=True,update_handle_limit=True,partial_new_scratch_alias=True),self_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
with (E/'test-amendment.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print('4source-only test coverage additions; original preserved')
