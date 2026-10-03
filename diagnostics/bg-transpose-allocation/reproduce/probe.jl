using JSimplex, SparseArrays, Profile

function probe_bg_transpose()
    factor = JSimplex.BartelsGolubFactorization(spdiagm(0 => ones(64)))
    JSimplex.replace_column!(factor, ones(64), 1)
    rhs = ones(64)
    destination = similar(rhs)
    for _ in 1:5
        JSimplex.transpose_solve!(destination, factor, rhs)
    end
    bytes = [@allocated(JSimplex.transpose_solve!(destination, factor, rhs)) for _ in 1:5]
    println("Warmed public BTRAN bytes: ", bytes)
    Profile.Allocs.clear()
    Profile.Allocs.@profile sample_rate=1.0 JSimplex.transpose_solve!(destination, factor, rhs)
    allocations = Profile.Allocs.fetch().allocs
    println("Profiled allocation count: ", length(allocations))
    for allocation in allocations
        println("Allocation: ", allocation.size, " bytes, ", allocation.type)
        for frame in allocation.stacktrace
            occursin("triangular_", string(frame.file)) && println(frame)
        end
    end
    return nothing
end

probe_bg_transpose()
