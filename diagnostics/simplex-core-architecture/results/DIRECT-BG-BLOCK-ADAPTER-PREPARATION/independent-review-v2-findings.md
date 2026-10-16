# Independent review: blocking alias findings in strengthened tests

This preserves the second review; initial v1 is not retroactively changed. Candidate remains e8770ec8ef7e965a9d9c171703bffde37d388ec628354b8e5c408d07478f1190; amended tests are 9571e4500c078d4df395b5bcf7ced4e57eb58ec56dcaa947d6b110c4b34b8348. No Julia was executed.

Read installed /home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/base/abstractarray.jl as source text only. Line1588 defines mightalias with !isempty(A) && !isempty(B) before intersecting dataids; line1612 defines Memory dataids as UInt(A.ptr); line1613 uses the Array's ref.mem.

1. P2 correctness: _bbg_destination replaced exact destination===f.work rejection with only Base.mightalias. For dimension0, f.work is empty and mightalias returns false even for the identical object. Reference rejected this alias before dimensions/backend. Restore explicit identity rejection (for work and new scratch) in addition to mightalias, and add an empty-work sentinel assertion before backend access.
2. P2 test/API scope: newly added unsafe_wrap(Vector{Float64},pointer(scratch,2),3;own=false) has a separate Memory with its own offset pointer. mightalias compares start dataids, not pointer intervals, so that test's expected ArgumentError is unsupported by the current gate and will reach the RejectBackend dimension error. Use a supported shared-Memory Array slice alias, or deliberately implement/review pointer-interval overlap handling if arbitrary unsafe_wrap aliasing is intended. Do not claim the present mightalias gate detects the offset unsafe wrapper.

The full ledger was read and its owner inventory, nine explicit constructor-vector additions, source-work scaling, high-water costs and unknown runtime terms otherwise agree with reviewed code. Final source acceptance is withheld until these alias findings are resolved and exact final sources/stage are bound. Runtime remains wholly unexecuted.
