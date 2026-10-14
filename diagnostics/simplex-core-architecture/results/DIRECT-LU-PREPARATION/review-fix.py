from pathlib import Path
import hashlib,json
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl')
D=R/'diagnostics/simplex-core-architecture/results/DIRECT-LU-PREPARATION'
p=R/'diagnostics/direct-lu-markowitz/reproduce/correctness.jl'
old=p.read_text()
if not (D/'review-initial.md').exists():raise SystemExit('Initial review must be saved first')
if p.read_bytes()!=(D/'initial/correctness.jl').read_bytes():raise SystemExit('Initial tests changed')
addition='''function test_scale_selection()
    @testset "Actual orientation helper selects multiply, divide or neither" begin
        L,U = sparse([1.0 0;0.25 1.0]),sparse([-2.0 1;0.0 4.0])
        p,q,s = [2,1],[2,1],[2.0,0.5]
        parts = JDL.BasisLUExport(L,U,p,q,s,false)
        frozen = _dl_export_snapshot(parts)
        for divide in (false,true)
            scale = divide ? 1.0 ./ s : s
            B = zeros(2,2)
            B[p,q] = Matrix(L*U)./reshape(scale[p],2,1)
            before = copy(B)
            F = lu(B)
            observed = JDL._hh_scale_mode(F,L,U,p,q,s,zeros(2),zeros(2))
            @test observed === divide
            @test isequal(B,before)
            @test isequal(_dl_export_snapshot(parts),frozen)
        end
        # The real helper solves with an ordinary dense identity factor. No
        # solve mock or existing method is replaced. The first scale vector
        # matches neither convention, the second matches both within its bound.
        I2 = spdiagm(0=>ones(2)); F = lu(Matrix(I2))
        for scaling in ([2.0,0.5],[nextfloat(1.0),nextfloat(1.0)])
            snapshot = _dl_matrix_snapshot(I2); before = copy(scaling)
            @test isnothing(JDL._hh_scale_mode(F,I2,I2,[1,2],[1,2],scaling,zeros(2),zeros(2)))
            @test isequal(_dl_matrix_snapshot(I2),snapshot)
            @test isequal(scaling,before)
        end
    end
end

'''
anchor='function test_normalization_and_scaling()\n'
if old.count(anchor)!=1:raise SystemExit('Unique insertion missing')
new=old.replace(anchor,addition+anchor).replace('        test_normalization_and_scaling()','        test_scale_selection()\n        test_normalization_and_scaling()')
p.write_text(new)
checks={'initial_missing_direct_helper_call':'JDL._hh_scale_mode(' not in old,'new_helper_calls_present':new.count('JDL._hh_scale_mode(')==2,'both_orientation_loop':'for divide in (false,true)' in addition,'both_ambiguity_cases':'[nextfloat(1.0),nextfloat(1.0)]' in addition,'runner_calls_helper_group':'        test_scale_selection()' in new,'inverse_exact':new.replace(addition,'').replace('        test_scale_selection()\n','')==old}
with (D/'review-fix.json').open('x') as f:json.dump({'all_passed':all(checks.values()),'checks':checks,'scope':'Offline text assertions, NOT executed Julia RED/GREEN; 3 additional dense LU constructions and 4 helper entries prospective','before_sha256':hashlib.sha256(old.encode()).hexdigest(),'after_sha256':hashlib.sha256(new.encode()).hexdigest()},f,indent=2);f.write('\n')
print(checks)
if not all(checks.values()):raise SystemExit(1)
