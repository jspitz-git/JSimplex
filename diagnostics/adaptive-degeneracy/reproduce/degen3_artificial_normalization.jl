# Test exact nonbasic artificial bounds at a saved Phase-I boundary.
using JSimplex,Serialization,LinearAlgebra
BLAS.set_num_threads(1)
function probe(prefix)
    phase=deserialize(prefix*"-phase.bin");map=deserialize(prefix*"-map.bin")
    original=deserialize(prefix*"-original.bin")
    report(label)=println(label," point=",JSimplex._legacy_primal_point_certified(phase),
        " quality=",JSimplex._recomputed_basis_reliable(phase)," sum=",sum(phase.primal[map.artificial_columns]),
        " maxart=",maximum(abs,phase.primal[map.artificial_columns]),
        " basic=",[(j,phase.primal[j]) for j in phase.basis.basic_indices if map.phase_to_original[j]==0])
    println("PREFIX ",prefix);report("BEFORE")
    changed=0
    for j in map.artificial_columns
        if phase.basis.states[j]!=JSimplex.BASIC && !iszero(phase.primal[j])
            phase.primal[j]=0;changed+=1
        end
    end
    println("SNAPPED ",changed)
    JSimplex._phase_refactor!(phase,original,()->false)
    report("REFACTORED")
    println("REPAIR ",JSimplex._complete_native_phase_transfer!(phase,()->false));report("REPAIRED")
    println("REMOVAL ",JSimplex.remove_artificials!(phase,map,original,phase.progress.numerical_policy,()->false),
        " iteration=",original.iterations," original_point=",JSimplex._legacy_primal_point_certified(original));flush(stdout)
end
foreach(probe,ARGS)
