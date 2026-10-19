# UNEXECUTED preparation amendment. No factor object is accepted or retained here.
const PREPARATION_CALLS = Ref(0)
const PREPARATION_COMPLETED = Ref(0)
function prepare_gc!(cell::Int,fixture)
    require(PREPARATION_CALLS[] == PREPARATION_COMPLETED[] == cell-1,
            "Preparation order or repeated call")
    PREPARATION_CALLS[] += 1 # Attempt count survives a thrown GC/recording failure.
    measured = @timed GC.gc(true) # Exactly one fixed full request per completed warm cell.
    row = Dict{String,Any}(
        "phase"=>PHASE,"fixture"=>fixture,"cell"=>cell,
        "after_pair"=>3,"before_pair"=>4,"requested_full_gc"=>true,
        "calls"=>1,"cumulative_calls"=>PREPARATION_CALLS[],"returned"=>true,
        "seconds"=>measured.time,"bytes"=>measured.bytes,
        "events"=>Base.gc_alloc_count(measured.gcstats),"gc_seconds"=>measured.gctime,
        "compile_seconds"=>measured.compile_time,"recompile_seconds"=>measured.recompile_time,
        "gc_pauses"=>measured.gcstats.pause,"full_collections"=>measured.gcstats.full_sweep)
    save_window("preparation-$cell.toml",row)
    PREPARATION_COMPLETED[] += 1 # Completed means cost record successfully saved.
    nothing
end
